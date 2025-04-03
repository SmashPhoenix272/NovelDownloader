import os
import sys
import logging
from DrissionPage import ChromiumPage
from bs4 import BeautifulSoup
import re
from tqdm import tqdm
from urllib.parse import urlparse, unquote
from CloudflareBypasser import CloudflareBypasser
from source.translation_site import PenguinSquadSite, GenesistudioSite, ReadingPiaSite, ZetroTranslationSite, GadgetizedPandaSite
from source.skydemonorder_site import SkyDemonOrderSite
from source.penguin_squad_site import PaywallException
from source.NU_getchapterlink import NovelUpdatesChapterRetriever
from cache.novel_cache import NovelCache
from ebooklib import epub
import io
from collections import defaultdict

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
        self.nu_retriever = NovelUpdatesChapterRetriever(self.page, self.cf_bypasser)

    def login_to_novelupdates(self):
        logger.info("Attempting to log in to NovelUpdates")
        if self.nu_retriever.login():
            logger.info("Successfully logged in to NovelUpdates")
            return True
        else:
            logger.error("Failed to log in to NovelUpdates")
            return False

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

    def check_cache(self):
        cached_chapters = self.cache.get_all_cached_chapters()
        if cached_chapters:
            logger.info(f"Found {len(cached_chapters)} cached chapters for '{self.novel_info['title']}'")
            return True
        return False

    def download_novel_penguin_squad(self, translation_site_url, use_cache=False):
        try:
            translation_site = PenguinSquadSite(self.page, self.cf_bypasser, self.nu_retriever)
            logger.info(f"Retrieving chapter links from {translation_site_url}")
            chapter_links = translation_site.get_chapter_links(translation_site_url)
            self.total_chapters = len(chapter_links)
            
            logger.info(f"Found {self.total_chapters} chapters. Starting download...")
            for i, link in enumerate(tqdm(chapter_links, desc="Downloading chapters", unit="chapter")):
                cached_chapter = self.cache.get_cached_chapter(i)
                if use_cache and cached_chapter:
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

    def download_novel_genesistudio(self, novelupdates_url, use_cache=False):
        try:
            if not self.login_to_novelupdates():
                logger.error("Failed to log in to NovelUpdates. Cannot proceed with download.")
                return

            translation_site = GenesistudioSite(self.page, self.cf_bypasser, self.nu_retriever)
            logger.info(f"Retrieving chapter links from NovelUpdates: {novelupdates_url}")
            chapter_links = translation_site.get_chapter_links(novelupdates_url)
            self.total_chapters = len(chapter_links)
            
            logger.info(f"Found {self.total_chapters} chapters. Starting download...")
            for i, link in enumerate(tqdm(chapter_links, desc="Downloading chapters", unit="chapter")):
                cached_chapter = self.cache.get_cached_chapter(i)
                if use_cache and cached_chapter:
                    chapter_title, chapter_content = cached_chapter
                else:
                    try:
                        chapter_title, chapter_content = translation_site.get_chapter_content(link)
                        if chapter_title and chapter_content:
                            self.cache.cache_chapter(i, chapter_title, chapter_content)
                        else:
                            logger.warning(f"Failed to retrieve content for chapter {i+1}")
                            continue
                    except Exception as e:
                        logger.warning(f"Error downloading chapter {i+1}: {str(e)}")
                        continue
                
                self.novel_content.append((chapter_title, chapter_content))
            
            logger.info(f"Novel '{self.novel_info['title']}' has been downloaded. Total chapters: {self.total_chapters}")
        except Exception as e:
            logger.error(f"Error downloading novel from Genesistudio: {str(e)}")
            sys.exit(1)

    def download_novel_readingpia(self, translation_site_url, use_cache=False):
        try:
            translation_site = ReadingPiaSite(self.page, self.cf_bypasser, self.nu_retriever)
            logger.info(f"Retrieving chapter links from {translation_site_url}")
            chapter_links = translation_site.get_chapter_links(translation_site_url)
            self.total_chapters = len(chapter_links)
            
            logger.info(f"Found {self.total_chapters} chapters. Starting download...")
            for i, link in enumerate(tqdm(chapter_links, desc="Downloading chapters", unit="chapter")):
                cached_chapter = self.cache.get_cached_chapter(i)
                if use_cache and cached_chapter:
                    chapter_title, chapter_content = cached_chapter
                else:
                    try:
                        chapter_title, chapter_content = translation_site.get_chapter_content(link)
                        if not chapter_title:
                            chapter_title = f"Chapter {i+1}"
                        self.cache.cache_chapter(i, chapter_title, chapter_content)
                    except Exception as e:
                        logger.warning(f"Error downloading chapter {i+1}: {str(e)}")
                        continue
                
                self.novel_content.append((chapter_title, chapter_content))
            
            logger.info(f"Novel '{self.novel_info['title']}' has been downloaded. Total chapters: {self.total_chapters}")
        except Exception as e:
            logger.error(f"Error downloading novel from ReadingPia: {str(e)}")
            sys.exit(1)

    def download_novel_zetrotranslation(self, translation_site_url, use_cache=False):
        try:
            translation_site = ZetroTranslationSite(self.page, self.cf_bypasser, self.nu_retriever)
            logger.info(f"Retrieving chapter links from {translation_site_url}")
            chapter_links = translation_site.get_chapter_links(translation_site_url)
            self.total_chapters = len(chapter_links)
            
            logger.info(f"Found {self.total_chapters} chapters. Starting download...")
            for i, link in enumerate(tqdm(chapter_links, desc="Downloading chapters", unit="chapter")):
                cached_chapter = self.cache.get_cached_chapter(i)
                if use_cache and cached_chapter:
                    chapter_title, chapter_content = cached_chapter
                else:
                    try:
                        chapter_title, chapter_content = translation_site.get_chapter_content(link)
                        if chapter_title and chapter_content:
                            self.cache.cache_chapter(i, chapter_title, chapter_content)
                        else:
                            logger.warning(f"Failed to retrieve content for chapter {i+1}")
                            continue
                    except Exception as e:
                        logger.warning(f"Error downloading chapter {i+1}: {str(e)}")
                        continue
                
                self.novel_content.append((chapter_title, chapter_content))
            
            logger.info(f"Novel '{self.novel_info['title']}' has been downloaded. Total chapters: {self.total_chapters}")
        except Exception as e:
            logger.error(f"Error downloading novel from Zetrotranslation: {str(e)}")
            sys.exit(1)

    def download_novel_skydemonorder(self, novelupdates_url, use_cache=False):
        try:
            if not self.login_to_novelupdates():
                logger.error("Failed to log in to NovelUpdates. Cannot proceed with download.")
                return

            translation_site = SkyDemonOrderSite(self.page, self.cf_bypasser, self.nu_retriever)
            logger.info(f"Retrieving chapter links from NovelUpdates: {novelupdates_url}")
            chapter_links = translation_site.get_chapter_links(novelupdates_url)
            self.total_chapters = len(chapter_links)
            
            logger.info(f"Found {self.total_chapters} chapters. Starting download...")
            for i, link in enumerate(tqdm(chapter_links, desc="Downloading chapters", unit="chapter")):
                cached_chapter = self.cache.get_cached_chapter(i)
                if use_cache and cached_chapter:
                    chapter_title, chapter_content = cached_chapter
                else:
                    try:
                        chapter_title, chapter_content = translation_site.get_chapter_content(link)
                        if chapter_title and chapter_content:
                            self.cache.cache_chapter(i, chapter_title, chapter_content)
                        else:
                            logger.warning(f"Failed to retrieve content for chapter {i+1}")
                            continue
                    except Exception as e:
                        logger.warning(f"Error downloading chapter {i+1}: {str(e)}")
                        continue
                
                self.novel_content.append((chapter_title, chapter_content))
            
            logger.info(f"Novel '{self.novel_info['title']}' has been downloaded. Total chapters: {self.total_chapters}")
        except Exception as e:
            logger.error(f"Error downloading novel from SkyDemonOrder: {str(e)}")
            sys.exit(1)

    def download_novel_gadgetizedpanda(self, novelupdates_url, use_cache=False):
        try:
            if not self.login_to_novelupdates():
                logger.error("Failed to log in to NovelUpdates. Cannot proceed with download.")
                return

            translation_site = GadgetizedPandaSite(self.page, self.cf_bypasser, self.novel_info['title'], self.nu_retriever)
            logger.info(f"Retrieving chapter links from NovelUpdates: {novelupdates_url}")
            chapter_links = translation_site.get_chapter_links(novelupdates_url)
            self.total_chapters = len(chapter_links)
            
            logger.info(f"Found {self.total_chapters} chapters. Starting download...")
            
            # Dictionary to store chapter parts
            chapter_parts = defaultdict(list)
            
            # First pass: Download all chapters and organize parts
            for i, link in enumerate(tqdm(chapter_links, desc="Downloading chapters", unit="chapter")):
                cached_chapter = self.cache.get_cached_chapter(link)
                if use_cache and cached_chapter:
                    chapter_title, chapter_content, chapter_images = cached_chapter
                else:
                    try:
                        chapter_title, (chapter_content, chapter_images) = translation_site.get_chapter_content(link)
                        if chapter_title and chapter_content:
                            self.cache.cache_chapter(link, chapter_title, chapter_content, chapter_images)
                        else:
                            logger.warning(f"Failed to retrieve content for chapter {i+1}")
                            continue
                    except Exception as e:
                        logger.warning(f"Error downloading chapter {i+1}: {str(e)}")
                        continue
                
                # Extract volume, chapter, and part numbers
                if "Light Novel Illustrations" in chapter_title:
                    # Extract volume number from illustration chapter title
                    vol_match = re.match(r'Volume (\d+) -', chapter_title)
                    if vol_match:
                        vol_num = vol_match.group(1)
                        # Use a special key format for illustrations to ensure proper ordering
                        key = f'Volume {vol_num} Chapter 0'  # Place illustrations at start of volume
                        chapter_parts[key] = [(0, chapter_title, chapter_content, chapter_images)]
                    else:
                        # If no volume number found, add to novel_content directly
                        self.novel_content.append((chapter_title, chapter_content, chapter_images))
                else:
                    match = re.match(r'Volume (\d+) Chapter (\d+)(?:\s+part (\d+))?', chapter_title)
                    if match:
                        vol_num, chap_num = match.group(1), match.group(2)
                        part_num = match.group(3) if match.group(3) else '1'
                        key = f'Volume {vol_num} Chapter {chap_num}'
                        if key not in chapter_parts:
                            chapter_parts[key] = []
                        chapter_parts[key].append((int(part_num), chapter_title, chapter_content, chapter_images))
                    else:
                        # Handle any other non-standard chapter titles
                        self.novel_content.append((chapter_title, chapter_content, chapter_images))
            
            # Second pass: Sort chapters by volume and chapter number
            sorted_chapters = sorted(chapter_parts.items(), key=lambda x: (
                int(re.match(r'Volume (\d+) Chapter (\d+)', x[0]).group(1)),  # Volume number
                int(re.match(r'Volume (\d+) Chapter (\d+)', x[0]).group(2))   # Chapter number
            ))
            
            # Add sorted chapters to novel_content
            for chapter_key, parts in sorted_chapters:
                # Sort parts by part number
                parts.sort(key=lambda x: x[0])
                
                # Use original title for illustrations, otherwise combine parts
                if "Light Novel Illustrations" in parts[0][1]:
                    combined_title = parts[0][1]  # Use the original illustration title
                else:
                    # If only one part exists and it's part 1, use original title without "part 1"
                    if len(parts) == 1 and parts[0][0] == 1:
                        combined_title = chapter_key
                    else:
                        combined_title = chapter_key + f" (Parts 1-{len(parts)})"
                
                # Combine content from all parts
                combined_content = ""
                combined_images = []
                for _, title, content, images in parts:
                    if combined_content:
                        combined_content += f"<div class='part-divider'></div>"
                    combined_content += content
                    combined_images.extend(images)
                
                self.novel_content.append((combined_title, combined_content, combined_images))
            
            logger.info(f"Novel '{self.novel_info['title']}' has been downloaded. Total chapters: {len(chapter_parts)}")
        except Exception as e:
            logger.error(f"Error downloading novel from GadgetizedPanda: {str(e)}")
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
            
            # Add CSS styles
            style = '''
                /* Base styles */
                body {
                    font-family: "Noto Serif", "DejaVu Serif", "Droid Serif", serif;
                    font-size: 1em;
                    line-height: 1.6;
                    color: #333333;
                    margin: 1.25em auto;
                    padding: 0 1em;
                }

                /* Headings */
                h1, h2, h3, h4, h5, h6 {
                    font-family: "Noto Sans", "DejaVu Sans", "Droid Sans", sans-serif;
                    color: #292929;
                    margin-top: 1.25em;
                    margin-bottom: 0.7em;
                    line-height: 1.3;
                }

                /* Paragraphs */
                p {
                    margin-bottom: 1em;
                    text-align: justify;
                }

                /* Links */
                a {
                    color: #0066cc;
                    text-decoration: underline;
                }

                /* Lists */
                ul, ol {
                    margin: 1em 0;
                    padding-left: 2em;
                }

                li {
                    margin-bottom: 0.5em;
                }

                /* Blockquotes */
                blockquote {
                    margin: 1em 2em;
                    padding-left: 1em;
                    border-left: 3px solid #cccccc;
                    font-style: italic;
                }

                /* Code blocks */
                code, pre {
                    font-family: "DejaVu Sans Mono", "Droid Sans Mono", monospace;
                    background-color: #f5f5f5;
                    padding: 0.3em;
                }

                /* Tables */
                table {
                    width: 100%;
                    margin: 1em 0;
                    border-collapse: collapse;
                }

                th, td {
                    border: 1px solid #dddddd;
                    padding: 0.5em;
                }

                /* Images */
                img {
                    max-width: 100%;
                    height: auto;
                    display: block;
                    margin: 1em auto;
                }

                /* Utility classes */
                .part-divider {
                    text-align: center;
                    margin: 2em 0;
                    border-top: 1px solid #cccccc;
                }

                .scene-break {
                    text-align: center;
                    margin: 1em 0;
                    color: #666666;
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

                /* Reading enhancements */
                html {
                    text-rendering: optimizeLegibility;
                    -webkit-font-smoothing: antialiased;
                }

                /* Footnotes */
                .footnote {
                    font-size: 0.8em;
                    color: #666666;
                }

                sup {
                    vertical-align: super;
                    font-size: 0.8em;
                }
            '''
            nav_css = epub.EpubItem(
                uid="style_nav",
                file_name="style/nav.css",
                media_type="text/css",
                content=style
            )
            book.add_item(nav_css)
            
            # Create images directory in EPUB
            images_added = set()
            
            # Add chapters
            logger.info("Adding novel chapters")
            chapters = []
            for i, chapter_data in enumerate(self.novel_content):
                if len(chapter_data) == 3:  # GadgetizedPanda format with images
                    title, content, images = chapter_data
                    # Add images to the book
                    for img_filename, img_data in images:
                        if img_filename not in images_added:
                            epub_image = epub.EpubItem(
                                file_name=f"images/{img_filename}",
                                content=img_data,
                                media_type="image/jpeg"
                            )
                            book.add_item(epub_image)
                            images_added.add(img_filename)
                else:  # Standard format without images
                    title, content = chapter_data
                
                chapter = epub.EpubHtml(title=title, file_name=f'chapter_{i+1}.xhtml', lang='en')
                chapter.content = f"<h1>{title}</h1>{content}"
                chapter.add_item(nav_css)
                book.add_item(chapter)
                chapters.append(chapter)
            
            # Define Table of Contents
            book.toc = [epub.Link('info.xhtml', 'Novel Information', 'intro')]
            book.toc.extend(chapters)
            
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

    def validate_url(self, url):
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except ValueError:
            return False

    def get_translation_site(self):
        while True:
            print("\nAvailable translation sites:")
            print("1. Penguin Squad")
            print("2. Genesis Studio")
            print("3. Reading Pia")
            print("4. Zetrotranslation")
            print("5. GadgetizedPanda")
            print("6. SkyDemonOrder")
            choice = input("\nSelect translation site (1-6): ")
            
            if choice == "1":
                return "penguin_squad"
            elif choice == "2":
                return "genesistudio"
            elif choice == "3":
                return "readingpia"
            elif choice == "4":
                return "zetrotranslation"
            elif choice == "5":
                return "gadgetizedpanda"
            elif choice == "6":
                return "skydemonorder"
            else:
                print("Invalid choice. Please try again.")

