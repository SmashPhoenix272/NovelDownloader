import unittest
import time
import logging
import re
from DrissionPage import ChromiumPage
from CloudflareBypasser import CloudflareBypasser
from selenium.common.exceptions import TimeoutException
from source.genesistudio_site import GenesistudioSite

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestGenesistudioSite(unittest.TestCase):
    """Test case for getting HTML content from a Genesis Studio URL."""

    def setUp(self):
        self.page = ChromiumPage()
        self.cf_bypasser = CloudflareBypasser(self.page)
        self.genesistudio_site = GenesistudioSite(self.page, self.cf_bypasser)

    def tearDown(self):
        self.page.quit()

    def test_get_html_content(self):
        """Test if we can successfully retrieve HTML content from a Genesis Studio URL."""
        url = "https://www.novelupdates.com/extnu/6792247/"
        
        # Navigate to the URL
        logger.info(f"Navigating to URL: {url}")
        self.page.get(url)

        # Use CloudflareBypasser to handle any challenges
        logger.info("Attempting to bypass Cloudflare challenge")
        self.cf_bypasser.bypass()

        # Check if bypass was successful
        if not self.cf_bypasser.is_bypassed():
            self.fail("Failed to bypass Cloudflare challenge")
        logger.info("Successfully bypassed Cloudflare challenge")

        # Add a small delay to allow for any redirects
        time.sleep(3)

        # Wait for the Genesis Studio page to load
        if not self.genesistudio_site.wait_for_genesis_studio_page():
            self.fail("Timed out waiting for Genesis Studio page to load")
        logger.info("Genesis Studio page loaded successfully")

        # Check if we've actually reached a Genesis Studio page
        final_url = self.page.url
        self.assertIn('genesistudio.com', final_url, f"Expected Genesis Studio URL, but got: {final_url}")

        # Get the chapter title and content
        chapter_title, chapter_content = self.genesistudio_site.extract_genesistudio_content()

        # Log the full title element HTML for debugging
        title_element = self.page.ele('main h1.sr-only', timeout=5)
        if title_element:
            logger.info(f"Found title element. Full title element HTML: {title_element.html}")
        else:
            logger.warning("Title element (main h1.sr-only) not found")
            # Fallback to searching in the entire HTML
            html_content = self.page.html
            title_match = re.search(r'<h1 class="sr-only">(.*?)</h1>', html_content)
            if title_match:
                logger.info(f"Found title in HTML. Full title: '{title_match.group(1).strip()}'")
            else:
                logger.warning("Failed to find title element in HTML")

        # Save the full HTML content to a text file
        with open('tests/genesistudio_full_html.txt', 'w', encoding='utf-8') as f:
            f.write(self.page.html)
        logger.info("Full HTML content saved to 'tests/genesistudio_full_html.txt'")

        # Save the extracted chapter content as an HTML file
        extracted_html_path = 'tests/extracted_chapter_content.html'
        with open(extracted_html_path, 'w', encoding='utf-8') as f:
            f.write(f"<html><head><title>{chapter_title}</title></head><body>{chapter_content}</body></html>")
        logger.info(f"Extracted chapter content saved as HTML to '{extracted_html_path}'")
        
        # Check if the chapter title and content are not empty
        self.assertIsNotNone(chapter_title, "Chapter title is None")
        self.assertNotEqual(chapter_title, "", "Chapter title is empty")
        self.assertIn("Chapter", chapter_title, "Chapter number not found in title")
        
        # Check for specific chapter title format
        chapter_title_pattern = r'^Chapter \d+:?\s*.+$'
        self.assertTrue(re.match(chapter_title_pattern, chapter_title), f"Chapter title '{chapter_title}' does not match expected format 'Chapter X: Title' or 'Chapter X Title'")
        
        self.assertIsNotNone(chapter_content, "Chapter content is None")
        self.assertNotEqual(chapter_content, "", "Chapter content is empty")
        
        # Log the extracted content for debugging
        logger.info(f"Extracted chapter title: {chapter_title}")
        logger.info(f"Extracted chapter content (first 500 characters): {chapter_content[:500]}")
        
        # Check for the presence of expected content
        self.assertIn('<div class="break-words">', chapter_content, "Opening break-words div not found in chapter content")
        self.assertNotIn('<div class="mb-48">', chapter_content, "Closing mb-48 div should not be in chapter content")
        
        # Check for specific content in the extracted chapter
        self.assertIn('<p class="narration">', chapter_content, "Narration paragraph not found in chapter content")
        self.assertIn('<p class="dialogue">', chapter_content, "Dialogue paragraph not found in chapter content")
        
        # Check for expected text content
        self.assertIn("The concept known as the butterfly effect", chapter_content, "Expected text content not found in chapter")
        self.assertIn("Eleanor, the Student Council President", chapter_content, "Expected text content not found in chapter")
        
        logger.info("All tests passed successfully")

if __name__ == '__main__':
    unittest.main()