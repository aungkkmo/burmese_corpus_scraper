#!/usr/bin/env python3
"""
CSS Selector Validation Tool for Burmese Corpus Scraper

Usage:
    python3 validate_selector.py "div.content-right > div > article > h4.title"
    python3 validate_selector.py --interactive
"""

import sys
import os
import argparse

# Add the scraper directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scraper'))

from utils import validate_selector_format
from bs4 import BeautifulSoup

def detailed_validation(selector: str) -> dict:
    """
    Perform detailed validation with comprehensive feedback
    
    Args:
        selector: CSS selector to validate
        
    Returns:
        Dictionary with validation results and feedback
    """
    result = {
        'selector': selector,
        'is_valid': False,
        'errors': [],
        'warnings': [],
        'suggestions': []
    }
    
    if not selector or not selector.strip():
        result['errors'].append("Selector is empty or contains only whitespace")
        return result
    
    selector = selector.strip()
    
    # Check for XPath indicators
    xpath_indicators = ['/', 'text()', 'contains(', 'following-sibling', 'preceding-sibling', '@']
    if any(indicator in selector for indicator in xpath_indicators):
        result['warnings'].append("Selector contains XPath syntax - CSS expected")
    
    # Test with BeautifulSoup
    try:
        test_html = """
        <html>
            <body>
                <div class="content-right">
                    <div class="article-container">
                        <article class="post">
                            <h4 class="title">Sample Article Title</h4>
                            <p class="excerpt">Article excerpt...</p>
                        </article>
                    </div>
                </div>
                <div class="sidebar">
                    <h4 class="widget-title">Sidebar Title</h4>
                </div>
            </body>
        </html>
        """
        
        soup = BeautifulSoup(test_html, 'html.parser')
        elements = soup.select(selector)
        
        result['is_valid'] = True
        result['test_matches'] = len(elements)
        
        if elements:
            result['suggestions'].append(f"✅ Selector matches {len(elements)} element(s) in test HTML")
            for i, elem in enumerate(elements, 1):
                text = elem.get_text().strip()[:50] + ("..." if len(elem.get_text().strip()) > 50 else "")
                result['suggestions'].append(f"   Match {i}: <{elem.name}> - '{text}'")
        else:
            result['warnings'].append("⚠️  Selector is valid but matches no elements in test HTML")
            result['suggestions'].append("This might be normal if selector is specific to target website")
        
        # Analyze selector complexity
        if selector.count('>') > 3:
            result['warnings'].append("Selector has many child combinators (>) - might be too specific")
        
        if selector.count(' ') > 5:
            result['warnings'].append("Selector has many descendant combinators - consider simplifying")
        
        # Positive feedback
        if '.' in selector:
            result['suggestions'].append("👍 Uses CSS classes - good for targeting styled elements")
        
        if '#' in selector:
            result['suggestions'].append("👍 Uses CSS IDs - should be unique elements")
            
    except Exception as e:
        result['errors'].append(f"CSS parsing failed: {str(e)}")
    
    return result

def print_validation_report(result: dict):
    """Print a formatted validation report"""
    
    print("=" * 70)
    print("CSS SELECTOR VALIDATION REPORT")
    print("=" * 70)
    print(f"Selector: {result['selector']}")
    print(f"Valid: {'✅ YES' if result['is_valid'] else '❌ NO'}")
    
    if 'test_matches' in result:
        print(f"Test Matches: {result['test_matches']}")
    
    print("-" * 70)
    
    if result['errors']:
        print("🚨 ERRORS:")
        for error in result['errors']:
            print(f"  • {error}")
        print()
    
    if result['warnings']:
        print("⚠️  WARNINGS:")
        for warning in result['warnings']:
            print(f"  • {warning}")
        print()
    
    if result['suggestions']:
        print("💡 FEEDBACK:")
        for suggestion in result['suggestions']:
            print(f"  • {suggestion}")
        print()
    
    print("=" * 70)

def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Validate CSS selectors for Burmese Corpus Scraper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 validate_selector.py "div.content-right > div > article > h4.title"
  python3 validate_selector.py --interactive
  python3 validate_selector.py "article h1, article h2"
        """
    )
    
    parser.add_argument('selector', nargs='?', help='CSS selector to validate')
    parser.add_argument('-i', '--interactive', action='store_true', 
                       help='Interactive mode - enter selectors one by one')
    
    args = parser.parse_args()
    
    if args.interactive:
        print("Interactive CSS Selector Validation")
        print("Enter selectors to validate (press Enter with empty line to exit)")
        print("-" * 50)
        
        while True:
            try:
                selector = input("\nEnter CSS selector: ").strip()
                if not selector:
                    break
                
                result = detailed_validation(selector)
                print_validation_report(result)
                
            except KeyboardInterrupt:
                print("\nExiting...")
                break
                
    elif args.selector:
        result = detailed_validation(args.selector)
        print_validation_report(result)
        
        # Also test with the basic validation function
        basic_valid = validate_selector_format(args.selector)
        print(f"Basic validation result: {'✅ PASS' if basic_valid else '❌ FAIL'}")
        
    else:
        # Test the specific selector mentioned by user
        test_selector = "div.content-right > div > article > h4.title"
        print("Testing your specific selector:")
        result = detailed_validation(test_selector)
        print_validation_report(result)
        
        print("\nThis selector is configured in sites.example.yaml for 'burmese_thanlwintimes'")
        print("and should work correctly with the scraper.")

if __name__ == "__main__":
    main()
