# NovelDownloader

NovelDownloader is a Python-based tool designed to download web novels from various translation sites and convert them into EPUB format for easy reading on e-book devices.

## Recent Updates

- Improved cover image downloading process to handle Cloudflare protection more effectively
- Enhanced error handling and logging for cover image downloads
- Optimized file handling for cover images using DrissionPage's built-in download functionality
- Fixed issues related to cover image path handling

## Features

- Retrieves novel information from NovelUpdates.com
- Downloads chapters from supported translation sites
- Bypasses Cloudflare protection on supported websites, including for cover image downloads
- Efficiently downloads and processes cover images using DrissionPage
- Caches novel information and chapters for faster subsequent downloads
- Exports novels as EPUB files with cover images and table of contents
- Detects paywalls on supported sites
- Improved error handling and logging
- Uses DrissionPage for efficient web scraping and Cloudflare bypassing

## Supported Sites

Currently, NovelDownloader supports:
- Penguin Squad

More sites will be added in future updates.

## Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/NovelDownloader.git
   cd NovelDownloader
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Quick Start

You can run the script in two ways:

1. With command-line arguments:
   ```
   python NovelDownloader.py [NovelUpdates URL] [Translation Site URL]
   ```

2. Without arguments (you'll be prompted to enter the URLs):
   ```
   python NovelDownloader.py
   ```

The script will then:
- Download the novel information from NovelUpdates
- Download all available chapters from the translation site
- Cache the content for faster subsequent downloads
- Download the cover image (with Cloudflare bypassing if necessary)
  - The cover image is downloaded directly to the script's directory
  - The image is then embedded into the EPUB file
  - The downloaded image file is automatically deleted after processing
- Save the novel as an EPUB file with all the collected information and content

For more detailed instructions, please refer to the [Usage Guide](claudeDev_docs/usage_guide.md).

## Project Structure

- `NovelDownloader.py`: Main script
- `source/`: Contains modules for different translation sites
- `cache/`: Contains caching module
- `CloudflareBypasser.py`: Module for bypassing Cloudflare protection

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## Troubleshooting

If you encounter any issues, particularly with cover image downloads or Cloudflare bypassing, please check the following:

1. Ensure you have the latest version of the script and all dependencies.
2. Check your internet connection and make sure you can access the novel and cover image URLs directly in your browser.
3. If problems persist, please open an issue on the GitHub repository with detailed information about the error and steps to reproduce it.

## Documentation

- [Project Overview](claudeDev_docs/project_overview.md)
- [Usage Guide](claudeDev_docs/usage_guide.md)
- [Technical Stack](claudeDev_docs/techStack.md)
- [Codebase Summary](claudeDev_docs/codebaseSummary.md)
- [Project Roadmap](claudeDev_docs/projectRoadmap.md)
- [Adaptive Instructions](claudeDev_docs/adaptive_instructions.md)
- [Error Handling](claudeDev_docs/errors.md)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Thanks to all the contributors who have helped to improve this project
- Special thanks to the open-source community for providing the tools and libraries that make this project possible

## Disclaimer

This tool is for personal use only. Please respect the copyright of the original authors and support them by purchasing official releases when available.