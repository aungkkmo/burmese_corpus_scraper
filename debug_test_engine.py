#!/usr/bin/env python3
"""
Debug script that mimics the exact test_engine method
"""

import sys
import os

# Add the scraper directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scraper'))

from scraper.crawler import RequestsEngine
from scraper.utils import is_css_selector, parse_delay_range
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

def debug_test_engine():
    """Debug the exact test_engine method for Shan News"""
    
    url = "https://burmese.shannews.org/archives/category/news"
    selector = ".td-module-title a"
    
    print("🔍 Debugging EXACT test_engine method...")
    print(f"URL: {url}")
    print(f"Selector: {selector}")
    print("=" * 60)
    
    try:
        # Parse delay exactly like the scraper does
        delay_str = "3,6"
        delay_tuple = parse_delay_range(delay_str)
        print(f"Parsed delay: {delay_tuple}")
        
        # Create engine exactly like test_engine does
        engine = RequestsEngine(
            proxy_rotator=None,
            header_rotator=None,
            delay=0,  # No delay for testing (like test_engine)
            timeout=30
        )
        
        print("✅ Created RequestsEngine for testing")
        
        # Get page content exactly like test_engine
        print("📥 Fetching page content...")
        content = engine.get_page(url)
        
        if not content:
            print("❌ Failed to get page content")
            return False, "Failed to get page content"
        
        print(f"✅ Got page content ({len(content)} characters)")
        
        # Test selector exactly like test_engine
        print(f"🧪 Testing selector: {selector}")
        elements = engine.find_elements(content, selector)
        
        if not elements:
            print("❌ No elements found!")
            return False, f"No elements found with selector '{selector}'"
        
        print(f"✅ Found {len(elements)} elements")
        
        # Show first few elements
        for i, elem in enumerate(elements[:3]):
            href = elem.get('href', 'No href')
            text = elem.get_text().strip()[:50] + ("..." if len(elem.get_text().strip()) > 50 else "")
            print(f"   {i+1}. {href} - '{text}'")
        
        # Cleanup if needed
        if hasattr(engine, 'cleanup'):
            engine.cleanup()
        
        return True, f"Found {len(elements)} elements"
        
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return False, str(e)

def test_with_different_delays():
    """Test with different delay configurations"""
    
    url = "https://burmese.shannews.org/archives/category/news"
    selector = ".td-module-title a"
    
    delay_configs = [
        (0, "No delay (test_engine style)"),
        ((0.5, 1.0), "Default delay tuple"),
        ((3.0, 6.0), "Configured delay tuple"),
        (3.0, "Single delay value")
    ]
    
    print("\n" + "=" * 60)
    print("TESTING WITH DIFFERENT DELAY CONFIGURATIONS")
    print("=" * 60)
    
    for delay, description in delay_configs:
        print(f"\n🧪 Testing with {description}: {delay}")
        
        try:
            engine = RequestsEngine(
                proxy_rotator=None,
                header_rotator=None,
                delay=delay,
                timeout=30
            )
            
            content = engine.get_page(url)
            if content:
                elements = engine.find_elements(content, selector)
                print(f"   Result: {len(elements)} elements found")
            else:
                print("   Result: Failed to get content")
                
        except Exception as e:
            print(f"   Result: Exception - {e}")

if __name__ == "__main__":
    success, message = debug_test_engine()
    print(f"\n🎯 Final result: {success} - {message}")
    
    test_with_different_delays()