def main():
    try:
        downloader = NovelDownloader()
        
        novelupdates_url = input("Enter NovelUpdates URL: ")
        if not downloader.validate_url(novelupdates_url):
            logger.warning("Invalid URL. Please enter a valid URL.")
            return
            
        downloader.get_novel_info(novelupdates_url)
        
        translation_site = downloader.get_translation_site()
        if translation_site not in ["zetrotranslation", "gadgetizedpanda", "skydemonorder"]:
            translation_site_url = input("Enter translation site URL: ")
            if not downloader.validate_url(translation_site_url):
                logger.warning("Invalid URL. Please enter a valid URL.")
                return
        else:
            translation_site_url = novelupdates_url
            
        use_cache = False
        if downloader.check_cache():
            while True:
                choice = input("Cache found. Do you want to use the existing cache? (y/n): ").strip().lower()
                if choice in ['y', 'n']:
                    use_cache = (choice == 'y')
                    break
                print("Invalid choice. Please enter 'y' or 'n'.")
        
        if translation_site == "penguin_squad":
            downloader.download_novel_penguin_squad(translation_site_url, use_cache)
        elif translation_site == "genesistudio":
            downloader.download_novel_genesistudio(novelupdates_url, use_cache)
        elif translation_site == "readingpia":
            downloader.download_novel_readingpia(translation_site_url, use_cache)
        elif translation_site == "zetrotranslation":
            downloader.download_novel_zetrotranslation(novelupdates_url, use_cache)
        elif translation_site == "gadgetizedpanda":
            downloader.download_novel_gadgetizedpanda(novelupdates_url, use_cache)
        elif translation_site == "skydemonorder":
            downloader.download_novel_skydemonorder(novelupdates_url, use_cache)
        
        downloader.save_novel_as_epub()
        print("\nDone! EPUB file has been created.")
        
    except KeyboardInterrupt:
        print("\nDownload cancelled by user.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
