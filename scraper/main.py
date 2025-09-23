#!/usr/bin/env python3
"""
Main CLI application for the Burmese corpus scraper
"""

import click
import json
import logging
import sys
import time
from pathlib import Path
from typing import Optional, List, Dict, Any
from tqdm import tqdm

# Import utility modules
sys.path.append(str(Path(__file__).parent.parent))
from utility.ip_rotation import ProxyRotator
from utility.header_rotation import HeaderRotator

# Import scraper modules
from .utils import (
    is_valid_url, setup_logging, load_existing_ids, 
    validate_selector_format, generate_id, normalize_slug
)
from .crawler import WebCrawler
from .extractor import ContentExtractor
from .storage import DataStorage

class BurmeseCorpusScraper:
    """Main scraper class"""
    
    def __init__(self, proxy_rotator=None, header_rotator=None, 
                 delay=1.0, timeout=30, respect_robots=True):
        self.proxy_rotator = proxy_rotator
        self.header_rotator = header_rotator
        self.delay = delay
        self.timeout = timeout
        self.respect_robots = respect_robots
        
        self.crawler = WebCrawler(
            proxy_rotator=proxy_rotator,
            header_rotator=header_rotator,
            delay=delay,
            timeout=timeout,
            respect_robots=respect_robots
        )
        
        # Separate engines for archive and detail pages
        self.archive_engine = None
        self.detail_engine = None
        
        self.extractor = ContentExtractor()
        self.logger = logging.getLogger('burmese_scraper')
        
        # Statistics
        self.stats = {
            'archive_pages_processed': 0,
            'archive_items_found': 0,
            'articles_processed': 0,
            'articles_saved': 0,
            'articles_skipped': 0,
            'errors': 0
        }
    
    def scrape(self, archive_url: str, archive_selector: str, content_selector: str,
               pagination_type: str = 'none', pagination_param: str = None,
               thumbnail_selector: str = None, output_file: str = 'output.jsonl',
               format_type: str = 'ndjson', force_engine: str = None,
               resume: bool = False, max_pages: int = None, urls_file: str = None,
               skip_archive: bool = False) -> Dict[str, Any]:
        """
        Main scraping method
        
        Args:
            archive_url: URL of archive/list page
            archive_selector: CSS/XPath selector for archive items
            content_selector: CSS/XPath selector for article content
            pagination_type: Type of pagination (none/queryparam/click/scroll)
            pagination_param: Pagination parameter template
            thumbnail_selector: Optional selector for thumbnails
            output_file: Output file path
            format_type: Output format (ndjson/json)
            force_engine: Force specific engine (requests/playwright/selenium)
            resume: Resume from existing output
            max_pages: Maximum pages to scrape
            urls_file: Path to URLs file for storage/loading
            skip_archive: Skip archive scraping, use existing URLs file
            
        Returns:
            Scraping results dictionary
        """
        
        self.logger.info("Starting Burmese corpus scraper")
        self.logger.info(f"Archive URL: {archive_url}")
        self.logger.info(f"Archive selector: {archive_selector}")
        self.logger.info(f"Content selector: {content_selector}")
        
        # Initialize storage
        storage = DataStorage(output_file, format_type)
        
        # Get existing IDs for resume functionality
        existing_ids = set()
        if resume:
            existing_ids = storage.get_existing_ids()
            self.logger.info(f"Resume mode: found {len(existing_ids)} existing articles")
        
        # Choose scraping engines separately for archive and detail pages
        self.logger.info("Testing and selecting scraping engines...")
        
        # Choose archive engine
        self.archive_engine = self.crawler.choose_engine(
            archive_url, archive_selector, content_selector, force_engine
        )
        
        if not self.archive_engine:
            self.logger.error("No working scraping engine found for archive")
            return self._get_results(success=False, error="No working scraping engine found for archive")
        
        # Set archive engine as current for validation
        self.crawler.current_engine = self.archive_engine
        
        # Validate archive page and selector (skip in skip-archive mode)
        if not skip_archive:
            if not self._validate_archive_page(archive_url, archive_selector):
                return self._get_results(success=False, error="Archive validation failed")
        else:
            self.logger.info("Skipping archive validation in skip-archive mode")
        
        try:
            all_article_urls = []
            
            if skip_archive and urls_file:
                # Load URLs from file
                with open(urls_file, 'r', encoding='utf-8') as f:
                    urls_data = json.load(f)
                    all_article_urls = urls_data.get('urls', [])
                
                self.logger.info(f"Loaded {len(all_article_urls)} URLs from {urls_file}")
                
                # Choose detail engine using first URL as sample
                if all_article_urls:
                    sample_url = all_article_urls[0]
                    self.detail_engine = self.crawler.choose_detail_engine(
                        sample_url, content_selector, force_engine
                    )
                    
                    if not self.detail_engine:
                        self.logger.error("No working scraping engine found for detail pages")
                        return self._get_results(success=False, error="No working scraping engine found for detail pages")
                    
                    # Set detail engine as current for article processing
                    self.crawler.current_engine = self.detail_engine
                
                # Process articles directly
                self._process_articles_from_urls(
                    all_article_urls, content_selector, storage, existing_ids, archive_url
                )
                
            else:
                # Get archive URLs to process
                archive_urls = self._get_archive_urls(
                    archive_url, pagination_type, pagination_param, max_pages
                )
                
                self.logger.info(f"Will process {len(archive_urls)} archive pages")
                
                # Process each archive page and collect URLs
                for page_num, url in enumerate(archive_urls, 1):
                    self.logger.info(f"Processing archive page {page_num}/{len(archive_urls)}: {url}")
                    
                    page_urls = self._process_archive_page(
                        url, archive_selector, content_selector, 
                        thumbnail_selector, storage, existing_ids, archive_url, collect_urls=True
                    )
                    
                    if page_urls:
                        all_article_urls.extend(page_urls)
                        self.stats['archive_pages_processed'] += 1
                    else:
                        self.stats['errors'] += 1
                        self.logger.warning(f"Failed to process archive page: {url}")
                
                # Save URLs to file
                if urls_file and all_article_urls:
                    self._save_urls_to_file(
                        urls_file, all_article_urls, archive_url, 
                        archive_selector, content_selector
                    )
                
                # Choose detail engine for article processing
                if all_article_urls:
                    sample_url = all_article_urls[0]
                    self.detail_engine = self.crawler.choose_detail_engine(
                        sample_url, content_selector, force_engine
                    )
                    
                    if not self.detail_engine:
                        self.logger.warning("No working scraping engine found for detail pages, using archive engine")
                        self.detail_engine = self.archive_engine
                    
                    # Set detail engine as current for article processing
                    self.crawler.current_engine = self.detail_engine
                    
                    # Process articles with detail engine
                    self._process_articles_from_urls(
                        all_article_urls, content_selector, storage, existing_ids, archive_url
                    )
            
            # Final statistics
            self.logger.info("Scraping completed")
            self._log_final_stats()
            
            return self._get_results(success=True)
            
        except KeyboardInterrupt:
            self.logger.info("Scraping interrupted by user")
            return self._get_results(success=False, error="Interrupted by user")
        
        except Exception as e:
            self.logger.error(f"Scraping failed: {e}")
            return self._get_results(success=False, error=str(e))
        
        finally:
            # Cleanup
            self.crawler.cleanup()
    
    def _validate_archive_page(self, archive_url: str, archive_selector: str) -> bool:
        """Validate archive page and selector"""
        
        self.logger.info("Validating archive page...")
        
        # Get archive page content
        content = self.crawler.get_page_content(archive_url)
        if not content:
            self.logger.error(f"Could not fetch archive page: {archive_url}")
            return False
        
        # Test archive selector
        elements = self.crawler.find_elements(content, archive_selector)
        if not elements:
            self.logger.error(f'No archive items found for selector "{archive_selector}" on "{archive_url}". '
                            'Make sure you provided a category/archive URL (not the site root) and correct selector.')
            return False
        
        self.logger.info(f"Archive validation successful: found {len(elements)} items")
        return True
    
    def _get_archive_urls(self, base_url: str, pagination_type: str, 
                         pagination_param: str = None, max_pages: int = None) -> List[str]:
        """Get list of archive URLs to process based on pagination type"""
        
        urls = [base_url]
        
        if pagination_type == 'none' or not pagination_param:
            return urls
        
        if pagination_type == 'queryparam':
            # Generate URLs with page parameters
            page = 2
            while True:
                if max_pages and len(urls) >= max_pages:
                    break
                
                # Replace {n} with page number
                param = pagination_param.replace('{n}', str(page))
                
                if param.startswith('?') or param.startswith('&'):
                    next_url = base_url + param
                else:
                    # Assume it's a path parameter
                    next_url = base_url.rstrip('/') + '/' + param.lstrip('/')
                
                # Test if page exists
                content = self.crawler.get_page_content(next_url)
                if not content:
                    self.logger.info(f"Pagination ended at page {page-1}")
                    break
                
                # Check if page has content (simple heuristic)
                if len(content) < 1000:  # Very small page, likely empty
                    self.logger.info(f"Pagination ended at page {page-1} (small content)")
                    break
                
                urls.append(next_url)
                page += 1
                
                # Safety limit
                if page > 1000:
                    self.logger.warning("Reached safety limit of 1000 pages")
                    break
        
        elif pagination_type in ['click', 'scroll']:
            # For click and scroll, we'd need to use headless browser
            # For now, just process the first page
            self.logger.warning(f"Pagination type '{pagination_type}' not fully implemented, processing first page only")
        
        return urls
    
    def _process_archive_page(self, archive_url: str, archive_selector: str, 
                            content_selector: str, thumbnail_selector: str,
                            storage: DataStorage, existing_ids: set, 
                            original_archive_url: str, collect_urls: bool = False) -> List[str]:
        """Process a single archive page"""
        
        try:
            # Get archive page content
            content = self.crawler.get_page_content(archive_url)
            if not content:
                self.logger.error(f"Could not fetch archive page: {archive_url}")
                return []
            
            # Extract archive items
            archive_items = self.extractor.extract_archive_items(
                content, archive_url, archive_selector, thumbnail_selector
            )
            
            if not archive_items:
                self.logger.warning(f"No archive items found on {archive_url}")
                return []
            
            self.stats['archive_items_found'] += len(archive_items)
            self.logger.info(f"Found {len(archive_items)} archive items")
            
            # Collect URLs if requested
            if collect_urls:
                urls = [item['url'] for item in archive_items]
                self.logger.info(f"Collected {len(urls)} URLs from archive page")
                return urls
            
            # Process each article
            with tqdm(archive_items, desc="Processing articles", unit="article") as pbar:
                for item in pbar:
                    article_url = item['url']
                    article_id = generate_id(article_url)
                    
                    # Skip if already processed (resume functionality)
                    if article_id in existing_ids:
                        self.stats['articles_skipped'] += 1
                        pbar.set_postfix(status="skipped (existing)")
                        continue
                    
                    # Process article
                    success = self._process_article(
                        article_url, content_selector, storage, 
                        original_archive_url, item.get('thumbnail_url')
                    )
                    
                    if success:
                        self.stats['articles_saved'] += 1
                        existing_ids.add(article_id)  # Add to set to avoid duplicates
                        pbar.set_postfix(status="saved")
                    else:
                        self.stats['articles_skipped'] += 1
                        pbar.set_postfix(status="failed")
                    
                    self.stats['articles_processed'] += 1
            
            return []  # Return empty list when not collecting URLs
            
        except Exception as e:
            self.logger.error(f"Error processing archive page {archive_url}: {e}")
            return []
    
    def _process_article(self, article_url: str, content_selector: str, 
                        storage: DataStorage, archive_url: str, 
                        thumbnail_url: str = None) -> bool:
        """Process a single article"""
        
        try:
            # Get article content
            content = self.crawler.get_page_content(article_url)
            if not content:
                self.logger.warning(f"Could not fetch article: {article_url}")
                return False
            
            # Extract article data
            article = self.extractor.extract_article_content(
                content, article_url, content_selector, 
                archive_url, self.crawler.current_engine.__class__.__name__
            )
            
            if not article:
                self.logger.warning(f"Could not extract content from: {article_url}")
                return False
            
            # Add thumbnail if available from archive data
            if thumbnail_url:
                article['thumbnail_url'] = thumbnail_url
            
            # Save article
            success = storage.save_article(article)
            if success:
                self.logger.debug(f"Saved article: {article_url}")
            else:
                self.logger.warning(f"Failed to save article: {article_url}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error processing article {article_url}: {e}")
            return False
    
    def _log_final_stats(self):
        """Log final scraping statistics"""
        self.logger.info("=== Scraping Statistics ===")
        self.logger.info(f"Archive pages processed: {self.stats['archive_pages_processed']}")
        self.logger.info(f"Archive items found: {self.stats['archive_items_found']}")
        self.logger.info(f"Articles processed: {self.stats['articles_processed']}")
        self.logger.info(f"Articles saved: {self.stats['articles_saved']}")
        self.logger.info(f"Articles skipped: {self.stats['articles_skipped']}")
        self.logger.info(f"Errors: {self.stats['errors']}")
    
    def _save_urls_to_file(self, urls_file: str, urls: List[str], 
                          archive_url: str, archive_selector: str, content_selector: str):
        """Save URLs to file for later use"""
        try:
            urls_data = {
                'archive_url': archive_url,
                'archive_selector': archive_selector,
                'content_selector': content_selector,
                'total_urls': len(urls),
                'urls': urls
            }
            
            with open(urls_file, 'w', encoding='utf-8') as f:
                json.dump(urls_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Saved {len(urls)} URLs to {urls_file}")
            
        except Exception as e:
            self.logger.error(f"Error saving URLs to file: {e}")
    
    def _process_articles_from_urls(self, urls: List[str], content_selector: str,
                                  storage: DataStorage, existing_ids: set, archive_url: str):
        """Process articles from a list of URLs"""
        
        self.logger.info(f"Processing {len(urls)} articles from URLs file")
        
        with tqdm(urls, desc="Processing articles", unit="article") as pbar:
            for article_url in pbar:
                article_id = generate_id(article_url)
                
                # Skip if already processed
                if article_id in existing_ids:
                    self.stats['articles_skipped'] += 1
                    pbar.set_postfix(status="skipped (existing)")
                    continue
                
                # Process article
                success = self._process_article(
                    article_url, content_selector, storage, archive_url
                )
                
                if success:
                    self.stats['articles_saved'] += 1
                    existing_ids.add(article_id)
                    pbar.set_postfix(status="saved")
                else:
                    self.stats['articles_skipped'] += 1
                    pbar.set_postfix(status="failed")
                
                self.stats['articles_processed'] += 1
    
    def _get_results(self, success: bool, error: str = None) -> Dict[str, Any]:
        """Get scraping results dictionary"""
        return {
            'success': success,
            'error': error,
            'stats': self.stats.copy()
        }

# CLI Commands
@click.command()
@click.option('--output', '-o', help='Output file path (will be overridden by slug if not provided)')
@click.option('--format', 'format_type', default='ndjson', 
              type=click.Choice(['ndjson', 'json']), help='Output format')
@click.option('--force-engine', type=click.Choice(['requests', 'playwright', 'selenium']),
              help='Force specific scraping engine')
@click.option('--delay', default=1.0, type=float, help='Delay between requests (seconds)')
@click.option('--timeout', default=30, type=int, help='Request timeout (seconds)')
@click.option('--ignore-robots', is_flag=True, help='Ignore robots.txt')
@click.option('--resume', is_flag=True, help='Resume from existing output file')
@click.option('--max-pages', type=int, help='Maximum pages to scrape')
@click.option('--log', help='Log file path (will be overridden by slug if not provided)')
@click.option('--log-level', default='INFO', 
              type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR']),
              help='Log level')
@click.option('--use-proxy', is_flag=True, help='Use proxy rotation')
@click.option('--test-proxies', is_flag=True, help='Test proxies before use')
@click.option('--skip-archive', is_flag=True, help='Skip archive scraping, only scrape from existing URLs file')
def main(output, format_type, force_engine, delay, timeout, ignore_robots,
         resume, max_pages, log, log_level, use_proxy, test_proxies, skip_archive):
    """Burmese Corpus Scraper CLI"""
    
    logger = None  # Will be set up after getting slug
    
    print("=== Burmese Corpus Scraper ===")
    
    # Get user input
    try:
        # Slug for file naming
        while True:
            slug_input = input("Enter project slug (will be used for file naming, e.g., 'Irrawaddy News' -> 'irrawaddy_news'): ").strip()
            if slug_input:
                slug = normalize_slug(slug_input)
                print(f"Normalized slug: {slug}")
                break
            print("Slug cannot be empty. Please enter a project name.")
        
        # Create directories if they don't exist
        Path("logs").mkdir(exist_ok=True)
        Path("data/raw").mkdir(parents=True, exist_ok=True)
        
        # Set up file paths based on slug
        if not output:
            output_extension = 'jsonl' if format_type == 'ndjson' else 'json'
            output = f"data/raw/{slug}.{output_extension}"
        
        if not log:
            log = f"logs/{slug}.log"
        
        # Set up URLs file path
        urls_file = f"data/raw/{slug}_urls.json"
        
        # Setup logging now that we have the log file path
        logger = setup_logging(log, log_level)
        logger.info("=== Burmese Corpus Scraper ===")
        logger.info(f"Project slug: {slug}")
        logger.info(f"Output file: {output}")
        logger.info(f"Log file: {log}")
        logger.info(f"URLs file: {urls_file}")
        
        # Skip prompts if skip-archive mode
        if skip_archive:
            # Check if URLs file exists
            if not Path(urls_file).exists():
                print(f"❌ URLs file {urls_file} not found. Cannot skip archive scraping.")
                print("Run without --skip-archive first to generate the URLs file.")
                sys.exit(1)
            
            # Load URLs from file
            with open(urls_file, 'r', encoding='utf-8') as f:
                urls_data = json.load(f)
            
            archive_url = urls_data.get('archive_url', '')
            archive_selector = urls_data.get('archive_selector', '')
            content_selector = urls_data.get('content_selector', '')
            pagination_type = 'none'  # Skip pagination in skip-archive mode
            pagination_param = None
            thumbnail_selector = "img"
            
            logger.info(f"Skip-archive mode: loaded {len(urls_data.get('urls', []))} URLs from {urls_file}")
            
        else:
            # Archive URL
            while True:
                archive_url = input("Enter archive/list page URL (must be a list/category/archive page; site root not accepted): ").strip()
                if is_valid_url(archive_url):
                    break
                print("Invalid URL. Please enter a valid URL with a path beyond the root domain.")
            
            # Archive selector
            while True:
                archive_selector = input("Enter archive/list item selector (CSS or XPath) — selector that identifies each article link block on the archive page: ").strip()
                if validate_selector_format(archive_selector):
                    break
                print("Invalid selector format. Please enter a valid CSS or XPath selector.")
            
            # Content selector
            while True:
                content_selector = input("Enter article detail page content selector (CSS or XPath) — selector that identifies the article main content (will capture raw HTML inside this selector): ").strip()
                if validate_selector_format(content_selector):
                    break
                print("Invalid selector format. Please enter a valid CSS or XPath selector.")
            
            # Pagination
            pagination_type = input("Is pagination/loadmore needed? Choose one: [none/queryparam/click/scroll] : ").strip().lower()
            pagination_param = None
            
            if pagination_type == 'queryparam':
                pagination_param = input("Enter page param template (example: ?page={n} or /page/{n}): ").strip()
            elif pagination_type == 'click':
                pagination_param = input("Enter CSS/XPath selector for the \"Load more\" or \"Next\" button to click: ").strip()
            elif pagination_type == 'scroll':
                pass  # No additional input needed
            elif pagination_type not in ['none', '']:
                print("Invalid pagination type, using 'none'")
                pagination_type = 'none'
            
            # Thumbnail - automatically include, find image in archive item
            thumbnail_selector = "img"  # Default to find any image in archive item
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    
    # Initialize rotators if requested
    proxy_rotator = None
    header_rotator = None
    
    if use_proxy:
        logger.info("Initializing proxy rotation...")
        proxy_rotator = ProxyRotator(max_proxies=20)
        proxy_rotator.create_proxy_pool(test_proxies=test_proxies)
    
    logger.info("Initializing header rotation...")
    header_rotator = HeaderRotator()
    
    # Initialize scraper
    scraper = BurmeseCorpusScraper(
        proxy_rotator=proxy_rotator,
        header_rotator=header_rotator,
        delay=delay,
        timeout=timeout,
        respect_robots=not ignore_robots
    )
    
    # Run scraper
    results = scraper.scrape(
        archive_url=archive_url,
        archive_selector=archive_selector,
        content_selector=content_selector,
        pagination_type=pagination_type,
        pagination_param=pagination_param,
        thumbnail_selector=thumbnail_selector,
        output_file=output,
        format_type=format_type,
        force_engine=force_engine,
        resume=resume,
        max_pages=max_pages,
        urls_file=urls_file,
        skip_archive=skip_archive
    )
    
    # Print results
    if results['success']:
        print("\n✅ Scraping completed successfully!")
        print(f"Output saved to: {output}")
        print(f"Articles saved: {results['stats']['articles_saved']}")
    else:
        print(f"\n❌ Scraping failed: {results['error']}")
        sys.exit(1)

if __name__ == '__main__':
    main()
