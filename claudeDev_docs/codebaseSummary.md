# NovelDownloader Codebase Summary

This document provides an overview of the NovelDownloader project structure and key components.

## Project Structure

```
NovelDownloader/
├── NovelDownloader.py
├── CloudflareBypasser.py
├── requirements.txt
├── README.md
├── source/
│   ├── base_translation_site.py
│   ├── translation_site.py
│   └── penguin_squad_site.py
└── cache/
    └── novel_cache.py
```

## Key Components

### NovelDownloader.py

The main script that orchestrates the novel downloading process. It includes the `NovelDownloader` class, which handles:
- Retrieving novel information from NovelUpdates.com
- Downloading chapters from translation sites
- Caching novel information and chapters
- Exporting novels as EPUB files with proper HTML formatting
- Command-line argument parsing for URL inputs
- Improved error handling and logging
- Retry mechanism for cover image download

Key updates:
- Now uses `from urllib3.util.retry import Retry` for compatibility with newer versions of the requests library.
- Implements a new `format_chapter_content` method to ensure proper HTML formatting for EPUB chapters.

### CloudflareBypasser.py

A module for bypassing Cloudflare protection on websites.

### source/base_translation_site.py

Contains the `TranslationSite` abstract base class, which defines the interface for translation site implementations.

### source/translation_site.py

Imports and exports specific translation site implementations.

### source/penguin_squad_site.py

Implementation of the `PenguinSquadSite` class, which extends `TranslationSite` for the Penguin Squad website. It includes paywall detection functionality.

### cache/novel_cache.py

Provides caching functionality using SQLite. The `NovelCache` class handles:
- Caching and retrieving novel information
- Caching and retrieving individual chapters

## Key Features

1. **Modular Translation Site Support**: The project uses a modular structure to support multiple translation sites. New sites can be added by implementing the `TranslationSite` base class.

2. **Cloudflare Bypass**: The `CloudflareBypasser` class allows the downloader to access sites protected by Cloudflare.

3. **Caching**: Novel information and chapters are cached using SQLite, improving performance for subsequent downloads of the same novel.

4. **EPUB Export**: Downloaded novels are exported as EPUB files, including cover images, a table of contents, and properly formatted HTML content for each chapter.

5. **Paywall Detection**: The system can detect paywalls (currently implemented for Penguin Squad site) and stop downloading when a paywall is encountered.

6. **Command-line Argument Support**: Users can now provide NovelUpdates and translation site URLs as command-line arguments for easier use and automation.

7. **Improved Error Handling and Logging**: The script now provides more detailed logging information throughout the download process, making it easier to identify and troubleshoot issues.

8. **Retry Mechanism for Cover Image Download**: If the cover image download fails, the script will retry up to 3 times with a backoff strategy, improving the chances of successfully downloading the cover image.

9. **Proper HTML Formatting for EPUB**: The `format_chapter_content` method ensures that chapter content is properly formatted as HTML for the EPUB file, improving readability and compatibility with e-readers.

## Recent Changes

1. Updated the import statement for the Retry class to use `from urllib3.util.retry import Retry` for compatibility with newer versions of the requests library.
2. Implemented command-line argument support for URL inputs.
3. Enhanced error handling with more detailed logging throughout the script.
4. Added a retry mechanism with backoff for cover image downloads.
5. Updated the main script to use the requests library for more robust HTTP requests.
6. Improved the EPUB creation process to handle cases where the cover image is not available.
7. Implemented a new `format_chapter_content` method to ensure proper HTML formatting for EPUB chapters.
8. Updated the `save_novel_as_epub` method to use the new formatting function for chapter content.

## Potential Future Improvements

1. Support for more translation sites.
2. User interface (CLI or GUI) for easier interaction.
3. Parallel downloading of chapters to improve speed.
4. Option to resume interrupted downloads.
5. Integration with e-reader devices or applications.
6. Customizable logging levels for users with different debugging needs.
7. Unit tests to ensure reliability of core functions and edge cases.
8. Advanced HTML parsing and cleaning for better formatted EPUB content.
9. Support for different EPUB styles or themes.

This codebase summary reflects the current state of the NovelDownloader project, including recent improvements in error handling, logging, user interaction, and EPUB formatting. The project continues to evolve with a focus on reliability, user-friendliness, expandability, and high-quality EPUB output.