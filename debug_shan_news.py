#!/usr/bin/env python3
"""
Debug script for Shan News selector issues
"""

import requests
from bs4 import BeautifulSoup
import time

def debug_shan_news():
    """Debug the Shan News website structure"""
    
    url = "https://burmese.shannews.org/archives/category/news"
    
    print("🔍 Debugging Shan News website structure...")
    print(f"URL: {url}")
    print("=" * 60)
    
    try:
        # Fetch the page
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        print(f"✅ Successfully fetched page (Status: {response.status_code})")
        print(f"📄 Page title: {soup.title.get_text() if soup.title else 'No title'}")
        print()
        
        # Test current selector
        current_selector = "div.td-module-meta-info > p > a"
        print(f"🧪 Testing current selector: {current_selector}")
        current_elements = soup.select(current_selector)
        print(f"   Found: {len(current_elements)} elements")
        
        if current_elements:
            for i, elem in enumerate(current_elements[:3]):
                print(f"   Element {i+1}: {elem}")
        print()
        
        # Try alternative selectors
        alternative_selectors = [
            "article a",
            ".td-module-title a", 
            ".entry-title a",
            ".td-module-meta-info a",
            "h3 a",
            ".td-module-container a",
            ".td-block-span12 a",
            "a[href*='/archives/']",
            ".td-module-thumb a",
            ".td-image-wrap a"
        ]
        
        print("🔍 Testing alternative selectors:")
        print("-" * 40)
        
        for selector in alternative_selectors:
            try:
                elements = soup.select(selector)
                print(f"'{selector}' -> {len(elements)} matches")
                
                if elements and len(elements) <= 5:
                    for i, elem in enumerate(elements[:3]):
                        href = elem.get('href', 'No href')
                        text = elem.get_text().strip()[:50] + ("..." if len(elem.get_text().strip()) > 50 else "")
                        print(f"   {i+1}. {href} - '{text}'")
                elif len(elements) > 5:
                    # Show first few
                    for i, elem in enumerate(elements[:2]):
                        href = elem.get('href', 'No href')
                        text = elem.get_text().strip()[:50] + ("..." if len(elem.get_text().strip()) > 50 else "")
                        print(f"   {i+1}. {href} - '{text}'")
                    print(f"   ... and {len(elements)-2} more")
                print()
                
            except Exception as e:
                print(f"'{selector}' -> ERROR: {e}")
        
        # Look for common article containers
        print("🏗️  Analyzing page structure:")
        print("-" * 40)
        
        # Find all divs with class containing 'module' or 'post' or 'article'
        containers = soup.find_all(['div', 'article'], class_=lambda x: x and any(
            keyword in ' '.join(x).lower() for keyword in ['module', 'post', 'article', 'item', 'entry']
        ))
        
        print(f"Found {len(containers)} potential article containers:")
        for i, container in enumerate(containers[:5]):
            classes = ' '.join(container.get('class', []))
            print(f"   {i+1}. <{container.name} class='{classes}'>")
            
            # Look for links within this container
            links = container.find_all('a', href=True)
            if links:
                for j, link in enumerate(links[:2]):
                    href = link.get('href')
                    if '/archives/' in href:
                        text = link.get_text().strip()[:40] + ("..." if len(link.get_text().strip()) > 40 else "")
                        print(f"      Link {j+1}: {href} - '{text}'")
            print()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_shan_news()
