import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from source.skydemonorder_site import SkyDemonOrderSite
from CloudflareBypasser import CloudflareBypasser
from DrissionPage import ChromiumPage

def test_skydemonorder():
    # Initialize ChromiumPage
    page = ChromiumPage()

    # Initialize CloudflareBypasser with the ChromiumPage object
    cf_bypasser = CloudflareBypasser(page)

    # Initialize SkyDemonOrderSite
    skydemonorder = SkyDemonOrderSite(None, cf_bypasser)

    # URL to test
    url = "https://skydemonorder.com/projects/reincarnated-user-manual/205-siriel-4"

    try:
        # Get chapter content
        chapter_title, chapter_content = skydemonorder.get_chapter_content(url)

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
    test_skydemonorder()
