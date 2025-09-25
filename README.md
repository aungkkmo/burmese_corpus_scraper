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

### 🚀 Quick Start with Pre-configured Sites

```bash
# Run all categories for a site (recommended!)
python3 -m scraper.main --site bbc_burmese --ignore-robots

# Run specific category
python3 -m scraper.main --site voa_burmese --category news --ignore-robots

# Run with page limits for testing
python3 -m scraper.main --site irrawaddy_burmese --max-pages 3 --ignore-robots

# Resume from specific category and page (NEW!)
python3 -m scraper.main --site myanmar_now --ignore-robots --resume=news,25
```

### 🆕 Multi-Category Processing

When you don't specify a `--category`, the scraper automatically runs **all available categories** for that site:

```bash
# This processes ALL categories for BBC Burmese
python3 -m scraper.main --site bbc_burmese --ignore-robots

# Output example:
# 🔄 No category specified for 'bbc_burmese'. Running all 6 categories:
#    📂 earthquake  📂 myanmar  📂 world  📂 article  📂 interview  📂 trade
# 
# 🚀 Processing category: earthquake
# ✅ earthquake: 24 articles saved
# 🚀 Processing category: myanmar  
# ✅ myanmar: 18 articles saved
# ... (continues for all categories)
```

**Benefits:**
- ✅ **Complete coverage** - Gets all content from a site
- ✅ **Organized output** - Each category saved to separate files (`bbc_burmese_earthquake.jsonl`, etc.)
- ✅ **Progress tracking** - Shows success/failure for each category
- ✅ **Error resilience** - Failed categories don't stop others

### 🔄 Resume Functionality

When processing large sites, you can resume from a specific category and page if the scraper stops:

```bash
# Resume from page 25 in the 'news' category
python3 -m scraper.main --site myanmar_now --ignore-robots --resume=news,25

# Resume from page 50 in 'opinion' category with page limit
python3 -m scraper.main --site myanmar_now --ignore-robots --resume=opinion,50 --max-pages=100

# Resume works with unlimited scraping (max-pages=0)
python3 -m scraper.main --site myanmar_now --ignore-robots --resume=news,25 --max-pages=0
```

**Resume Features:**
- ✅ **Category skipping** - Automatically skips categories before the resume point
- ✅ **Page resumption** - Starts from the specified page number
- ✅ **Smart continuation** - Works with both limited and unlimited scraping
- ✅ **Queryparam support** - Works with numbered pagination (page/1/, page/2/, etc.)
- ℹ️ **Note**: Resume only works with `queryparam` pagination type

### Manual Configuration Mode

For custom sites, run without arguments for interactive setup:

```bash
python3 -m scraper.main
```

The tool will prompt you for:

1. **Archive/List Page URL**: The URL of the category or archive page (not the site root)
2. **Archive Item Selector**: CSS or XPath selector for article containers on the archive page
3. **Content Selector**: CSS or XPath selector for the main article content on detail pages
4. **Pagination Type**: Choose from none/queryparam/loadmore/scroll
5. **Thumbnail Inclusion**: Whether to extract thumbnail images from archive items

## 📄 Pagination Types

The scraper supports different pagination methods:

### ✅ **Supported Pagination Types:**

1. **`none`** - Single page, no pagination
2. **`queryparam`** - URL-based pagination (page/1/, page/2/, ?page=1, etc.)
   - ✅ **Resume support** - Can resume from specific page
   - ✅ **Smart stopping** - Automatically detects when content ends
3. **`loadmore`** - Button-based pagination ("Load More" buttons)
   - ✅ **Automatic clicking** - Clicks button until no more content
   - ✅ **Duplicate handling** - Automatically removes duplicate URLs

### 🚧 **In Development:**

4. **`scroll`** - Infinite scroll pagination
   - ⚠️ **Status**: Not yet implemented
   - 🤝 **Contribution Welcome**: If you're interested in implementing scroll pagination, please submit a pull request!

**Note**: Resume functionality (`--resume=category,page`) only works with `queryparam` pagination type.

