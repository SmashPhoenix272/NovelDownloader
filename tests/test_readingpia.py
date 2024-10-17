import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from source.readingpia_site import ReadingPiaSite
from CloudflareBypasser import CloudflareBypasser
from DrissionPage import ChromiumPage

def test_readingpia():
    # Initialize ChromiumPage
    page = ChromiumPage()

    # Initialize CloudflareBypasser with the ChromiumPage object
    cf_bypasser = CloudflareBypasser(page)

    # Initialize ReadingPiaSite
    readingpia = ReadingPiaSite(None, cf_bypasser)

    # URL to test
    url = "https://www.readingpia.me/incompatible-interspecies-wives-chapter-1"

    try:
        # Get chapter content
        chapter_title, chapter_content = readingpia.get_chapter_content(url)

        # Create HTML content
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{chapter_title}</title>
        </head>
        <body>
            <h1>{chapter_title}</h1>
            {chapter_content}
        </body>
        </html>
        """

        # Write to file
        with open('test_output.html', 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"Chapter content has been exported to 'test_output.html'")

    finally:
        # Close the ChromiumPage object to clean up resources
        page.quit()

if __name__ == "__main__":
    test_readingpia()
