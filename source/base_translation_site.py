from abc import ABC, abstractmethod

class TranslationSite(ABC):
    def __init__(self, page, cf_bypasser):
        self.page = page
        self.cf_bypasser = cf_bypasser

    @abstractmethod
    def get_chapter_links(self, url):
        pass

    @abstractmethod
    def get_chapter_content(self, url):
        pass