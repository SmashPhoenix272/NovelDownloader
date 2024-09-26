from bs4 import BeautifulSoup
from .base_translation_site import TranslationSite

class PenguinSquadSite(TranslationSite):
    def get_chapter_links(self, url):
        self.page.get(url)
        html_content = self.page.html
        soup = BeautifulSoup(html_content, 'html.parser')
        chapter_links = soup.find_all('a', class_='chapter-group__list-item-link')
        return [link['href'] for link in chapter_links]

    def get_chapter_content(self, url):
        self.page.get(url)
        self.cf_bypasser.bypass()
        chapter_html = self.page.html
        chapter_soup = BeautifulSoup(chapter_html, 'html.parser')
        
        chapter_title = chapter_soup.find('h1', class_='chapter__title').text.strip()
        chapter_content = chapter_soup.find('section', id='chapter-content').text.strip()
        
        # Check for paywall message
        paywall_message = "You are attempting to access the Glacial Archives when you are not even a citizen of the Antarctic Empire. Immigrate to the Antarctic Empire to buy access to the Glacial Archives."
        if paywall_message in chapter_content:
            raise PaywallException("Paywall detected. Unable to access further chapters.")
        
        return chapter_title, chapter_content

class PaywallException(Exception):
    pass