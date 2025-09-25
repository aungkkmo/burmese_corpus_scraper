#!/usr/bin/env python3
"""
Test the enhanced selector validation function
"""

import sys
import os

# Add the scraper directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scraper'))

from utils import validate_selector_format

def test_selectors():
    """Test various selectors including the specific one"""
    
    test_cases = [
        # Valid CSS selectors
        ("div.content-right > div > article > h4.title", True, "Your specific selector"),
        ("div.content", True, "Simple class selector"),
        ("#main-content", True, "ID selector"),
        ("article h1, article h2", True, "Multiple selectors"),
        ("div[data-testid='content']", True, "Attribute selector"),
        ("ul li:first-child", True, "Pseudo-class selector"),
        ("p.entry-title.td-module-title a", True, "Specific selector"),
        
        # Invalid selectors
        ("", False, "Empty selector"),
        ("   ", False, "Whitespace only"),
        ("div..class", False, "Double dot (invalid CSS)"),
        ("div > > article", False, "Double combinator"),
        
        # XPath selectors (should warn but not fail)
        ("//div[@class='content']", True, "XPath selector (should warn)"),
        ("/html/body/div", True, "Absolute XPath (should warn)"),
        ("div[contains(@class, 'content')]", True, "XPath with contains (should warn)"),
    ]
    
    print("=" * 70)
    print("ENHANCED SELECTOR VALIDATION TEST")
    print("=" * 70)
    
    for selector, expected, description in test_cases:
        print(f"\nTesting: {description}")
        print(f"Selector: '{selector}'")
        
        result = validate_selector_format(selector)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        
        print(f"Expected: {expected}, Got: {result} - {status}")
        
        if selector == "div.content-right > div > article > h4.title":
            print("🎯 This is your specific selector - validation result above!")

if __name__ == "__main__":
    test_selectors()
