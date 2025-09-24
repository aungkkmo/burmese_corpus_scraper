#!/usr/bin/env python3
"""
Web crawler module for the Burmese corpus scraper
Handles different scraping engines: requests, playwright, selenium
"""

import requests
from bs4 import BeautifulSoup
import time
import random
import logging
from typing import Optional, Dict, List, Tuple
from urllib.robotparser import RobotFileParser
from urllib.parse import urljoin, urlparse
import asyncio

# Optional imports for headless browsers
try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.firefox.options import Options as FirefoxOptions
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

from .utils import normalize_url, extract_domain, is_css_selector

class ScrapingEngine:
    """Base class for scraping engines"""
    
    def __init__(self, proxy_rotator=None, header_rotator=None, delay=(0.5, 1.0), timeout=30):
        self.proxy_rotator = proxy_rotator
        self.header_rotator = header_rotator
        self.delay = delay
        self.timeout = timeout
        self.logger = logging.getLogger('burmese_scraper.engine')
    
    def get_page(self, url: str) -> Optional[str]:
        """Get page content - to be implemented by subclasses"""
        raise NotImplementedError
    
    def find_elements(self, content: str, selector: str) -> List[str]:
        """Find elements using selector - to be implemented by subclasses"""
        raise NotImplementedError
    
    def add_delay(self):
        """Add random delay between requests"""
        if isinstance(self.delay, tuple) and len(self.delay) == 2:
            min_delay, max_delay = self.delay
            if max_delay > 0:
                delay_time = random.uniform(min_delay, max_delay)
                time.sleep(delay_time)
        elif self.delay > 0:
            # Backward compatibility for single delay value
            delay_time = random.uniform(0.5, self.delay)
            time.sleep(delay_time)

