"""
NovelDownloader.py

This script downloads novels from translation websites using information from NovelUpdates.com.
It supports multiple translation sites through a modular structure and can bypass Cloudflare protection.
It also implements caching and EPUB export functionality.

Usage:
1. Run the script: python NovelDownloader.py [NovelUpdates URL] [Translation Site URL]
2. If URLs are not provided as arguments, you will be prompted to enter them.
3. The script will download the novel, cache the content, and save it as an EPUB file.
"""

import os
import sys
import logging
from DrissionPage import ChromiumPage
from bs4 import BeautifulSoup
import re
from tqdm import tqdm
from urllib.parse import urlparse, unquote
from CloudflareBypasser import CloudflareBypasser
from source.translation_site import PenguinSquadSite
from source.penguin_squad_site import PaywallException
from cache.novel_cache import NovelCache
from ebooklib import epub
import io

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NovelDownloader:
    def __init__(self):
        self.page = ChromiumPage()
        self.cf_bypasser = CloudflareBypasser(self.page)
        self.novel_info = {}
        self.novel_content = []
        self.total_chapters = 0
        self.cache = None

    def get_novel_info(self, novelupdates_url):
        logger.info(f"Retrieving novel information from {novelupdates_url}")
        self.page.get(novelupdates_url)
        self.cf_bypasser.bypass()
        html_content = self.page.html
        
        if not html_content:
            logger.error("Failed to retrieve novel information. Exiting.")
            sys.exit(1)
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        try:
            self.novel_info['title'] = soup.find('meta', property='og:title')['content']
            self.novel_info['cover'] = soup.find('meta', property='og:image')['content']
            self.novel_info['author'] = soup.find('a', id='authtag').text
            self.novel_info['type'] = soup.find('a', class_='genre type').text
            
            associated_names = soup.find('div', id='editassociated').text.split('<br>')
            self.novel_info['associated_names'] = [name.strip() for name in associated_names if name.strip()]
            
            self.novel_info['genre'] = ', '.join([tag.text.strip() for tag in soup.find('div', {'id': 'seriesgenre'}).find_all('a', {'class': 'genre'})])
            self.novel_info['tags'] = ', '.join([tag.text.strip() for tag in soup.find('div', {'id': 'showtags'}).find_all('a', {'class': 'genre'})])
            self.novel_info['description'] = soup.find('meta', property='og:description')['content']
            
            logger.info(f"Successfully retrieved information for novel: {self.novel_info['title']}")
        except Exception as e:
            logger.error(f"Error parsing novel information: {str(e)}")
            sys.exit(1)

        self.cache = NovelCache(self.novel_info['title'])
        self.cache.cache_novel_info(self.novel_info)

    def download_novel(self, translation_site, translation_site_url):
        try:
            logger.info(f"Retrieving chapter links from {translation_site_url}")
            chapter_links = translation_site.get_chapter_links(translation_site_url)
            self.total_chapters = len(chapter_links)
            
            logger.info(f"Found {self.total_chapters} chapters. Starting download...")
            for i, link in enumerate(tqdm(chapter_links, desc="Downloading chapters", unit="chapter")):
                cached_chapter = self.cache.get_cached_chapter(i)
                if cached_chapter:
                    chapter_title, chapter_content = cached_chapter
                else:
                    try:
                        chapter_title, chapter_content = translation_site.get_chapter_content(link)
                        self.cache.cache_chapter(i, chapter_title, chapter_content)
                    except PaywallException as e:
                        logger.warning(f"{str(e)}")
                        self.total_chapters = i
                        break
                
                self.novel_content.append((chapter_title, chapter_content))
            
            logger.info(f"Novel '{self.novel_info['title']}' has been downloaded. Total chapters: {self.total_chapters}")
        except Exception as e:
            logger.error(f"Error downloading novel: {str(e)}")
            sys.exit(1)

    def save_novel_as_epub(self):
        try:
            logger.info(f"Creating EPUB for novel: {self.novel_info['title']}")
            book = epub.EpubBook()
            
            # Set metadata
            book.set_identifier(self.novel_info['title'])
            book.set_title(self.novel_info['title'])
            book.set_language('en')
            book.add_author(self.novel_info['author'])
            
            # Add cover
            try:
                logger.info("Downloading cover image")
                self.page.get(self.novel_info['cover'])
                self.cf_bypasser.bypass()
                
                # Download the image and get the file path from DrissionPage
                self.page.download(self.novel_info['cover'])
                cover_path = os.path.join(os.getcwd(), os.path.basename(self.novel_info['cover']))
                
                logger.info(f"Cover image downloaded to: {cover_path}")
                
                # Read the content of the downloaded file
                with open(cover_path, 'rb') as cover_file:
                    cover_content = cover_file.read()
                
                if cover_content:
                    book.set_cover("cover.jpg", cover_content)
                    logger.info("Cover image successfully added to EPUB")
                else:
                    logger.warning("Failed to read cover image content.")
                
                # Delete the downloaded file
                os.remove(cover_path)
                logger.info("Downloaded cover file deleted")
                
            except Exception as e:
                logger.warning(f"Failed to download or process cover image. Error: {str(e)}")
                logger.info("Continuing without cover image.")
            
            # Add info chapter
            logger.info("Adding novel information chapter")
            info_content = f"<h1>{self.novel_info['title']}</h1>"
            info_content += f"<p><strong>Author:</strong> {self.novel_info['author']}</p>"
            info_content += f"<p><strong>Type:</strong> {self.novel_info['type']}</p>"
            info_content += f"<p><strong>Genre:</strong> {self.novel_info['genre']}</p>"
            info_content += f"<p><strong>Tags:</strong> {self.novel_info['tags']}</p>"
            info_content += f"<p><strong>Description:</strong> {self.novel_info['description']}</p>"
            
            info_chapter = epub.EpubHtml(title='Novel Information', file_name='info.xhtml', lang='en')
            info_chapter.content = info_content
            book.add_item(info_chapter)
            
            # Add chapters
            logger.info("Adding novel chapters")
            chapters = []
            for i, (title, content) in enumerate(self.novel_content):
                chapter = epub.EpubHtml(title=title, file_name=f'chapter_{i+1}.xhtml', lang='en')
                
                # Convert content to proper HTML
                formatted_content = self.format_chapter_content(content)
                
                chapter.content = f"<h1>{title}</h1>{formatted_content}"
                book.add_item(chapter)
                chapters.append(chapter)
            
            # Define Table of Contents
            book.toc = (epub.Link('info.xhtml', 'Novel Information', 'intro'),
                        (epub.Section('Chapters'), chapters))
            
            # Add default NCX and Nav file
            book.add_item(epub.EpubNcx())
            book.add_item(epub.EpubNav())
            
            # Define spine
            book.spine = ['nav', info_chapter] + chapters
            
            # Create filename
            filename = f"{self.novel_info['title']} - {self.total_chapters} chapters.epub"
            filename = re.sub(r'[^\w\-_\. ]', '_', filename)  # Replace invalid filename characters
            
            # Write EPUB file
            logger.info(f"Writing EPUB file: {filename}")
            epub.write_epub(filename, book, {})
            
            logger.info(f"Novel '{self.novel_info['title']}' has been saved as '{filename}'.")
        except Exception as e:
            logger.error(f"Error saving novel as EPUB: {str(e)}")
            sys.exit(1)

    def format_chapter_content(self, content):
        # Check if content is already HTML
        if content.strip().startswith('<') and content.strip().endswith('>'):
            # Content is already HTML, return as is
            return content
        
        # Convert line breaks to paragraph tags
        paragraphs = content.split('\n')
        formatted_content = ''.join([f'<p>{p.strip()}</p>' for p in paragraphs if p.strip()])
        
        return formatted_content

def validate_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

def main():
    downloader = NovelDownloader()
    
    if len(sys.argv) == 3:
        novelupdates_url = sys.argv[1]
        translation_site_url = sys.argv[2]
    else:
        while True:
            novelupdates_url = input("Enter NovelUpdates URL: ")
            if validate_url(novelupdates_url):
                break
            logger.warning("Invalid URL. Please enter a valid URL.")

        while True:
            translation_site_url = input("Enter translation site URL: ")
            if validate_url(translation_site_url):
                break
            logger.warning("Invalid URL. Please enter a valid URL.")

    # For now, we're using PenguinSquadSite as an example
    translation_site = PenguinSquadSite(downloader.page, downloader.cf_bypasser)

    downloader.get_novel_info(novelupdates_url)
    downloader.download_novel(translation_site, translation_site_url)
    downloader.save_novel_as_epub()

if __name__ == "__main__":
    main()
