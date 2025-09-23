# Burmese Corpus Scraper

A powerful CLI tool for scraping Burmese articles from websites. This scraper collects raw HTML content and metadata from archive/list pages with support for multiple scraping engines and intelligent fallback mechanisms.

## Features

- **Multiple Scraping Engines**: Automatically tests and selects the best engine (Requests → Playwright → Selenium)
- **IP & Header Rotation**: Built-in proxy and user-agent rotation to avoid blocking
- **Pagination Support**: Handles URL-based pagination, click-based navigation, and infinite scroll
- **Resume Capability**: Continue scraping from where you left off
- **Raw HTML Preservation**: Keeps original HTML content with tags intact
- **Flexible Output**: Supports NDJSON and JSON array formats
- **Robust Error Handling**: Skips failed articles and continues scraping
- **Progress Tracking**: Real-time progress bars and detailed statistics

## Installation

1. Clone or download this repository
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. For Playwright support (optional but recommended):

```bash
playwright install chromium
```

## Usage

Run the scraper with:

```bash
python -m scraper.main
```

The tool will prompt you for the following information:

1. **Archive/List Page URL**: The URL of the category or archive page (not the site root)
2. **Archive Item Selector**: CSS or XPath selector for article containers on the archive page
3. **Content Selector**: CSS or XPath selector for the main article content on detail pages
4. **Pagination Type**: Choose from none/queryparam/click/scroll
5. **Thumbnail Inclusion**: Whether to extract thumbnail images from archive items

### Command Line Options

```bash
python -m scraper.main [OPTIONS]

Options:
  -o, --output TEXT              Output file path [default: output.jsonl]
  --format [ndjson|json]         Output format [default: ndjson]
  --force-engine [requests|playwright|selenium]
                                 Force specific scraping engine
  --delay FLOAT                  Delay between requests in seconds [default: 1.0]
  --timeout INTEGER              Request timeout in seconds [default: 30]
  --ignore-robots                Ignore robots.txt
  --resume                       Resume from existing output file
  --max-pages INTEGER            Maximum pages to scrape
  --log TEXT                     Log file path
  --log-level [DEBUG|INFO|WARNING|ERROR]
                                 Log level [default: INFO]
  --use-proxy                    Use proxy rotation
  --test-proxies                 Test proxies before use
  --help                         Show this message and exit
```

### Example Usage

```bash
# Basic scraping
python -m scraper.main --output articles.jsonl

# With proxy rotation and custom delay
python -m scraper.main --use-proxy --delay 2.0 --output articles.jsonl

# Resume previous scraping session
python -m scraper.main --resume --output articles.jsonl

# Force specific engine with JSON output
python -m scraper.main --force-engine playwright --format json --output articles.json
```

## Output Format

The scraper outputs articles in the following format:

```json
{
  "id": "generated_md5_hash",
  "title": "Article Title",
  "url": "https://example.com/article",
  "thumbnail_url": "https://example.com/thumb.jpg",
  "raw_html_content": "<div>...raw html content...</div>",
  "scraped_date": "2023-12-01",
  "source_url": "https://example.com"
}
```

### Output Formats

- **NDJSON** (default): Each article on a separate line as JSON
- **JSON**: Single JSON array containing all articles

## Configuration

### Proxy Configuration

The scraper includes built-in proxy rotation using free proxies. You can also provide your own proxy list by modifying the `utility/ip_rotation.py` file.

### Header Rotation

Automatic user-agent and header rotation is enabled by default to simulate different browsers and avoid detection.

## Project Structure

```
burmese_corpus_scraper/
├── scraper/
│   ├── __init__.py
│   ├── main.py          # Main CLI application
│   ├── crawler.py       # Web crawling engines
│   ├── extractor.py     # Content extraction
│   ├── storage.py       # Data storage
│   └── utils.py         # Utility functions
├── utility/
│   ├── ip_rotation.py   # Proxy rotation
│   └── header_rotation.py # Header rotation
├── data/
│   └── raw/             # Scraped data output
├── logs/                # Log files
├── config.json          # Configuration
├── requirements.txt     # Python dependencies
└── README.md
```

## Troubleshooting

### Common Issues

1. **No archive items found**: Make sure you're using a category/archive URL, not the site root
2. **Content selector not found**: Verify the CSS/XPath selector on the article detail pages
3. **Engine failures**: Try forcing a specific engine with `--force-engine`
4. **Proxy issues**: Disable proxy rotation or use `--test-proxies` flag

### Debugging

Enable debug logging to see detailed information:

```bash
python -m scraper.main --log-level DEBUG --log debug.log
```

### Engine Selection

The scraper automatically tests engines in this order:
1. **Requests** (fastest, works for static content)
2. **Playwright** (handles JavaScript, recommended)
3. **Selenium** (fallback for complex sites)

## Best Practices

1. **Respect robots.txt**: The scraper respects robots.txt by default
2. **Use delays**: Set appropriate delays to avoid overwhelming servers
3. **Test selectors**: Verify your CSS/XPath selectors work on a few pages first
4. **Monitor progress**: Use the built-in progress bars and logging
5. **Resume capability**: Use `--resume` for long scraping sessions

## Requirements

- Python 3.10+
- See `requirements.txt` for Python package dependencies
- Optional: Chrome/Chromium for Playwright
- Optional: ChromeDriver for Selenium

## License

This project is provided as-is for educational and research purposes. Please respect website terms of service and robots.txt when scraping.
