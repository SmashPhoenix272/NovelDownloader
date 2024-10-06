from DrissionPage import ChromiumPage
from bs4 import BeautifulSoup
import time
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class NovelUpdatesChapterRetriever:
    def __init__(self, page: ChromiumPage, cf_bypasser):
        self.page = page
        self.cf_bypasser = cf_bypasser
        self.base_url = "https://www.novelupdates.com"
        self.logged_in = False
        self.username = os.getenv('NU_USERNAME')
        self.password = os.getenv('NU_PASSWORD')

    def login(self):
        if not self.username or not self.password:
            logger.error("NovelUpdates credentials not found in .env file.")
            return False

        login_url = f"{self.base_url}/login/"
        self.page.get(login_url)
        self.cf_bypasser.bypass()

        # Check if already logged in
        if self.page.ele('text:Log Out'):
            logger.info("Already logged in to NovelUpdates.")
            self.logged_in = True
            return True

        try:
            # Fill in login form
            self.page.ele('#user_login').input(self.username)
            self.page.ele('#user_pass').input(self.password)
            self.page.ele('#rememberme').click()
            self.page.ele('#wp-submit').click()

            # Wait for login to complete
            time.sleep(2)

            # Check if login was successful
            if self.page.ele('text:Log Out'):
                logger.info("Login to NovelUpdates successful.")
                self.logged_in = True
                return True
            else:
                logger.error("Login to NovelUpdates failed.")
                return False
        except Exception as e:
            logger.error(f"Login to NovelUpdates failed. Error: {str(e)}")
            return False

    def get_chapter_links(self, novel_url):
        if not self.logged_in:
            logger.error("Please login to NovelUpdates first.")
            return []

        self.page.get(novel_url)
        self.cf_bypasser.bypass()

        try:
            # Click the button to show all chapters
            self.page.ele('.my_popupreading_open').click()
            time.sleep(2)  # Wait for the chapter list to load

            # Get the chapter list HTML
            chapter_list_html = self.page.ele('.sp_chp').html
            soup = BeautifulSoup(chapter_list_html, 'html.parser')

            # Extract chapter links
            chapter_links = []
            for li in soup.find_all('li', class_='sp_li_chp'):
                link = li.find('a', href=lambda h: h and h.startswith('//www.novelupdates.com/extnu/'))
                if link:
                    chapter_links.append(f"https:{link['href']}")

            # Reverse the list to get oldest first
            chapter_links.reverse()
            return chapter_links

        except Exception as e:
            logger.error(f"Error retrieving chapter links from NovelUpdates: {str(e)}")
            return []

    def get_chapter_content(self, chapter_url):
        try:
            self.page.get(chapter_url)
            self.cf_bypasser.bypass()
            
            # NovelUpdates redirects to the actual chapter page, so we need to get the content from there
            chapter_title = self.page.ele('tag:h1').text.strip()
            
            # The content structure may vary depending on the target site, so we'll use a general approach
            content = self.page.ele('tag:article') or self.page.ele('id:chapter-content') or self.page.ele('class:chapter-content')
            
            if content:
                chapter_content = content.html
            else:
                logger.warning(f"Could not find chapter content for URL: {chapter_url}")
                chapter_content = "Chapter content could not be retrieved."

            return chapter_title, chapter_content
        except Exception as e:
            logger.error(f"Error retrieving chapter content from URL {chapter_url}: {str(e)}")
            return "Error", f"Failed to retrieve chapter content: {str(e)}"

# Usage example:
# retriever = NovelUpdatesChapterRetriever(page, cf_bypasser)
# if retriever.login():
#     chapters = retriever.get_chapter_links("https://www.novelupdates.com/series/novel-title/")
#     for chapter_url in chapters:
#         title, content = retriever.get_chapter_content(chapter_url)
#         print(f"{title}: {content[:100]}...")