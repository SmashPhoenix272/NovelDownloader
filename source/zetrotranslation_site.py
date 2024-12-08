from bs4 import BeautifulSoup
import logging
from .base_translation_site import TranslationSite
from .NU_getchapterlink import NovelUpdatesChapterRetriever

logger = logging.getLogger(__name__)

class ZetroTranslationSite(TranslationSite):
    def __init__(self, page, cf_bypasser):
        super().__init__(page, cf_bypasser)
        self.nu_retriever = NovelUpdatesChapterRetriever(page, cf_bypasser)

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
        logger.info(f"Getting chapter content from {url}")
        self.page.get(url)
        self.cf_bypasser.bypass()
        html_content = self.page.html
        
        if not html_content:
            logger.error("Failed to retrieve chapter content")
            return None, None
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Get chapter title
        title_element = soup.select_one('li.active')
        chapter_title = title_element.text.strip() if title_element else "Untitled Chapter"
        
        # Get chapter content
        content_div = soup.select_one('div.text-left')
        if not content_div:
            logger.error("Could not find chapter content")
            return None, None
            
        # Remove style attributes from all elements
        for element in content_div.find_all(style=True):
            del element['style']
            
        chapter_content = str(content_div)
        
        return chapter_title, chapter_content
