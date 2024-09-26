# NovelDownloader Usage Guide

This guide explains how to use the NovelDownloader to download novels from translation websites and save them as EPUB files.

## Prerequisites

1. Ensure you have Python 3.7 or higher installed on your system.
2. Install the required dependencies by running:
   ```
   pip install -r requirements.txt
   ```

## Running the NovelDownloader

There are two ways to run the NovelDownloader:

### 1. With Command-line Arguments

You can provide the NovelUpdates URL and the translation site URL directly as command-line arguments:

```
python NovelDownloader.py [NovelUpdates URL] [Translation Site URL]
```

Example:
```
python NovelDownloader.py https://www.novelupdates.com/series/i-killed-the-player-of-the-academy/ https://penguin-squad.com/story/i-killed-the-player-of-the-academy/
```

### 2. Without Arguments (Interactive Mode)

If you run the script without arguments, you'll be prompted to enter the URLs:

1. Open a terminal or command prompt.
2. Navigate to the NovelDownloader project directory.
3. Run the following command:
   ```
   python NovelDownloader.py
   ```
4. When prompted, enter the NovelUpdates URL for the novel you want to download.
5. Next, enter the URL of the translation site where the novel chapters are hosted.

## What the Script Does

Once you've provided the URLs (either via command-line or interactively), the script will:

1. Retrieve the novel information from NovelUpdates
2. Download all available chapters from the translation site
3. Cache the novel information and chapters for faster future downloads
4. Create an EPUB file with the downloaded content

The saved novel will be in the same directory as the script, named after the novel title and including the total number of chapters.

## New Features and Improvements

### Improved Error Handling and Logging

The script now provides more detailed logging information throughout the download process. This helps you understand what's happening at each step and makes it easier to identify and troubleshoot any issues.

### Retry Mechanism for Cover Image Download

If the cover image download fails, the script will now retry up to 3 times with a backoff strategy. This improves the chances of successfully downloading the cover image even with temporary network issues.

## Supported Features

- **Caching**: Novel information and chapters are cached to improve performance for repeated downloads. The cache is stored in a SQLite database in the `cache/db/` directory.

- **EPUB Output**: The downloaded novel is saved as an EPUB file, which includes:
  - Novel metadata (title, author, etc.)
  - Cover image (if available)
  - Table of contents
  - All downloaded chapters

- **Cloudflare Bypass**: The tool can bypass Cloudflare protection on supported websites.

- **Paywall Detection**: For supported sites, the tool can detect paywalls and stop downloading when encountered.

## Supported Sites

Currently, NovelDownloader supports the following translation sites:
- Penguin Squad

Support for additional sites will be added in future updates.

## Troubleshooting

- If you encounter any issues with Cloudflare protection, ensure that the `CloudflareBypasser.py` file is in the same directory as `NovelDownloader.py`.
- Make sure you have a stable internet connection throughout the download process.
- If a specific translation site is not working, check if there's an implementation for that site in the `source` directory. If not, you may need to add support for that site (see `claudeDev_docs/adaptive_instructions.md` for guidance).
- If you encounter a paywall message, the download will stop at the last freely available chapter.

## Error Handling

If you encounter any errors during the download process:

1. Check the console output for any error messages or warnings. The improved logging should provide more detailed information about what went wrong.
2. If the cover image download fails, the script will attempt to retry. If it still fails after retries, the script will continue without the cover image.
3. Refer to the `claudeDev_docs/errors.md` file for known issues and their solutions.
4. Ensure you're using the latest version of NovelDownloader and that all dependencies are correctly installed.

## Reporting Issues

If you encounter a bug or have a feature request, please open an issue on the GitHub repository, providing as much detail as possible about the problem or suggestion. Include any relevant log messages or error outputs to help diagnose the issue.

## Future Features

We're constantly working to improve NovelDownloader. Some planned features include:
- Support for more translation sites
- A graphical user interface
- Additional output formats
- Parallel downloading for improved speed

Check the `claudeDev_docs/projectRoadmap.md` file for more information on upcoming features.

Thank you for using NovelDownloader! We hope it enhances your web novel reading experience.