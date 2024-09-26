# NovelDownloader Error Log

This document logs issues encountered during the development and use of NovelDownloader, along with their solutions. It serves as a reference for troubleshooting and improving the tool.

## Error 001: Cloudflare Detection

**Date:** [Insert Date]

**Description:** The Cloudflare protection on certain websites is detecting and blocking our scraper.

**Solution:** Implemented a custom CloudflareBypasser class using DrissionPage. This class mimics human-like behavior to bypass Cloudflare protection.

**Prevention:** Regularly update the CloudflareBypasser class to adapt to changes in Cloudflare's detection methods.

## Error 002: Inconsistent HTML Structure

**Date:** [Insert Date]

**Description:** Some translation sites have inconsistent HTML structures, causing the scraper to fail in extracting chapter content.

**Solution:** Implemented more robust parsing logic in the site-specific classes. Added multiple fallback methods for extracting chapter content.

**Prevention:** Regularly test the scraper against various translation sites and update the parsing logic as needed.

## Error 003: Rate Limiting

**Date:** [Insert Date]

**Description:** Rapid requests to translation sites are resulting in temporary IP bans due to rate limiting.

**Solution:** Implemented a delay between requests and added exponential backoff for retry attempts.

**Prevention:** Monitor and adjust request rates based on each site's specific limitations. Consider implementing proxy rotation for high-volume usage.

## Error 004: Memory Usage for Large Novels

**Date:** [Insert Date]

**Description:** Downloading very large novels (1000+ chapters) is causing high memory usage and potential crashes.

**Solution:** Implemented incremental saving of downloaded content instead of keeping everything in memory.

**Prevention:** Monitor memory usage during downloads and implement more efficient data handling for large novels.

## Error 005: Encoding Issues

**Date:** [Insert Date]

**Description:** Some novels with non-ASCII characters are not being saved correctly, resulting in garbled text.

**Solution:** Ensured consistent use of UTF-8 encoding when reading from websites and writing to files.

**Prevention:** Always specify encoding in file operations and add checks for proper encoding throughout the codebase.

---

This log will be updated as new issues are encountered and resolved. Each entry should include:

1. A unique error identifier
2. The date the error was encountered
3. A description of the error
4. The solution implemented
5. Steps for prevention or mitigation of similar errors in the future

Regularly reviewing and updating this log will help improve the reliability and robustness of the NovelDownloader tool.