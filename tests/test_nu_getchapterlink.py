import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from DrissionPage import ChromiumPage
from CloudflareBypasser import CloudflareBypasser
from source.NU_getchapterlink import NovelUpdatesChapterRetriever
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_nu_getchapterlink():
    page = ChromiumPage()
    cf_bypasser = CloudflareBypasser(page)
    retriever = NovelUpdatesChapterRetriever(page, cf_bypasser)

    # Test login
    if not retriever.login():
        logger.error("Login failed. Make sure your .env file contains valid NU_USERNAME and NU_PASSWORD.")
        return

    # Test get_chapter_links
    novel_url = "https://www.novelupdates.com/series/fated-to-be-loved-by-villains/"
    chapter_links = retriever.get_chapter_links(novel_url)

    if not chapter_links:
        logger.error("Failed to retrieve chapter links.")
        return

    logger.info(f"Successfully retrieved {len(chapter_links)} chapter links.")
    logger.info(f"First chapter link: {chapter_links[0]}")
    logger.info(f"Last chapter link: {chapter_links[-1]}")

    # Test get_chapter_content
    first_chapter_url = chapter_links[0]
    chapter_title, chapter_content = retriever.get_chapter_content(first_chapter_url)

    if not chapter_title or not chapter_content:
        logger.error("Failed to retrieve chapter content.")
        return

    logger.info(f"Successfully retrieved content for chapter: {chapter_title}")
    logger.info(f"Content preview: {chapter_content[:200]}...")

    logger.info("All tests passed successfully!")

if __name__ == "__main__":
    test_nu_getchapterlink()