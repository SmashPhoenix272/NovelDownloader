import re
import time
import logging
from bs4 import BeautifulSoup
from .base_translation_site import TranslationSite
from .NU_getchapterlink import NovelUpdatesChapterRetriever

logger = logging.getLogger(__name__)

class SkyDemonOrderSite(TranslationSite):
    def __init__(self, page, cf_bypasser, nu_retriever=None):
        super().__init__(page, cf_bypasser)
        self.base_url = "https://skydemonorder.com"
        if nu_retriever is None:
            self.nu_retriever = NovelUpdatesChapterRetriever(page, cf_bypasser)
        else:
            self.nu_retriever = nu_retriever

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

    def get_chapter_links(self, novelupdates_url):
        logger.info(f"Getting chapter links from {novelupdates_url}")
        
        # Login to NovelUpdates first
        if not self.nu_retriever.login():
            logger.error("Failed to log in to NovelUpdates")
            return []
            
        # Get chapter links from NovelUpdates
        chapter_links = self.nu_retriever.get_chapter_links(novelupdates_url)
        logger.info(f"Found {len(chapter_links)} chapters")
        return chapter_links

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
                return None, None

            # First try to get content directly
            title_element = soup.select_one('div.font-medium.text-sm')
            content_div = soup.select_one('div#chapter-body')

            # If content not found, might need age verification
            if not content_div:
                logger.info("Content not found, checking for age verification...")
                try:
                    # Try multiple selectors for the button
                    selectors = [
                        ('text', 'Yes'),  # by button text
                        ('css', 'button.bg-\\[\\#F65252\\]'),  # by class
                        ('xpath', '//button[contains(text(), "Yes")]')  # by xpath
                    ]
                    
                    page = self.cf_bypasser.driver
                    for method, selector in selectors:
                        try:
                            if method == 'text':
                                btn = page.ele('tag:button', text=selector, timeout=1)
                            elif method == 'css':
                                btn = page.ele(selector, timeout=1)
                            else:
                                btn = page.ele(selector, timeout=1)
                                
                            if btn and btn.style.display != 'none':
                                logger.info(f"Found age verification button using {method}")
                                btn.click(by_js=True)
                                time.sleep(1)
                                html_content = page.html
                                soup = BeautifulSoup(html_content, 'html.parser')
                                # Try to get content again after verification
                                title_element = soup.select_one('div.font-medium.text-sm')
                                content_div = soup.select_one('div#chapter-body')
                                break
                        except Exception as e:
                            logger.debug(f"Button not found with {method}: {str(e)}")
                            continue
                except Exception as e:
                    logger.debug(f"Error in age verification handling: {str(e)}")

            # Check if we have the title and content
            if not title_element:
                logging.warning(f"No title element found for URL: {url}")
                if attempt < max_retries - 1:
                    time.sleep(attempt + 1)
                    continue
                return None, None

            chapter_title = title_element.text.strip()
            logger.info(f"Extracted chapter title: {chapter_title}")

            if not content_div:
                logging.warning(f"No chapter body found for URL: {url}")
                if attempt < max_retries - 1:
                    time.sleep(attempt + 1)
                    continue
                return None, None

            # Convert the content to string
            content = str(content_div)
            
            if content:
                logger.info(f"Successfully extracted content for URL: {url}")
                return chapter_title, content
            else:
                logging.warning(f"Extracted content is empty for URL: {url}")
            
            if attempt < max_retries - 1:
                time.sleep(attempt + 1)

        logging.error(f"Failed to get content after {max_retries} attempts for URL: {url}")
        return None, None
