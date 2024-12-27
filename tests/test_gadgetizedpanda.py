import unittest
import logging
from unittest.mock import MagicMock
from DrissionPage import ChromiumPage
from CloudflareBypasser import CloudflareBypasser
from source.gadgetizedpanda_site import GadgetizedPandaSite
from ebooklib import epub
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_test_epub():
    logger.info("Creating test EPUB file")
    book = epub.EpubBook()
    
    # Set metadata
    book.set_identifier('test-novel')
    book.set_title('Harem life with the hypnosis app I got')
    book.set_language('en')
    book.add_author('Test Author')
    
    # Add default CSS
    style = '''
        .scene-break {
            text-align: center;
            margin: 1em 0;
            color: #666;
        }
        .epub-image-container {
            text-align: center;
            margin: 1em 0;
        }
        .epub-image-container img {
            max-width: 100%;
            height: auto;
            display: block;
            margin: 0 auto;
        }
    '''
    nav_css = epub.EpubItem(
        uid="style_nav",
        file_name="style/nav.css",
        media_type="text/css",
        content=style)
    book.add_item(nav_css)
    
    # Create test chapters
    chapters = []
    
    # Create regular chapter
    page = ChromiumPage()
    cf_bypasser = CloudflareBypasser(page)
    panda_site = GadgetizedPandaSite(page, cf_bypasser)
    
    try:
        # Get regular chapter
        chapter_url = "https://gadgetizedpanda.com/2024/03/30/harem-life-with-the-hypnosis-app-i-got-volume-1-chapter-1/"
        chapter_title, (chapter_content, chapter_images) = panda_site.get_chapter_content(chapter_url)
        
        # Add images to the book
        for img_filename, img_data in chapter_images:
            # Determine image type from filename
            media_type = "image/jpeg" if img_filename.endswith(('.jpg', '.jpeg')) else "image/png"
            img_item = epub.EpubImage(
                uid=img_filename,
                file_name=f"images/{img_filename}",
                media_type=media_type,
                content=img_data
            )
            book.add_item(img_item)
            logger.info(f"Added image {img_filename} to EPUB")
        
        # Create chapter with images
        chapter = epub.EpubHtml(title=chapter_title, file_name='chapter_1.xhtml', lang='en')
        chapter.content = f"<h1>{chapter_title}</h1>{chapter_content}"
        chapter.add_item(nav_css)
        book.add_item(chapter)
        chapters.append(chapter)
        
        # Get illustration chapter
        illustration_url = "https://gadgetizedpanda.com/2024/03/29/harem-life-with-the-hypnosis-app-i-got-volume-1-illustrations/"
        illustration_title, (illustration_content, illustration_images) = panda_site.get_chapter_content(illustration_url)
        
        # Add illustration images to the book
        for img_filename, img_data in illustration_images:
            # Determine image type from filename
            media_type = "image/jpeg" if img_filename.endswith(('.jpg', '.jpeg')) else "image/png"
            img_item = epub.EpubImage(
                uid=img_filename,
                file_name=f"images/{img_filename}",
                media_type=media_type,
                content=img_data
            )
            book.add_item(img_item)
            logger.info(f"Added illustration {img_filename} to EPUB")
        
        # Create illustration chapter
        illustration_chapter = epub.EpubHtml(title=illustration_title, file_name='illustrations.xhtml', lang='en')
        illustration_chapter.content = f"<h1>{illustration_title}</h1>{illustration_content}"
        illustration_chapter.add_item(nav_css)
        book.add_item(illustration_chapter)
        chapters.append(illustration_chapter)
        
        # Add default NCX and Nav file
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        
        # Define spine
        book.spine = ['nav'] + chapters
        
        # Create filename
        filename = "test_novel.epub"
        
        # Write EPUB file
        logger.info(f"Writing EPUB file: {filename}")
        epub.write_epub(filename, book, {})
        
        logger.info(f"Test novel has been saved as '{filename}'.")
        return True
        
    except Exception as e:
        logger.error(f"Error creating test EPUB: {str(e)}")
        return False
    finally:
        page.quit()

class TestEpubGeneration(unittest.TestCase):
    def test_create_epub(self):
        self.assertTrue(create_test_epub())
        self.assertTrue(os.path.exists("test_novel.epub"))

if __name__ == '__main__':
    unittest.main()
