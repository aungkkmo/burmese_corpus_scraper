#!/usr/bin/env python3
"""
Content extraction module for the Burmese corpus scraper
Handles extraction of article data from HTML content
"""

import re
import logging
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup, Tag
from datetime import datetime

from .utils import generate_id, normalize_url, clean_text, get_current_timestamp

class ContentExtractor:
    """Extract article content and metadata from HTML"""
    
    def __init__(self):
        self.logger = logging.getLogger('burmese_scraper.extractor')
    
    def extract_archive_items(self, content: str, base_url: str, 
                            item_selector: str, thumbnail_selector: str = None) -> List[Dict[str, Any]]:
        """
        Extract archive items from archive/list page
        
        Args:
            content: HTML content of archive page
            base_url: Base URL for resolving relative links
            item_selector: CSS/XPath selector for archive items
            thumbnail_selector: Optional selector for thumbnails
            
        Returns:
            List of archive item dictionaries
        """
        items = []
        
        try:
            soup = BeautifulSoup(content, 'html.parser')
            
            # Find archive items
            if self._is_css_selector(item_selector):
                elements = soup.select(item_selector)
            else:
                # For XPath, we'll treat as CSS for now
                self.logger.warning(f"XPath selector '{item_selector}' treated as CSS")
                elements = soup.select(item_selector)
            
            self.logger.info(f"Found {len(elements)} archive items")
            
            for i, element in enumerate(elements):
                try:
                    item = self._extract_single_archive_item(
                        element, base_url, thumbnail_selector
                    )
                    if item:
                        items.append(item)
                        
                except Exception as e:
                    self.logger.warning(f"Error extracting archive item {i}: {e}")
                    continue
            
        except Exception as e:
            self.logger.error(f"Error extracting archive items: {e}")
        
        return items
    
    def _extract_single_archive_item(self, element: Tag, base_url: str, 
                                   thumbnail_selector: str = None) -> Optional[Dict[str, Any]]:
        """Extract data from a single archive item element"""
        
        # Find the main link
        link_element = None
        
        # Check if the element itself is a link
        if element.name == 'a' and element.get('href'):
            link_element = element
        else:
            # Look for link inside the element
            link_element = element.find('a')
            if not link_element or not link_element.get('href'):
                # Try to find link in children
                link_element = element.find('a', href=True)
        
        if not link_element:
            self.logger.warning("No link found in archive item")
            return None
        
        # Extract URL (clean/stripped)
        relative_url = link_element.get('href').strip()
        article_url = normalize_url(base_url, relative_url)
        
        # Extract title (clean/stripped) - try link text first, then look for title elements
        title = clean_text(link_element.get_text())
        
        # Try to find a better title from common title elements within the archive item
        title_selectors = ['h1', 'h2', 'h3', '.title', '.headline', '.post-title', '.article-title']
        for selector in title_selectors:
            title_element = element.select_one(selector)
            if title_element:
                potential_title = clean_text(title_element.get_text())
                if potential_title and len(potential_title) > len(title):
                    title = potential_title
                    break
        
        item = {
            'url': article_url,
            'title': title,  # Clean/stripped title
            'thumbnail_url': None
        }
        
        # Extract thumbnail if selector provided (clean/stripped URL)
        if thumbnail_selector:
            try:
                if self._is_css_selector(thumbnail_selector):
                    thumb_element = element.select_one(thumbnail_selector)
                else:
                    # Treat XPath as CSS for now
                    thumb_element = element.select_one(thumbnail_selector)
                
                if thumb_element:
                    # Try different attributes for image URL
                    thumb_url = None
                    for attr in ['src', 'data-src', 'data-lazy-src', 'data-original', 'data-lazy']:
                        if thumb_element.get(attr):
                            thumb_url = normalize_url(base_url, thumb_element.get(attr).strip())
                            break
                    
                    if thumb_url:
                        item['thumbnail_url'] = thumb_url
                        
            except Exception as e:
                self.logger.warning(f"Error extracting thumbnail: {e}")
        
        return item
    
    def extract_article_content(self, content: str, url: str, content_selector: str,
                              archive_url: str = None, engine: str = None) -> Optional[Dict[str, Any]]:
        """
        Extract article content and metadata from article page
        
        Args:
            content: HTML content of article page
            url: Article URL
            content_selector: CSS/XPath selector for main content
            archive_url: URL of archive page this article came from
            engine: Scraping engine used
            
        Returns:
            Article data dictionary or None if extraction failed
        """
        
        try:
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract main content
            if self._is_css_selector(content_selector):
                content_element = soup.select_one(content_selector)
            else:
                # Treat XPath as CSS for now
                content_element = soup.select_one(content_selector)
            
            if not content_element:
                self.logger.warning(f"Content selector '{content_selector}' not found in {url}")
                return None
            
            # Extract raw HTML content (unprocessed from the specified identifier)
            raw_html_content = str(content_element)
            
            # Extract title (clean/stripped)
            title = self._extract_title(soup, content_element)
            
            # Create article data matching the instruction format
            article = {
                'id': generate_id(url),
                'title': title,
                'url': url,
                'thumbnail_url': None,  # Will be set from archive data
                'raw_html_content': raw_html_content,  # Raw HTML from detail page content selector
                'scraped_date': get_current_timestamp().split('T')[0],  # YYYY-MM-DD format
                'source_url': urlparse(url).scheme + '://' + urlparse(url).netloc
            }
            
            return article
            
        except Exception as e:
            self.logger.error(f"Error extracting article content from {url}: {e}")
            return {
                'id': generate_id(url),
                'title': None,
                'url': url,
                'thumbnail_url': None,
                'raw_html_content': None,
                'scraped_date': get_current_timestamp().split('T')[0],
                'source_url': urlparse(url).scheme + '://' + urlparse(url).netloc
            }
    
    def _extract_title(self, soup: BeautifulSoup, content_element: Tag = None) -> Optional[str]:
        """Extract article title from various sources"""
        
        # Try multiple title extraction methods
        title_candidates = []
        
        # 1. HTML title tag
        title_tag = soup.find('title')
        if title_tag:
            title_candidates.append(clean_text(title_tag.get_text()))
        
        # 2. Open Graph title
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            title_candidates.append(clean_text(og_title.get('content')))
        
        # 3. Twitter title
        twitter_title = soup.find('meta', attrs={'name': 'twitter:title'})
        if twitter_title and twitter_title.get('content'):
            title_candidates.append(clean_text(twitter_title.get('content')))
        
        # 4. H1 tags
        h1_tags = soup.find_all('h1')
        for h1 in h1_tags:
            title_candidates.append(clean_text(h1.get_text()))
        
        # 5. H2 tags (if no H1)
        if not any(h1_tags):
            h2_tags = soup.find_all('h2')
            for h2 in h2_tags:
                title_candidates.append(clean_text(h2.get_text()))
        
        # 6. Title from content element
        if content_element:
            content_h1 = content_element.find('h1')
            if content_h1:
                title_candidates.append(clean_text(content_h1.get_text()))
        
        # Filter and select best title
        valid_titles = [t for t in title_candidates if t and len(t.strip()) > 5]
        
        if valid_titles:
            # Return the first valid title (usually the most reliable)
            return valid_titles[0]
        
        return None
    
    def _extract_published_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract published date from various sources"""
        
        # Try multiple date extraction methods
        date_selectors = [
            # Meta tags
            ('meta', {'property': 'article:published_time'}),
            ('meta', {'name': 'publishdate'}),
            ('meta', {'name': 'date'}),
            ('meta', {'name': 'publication-date'}),
            ('meta', {'property': 'og:updated_time'}),
            
            # Time tags
            ('time', {'datetime': True}),
            ('time', {'pubdate': True}),
            
            # Common class names
            ('.published', {}),
            ('.date', {}),
            ('.post-date', {}),
            ('.article-date', {}),
            ('.entry-date', {}),
        ]
        
        for selector, attrs in date_selectors:
            try:
                if selector.startswith('.'):
                    # CSS class selector
                    elements = soup.select(selector)
                else:
                    # Tag with attributes
                    elements = soup.find_all(selector, attrs)
                
                for element in elements:
                    # Try different attributes
                    for attr in ['datetime', 'content', 'value']:
                        date_value = element.get(attr)
                        if date_value:
                            return self._normalize_date(date_value)
                    
                    # Try text content
                    text = clean_text(element.get_text())
                    if text and self._looks_like_date(text):
                        return self._normalize_date(text)
                        
            except Exception:
                continue
        
        return None
    
    def _extract_author(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract author from various sources"""
        
        # Try multiple author extraction methods
        author_selectors = [
            # Meta tags
            ('meta', {'name': 'author'}),
            ('meta', {'property': 'article:author'}),
            ('meta', {'name': 'article:author'}),
            
            # Common class names
            ('.author', {}),
            ('.byline', {}),
            ('.writer', {}),
            ('.post-author', {}),
            ('.article-author', {}),
            ('.entry-author', {}),
        ]
        
        for selector, attrs in author_selectors:
            try:
                if selector.startswith('.'):
                    # CSS class selector
                    elements = soup.select(selector)
                else:
                    # Tag with attributes
                    elements = soup.find_all(selector, attrs)
                
                for element in elements:
                    # Try content attribute first
                    author = element.get('content')
                    if author:
                        return clean_text(author)
                    
                    # Try text content
                    text = clean_text(element.get_text())
                    if text and len(text) < 100:  # Reasonable author name length
                        return text
                        
            except Exception:
                continue
        
        return None
    
    def _is_css_selector(self, selector: str) -> bool:
        """Check if selector is CSS (vs XPath)"""
        xpath_indicators = ['/', 'text()', 'contains(', 'following-sibling', 'preceding-sibling', '@']
        return not any(indicator in selector for indicator in xpath_indicators)
    
    def _normalize_date(self, date_str: str) -> str:
        """Normalize date string to ISO format"""
        try:
            # Remove extra whitespace
            date_str = clean_text(date_str)
            
            # Try to parse various date formats
            from dateutil import parser
            parsed_date = parser.parse(date_str)
            return parsed_date.isoformat()
            
        except:
            # Return original string if parsing fails
            return date_str
    
    def _looks_like_date(self, text: str) -> bool:
        """Check if text looks like a date"""
        if not text or len(text) < 4:
            return False
        
        # Simple heuristics for date detection
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
            r'\d{2}/\d{2}/\d{4}',  # MM/DD/YYYY
            r'\d{2}-\d{2}-\d{4}',  # MM-DD-YYYY
            r'\w+ \d{1,2}, \d{4}', # Month DD, YYYY
        ]
        
        for pattern in date_patterns:
            if re.search(pattern, text):
                return True
        
        return False
