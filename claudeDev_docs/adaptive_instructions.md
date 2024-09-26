# Adaptive Instructions for NovelDownloader

This document provides guidelines for adapting the NovelDownloader project to various scenarios and user preferences. It aims to ensure flexibility and maintainability as the project evolves.

## 1. Adding Support for New Translation Sites

When adding support for a new translation site:

1. Create a new file in the `source/` directory (e.g., `new_site.py`).
2. Implement a new class that inherits from `TranslationSite` in `base_translation_site.py`.
3. Override the `get_chapter_links` and `get_chapter_content` methods.
4. Handle site-specific logic, including any necessary Cloudflare bypass techniques.
5. Add paywall detection if applicable.
6. Update `source/translation_site.py` to include the new site class.
7. Add appropriate error handling and logging.

Example structure:

```python
from .base_translation_site import TranslationSite

class NewSite(TranslationSite):
    def get_chapter_links(self, url):
        # Implement site-specific logic
        pass

    def get_chapter_content(self, url):
        # Implement site-specific logic
        pass
```

## 2. Modifying Caching Behavior

To adapt the caching system:

1. Modify `cache/novel_cache.py` to change caching logic.
2. Consider implementing cache expiration for long-term storage.
3. For larger scale applications, consider using a more robust database system.

## 3. Customizing EPUB Output

To customize the EPUB output:

1. Modify the `save_novel_as_epub` method in `NovelDownloader.py`.
2. Consider adding options for different styling or metadata inclusion.
3. Implement support for custom templates for EPUB generation.

## 4. Implementing New Output Formats

To add support for new output formats (e.g., PDF, MOBI):

1. Create a new module for the format (e.g., `pdf_exporter.py`).
2. Implement a method similar to `save_novel_as_epub` for the new format.
3. Update `NovelDownloader.py` to include the new export option.

## 5. Enhancing User Interface

As the project evolves from CLI to GUI:

1. Consider using a framework like PyQt or Tkinter for the GUI.
2. Implement the GUI as a separate module that interacts with the core `NovelDownloader` class.
3. Ensure that core functionality remains separate from the UI to maintain modularity.

## 6. Implementing Parallel Downloads

To improve download speed:

1. Modify the `download_novel` method to use asynchronous programming (e.g., `asyncio`).
2. Implement a connection pool to manage multiple simultaneous requests.
3. Add user-configurable options for controlling the level of parallelism.

## 7. Error Handling and Logging

To improve error handling and logging:

1. Implement a centralized logging system using Python's `logging` module.
2. Create custom exceptions for different error scenarios.
3. Implement a system for reporting errors to users and optionally to developers.

## 8. Configuration Management

For managing user preferences and application settings:

1. Implement a configuration file system (e.g., using `configparser`).
2. Allow users to set preferences such as default output format, download location, etc.
3. Implement a method to validate and sanitize user-provided configuration.

## 9. Internationalization

To support multiple languages:

1. Use Python's `gettext` module for internationalization.
2. Externalize all user-facing strings into language files.
3. Implement a language selection option in the user interface.

## 10. Testing and Quality Assurance

As the project grows:

1. Implement unit tests for core functionalities using a framework like `pytest`.
2. Set up continuous integration to run tests automatically on code changes.
3. Implement integration tests to ensure different components work together correctly.

Remember to update this document as new adaptation needs arise or as the project's architecture evolves. These guidelines should help maintain the project's flexibility and scalability over time.