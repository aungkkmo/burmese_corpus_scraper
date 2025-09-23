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
- **Comprehensive Logging**: Detailed logs for monitoring and debugging

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

### Multi-Site Configuration (Recommended)

Create a `sites.yaml` file to configure multiple sites and easily switch between them:

```bash
# Copy the example and customize
cp sites.example.yaml sites.yaml
```

**Example sites.yaml:**
```yaml
defaults:
  delay: 1.0
  timeout: 30
  max_pages: 5

sites:
  voa_burmese:
    name: "VOA Burmese"
    # Multiple categories with same selectors
    archive_urls:
      myanmar: "https://burmese.voanews.com/myanmar"
      world: "https://burmese.voanews.com/world"
      usa: "https://burmese.voanews.com/usa"
    archive_selector: ".media-block.media-block--t-spac.media-block--contain"
    content_selector: "main.container"
    pagination_type: "click"
    pagination_param: "a.btn.link-showMore.btn__text.btn-anim"
    
  bbc_burmese:
    name: "BBC Burmese"
    archive_urls:
      topics: "https://www.bbc.com/burmese/topics/c95y35118gyt"
      myanmar: "https://www.bbc.com/burmese/topics/cjnwl8q4g7nt"
    archive_selector: ".gs-c-promo"
    content_selector: ".article-content"
    delay: 2.0  # Override default for this site
```

**Interactive mode** - shows site menu:
```bash
python3 -m scraper.main
# Output: 🌐 Found sites.yaml configuration file
#         Available sites:
#            voa_burmese: VOA Burmese
#            bbc_burmese: BBC Burmese
#         Enter site key to use: voa_burmese
```

**Direct site selection** - specify site directly:
```bash
# Run specific site without prompts
python3 -m scraper.main --site voa_burmese
python3 -m scraper.main --site bbc_burmese --max-pages 3
python3 -m scraper.main --site rfa_burmese --delay 2.0

# Run specific category within a site
python3 -m scraper.main --site voa_burmese --category myanmar
python3 -m scraper.main --site irrawaddy --category politics
python3 -m scraper.main --site bbc_burmese --category world --max-pages 2

# Unlimited scraping (override YAML setting)
python3 -m scraper.main --site news_unlimited  # Uses max_pages: null from YAML
python3 -m scraper.main --site simple_news --max-pages 0  # Override to unlimited
```

### Environment File (.env)

Alternative single-site configuration using `.env` file:

```bash
# Copy the example and customize
cp .env.example .env
```

The scraper will use sites.yaml first, then fall back to .env if no site is selected.

## Site Configuration Guide

### Quick Copy Template

Use this template to add a new site to your `sites.yaml`:

```yaml
  your_site_name:
    name: "Your Site Display Name"
    description: "Brief description"
    
    # Choose ONE of these URL formats:
    
    # Single URL:
    archive_url: "https://yoursite.com/news"
    
    # OR Multiple categories:
    archive_urls:
      news: "https://yoursite.com/news"
      politics: "https://yoursite.com/politics"
      world: "https://yoursite.com/world"
    
    # Required selectors (inspect the website to find these)
    archive_selector: ".article-item"      # Selector for each article on archive page
    content_selector: ".article-content"   # Selector for article content on detail page
    
    # Pagination (choose one)
    pagination_type: 0                     # 0=none, 1=queryparam, 2=click, 3=scroll
    # pagination_type: 1                   # URL-based: ?page=2
    # pagination_param: "?page={n}"
    # pagination_type: 2                   # Button-based
    # pagination_param: ".load-more-btn"
    
    # Optional overrides
    delay: 1.0                             # Seconds between requests
    max_pages: 5                           # Maximum pages to scrape (null = unlimited)
    timeout: 30                            # Request timeout
```

### Parameter Reference

#### Required Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `name` | Display name for the site | `"BBC Burmese"` |
| `archive_url` OR `archive_urls` | URL(s) to scrape | See examples below |
| `archive_selector` | CSS/XPath for archive items | `".news-item"` |
| `content_selector` | CSS/XPath for article content | `".article-body"` |

#### Archive URL Formats

**Single URL:**
```yaml
archive_url: "https://site.com/news"
```

