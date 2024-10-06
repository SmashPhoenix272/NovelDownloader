"""
NovelDownloader.py

This script downloads novels from translation websites using information from NovelUpdates.com.
It supports multiple translation sites through a modular structure and can bypass Cloudflare protection.
It also implements caching and EPUB export functionality.

Usage:
1. Run the script: python NovelDownloader.py
2. Follow the prompts to select the translation site and provide necessary URLs.
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
from source.genesistudio_site import GenesistudioSite
from source.NU_getchapterlink import NovelUpdatesChapterRetriever
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

    def download_novel_penguin_squad(self, translation_site_url):
        try:
            translation_site = PenguinSquadSite(self.page, self.cf_bypasser)
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

    def download_novel_genesistudio(self, novelupdates_url):
        try:
            if not self.login_to_novelupdates():
                logger.error("Failed to log in to NovelUpdates. Cannot proceed with download.")
                return

            translation_site = GenesistudioSite(self.page, self.cf_bypasser)
            logger.info(f"Retrieving chapter links from NovelUpdates: {novelupdates_url}")
            chapter_links = translation_site.get_chapter_links(novelupdates_url)
            self.total_chapters = len(chapter_links)
            
            logger.info(f"Found {self.total_chapters} chapters. Starting download...")
            for i, link in enumerate(tqdm(chapter_links, desc="Downloading chapters", unit="chapter")):
                cached_chapter = self.cache.get_cached_chapter(i)
                if cached_chapter:
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
                chapter.content = f"<h1>{title}</h1>{content}"
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

def validate_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

def get_translation_site():
    while True:
        choice = input("Select translation site (1 for PenguinSquad, 2 for Genesistudio): ").strip()
        if choice in ['1', '2']:
            return 'PenguinSquad' if choice == '1' else 'Genesistudio'
        print("Invalid choice. Please enter 1 or 2.")

def main():
    downloader = NovelDownloader()
    
    translation_site = get_translation_site()
    
    while True:
        novelupdates_url = input("Enter NovelUpdates URL: ")
        if validate_url(novelupdates_url):
            break
        logger.warning("Invalid URL. Please enter a valid URL.")

    downloader.get_novel_info(novelupdates_url)

    if translation_site == 'PenguinSquad':
        while True:
            translation_site_url = input("Enter PenguinSquad URL: ")
            if validate_url(translation_site_url):
                break
            logger.warning("Invalid URL. Please enter a valid URL.")
        downloader.download_novel_penguin_squad(translation_site_url)
    else:  # Genesistudio
        downloader.download_novel_genesistudio(novelupdates_url)

    downloader.save_novel_as_epub()

if __name__ == "__main__":
    main()
