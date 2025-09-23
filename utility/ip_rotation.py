#!/usr/bin/env python3
"""
IP Rotation Utility for Web Scraping
Provides proxy rotation functionality for avoiding IP blocks during scraping

Features:
- Fetches free proxies from free-proxy-list.net
- Tests proxy functionality
- Provides rotation mechanism for scrapers
- Fallback to manual proxy list
- Error handling and logging
"""

import requests
from itertools import cycle
import traceback
import time
import random
import logging

# Try to import lxml, fallback to BeautifulSoup if not available
try:
    from lxml.html import fromstring
    LXML_AVAILABLE = True
except ImportError:
    try:
        from bs4 import BeautifulSoup
        LXML_AVAILABLE = False
        print("Warning: lxml not available, using BeautifulSoup as fallback")
    except ImportError:
        print("Error: Neither lxml nor BeautifulSoup available. Install with: pip install lxml beautifulsoup4")
        LXML_AVAILABLE = False
        BeautifulSoup = None

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProxyRotator:
    def __init__(self, manual_proxies=None, max_proxies=20):
        """
        Initialize proxy rotator
        
        Args:
            manual_proxies (list): Optional list of manual proxy IPs
            max_proxies (int): Maximum number of proxies to fetch
        """
        self.manual_proxies = manual_proxies or []
        self.max_proxies = max_proxies
        self.working_proxies = []
        self.proxy_pool = None
        self.failed_proxies = set()
        
    def get_free_proxies(self):
        """
        Fetch free proxies from free-proxy-list.net
        
        Returns:
            set: Set of proxy addresses in format 'ip:port'
        """
        logger.info("Fetching free proxies...")
        proxies = set()
        
        try:
            url = 'https://free-proxy-list.net/'
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            if LXML_AVAILABLE:
                # Use lxml for parsing
                parser = fromstring(response.text)
                rows = parser.xpath('//tbody/tr')[:self.max_proxies]
                
                for row in rows:
                    # Check if HTTPS is supported (column 7)
                    https_support = row.xpath('.//td[7][contains(text(),"yes")]')
                    if https_support:
                        try:
                            ip = row.xpath('.//td[1]/text()')[0]
                            port = row.xpath('.//td[2]/text()')[0]
                            proxy = f"{ip}:{port}"
                            proxies.add(proxy)
                        except (IndexError, AttributeError):
                            continue
            
            elif BeautifulSoup:
                # Use BeautifulSoup as fallback
                soup = BeautifulSoup(response.text, 'html.parser')
                table = soup.find('table', {'id': 'proxylisttable'})
                if table:
                    rows = table.find('tbody').find_all('tr')[:self.max_proxies]
                    
                    for row in rows:
                        cells = row.find_all('td')
                        if len(cells) >= 7 and 'yes' in cells[6].text.lower():
                            try:
                                ip = cells[0].text.strip()
                                port = cells[1].text.strip()
                                proxy = f"{ip}:{port}"
                                proxies.add(proxy)
                            except (IndexError, AttributeError):
                                continue
            
            logger.info(f"Found {len(proxies)} potential proxies")
            
        except Exception as e:
            logger.error(f"Error fetching proxies: {e}")
        
        return proxies
    
    def test_proxy(self, proxy, test_url='https://httpbin.org/ip', timeout=10):
        """
        Test if a proxy is working
        
        Args:
            proxy (str): Proxy address in format 'ip:port'
            test_url (str): URL to test proxy against
            timeout (int): Request timeout in seconds
            
        Returns:
            bool: True if proxy works, False otherwise
        """
        try:
            proxy_dict = {
                'http': f'http://{proxy}',
                'https': f'http://{proxy}'
            }
            
            response = requests.get(
                test_url, 
                proxies=proxy_dict, 
                timeout=timeout,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            )
            
            if response.status_code == 200:
                return True
                
        except Exception:
            pass
        
        return False
    
    def get_working_proxies(self, test_proxies=True):
        """
        Get list of working proxies
        
        Args:
            test_proxies (bool): Whether to test proxies before adding to pool
            
        Returns:
            list: List of working proxy addresses
        """
        all_proxies = set()
        
        # Add manual proxies if provided
        if self.manual_proxies:
            all_proxies.update(self.manual_proxies)
            logger.info(f"Added {len(self.manual_proxies)} manual proxies")
        
        # Fetch free proxies
        free_proxies = self.get_free_proxies()
        all_proxies.update(free_proxies)
        
        # Test proxies if requested
        if test_proxies and all_proxies:
            logger.info(f"Testing {len(all_proxies)} proxies...")
            working_proxies = []
            
            for i, proxy in enumerate(all_proxies, 1):
                if proxy in self.failed_proxies:
                    continue
                    
                logger.info(f"Testing proxy {i}/{len(all_proxies)}: {proxy}")
                
                if self.test_proxy(proxy):
                    working_proxies.append(proxy)
                    logger.info(f"✅ Proxy {proxy} is working")
                else:
                    self.failed_proxies.add(proxy)
                    logger.warning(f"❌ Proxy {proxy} failed")
                
                # Add small delay between tests
                time.sleep(random.uniform(0.5, 1.5))
            
            self.working_proxies = working_proxies
            logger.info(f"Found {len(working_proxies)} working proxies")
            
        else:
            self.working_proxies = list(all_proxies)
            logger.info(f"Using {len(self.working_proxies)} proxies without testing")
        
        return self.working_proxies
    
    def create_proxy_pool(self, test_proxies=True):
        """
        Create a cycling proxy pool
        
        Args:
            test_proxies (bool): Whether to test proxies before adding to pool
            
        Returns:
            itertools.cycle: Cycling iterator of working proxies
        """
        working_proxies = self.get_working_proxies(test_proxies)
        
        if working_proxies:
            self.proxy_pool = cycle(working_proxies)
            logger.info(f"Created proxy pool with {len(working_proxies)} proxies")
            return self.proxy_pool
        else:
            logger.warning("No working proxies found!")
            return None
    
    def get_next_proxy(self):
        """
        Get next proxy from the pool
        
        Returns:
            str: Next proxy address or None if no proxies available
        """
        if self.proxy_pool:
            return next(self.proxy_pool)
        return None
    
    def make_request(self, url, max_retries=3, **kwargs):
        """
        Make a request using proxy rotation
        
        Args:
            url (str): URL to request
            max_retries (int): Maximum number of proxy retries
            **kwargs: Additional arguments for requests.get()
            
        Returns:
            requests.Response: Response object or None if all proxies failed
        """
        if not self.proxy_pool:
            logger.warning("No proxy pool available, making direct request")
            try:
                return requests.get(url, **kwargs)
            except Exception as e:
                logger.error(f"Direct request failed: {e}")
                return None
        
        for attempt in range(max_retries):
            proxy = self.get_next_proxy()
            if not proxy:
                logger.error("No more proxies available")
                break
                
            try:
                proxy_dict = {
                    'http': f'http://{proxy}',
                    'https': f'http://{proxy}'
                }
                
                logger.info(f"Attempt {attempt + 1}: Using proxy {proxy}")
                response = requests.get(url, proxies=proxy_dict, **kwargs)
                
                if response.status_code == 200:
                    logger.info(f"✅ Request successful with proxy {proxy}")
                    return response
                else:
                    logger.warning(f"❌ Proxy {proxy} returned status {response.status_code}")
                    
            except Exception as e:
                logger.warning(f"❌ Proxy {proxy} failed: {e}")
                self.failed_proxies.add(proxy)
                continue
        
        logger.error("All proxy attempts failed")
        return None