### Command Line Options

```bash
python3 -m scraper.main [OPTIONS]

Options:
  --site TEXT                    Pre-configured site to scrape (e.g., bbc_burmese, voa_burmese)
  --category TEXT                Specific category to scrape (optional - runs all if not specified)
  -o, --output TEXT              Output file path [default: output.jsonl]
  --format [ndjson|json]         Output format [default: ndjson]
  --force-engine [requests|playwright|selenium]
                                 Force specific scraping engine
  --delay TEXT                   Delay between requests (seconds or range like "2,5") [default: "1.0"]
  --timeout INTEGER              Request timeout in seconds [default: 30]
  --ignore-robots                Ignore robots.txt restrictions
  --resume TEXT                  Resume from existing output file or specific category,page (e.g., "news,25")
  --max-pages INTEGER            Maximum pages to scrape per category (0 = unlimited)
  --skip-archive                 Skip archive scraping, process existing URLs
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

# With proxy rotation and delay range
python -m scraper.main --use-proxy --delay "2,5" --output articles.jsonl

# Resume previous scraping session
python -m scraper.main --resume --output articles.jsonl
```

### 🔥 Batch Processing Scripts

For processing multiple sites at once, use the provided bash scripts:

```bash
# Simple script - runs primary category for each site
./run_all_sites.sh

# Advanced script - runs all categories for all sites
./run_all_sites_advanced.sh

# Advanced script with page limits (for testing)
./run_all_sites_advanced.sh 5
```

**Script Features:**
- ✅ **Automated processing** of all configured sites
- ✅ **Progress tracking** with success/failure reporting
- ✅ **Error resilience** - failed sites don't stop others
- ✅ **Easy customization** - edit site lists in the scripts
- ✅ **Full robots.txt bypass** - all sites run with `--ignore-robots`

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

## ⚠️ Data Cleaning Notice

**This scraper intentionally extracts raw content without extensive cleaning.** The extracted data may contain:

- HTML tags and formatting elements
- Navigation elements, advertisements, or sidebar content  
- Timestamps, author information, and metadata mixed with article text
- Special characters and encoding issues
- Unwanted page elements (headers, footers, comments, etc.)

### Why Raw Data?

This design choice allows maximum flexibility for different use cases. Users can implement their own cleaning pipeline based on their specific requirements.

### Recommended Cleaning Tools

If you need clean text data, consider implementing post-processing with:

- **BeautifulSoup**: For HTML tag removal and parsing
- **Regular expressions**: For text normalization and pattern matching
- **Language-specific processors**: For Burmese text processing and normalization
- **Custom filters**: For removing site-specific unwanted elements
- **Text cleaning libraries**: Such as `clean-text`, `ftfy`, or custom solutions

### Example Cleaning Pipeline

```python
from bs4 import BeautifulSoup
import re

def clean_article_content(raw_html):
    # Remove HTML tags
    soup = BeautifulSoup(raw_html, 'html.parser')
    text = soup.get_text()
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Remove common unwanted patterns (customize as needed)
    text = re.sub(r'Share this article.*$', '', text)
    text = re.sub(r'Related articles:.*$', '', text)
    
    return text
```

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
  delay: "0.5,1.5"  # Delay range: 0.5 to 1.5 seconds
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
    delay: "1,3"  # Override default: 1 to 3 seconds for JS-heavy site
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
python3 -m scraper.main --site rfa_burmese --delay "2,4"

# Run all categories for a site (NEW!)
python3 -m scraper.main --site bbc_burmese --ignore-robots

# Run specific category
python3 -m scraper.main --site voa_burmese --category news

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
    delay: "1,2"                           # Delay range: 1 to 2 seconds between requests
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
| `delay` | "0.5,1.5" | Delay range or single value (seconds) |
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
    delay: "1,2"  # 1 to 2 seconds range
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
    delay: "1,3"  # 1 to 3 seconds for JS-heavy site
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
    delay: "2,4"        # Be respectful with unlimited scraping: 2-4 seconds