class RequestsEngine(ScrapingEngine):
    """Requests-based scraping engine"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.session = requests.Session()
    
    def get_page(self, url: str) -> Optional[str]:
        """Get page content using requests"""
        try:
            # Get headers
            headers = {}
            if self.header_rotator:
                headers = self.header_rotator.generate_headers()
            
            # Make request with or without proxy
            if self.proxy_rotator:
                response = self.proxy_rotator.make_request(
                    url, 
                    headers=headers, 
                    timeout=self.timeout,
                    max_retries=3
                )
            else:
                response = self.session.get(
                    url, 
                    headers=headers, 
                    timeout=self.timeout
                )
            
            if response and response.status_code == 200:
                self.add_delay()
                return response.text
            else:
                self.logger.warning(f"Failed to get {url}: {response.status_code if response else 'No response'}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting {url}: {e}")
            return None
    
    def find_elements(self, content: str, selector: str) -> List[BeautifulSoup]:
        """Find elements using CSS selector with BeautifulSoup"""
        try:
            soup = BeautifulSoup(content, 'html.parser')
            
            if is_css_selector(selector):
                elements = soup.select(selector)
            else:
                # For XPath, we'll need to use lxml or convert to CSS
                # For now, treat as CSS and log warning
                self.logger.warning(f"XPath selector '{selector}' treated as CSS selector")
                elements = soup.select(selector)
            
            return elements
            
        except Exception as e:
            self.logger.error(f"Error finding elements with selector '{selector}': {e}")
            return []

class PlaywrightEngine(ScrapingEngine):
    """Playwright-based scraping engine"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.browser = None
        self.context = None
        self.page = None
    
    async def setup(self):
        """Setup playwright browser"""
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError("Playwright not available")
        
        try:
            self.playwright = await async_playwright().start()
            
            # Browser options - try headless first
            launch_options = {
                'headless': True,
                'args': ['--no-sandbox', '--disable-dev-shm-usage']
            }
            
            self.browser = await self.playwright.chromium.launch(**launch_options)
            
            # Context options
            context_options = {}
            if self.proxy_rotator and hasattr(self.proxy_rotator, 'get_next_proxy'):
                proxy = self.proxy_rotator.get_next_proxy()
                if proxy:
                    context_options['proxy'] = {
                        'server': f'http://{proxy}'
                    }
            
            self.context = await self.browser.new_context(**context_options)
            
            # Set headers
            if self.header_rotator:
                headers = self.header_rotator.generate_headers()
                await self.context.set_extra_http_headers(headers)
            
            self.page = await self.context.new_page()
            
        except Exception as e:
            self.logger.error(f"Error setting up Playwright: {e}")
            raise
    
    async def cleanup(self):
        """Cleanup playwright resources"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if hasattr(self, 'playwright'):
                await self.playwright.stop()
        except Exception as e:
            self.logger.error(f"Error cleaning up Playwright: {e}")
    
    async def get_page_async(self, url: str) -> Optional[str]:
        """Get page content using Playwright"""
        try:
            if not self.page:
                await self.setup()
            
            await self.page.goto(url, timeout=self.timeout * 1000)
            await self.page.wait_for_load_state('networkidle')
            
            content = await self.page.content()
            
            # Add delay
            if isinstance(self.delay, tuple) and len(self.delay) == 2:
                min_delay, max_delay = self.delay
                if max_delay > 0:
                    delay_time = random.uniform(min_delay, max_delay)
                    await asyncio.sleep(delay_time)
            elif self.delay > 0:
                # Backward compatibility for single delay value
                await asyncio.sleep(random.uniform(0.5, self.delay))
            
            return content
            
        except Exception as e:
            self.logger.warning(f"Headless Playwright failed for {url}: {e}")
            # Try with visible browser if headless fails
            try:
                await self.cleanup()
                await self.setup_visible()
                
                await self.page.goto(url, timeout=self.timeout * 1000)
                await self.page.wait_for_load_state('networkidle')
                
                content = await self.page.content()
                
                if isinstance(self.delay, tuple) and len(self.delay) == 2:
                    min_delay, max_delay = self.delay
                    if max_delay > 0:
                        delay_time = random.uniform(min_delay, max_delay)
                        await asyncio.sleep(delay_time)
                elif self.delay > 0:
                    # Backward compatibility for single delay value
                    await asyncio.sleep(random.uniform(0.5, self.delay))
                
                self.logger.info(f"Visible browser succeeded for {url}")
                return content
                
            except Exception as e2:
                self.logger.error(f"Both headless and visible Playwright failed for {url}: {e2}")
                return None
    
    async def setup_visible(self):
        """Setup playwright browser in visible mode"""
        try:
            self.playwright = await async_playwright().start()
            
            # Browser options - visible mode
            launch_options = {
                'headless': False,
                'args': ['--no-sandbox', '--disable-dev-shm-usage']
            }
            
            self.browser = await self.playwright.chromium.launch(**launch_options)
            
            # Context options
            context_options = {}
            if self.proxy_rotator and hasattr(self.proxy_rotator, 'get_next_proxy'):
                proxy = self.proxy_rotator.get_next_proxy()
                if proxy:
                    context_options['proxy'] = {
                        'server': f'http://{proxy}'
                    }
            
            self.context = await self.browser.new_context(**context_options)
            
            # Set headers
            if self.header_rotator:
                headers = self.header_rotator.generate_headers()
                await self.context.set_extra_http_headers(headers)
            
            self.page = await self.context.new_page()
            
        except Exception as e:
            self.logger.error(f"Error setting up visible Playwright: {e}")
            raise
    
    def get_page(self, url: str) -> Optional[str]:
        """Sync wrapper for get_page_async"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.get_page_async(url))
    
    def find_elements(self, content: str, selector: str) -> List[BeautifulSoup]:
        """Find elements using BeautifulSoup (same as requests engine)"""
        try:
            soup = BeautifulSoup(content, 'html.parser')
            
            if is_css_selector(selector):
                elements = soup.select(selector)
            else:
                self.logger.warning(f"XPath selector '{selector}' treated as CSS selector")
                elements = soup.select(selector)
            
            return elements
            
        except Exception as e:
            self.logger.error(f"Error finding elements with selector '{selector}': {e}")
            return []

