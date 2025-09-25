#!/usr/bin/env python3
"""
Debug script that mimics the exact scraper flow
"""

import sys
import os

# Add the scraper directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scraper'))

from scraper.crawler import RequestsEngine
from scraper.utils import is_css_selector
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

def debug_scraper_flow():
    """Debug the exact scraper flow for Shan News"""
    
    url = "https://burmese.shannews.org/archives/category/news"
    selector = ".td-module-title a"
    
    print("🔍 Debugging EXACT scraper flow...")
    print(f"URL: {url}")
    print(f"Selector: {selector}")
    print("=" * 60)
    
    try:
        # Create the exact same engine the scraper uses
        engine = RequestsEngine(
            proxy_rotator=None,
            header_rotator=None,
            delay=(3.0, 6.0),
            timeout=30
        )
        
        print("✅ Created RequestsEngine")
        
        # Get page content exactly like the scraper
        print("📥 Fetching page content...")
        content = engine.get_page(url)
        
        if not content:
            print("❌ Failed to get page content")
            return
        
        print(f"✅ Got page content ({len(content)} characters)")
        
        # Test selector exactly like the scraper
        print(f"🧪 Testing selector: {selector}")
        print(f"   is_css_selector: {is_css_selector(selector)}")
        
        elements = engine.find_elements(content, selector)
        print(f"   Found: {len(elements)} elements")
        
        if elements:
            print("📋 First few elements:")
            for i, elem in enumerate(elements[:5]):
                href = elem.get('href', 'No href')
                text = elem.get_text().strip()[:50] + ("..." if len(elem.get_text().strip()) > 50 else "")
                print(f"   {i+1}. {href} - '{text}'")
        else:
            print("❌ No elements found!")
            
            # Debug: Let's see what the page actually contains
            print("\n🔍 Debugging page content...")
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(content, 'html.parser')
            
            # Look for any elements with 'td-module' in class
            td_elements = soup.find_all(class_=lambda x: x and 'td-module' in ' '.join(x))
            print(f"   Elements with 'td-module' class: {len(td_elements)}")
            
            for i, elem in enumerate(td_elements[:3]):
                classes = ' '.join(elem.get('class', []))
                print(f"   {i+1}. <{elem.name} class='{classes}'>")
            
            # Look for any title elements
            title_elements = soup.find_all(class_=lambda x: x and 'title' in ' '.join(x).lower())
            print(f"   Elements with 'title' in class: {len(title_elements)}")
            
            for i, elem in enumerate(title_elements[:3]):
                classes = ' '.join(elem.get('class', []))
                print(f"   {i+1}. <{elem.name} class='{classes}'>")
            
            # Look for any links to archives
            archive_links = soup.find_all('a', href=lambda x: x and '/archives/' in x)
            print(f"   Links to /archives/: {len(archive_links)}")
            
            for i, link in enumerate(archive_links[:5]):
                href = link.get('href')
                text = link.get_text().strip()[:40] + ("..." if len(link.get_text().strip()) > 40 else "")
                parent_classes = ' '.join(link.parent.get('class', [])) if link.parent else 'No parent'
                print(f"   {i+1}. {href} - '{text}' (parent: {parent_classes})")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_scraper_flow()
