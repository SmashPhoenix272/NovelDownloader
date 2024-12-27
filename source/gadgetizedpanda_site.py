from bs4 import BeautifulSoup
import logging
import re
import os
import uuid
import time
from urllib.parse import urljoin
from .base_translation_site import TranslationSite
from .NU_getchapterlink import NovelUpdatesChapterRetriever
from cache.novel_cache import NovelCache

logger = logging.getLogger(__name__)

class GadgetizedPandaSite(TranslationSite):
    def __init__(self, page, cf_bypasser, novel_title=None, nu_retriever=None):
        super().__init__(page, cf_bypasser)
        self.nu_retriever = nu_retriever or NovelUpdatesChapterRetriever(page, cf_bypasser)
        self.novel_title = novel_title
        self.cache = NovelCache(novel_title) if novel_title else None

    def get_chapter_links(self, novelupdates_url):
        logger.info(f"Getting chapter links from {novelupdates_url}")
        return self.nu_retriever.get_chapter_links(novelupdates_url)

    def get_novel_info(self, novelupdates_url):
        logger.info(f"Getting novel info from {novelupdates_url}")
        return self.nu_retriever.get_novel_info(novelupdates_url)

    def download_image(self, img_url):
        """Download image and return the image data"""
        # Check cache first if available
        if self.cache:
            cached_image = self.cache.get_cached_image(img_url)
            if cached_image:
                logger.info(f"Using cached image for {img_url}")
                return cached_image

        try:
            logger.info(f"Downloading image from {img_url}")
            
            # Use curl headers for imgur to avoid rate limiting
            headers = {}
            if 'imgur.com' in img_url:
                headers = {
                    "user-agent": "curl/7.84.0",
                    "accept": "*/*"
                }
            
            # Use DrissionPage's session to get the image
            response = self.page.session.get(img_url, headers=headers)
            if response.status_code == 200:
                img_data = response.content
                # Generate a unique filename for the image
                img_ext = os.path.splitext(img_url)[1]
                if not img_ext:
                    img_ext = '.jpg'  # Default to jpg if no extension found
                img_filename = f"image_{uuid.uuid4().hex[:8]}{img_ext}"
                
                # Cache the image if caching is enabled
                if self.cache:
                    self.cache.cache_image(img_url, img_filename, img_data)
                
                return img_filename, img_data
            else:
                logger.error(f"Failed to download image from {img_url}: HTTP {response.status_code}")
                return None, None
                
        except Exception as e:
            logger.error(f"Failed to download image from {img_url}: {str(e)}")
            return None, None

    def get_chapter_content(self, url):
        """Get chapter content with caching"""
        # Check cache first if available
        if self.cache:
            cached_chapter = self.cache.get_cached_chapter(url)
            if cached_chapter:
                logger.info(f"Using cached content for {url}")
                return cached_chapter[0], (cached_chapter[1], cached_chapter[2])

        logger.info(f"Getting chapter content from {url}")
        self.page.get(url)
        self.cf_bypasser.bypass()
        html_content = self.page.html
        
        if not html_content:
            logger.error("Failed to retrieve chapter content")
            return None, None
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Get chapter title
        title_element = soup.select_one('h1.entry-title')
        if not title_element:
            logger.error("Could not find chapter title")
            return None, None
            
        # Extract chapter info using regex
        title_text = title_element.text.strip()
        # Replace &nbsp; with regular space in the title text
        title_text = title_text.replace('\xa0', ' ')
        
        # Get chapter content
        content_div = soup.select_one('div.entry-content')
        if not content_div:
            logger.error("Could not find chapter content")
            return None, None
        
        # Check if this is an illustration chapter
        is_illustration = "light novel illustrations" in title_text.lower()
        if is_illustration:
            chapter_title = "Light Novel Illustrations"
            # Try to extract volume number from content
            volume_header = content_div.find('p', class_='has-large-font-size')
            if volume_header and 'VOLUME' in volume_header.text.upper():
                volume_match = re.search(r'VOLUME\s+(\d+)', volume_header.text.upper())
                if volume_match:
                    chapter_title = f"Volume {volume_match.group(1)} - {chapter_title}"
        else:
            # Updated regex pattern to handle spaces more flexibly
            chapter_info_match = re.search(r'Volume\s+\d+\s+Chapter\s+\d+(?:\s+part\s+\d+)?', title_text)
            chapter_title = chapter_info_match.group(0) if chapter_info_match else "Untitled Chapter"
        
        # Remove unwanted elements
        for element in content_div.select('p.has-black-color'):
            element.decompose()
            
        # Find the end marker and remove it along with everything after
        end_marker = content_div.find('h2', style='text-align: center;')
        if not end_marker:
            # Try alternative end marker
            for p in content_div.find_all('p'):
                if p.get_text().strip() == "BUY THE SOURCE MATERIAL TO SUPPORT THE AUTHOR !!!":
                    end_marker = p
                    break
        
        if end_marker:
            for element in end_marker.find_all_next():
                element.decompose()
            end_marker.decompose()
        
        # Process images and clean up HTML
        downloaded_images = []
        
        # Convert hr tags to more semantic dividers
        for hr in content_div.find_all('hr', class_='wp-block-separator'):
            divider = soup.new_tag('div')
            divider['class'] = 'scene-break'
            divider.string = '* * *'
            hr.replace_with(divider)
            
        # Clean up empty paragraphs and normalize spacing
        for p in content_div.find_all('p'):
            text = p.get_text().strip()
            if text == '' or text.isspace():
                p.decompose()
            elif text == 'scene transition':
                # Nullify the scene transition text
                p.decompose()
                
        # Process images
        for figure in content_div.find_all('figure', class_='wp-block-image'):
            img = figure.find('img')
            if img:
                # Get the highest resolution image URL from srcset if available
                img_url = None
                if img.get('srcset'):
                    srcset = img['srcset']
                    # Parse srcset and get the URL with the highest width
                    urls = [s.strip().split() for s in srcset.split(',')]
                    highest_res_url = max(urls, key=lambda x: int(x[1].replace('w', '')))[0]
                    img_url = highest_res_url
                else:
                    img_url = img.get('src')

                if img_url:
                    # Make sure the URL is absolute
                    img_url = urljoin(url, img_url)
                    # Download the image
                    img_filename, img_data = self.download_image(img_url)
                    if img_filename and img_data:
                        downloaded_images.append((img_filename, img_data))
                        # Create a new div for the image
                        img_div = soup.new_tag('div')
                        img_div['class'] = 'epub-image-container'
                        
                        # Create new img tag with clean attributes
                        new_img = soup.new_tag('img')
                        new_img['src'] = f"images/{img_filename}"  # Update path to match EPUB structure
                        new_img['alt'] = img.get('alt', '')
                        
                        img_div.append(new_img)
                        figure.replace_with(img_div)
                    else:
                        # If image download failed, remove the figure
                        figure.decompose()
                else:
                    figure.decompose()
            else:
                figure.decompose()
                
        # Add CSS for scene breaks and images
        style_tag = soup.new_tag('style')
        style_tag.string = '''
            .scene-break {
                text-align: center;
                margin: 1em 0;
                color: #666;
            }
            .epub-image-container {
                text-align: center;
                margin: 1em 0;
            }
            .epub-image-container img {
                max-width: 100%;
                height: auto;
                display: block;
                margin: 0 auto;
            }
        '''
        content_div.insert(0, style_tag)
                    
        # Keep HTML structure for proper styling
        chapter_content = str(content_div)
        
        # Cache the chapter content and images if caching is enabled
        if self.cache:
            self.cache.cache_chapter(url, chapter_title, chapter_content, downloaded_images)
        
        return chapter_title, (chapter_content, downloaded_images)

    def __del__(self):
        if self.cache:
            self.cache.close()