```

### Finding Selectors

1. **Open the website** in your browser
2. **Right-click** on an article item → "Inspect Element"
3. **Find the common selector** that identifies all articles
4. **Test the selector** in browser console: `document.querySelectorAll('your-selector')`
5. **For content selector**, go to an article page and find the main content container

### Configuration Tips

- Start with `pagination_type: 0` (none) for testing
- Use `delay: "2,5"` or higher ranges for sites that might block requests
- Set `use_proxy: true` for sites that are strict about blocking
- Use `force_engine: "playwright"` for JavaScript-heavy sites
- Test with `max_pages: 1` first to verify selectors work

### Delay Configuration

The scraper supports flexible delay configurations:

- **No delay**: `delay: "0"` (fastest, use with caution)
- **Single delay**: `delay: "2"` → Random delay between 0.5 and 2 seconds
- **Range format**: `delay: "2,5"` → Random delay between 2 and 5 seconds
- **Alternative format**: `delay: "3 to 6"` → Random delay between 3 and 6 seconds
- **Decimal ranges**: `delay: "0.5,1.5"` → Random delay between 0.5 and 1.5 seconds

**Recommended delays by site type:**
- Static sites: `"0.5,1.5"`
- JS-heavy sites: `"2,5"`
- Rate-limited sites: `"3,6"`
- With proxy rotation: `"2,4"`

### Proxy Configuration

The scraper includes built-in proxy rotation using free proxies. You can also provide your own proxy list by modifying the `utility/ip_rotation.py` file.

### Header Rotation

Automatic user-agent and header rotation is enabled by default to simulate different browsers and avoid detection.

## ✅ Tested Sites

**All sites in `sites.example.yaml` have been successfully tested and verified!** ✅

This section tracks sites that have been successfully tested with the scraper:

| Site | Status | Date Tested | Notes |
|------|--------|-------------|-------|
| VOA Burmese | ✅ Success | 2025-09-24 | Selector: `.media-block.media-block--t-spac.media-block--contain`, Content: `main.container` |
| BBC Burmese | ✅ Success | 2025-09-24 | Selector: `div[data-testid="curation-grid-normal"] ul li`, Content: `main`, Delay: "1,3" |
| RFA Burmese | ✅ Success | 2025-09-24 | Selector: `.c-stack.b-rfa-results-list.b-rfa-results-list--show-image`, Force: Playwright, Load more pagination: 3 clicks → 40 articles (100% success) |
| Irrawaddy | ✅ Success | 2025-09-24 | Selector: `article.jeg_post.format-standard`, Force: Playwright, Query pagination, 25 unique URLs |
| Myanmar Now | ✅ Success | 2025-09-24 | Selector: `ul#posts-container li.post-item`, Content: `div.main-content article#the-post`, Proxy rotation, 2 pages → 8/10 articles (80% success) |
| Myanmar National Portal | ✅ Success | 2025-09-24 | Selector: `div.smallcardstyle`, Content: `div.journal-content-article`, Liferay pagination: 3 pages → 30 unique URLs (100% success), `--ignore-robots` required |
| ThanLwinTimes | ✅ Success | 2025-09-25 | Selector: `div.content-right > div > article > h4.title`, Content: `div.bs-blog-post.single`, Query pagination: 5 pages → 40 unique URLs (100% success) |
| Duwun News | ✅ Success | 2025-09-25 | Selector: `div[style*="margin-top: 10px"] div > a.anchor-link`, Force: Playwright, Load more pagination |
| ISEC Myanmar | ✅ Success | 2025-09-25 | Selector: `article.shadow-md`, Content: `div.content`, Query pagination |
| PCT News | ✅ Success | 2025-09-25 | Selector: `.post-item.post-grid`, Content: `article.post`, Query pagination |
| Food Industry Directory | ✅ Success | 2025-09-25 | Selector: `div.item`, Content: `div.itemBody`, Custom pagination increment (9 items per page) |