**Multiple Categories:**
```yaml
archive_urls:
  news: "https://site.com/news"
  politics: "https://site.com/politics"
  sports: "https://site.com/sports"
```

#### Pagination Types

| Number | Type | Description | Parameter Example |
|--------|------|-------------|-------------------|
| `0` | none | No pagination | `pagination_param: null` |
| `1` | queryparam | URL-based pagination | `"?page={n}"` or `"/page/{n}/"` |
| `2` | click | Click button/link | `".load-more"` or `"a.next-page"` |
| `3` | scroll | Infinite scroll | `pagination_param: null` |

#### Max Pages Behavior

| Value | Behavior | Example |
|-------|----------|---------|
| `5` | Scrape maximum 5 pages | `max_pages: 5` |
| `null` | Scrape all available pages | `max_pages: null` |
| `1` | Scrape only first page | `max_pages: 1` |

**Note**: When `max_pages` is `null`, the scraper will continue until:
- No more pages are found (404 errors)
- Content becomes too small (likely empty pages)
- Manual interruption (Ctrl+C)

#### Optional Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `description` | - | Site description |
| `delay` | 1.0 | Seconds between requests |
| `timeout` | 30 | Request timeout (seconds) |
| `max_pages` | 5 | Maximum pages to scrape (null = unlimited) |
| `use_proxy` | false | Enable proxy rotation |
| `force_engine` | null | Force engine (requests/playwright/selenium) |
| `output_format` | ndjson | Output format (ndjson/json) |
| `thumbnail_selector` | img | Thumbnail image selector |

### Configuration Examples

#### VOA Burmese
```yaml
  voa_burmese:
    name: "VOA Burmese"
    archive_urls:
      myanmar: "https://burmese.voanews.com/myanmar"
      world: "https://burmese.voanews.com/world"
    archive_selector: ".media-block.media-block--t-spac.media-block--contain"
    content_selector: "main.container"
    pagination_type: 2  # 0=none, 1=queryparam, 2=click, 3=scroll
    pagination_param: "a.btn.link-showMore.btn__text.btn-anim"
    delay: 1.5
```

#### BBC Burmese
```yaml
  bbc_burmese:
    name: "BBC Burmese"
    archive_urls:
      topics: "https://www.bbc.com/burmese/topics/c95y35118gyt"
      myanmar: "https://www.bbc.com/burmese/topics/cjnwl8q4g7nt"
    archive_selector: ".gs-c-promo"
    content_selector: ".ssrcss-11r1m41-RichTextComponentWrapper"
    pagination_type: 0  # 0=none, 1=queryparam, 2=click, 3=scroll
    delay: 2.0
```

#### Simple Site (Limited Pages)
```yaml
  simple_news:
    name: "Simple News Site"
    archive_url: "https://example.com/news"
    archive_selector: ".article"
    content_selector: ".content"
    pagination_type: 1  # 0=none, 1=queryparam, 2=click, 3=scroll
    pagination_param: "?page={n}"
    max_pages: 10       # Limit to 10 pages
```

#### Unlimited Scraping Example
```yaml
  news_unlimited:
    name: "News Site (All Pages)"
    archive_url: "https://example.com/news"
    archive_selector: ".article"
    content_selector: ".content"
    pagination_type: 1  # URL-based pagination
    pagination_param: "?page={n}"
    max_pages: null     # Scrape ALL pages
    delay: 2.0          # Be respectful with unlimited scraping
```

### Finding Selectors

1. **Open the website** in your browser
2. **Right-click** on an article item → "Inspect Element"
3. **Find the common selector** that identifies all articles
4. **Test the selector** in browser console: `document.querySelectorAll('your-selector')`
5. **For content selector**, go to an article page and find the main content container

### Configuration Tips

- Start with `pagination_type: 0` (none) for testing
- Use `delay: 2.0` or higher for sites that might block requests
- Set `use_proxy: true` for sites that are strict about blocking
- Use `force_engine: "playwright"` for JavaScript-heavy sites
- Test with `max_pages: 1` first to verify selectors work

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
├── sites.example.yaml   # Site configuration examples
├── sites.template.yaml  # Complete configuration template
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