class SeleniumEngine(ScrapingEngine):
    """Selenium-based scraping engine"""
    
    def __init__(self, browser='chrome', **kwargs):
        super().__init__(**kwargs)
        self.browser_type = browser
        self.driver = None
    
    def setup(self):
        """Setup selenium webdriver"""
        if not SELENIUM_AVAILABLE:
            raise ImportError("Selenium not available")
        
        try:
            if self.browser_type.lower() == 'chrome':
                options = ChromeOptions()
                options.add_argument('--headless')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--disable-gpu')
                
                # Add proxy if available
                if self.proxy_rotator and hasattr(self.proxy_rotator, 'get_next_proxy'):
                    proxy = self.proxy_rotator.get_next_proxy()
                    if proxy:
                        options.add_argument(f'--proxy-server=http://{proxy}')
                
                # Add user agent if available
                if self.header_rotator:
                    headers = self.header_rotator.generate_headers()
                    if 'User-Agent' in headers:
                        options.add_argument(f'--user-agent={headers["User-Agent"]}')
                
                self.driver = webdriver.Chrome(options=options)
                
            elif self.browser_type.lower() == 'firefox':
                options = FirefoxOptions()
                options.add_argument('--headless')
                
                self.driver = webdriver.Firefox(options=options)
            
            else:
                raise ValueError(f"Unsupported browser: {self.browser_type}")
            
            self.driver.set_page_load_timeout(self.timeout)
            
        except Exception as e:
            self.logger.error(f"Error setting up Selenium: {e}")
            raise
    
    def cleanup(self):
        """Cleanup selenium resources"""
        try:
            if self.driver:
                self.driver.quit()
        except Exception as e:
            self.logger.error(f"Error cleaning up Selenium: {e}")
    
    def get_page(self, url: str) -> Optional[str]:
        """Get page content using Selenium"""
        try:
            if not self.driver:
                self.setup()
            
            self.driver.get(url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            content = self.driver.page_source
            self.add_delay()
            
            return content
            
        except Exception as e:
            self.logger.warning(f"Headless Selenium failed for {url}: {e}")
            # Try with visible browser if headless fails
            try:
                self.cleanup()
                self.setup_visible()
                
                self.driver.get(url)
                
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                content = self.driver.page_source
                self.add_delay()
                
                self.logger.info(f"Visible Selenium succeeded for {url}")
                return content
                
            except Exception as e2:
                self.logger.error(f"Both headless and visible Selenium failed for {url}: {e2}")
                return None
    
    def setup_visible(self):
        """Setup selenium webdriver in visible mode"""
        if not SELENIUM_AVAILABLE:
            raise ImportError("Selenium not available")
        
        try:
            if self.browser_type.lower() == 'chrome':
                options = ChromeOptions()
                # Remove headless option for visible mode
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--disable-gpu')
                
                # Add proxy if available
                if self.proxy_rotator and hasattr(self.proxy_rotator, 'get_next_proxy'):
                    proxy = self.proxy_rotator.get_next_proxy()
                    if proxy:
                        options.add_argument(f'--proxy-server=http://{proxy}')
                
                # Add user agent if available
                if self.header_rotator:
                    headers = self.header_rotator.generate_headers()
                    if 'User-Agent' in headers:
                        options.add_argument(f'--user-agent={headers["User-Agent"]}')
                
                self.driver = webdriver.Chrome(options=options)
                
            elif self.browser_type.lower() == 'firefox':
                options = FirefoxOptions()
                # Remove headless option for visible mode
                
                self.driver = webdriver.Firefox(options=options)
            
            else:
                raise ValueError(f"Unsupported browser: {self.browser_type}")
            
            self.driver.set_page_load_timeout(self.timeout)
            
        except Exception as e:
            self.logger.error(f"Error setting up visible Selenium: {e}")
            raise
    
    def find_elements(self, content: str, selector: str) -> List[BeautifulSoup]:
        """Find elements using BeautifulSoup (same as other engines)"""
        try:
            soup = BeautifulSoup(content, 'html.parser')
            
            if is_css_selector(selector):
                elements = soup.select(selector)
            else:
                self.logger.warning(f"XPath selector '{selector}' treated as CSS selector")
                elements = soup.select(selector)
            
            return elements
            
        except Exception as e:
            self.logger.error(f"Error finding elements with selector '{selector}': {e}")
            return []

class WebCrawler:
    """Main web crawler that manages different engines"""
    
    def __init__(self, proxy_rotator=None, header_rotator=None, 
                 delay=(0.5, 1.0), timeout=30, respect_robots=True):
        self.proxy_rotator = proxy_rotator
        self.header_rotator = header_rotator
        self.delay = delay
        self.timeout = timeout
        self.respect_robots = respect_robots
        self.logger = logging.getLogger('burmese_scraper.crawler')
        
        self.current_engine = None
        self.robots_cache = {}
    
    def check_robots_txt(self, url: str, user_agent: str = '*') -> bool:
        """Check if URL is allowed by robots.txt"""
        if not self.respect_robots:
            return True
        
        try:
            domain = extract_domain(url)
            
            if domain not in self.robots_cache:
                robots_url = f"http://{domain}/robots.txt"
                rp = RobotFileParser()
                rp.set_url(robots_url)
                rp.read()
                self.robots_cache[domain] = rp
            
            return self.robots_cache[domain].can_fetch(user_agent, url)
            
        except Exception as e:
            self.logger.warning(f"Error checking robots.txt for {url}: {e}")
            return True  # Allow by default if can't check
    
    def test_engine(self, engine_class, url: str, selector: str) -> Tuple[bool, Optional[str]]:
        """Test if an engine can successfully scrape the given URL and selector"""
        try:
            engine = engine_class(
                proxy_rotator=self.proxy_rotator,
                header_rotator=self.header_rotator,
                delay=0,  # No delay for testing
                timeout=self.timeout
            )
            
            # Get page content
            content = engine.get_page(url)
            if not content:
                return False, "Failed to get page content"
            
            # Test selector
            elements = engine.find_elements(content, selector)
            if not elements:
                return False, f"No elements found with selector '{selector}'"
            
            # Cleanup if needed
            if hasattr(engine, 'cleanup'):
                engine.cleanup()
            
            return True, f"Found {len(elements)} elements"
            
        except Exception as e:
            return False, str(e)
    
    def choose_engine(self, archive_url: str, archive_selector: str, 
                     content_selector: str, force_engine: str = None) -> Optional[ScrapingEngine]:
        """Choose the best scraping engine based on testing"""
        
        if force_engine:
            engine_map = {
                'requests': RequestsEngine,
                'playwright': PlaywrightEngine,
                'selenium': SeleniumEngine
            }
            
            if force_engine not in engine_map:
                self.logger.error(f"Unknown engine: {force_engine}")
                return None
            
            try:
                engine = engine_map[force_engine](
                    proxy_rotator=self.proxy_rotator,
                    header_rotator=self.header_rotator,
                    delay=self.delay,
                    timeout=self.timeout
                )
                self.logger.info(f"Using forced engine: {force_engine}")
                return engine
            except Exception as e:
                self.logger.error(f"Failed to initialize forced engine {force_engine}: {e}")
                return None
        
        # Test engines in order of preference for archive page
        engines_to_test = [
            ('requests', RequestsEngine),
            ('playwright', PlaywrightEngine) if PLAYWRIGHT_AVAILABLE else None,
            ('selenium', SeleniumEngine) if SELENIUM_AVAILABLE else None
        ]
        
        engines_to_test = [e for e in engines_to_test if e is not None]
        
        for engine_name, engine_class in engines_to_test:
            self.logger.info(f"Testing {engine_name} engine for archive page...")
            
            # Test archive page
            success, message = self.test_engine(engine_class, archive_url, archive_selector)
            if not success:
                self.logger.warning(f"{engine_name} failed archive test: {message}")
                continue
            
            self.logger.info(f"{engine_name} passed archive test: {message}")
            
            # Initialize and return the working engine
            try:
                engine = engine_class(
                    proxy_rotator=self.proxy_rotator,
                    header_rotator=self.header_rotator,
                    delay=self.delay,
                    timeout=self.timeout
                )
                self.logger.info(f"Selected {engine_name} engine for archive")
                return engine
            except Exception as e:
                self.logger.error(f"Failed to initialize {engine_name}: {e}")
                continue
        
        self.logger.error("No working engines found for archive")
        return None
    
    def choose_detail_engine(self, sample_url: str, content_selector: str, 
                           force_engine: str = None) -> Optional[ScrapingEngine]:
        """Choose the best scraping engine for detail pages"""
        
        if force_engine:
            engine_map = {
                'requests': RequestsEngine,
                'playwright': PlaywrightEngine,
                'selenium': SeleniumEngine
            }
            
            if force_engine not in engine_map:
                self.logger.error(f"Unknown engine: {force_engine}")
                return None
            
            try:
                engine = engine_map[force_engine](
                    proxy_rotator=self.proxy_rotator,
                    header_rotator=self.header_rotator,
                    delay=self.delay,
                    timeout=self.timeout
                )
                self.logger.info(f"Using forced engine for detail pages: {force_engine}")
                return engine
            except Exception as e:
                self.logger.error(f"Failed to initialize forced engine {force_engine}: {e}")
                return None
        
        # Test engines in order of preference for detail pages
        engines_to_test = [
            ('requests', RequestsEngine),
            ('playwright', PlaywrightEngine) if PLAYWRIGHT_AVAILABLE else None,
            ('selenium', SeleniumEngine) if SELENIUM_AVAILABLE else None
        ]
        
        engines_to_test = [e for e in engines_to_test if e is not None]
        
        for engine_name, engine_class in engines_to_test:
            self.logger.info(f"Testing {engine_name} engine for detail pages...")
            
            # Test detail page
            success, message = self.test_engine(engine_class, sample_url, content_selector)
            if not success:
                self.logger.warning(f"{engine_name} failed detail page test: {message}")
                continue
            
            self.logger.info(f"{engine_name} passed detail page test: {message}")
            
            # Initialize and return the working engine
            try:
                engine = engine_class(
                    proxy_rotator=self.proxy_rotator,
                    header_rotator=self.header_rotator,
                    delay=self.delay,
                    timeout=self.timeout
                )
                self.logger.info(f"Selected {engine_name} engine for detail pages")
                return engine
            except Exception as e:
                self.logger.error(f"Failed to initialize {engine_name}: {e}")
                continue
        
        self.logger.error("No working engines found for detail pages")
        return None
    
    def get_page_content(self, url: str) -> Optional[str]:
        """Get page content using current engine"""
        if not self.current_engine:
            self.logger.error("No engine selected")
            return None
        
        if not self.check_robots_txt(url):
            self.logger.warning(f"Robots.txt disallows access to {url}")
            return None
        
        return self.current_engine.get_page(url)
    
    def get_page_with_pagination(self, url: str, button_selector: str, max_pages: int) -> Optional[str]:
        """Get page content with load more button pagination"""
        if not self.current_engine:
            self.logger.error("No engine selected")
            return None
        
        # Only works with Playwright engine
        if not hasattr(self.current_engine, 'page') or not self.current_engine.page:
            self.logger.warning("Load more pagination requires Playwright engine")
            return self.get_page_content(url)  # Fallback to regular content
        
        try:
            import asyncio
            import random
            
            async def load_more_pagination():
                # Use the EXISTING page from current engine
                page = self.current_engine.page
                
                # Make sure we're on the right page
                current_url = page.url
                if current_url != url:
                    await page.goto(url, timeout=self.timeout * 1000)
                    await page.wait_for_load_state('networkidle')
                
                clicks_performed = 0
                max_clicks = max_pages - 1 if max_pages else 10  # Default to 10 clicks
                
                # Simple load more button clicking loop
                while clicks_performed < max_clicks:
                    try:
                        # Check if load more button exists
                        button_exists = await page.evaluate(f"""
                            () => {{
                                const btn = document.querySelector("{button_selector}");
                                return btn !== null && btn.offsetParent !== null;
                            }}
                        """)
                        
                        if not button_exists:
                            self.logger.info(f"No more load more button found after {clicks_performed} button clicks")
                            break
                        
                        self.logger.info(f"Clicking load more button ({clicks_performed + 1})")
                        
                        # Click the button
                        await page.evaluate(f"""
                            () => {{
                                const btn = document.querySelector("{button_selector}");
                                if (btn) {{
                                    btn.click();
                                }}
                            }}
                        """)
                        
                        clicks_performed += 1
                        
                        # Wait 1 second as requested
                        await page.wait_for_timeout(1000)
                        
                    except Exception as e:
                        self.logger.warning(f"Error clicking load more button: {e}")
                        break
                
                self.logger.info(f"Completed load more pagination with {clicks_performed} button clicks")
                
                # Get final content
                return await page.content()
            
            # Run the async function using existing event loop
            try:
                # Try to get existing event loop
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If loop is already running, we need to use a different approach
                    import nest_asyncio
                    nest_asyncio.apply()
                    return loop.run_until_complete(load_more_pagination())
                else:
                    return loop.run_until_complete(load_more_pagination())
            except RuntimeError:
                # No event loop exists, create a new one
                return asyncio.run(load_more_pagination())
                
        except Exception as e:
            self.logger.error(f"Error during load more pagination: {e}")
            return self.get_page_content(url)  # Fallback to regular content
    
    def find_elements(self, content: str, selector: str) -> List:
        """Find elements using current engine"""
        if not self.current_engine:
            self.logger.error("No engine selected")
            return []
        
        return self.current_engine.find_elements(content, selector)
    
    def cleanup(self):
        """Cleanup current engine"""
        if self.current_engine and hasattr(self.current_engine, 'cleanup'):
            self.current_engine.cleanup()