### Testing Notes:
- **VOA Burmese**: Successfully extracted articles using the configured selectors. The `.media-block.media-block--t-spac.media-block--contain` selector correctly identifies article items, and `main.container` selector captures the full article content.
- **BBC Burmese**: Successfully tested with updated selectors and delay ranges. The `div[data-testid="curation-grid-normal"] ul li` selector works with current BBC site structure, `main` content selector captures articles, and 1-3 second delay range handles JS-heavy content appropriately.
- **RFA Burmese**: Successfully tested with advanced load more pagination! Archive selector works perfectly, forced Playwright engine handles site restrictions. **Load more pagination fully implemented**: 3 clicks on load more button → 40 unique articles collected and processed with 100% success rate (40/40 articles saved). Complete pipeline working from URL collection to article extraction.
- **Irrawaddy**: Successfully tested with forced Playwright engine and query parameter pagination (`?page={n}`). Archive selector `article.jeg_post.format-standard` works perfectly, automatic deduplication removes overlapping content between pages (31→25 unique URLs), and 3-5 second delays handle JS-heavy content appropriately.
- **Myanmar Now**: Successfully tested with proxy rotation and query parameter pagination (`page/{n}/`). Archive selector `ul#posts-container li.post-item` works perfectly, content selector `div.main-content article#the-post` captures articles effectively. Processed 2 pages → 10 URLs → 8/10 articles successfully extracted (80% success rate due to proxy limitations). Automatic proxy failover working correctly.
- **Myanmar National Portal**: Successfully tested with complex Liferay pagination system! Government portal requires `--ignore-robots` flag due to robots.txt restrictions. Archive selector `div.smallcardstyle` works perfectly, content selector `div.journal-content-article` captures official government content. **Complex URL structure mastered**: Complete Liferay parameter chain with `&sorted=latest` and proper pagination parameter `&_com_liferay_asset_publisher_web_portlet_AssetPublisherPortlet_INSTANCE_idasset354_cur={n}`. Processed 3 pages → 30 unique URLs (100% success rate). Demonstrates scraper's ability to handle the most complex government CMS systems.
- **ThanLwinTimes**: Successfully tested with enhanced CSS selector validation! Archive selector `div.content-right > div > article > h4.title` works perfectly after comprehensive validation testing. Content selector `div.bs-blog-post.single` captures article content effectively. Query parameter pagination (`page/{n}/`) processed 5 pages → 40 unique URLs (100% success rate). Demonstrates scraper's robust selector validation system.
- **All Other Sites**: Successfully tested and verified with their respective configurations in `sites.example.yaml`. Each site's selectors, pagination methods, and delay configurations have been validated for optimal performance.

*Add new test results here as sites are verified...*

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
5. **Playwright CLI Environment Issues**: Playwright may encounter errors in CLI-only environments (servers without display). If you experience Playwright failures, try using `--force-engine requests` or `--force-engine selenium` as alternatives.

### ✅ Verified Configurations

The `sites.example.yaml` file contains **tested and verified** selectors and settings for supported sites:

- **VOA Burmese**: Confirmed working selectors and pagination settings
- **BBC Burmese**: Updated selectors for current site structure  
- **Irrawaddy**: Configured with proper delay ranges for JS-heavy content
- **RFA Burmese**: Standard configuration for basic pagination
- **Myanmar Now**: Optimized for proxy usage and click-based pagination

**Tip**: If you're having issues with a site, check if it's already configured in `sites.example.yaml` with verified selectors before creating custom configurations.

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

### System Compatibility

**Tested and verified on:**
- ✅ **macOS 15.5 Sequoia**
- ✅ **macOS 26 Tahoe** 
- ✅ **Ubuntu Server 24.04.3 LTS (Noble)**

**Note**: Playwright may encounter issues in CLI-only environments (headless servers). If you experience problems with Playwright on server environments, use `--force-engine requests` or `--force-engine selenium` as alternatives.

## License

This project is provided as-is for educational and research purposes. Please respect website terms of service and robots.txt when scraping.
