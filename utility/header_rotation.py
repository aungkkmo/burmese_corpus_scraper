#!/usr/bin/env python3
"""
Header Rotation Utility for Web Scraping
Provides user agent and header rotation functionality to avoid detection

Features:
- Realistic user agent rotation
- Browser header simulation
- Language and encoding variation
- Random header combinations
- Easy integration with scrapers
"""

import random
import time
from itertools import cycle

class HeaderRotator:
    def __init__(self, custom_user_agents=None):
        """
        Initialize header rotator
        
        Args:
            custom_user_agents (list): Optional list of custom user agents
        """
        self.custom_user_agents = custom_user_agents or []
        self.user_agent_pool = None
        self.current_headers = {}
        
        # Initialize user agent pool
        self.create_user_agent_pool()
    
    def get_default_user_agents(self):
        """Get list of realistic user agents"""
        user_agents = [
            # Chrome on Windows
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
            
            # Chrome on macOS
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
            
            # Firefox on Windows
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:119.0) Gecko/20100101 Firefox/119.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:118.0) Gecko/20100101 Firefox/118.0',
            
            # Firefox on macOS
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:119.0) Gecko/20100101 Firefox/119.0',
            
            # Safari on macOS
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15',
            
            # Edge on Windows
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0',
            
            # Chrome on Linux
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            
            # Mobile Chrome
            'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/120.0.0.0 Mobile/15E148 Safari/604.1'
        ]
        
        return user_agents
    
    def create_user_agent_pool(self):
        """Create a cycling pool of user agents"""
        all_user_agents = self.get_default_user_agents()
        
        # Add custom user agents if provided
        if self.custom_user_agents:
            all_user_agents.extend(self.custom_user_agents)
        
        # Create cycling pool
        self.user_agent_pool = cycle(all_user_agents)
    
    def get_next_user_agent(self):
        """Get next user agent from the pool"""
        if self.user_agent_pool:
            return next(self.user_agent_pool)
        return self.get_default_user_agents()[0]  # Fallback
    
    def get_random_user_agent(self):
        """Get a random user agent"""
        all_user_agents = self.get_default_user_agents()
        if self.custom_user_agents:
            all_user_agents.extend(self.custom_user_agents)
        return random.choice(all_user_agents)
    
    def get_accept_headers(self):
        """Get realistic Accept headers"""
        accept_options = [
            'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        ]
        return random.choice(accept_options)
    
    def get_accept_language_headers(self):
        """Get realistic Accept-Language headers"""
        language_options = [
            'en-US,en;q=0.9',
            'en-US,en;q=0.9,my;q=0.8',
            'en-GB,en;q=0.9,en-US;q=0.8',
            'en-US,en;q=0.8,my;q=0.7',
            'my-MM,my;q=0.9,en;q=0.8',
            'my,en-US;q=0.9,en;q=0.8',
        ]
        return random.choice(language_options)
    
    def get_accept_encoding_headers(self):
        """Get realistic Accept-Encoding headers"""
        encoding_options = [
            'gzip, deflate, br',
            'gzip, deflate',
            'gzip, deflate, br, zstd',
        ]
        return random.choice(encoding_options)
    
    def get_connection_headers(self):
        """Get realistic Connection headers"""
        connection_options = [
            'keep-alive',
            'close',
        ]
        return random.choice(connection_options)
    
    def get_cache_control_headers(self):
        """Get realistic Cache-Control headers"""
        cache_options = [
            'max-age=0',
            'no-cache',
            'max-age=0, no-cache',
            None  # Sometimes no cache control
        ]
        return random.choice(cache_options)
    
    def get_sec_headers(self, user_agent):
        """Get Sec-* headers based on user agent"""
        headers = {}
        
        # Determine browser type from user agent
        if 'Chrome' in user_agent:
            headers.update({
                'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"' if 'Windows' in user_agent else '"macOS"',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1'
            })
        elif 'Firefox' in user_agent:
            # Firefox doesn't send Sec-Ch-Ua headers
            headers.update({
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1'
            })
        
        return headers
    
    def generate_headers(self, use_random=True, include_sec_headers=True):
        """
        Generate a complete set of realistic headers
        
        Args:
            use_random (bool): Use random user agent vs cycling
            include_sec_headers (bool): Include Sec-* headers
            
        Returns:
            dict: Complete header set
        """
        # Get user agent
        if use_random:
            user_agent = self.get_random_user_agent()
        else:
            user_agent = self.get_next_user_agent()
        
        # Build headers
        headers = {
            'User-Agent': user_agent,
            'Accept': self.get_accept_headers(),
            'Accept-Language': self.get_accept_language_headers(),
            'Accept-Encoding': self.get_accept_encoding_headers(),
            'Connection': self.get_connection_headers(),
            'Upgrade-Insecure-Requests': '1',
            'DNT': random.choice(['1', None]),  # Do Not Track (sometimes present)
        }
        
        # Add cache control (sometimes)
        cache_control = self.get_cache_control_headers()
        if cache_control:
            headers['Cache-Control'] = cache_control
        
        # Add Sec-* headers for modern browsers
        if include_sec_headers:
            sec_headers = self.get_sec_headers(user_agent)
            headers.update(sec_headers)
        
        # Remove None values
        headers = {k: v for k, v in headers.items() if v is not None}
        
        # Store current headers
        self.current_headers = headers.copy()
        
        return headers
    
    def get_current_headers(self):
        """Get the current headers"""
        return self.current_headers.copy()
    
    def update_referer(self, referer_url):
        """Update the Referer header"""
        if self.current_headers:
            self.current_headers['Referer'] = referer_url
        return self.current_headers.copy()
    
    def add_custom_headers(self, custom_headers):
        """Add custom headers to current headers"""
        if self.current_headers:
            self.current_headers.update(custom_headers)
        return self.current_headers.copy()
    
    def get_mobile_headers(self):
        """Get mobile-specific headers"""
        mobile_user_agents = [
            'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/120.0.0.0 Mobile/15E148 Safari/604.1'
        ]
        
        user_agent = random.choice(mobile_user_agents)
        
        headers = {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Add mobile-specific headers
        if 'Android' in user_agent:
            headers.update({
                'Sec-Ch-Ua-Mobile': '?1',
                'Sec-Ch-Ua-Platform': '"Android"'
            })
        elif 'iPhone' in user_agent:
            headers.update({
                'Sec-Ch-Ua-Mobile': '?1',
                'Sec-Ch-Ua-Platform': '"iOS"'
            })
        
        self.current_headers = headers.copy()
        return headers


def demo_header_rotation():
    """Demonstrate header rotation usage"""
    print("🔄 Header Rotation Demo")
    print("=" * 50)
    
    # Initialize header rotator
    rotator = HeaderRotator()
    
    print("🖥️  Desktop Headers:")
    for i in range(3):
        headers = rotator.generate_headers(use_random=True)
        print(f"\nSet {i+1}:")
        print(f"  User-Agent: {headers['User-Agent'][:60]}...")
        print(f"  Accept: {headers['Accept'][:50]}...")
        print(f"  Accept-Language: {headers['Accept-Language']}")
        print(f"  Connection: {headers['Connection']}")
    
    print("\n📱 Mobile Headers:")
    for i in range(2):
        headers = rotator.get_mobile_headers()
        print(f"\nMobile Set {i+1}:")
        print(f"  User-Agent: {headers['User-Agent'][:60]}...")
        print(f"  Accept: {headers['Accept'][:50]}...")
    
    print("\n🔧 Custom Headers Example:")
    headers = rotator.generate_headers()
    rotator.update_referer('https://google.com')
    rotator.add_custom_headers({'X-Requested-With': 'XMLHttpRequest'})
    updated_headers = rotator.get_current_headers()
    
    print(f"  Added Referer: {updated_headers.get('Referer')}")
    print(f"  Added Custom: {updated_headers.get('X-Requested-With')}")
    
    print("\n💡 Integration Example:")
    print("""
# Basic usage
rotator = HeaderRotator()
headers = rotator.generate_headers()
response = requests.get(url, headers=headers)

# With proxy rotation
from utility import ProxyRotator, HeaderRotator

proxy_rotator = ProxyRotator()
header_rotator = HeaderRotator()

headers = header_rotator.generate_headers()
response = proxy_rotator.make_request(url, headers=headers)
""")


if __name__ == "__main__":
    demo_header_rotation()
