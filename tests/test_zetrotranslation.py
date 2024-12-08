import unittest
import logging
from unittest.mock import MagicMock
from DrissionPage import ChromiumPage
from CloudflareBypasser import CloudflareBypasser
from source import zetrotranslation_site

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestZetroTranslationSite))
    return suite

class TestZetroTranslationSite(unittest.TestCase):
    def setUp(self):
        self.page = ChromiumPage()
        self.cf_bypasser = CloudflareBypasser(self.page)
        self.zetro_site = zetrotranslation_site.ZetroTranslationSite(self.page, self.cf_bypasser)

    def tearDown(self):
        self.page.quit()

    def test_get_chapter_content(self):
        chapter_url = "https://zetrotranslation.com/novel/someone-who-believes-they-can-live-normally-in-a-world-where-chastity-is-reversed-did-you-think-you-could-live-normally-in-a-world-with-a-male-to-female-ratio-of-15/chapter-1-my-childhood-friend-type-college-student-is-occasionally-scary/"
        
        # No need to mock, we will access the actual URL
        # Call the method to fetch the chapter content directly from the live site
        chapter_title, chapter_content = self.zetro_site.get_chapter_content(chapter_url)

        # Save the crawled content to a file
        with open('crawled_chapter_content.txt', 'w', encoding='utf-8') as file:
            file.write(f"Title: {chapter_title}\n\nContent:\n{chapter_content}")
            
        logger.info(f"Crawled content saved to 'crawled_chapter_content.txt'.")

if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
