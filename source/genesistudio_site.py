from DrissionPage import ChromiumPage
import logging
from .NU_getchapterlink import NovelUpdatesChapterRetriever
import time
from selenium.common.exceptions import TimeoutException
import re

logger = logging.getLogger(__name__)

class GenesistudioSite:
    def __init__(self, page: ChromiumPage, cf_bypasser):
        self.page = page
        self.cf_bypasser = cf_bypasser
        self.nu_retriever = NovelUpdatesChapterRetriever(page, cf_bypasser)

    def get_chapter_links(self, novelupdates_url):
        if self.nu_retriever.login():
            return self.nu_retriever.get_chapter_links(novelupdates_url)
        else:
            logger.error("Failed to log in to NovelUpdates. Cannot retrieve chapter links.")
            return []

    def get_chapter_content(self, chapter_url, max_retries=3, retry_delay=5):
        """
        Retrieves the chapter content from a Genesis Studio URL.
        Implements a retry mechanism to handle potential failures.
        """
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempt {attempt + 1} to get chapter content from {chapter_url}")
                self.page.get(chapter_url)
                logger.info("Attempting to bypass Cloudflare challenge")
                self.cf_bypasser.bypass()
                
                # Add a small delay to allow for any redirects
                time.sleep(2)
                
                redirected_url = self.page.url
                logger.info(f"Redirected URL: {redirected_url}")
                
                if 'genesistudio.com' not in redirected_url:
                    logger.warning(f"Expected Genesis Studio URL, but got: {redirected_url}")
                    continue
                
                if not self.wait_for_genesis_studio_page():
                    logger.error("Failed to load Genesis Studio page")
                    continue
                
                chapter_title, chapter_content = self.extract_genesistudio_content()
                
                if chapter_content:
                    return chapter_title, chapter_content
                
                logger.warning(f"Attempt {attempt + 1} failed to retrieve content. Retrying...")
            except Exception as e:
                logger.error(f"Error in attempt {attempt + 1} getting chapter content from {chapter_url}: {str(e)}")
            
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
        
        logger.error(f"Failed to retrieve chapter content after {max_retries} attempts")
        return None, None

    def extract_genesistudio_content(self):
        logger.info("Extracting content from Genesis Studio page")
        
        # Extract chapter title
        title_element = self.page.ele('main h1.sr-only', timeout=2)
        if title_element:
            full_title = title_element.text.strip()
            logger.info(f"Found title element. Full title: '{full_title}'")
        else:
            # Fallback to searching in the entire HTML
            html_content = self.page.html
            title_match = re.search(r'<h1 class="sr-only">(.*?)</h1>', html_content)
            if title_match:
                full_title = title_match.group(1).strip()
                logger.info(f"Found title in HTML. Full title: '{full_title}'")
            else:
                full_title = "Unknown Title"
                logger.warning("Failed to find title element (main h1.sr-only) and in HTML")

        # Extract chapter number and name
        match = re.search(r'Read .+ - Chapter (\d+)(?::\s*(.+))? \|', full_title)
        if match:
            chapter_number = match.group(1)
            chapter_name = match.group(2) if match.group(2) else ""
            chapter_title = f"Chapter {chapter_number}: {chapter_name}".strip()
            logger.info(f"Extracted chapter title: '{chapter_title}'")
        else:
            chapter_title = "Unknown Chapter"
            logger.warning(f"Regex match failed. Full title: '{full_title}'")
        
        # Extract chapter content
        html_content = self.page.html
        start_tag = '<div class="break-words">'
        end_tag = '<div class="mb-48">'
        start_index = html_content.find(start_tag)
        end_index = html_content.find(end_tag, start_index)
        
        if start_index != -1 and end_index != -1:
            chapter_content = html_content[start_index:end_index]
            logger.info(f"Extracted chapter content (length: {len(chapter_content)})")
        else:
            chapter_content = ""
            logger.warning("Could not find chapter content between specified div tags")
        
        return chapter_title, chapter_content

    def wait_for_genesis_studio_page(self, timeout=30):
        start_time = time.time()
        while time.time() - start_time < timeout:
            current_url = self.page.url
            logger.info(f"Current URL: {current_url}")
            if 'genesistudio.com' in current_url:
                try:                    
                    # Check for the presence of the content div
                    content_div = self.page.ele('.break-words')
                    if content_div:
                        logger.info("Found .break-words div, page loaded successfully")
                        return True
                    else:
                        logger.warning(".break-words div not found, page might not be fully loaded")
                except Exception as e:
                    logger.warning(f"Error while checking page content: {str(e)}")
            time.sleep(1)
        logger.error(f"Timed out waiting for Genesis Studio page to load after {timeout} seconds")
        return False