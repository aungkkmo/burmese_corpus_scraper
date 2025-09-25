#!/usr/bin/env python3
"""
Debug script to examine what the extractor receives
"""

import sys
import os

# Add the scraper directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scraper'))

from scraper.crawler import RequestsEngine
from scraper.extractor import ContentExtractor
from bs4 import BeautifulSoup
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

def debug_extractor():
    """Debug what the extractor receives vs what it processes"""
    
    url = "https://burmese.shannews.org/archives/category/news"
    selector = ".td-module-title a"
    
    print("🔍 Debugging extractor processing...")
    print(f"URL: {url}")
    print(f"Selector: {selector}")
    print("=" * 60)
    
    try:
        # Get page content like the scraper does
        engine = RequestsEngine(
            proxy_rotator=None,
            header_rotator=None,
            delay=(3.0, 6.0),
            timeout=30
        )
        
        content = engine.get_page(url)
        if not content:
            print("❌ Failed to get content")
            return
        
        print(f"✅ Got content ({len(content)} characters)")
        
        # Test what the validation finds
        elements = engine.find_elements(content, selector)
        print(f"✅ Validation finds: {len(elements)} elements")
        
        # Show first few elements found by validation
        print("\n📋 Elements found by validation:")
        for i, elem in enumerate(elements[:3]):
            href = elem.get('href', 'NO HREF')
            text = elem.get_text().strip()[:50] + ("..." if len(elem.get_text().strip()) > 50 else "")
            print(f"   {i+1}. href='{href}' text='{text}'")
            print(f"      tag='{elem.name}' attrs={dict(elem.attrs)}")
        
        # Now test what the extractor finds
        print("\n🔍 Testing extractor...")
        extractor = ContentExtractor()
        
        # Use the same content and selector
        archive_items = extractor.extract_archive_items(content, url, selector)
        print(f"✅ Extractor finds: {len(archive_items)} items")
        
        if archive_items:
            print("\n📋 Items found by extractor:")
            for i, item in enumerate(archive_items[:3]):
                print(f"   {i+1}. {item}")
        else:
            print("❌ No items found by extractor")
            
            # Let's debug the extractor step by step
            print("\n🔍 Debugging extractor step by step...")
            
            soup = BeautifulSoup(content, 'html.parser')
            elements = soup.select(selector)
            print(f"   BeautifulSoup.select() finds: {len(elements)} elements")
            
            for i, element in enumerate(elements[:3]):
                print(f"\n   Element {i+1}:")
                print(f"     Tag: {element.name}")
                print(f"     Attrs: {dict(element.attrs)}")
                print(f"     Text: '{element.get_text().strip()[:50]}'")
                
                # Test the extractor's link finding logic
                link_element = element.find('a')
                print(f"     element.find('a'): {link_element}")
                
                if not link_element or not link_element.get('href'):
                    link_element = element.find('a', href=True)
                    print(f"     element.find('a', href=True): {link_element}")
                
                # Check if the element itself is an 'a' tag
                if element.name == 'a':
                    print(f"     Element IS an 'a' tag")
                    print(f"     href: {element.get('href')}")
                else:
                    print(f"     Element is NOT an 'a' tag")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_extractor()
