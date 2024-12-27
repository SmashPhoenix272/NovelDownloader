from abc import ABC, abstractmethod

class TranslationSite(ABC):
    def __init__(self, page, cf_bypasser, nu_retriever=None):
        self.page = page
        self.cf_bypasser = cf_bypasser
        self.nu_retriever = nu_retriever

    @abstractmethod
    def get_chapter_links(self, url):
        pass

    @abstractmethod
    def get_chapter_content(self, url):
        pass