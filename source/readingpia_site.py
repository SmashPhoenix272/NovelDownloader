import re
import time
import logging
from bs4 import BeautifulSoup
from .base_translation_site import TranslationSite

class ReadingPiaSite(TranslationSite):
    def __init__(self, page, cf_bypasser):
        super().__init__(page, cf_bypasser)
        self.base_url = "https://www.readingpia.me"

    def get_soup(self, url):
        logging.info(f"Fetching content for URL: {url}")
        try:
            self.cf_bypasser.driver.get(url)
            self.cf_bypasser.bypass()
            
            if self.cf_bypasser.is_bypassed():
                content = self.cf_bypasser.driver.html
                return BeautifulSoup(content, 'html.parser')
            else:
                logging.error(f"Failed to bypass Cloudflare for URL: {url}")
                return None
        except Exception as e:
            logging.error(f"Error while fetching content for URL {url}: {str(e)}")
            return None

    def get_chapter_links(self, url):
        logging.info(f"Getting chapter links for URL: {url}")
        soup = self.get_soup(url)
        if not soup:
            logging.error(f"Failed to get soup for URL: {url}")
            return []

        chapter_list = soup.find('div', class_='chapter-list')
        if not chapter_list:
            logging.warning(f"No chapter list found for URL: {url}")
            return []

        links = []
        seen_links = set()
        for chapter in chapter_list.find_all('a'):
            try:
                if 'href' not in chapter.attrs:
                    logging.warning(f"Found 'a' tag without 'href' attribute: {chapter}")
                    continue
                
                href = chapter['href']
                if not href.startswith('/'):
                    logging.warning(f"Invalid href found: {href}")
                    continue

                link = self.base_url + href
                if link not in seen_links:
                    links.append(link)
                    seen_links.add(link)
                    logging.debug(f"Added chapter link: {link}")
            except Exception as e:
                logging.error(f"Error processing chapter link: {str(e)}")

        # Reverse the order as the site shows latest chapters first
        links.reverse()
        logging.info(f"Found {len(links)} chapter links")
        return links

    def get_chapter_content(self, url):
        max_retries = 3
        for attempt in range(max_retries):
            logging.info(f"Attempting to get content for URL: {url} (Attempt {attempt + 1}/{max_retries})")
            soup = self.get_soup(url)
            if not soup:
                logging.warning(f"Failed to get soup for URL: {url}")
                if attempt < max_retries - 1:
                    time.sleep(attempt + 1)
                    continue
                return "", ""

            chapter_body = soup.find('div', class_='chapter-body')
            if not chapter_body:
                logging.warning(f"No chapter body found for URL: {url}")
                if attempt < max_retries - 1:
                    time.sleep(attempt + 1)
                    continue
                return "", ""

            # Extract chapter title
            title_tag = chapter_body.find('strong')
            chapter_title = title_tag.get_text(strip=True) if title_tag else ""
            logging.info(f"Extracted chapter title: {chapter_title}")

            # Remove the title from the chapter body
            if title_tag:
                title_tag.decompose()

            # Remove ads
            for ad in chapter_body.find_all('div', class_='m_ad_code'):
                ad.decompose()

            # Convert the chapter body to a string for easier text manipulation
            content = str(chapter_body)

            # 1. Remove "Join Discord" text
            content = re.sub(r'Join Discord', '', content, flags=re.IGNORECASE)

            # 2. Remove "[ Join Our Discord to </a> ]"
            content = re.sub(r'\[ Join Our Discord for regular updates and have fun with other community members: <a href="(https://discord\.com/invite/\S+)">\1</a> \]', '', content)

            # 3. Remove Discord invite links
            content = re.sub(r'https://discord\.com/invite/\w{10}', '', content)

            # 4. Remove unnecessary div with text-align: center
            content = re.sub(r'<div class="chapter-body" data-theme="default" id="chapter-body" style="">\s*<div style="text-align: center;">', '<div class="chapter-body" data-theme="default" id="chapter-body" style="">', content)

            # Convert the content back to BeautifulSoup object
            chapter_body = BeautifulSoup(content, 'html.parser')

            content = str(chapter_body).strip()
            if content:
                logging.info(f"Successfully extracted content for URL: {url}")
                return chapter_title, content
            else:
                logging.warning(f"Extracted content is empty for URL: {url}")
            
            if attempt < max_retries - 1:
                time.sleep(attempt + 1)

        logging.error(f"Failed to get content after {max_retries} attempts for URL: {url}")
        return "", ""