def demo_usage():
    """Demonstrate proxy rotation usage"""
    print("🔄 IP Rotation Demo")
    print("=" * 50)
    
    # Manual proxy list (add your own working proxies here)
    manual_proxies = [
        # '121.129.127.209:80',
        # '124.41.215.238:45169',
        # '185.93.3.123:8080'
    ]
    
    # Initialize proxy rotator
    rotator = ProxyRotator(manual_proxies=manual_proxies, max_proxies=10)
    
    # Create proxy pool (set test_proxies=False for faster setup)
    proxy_pool = rotator.create_proxy_pool(test_proxies=True)
    
    if proxy_pool:
        # Test URL to check IP
        test_url = 'https://httpbin.org/ip'
        
        print(f"\n🧪 Testing {min(5, len(rotator.working_proxies))} requests with different proxies:")
        
        for i in range(min(5, len(rotator.working_proxies))):
            print(f"\nRequest #{i + 1}:")
            response = rotator.make_request(test_url, timeout=10)
            
            if response:
                try:
                    ip_info = response.json()
                    print(f"  Current IP: {ip_info.get('origin', 'Unknown')}")
                except:
                    print(f"  Response received but couldn't parse JSON")
            else:
                print(f"  Request failed")
            
            # Small delay between requests
            time.sleep(2)
    
    else:
        print("❌ No working proxies found. You can:")
        print("1. Add manual proxies to the manual_proxies list")
        print("2. Check your internet connection")
        print("3. Try running again (free proxies change frequently)")


if __name__ == "__main__":
    demo_usage()