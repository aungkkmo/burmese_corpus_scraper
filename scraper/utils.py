#!/usr/bin/env python3
"""
Utility functions for the Burmese corpus scraper
"""

import hashlib
import re
import logging
from urllib.parse import urljoin, urlparse
from datetime import datetime
import json

def generate_id(url: str) -> str:
    """Generate a unique ID for the article based on URL"""
    return hashlib.md5(url.encode()).hexdigest()

def is_valid_url(url: str) -> bool:
    """Check if URL is valid and has a path beyond root"""
    try:
        parsed = urlparse(url)
        return bool(parsed.netloc) and bool(parsed.scheme) and len(parsed.path) > 1
    except:
        return False

def normalize_url(base_url: str, relative_url: str) -> str:
    """Convert relative URL to absolute URL"""
    return urljoin(base_url, relative_url)

def clean_text(text: str) -> str:
    """Clean and normalize text content"""
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_domain(url: str) -> str:
    """Extract domain from URL"""
    try:
        return urlparse(url).netloc
    except:
        return ""

def get_current_timestamp() -> str:
    """Get current UTC timestamp in ISO8601 format"""
    return datetime.utcnow().isoformat() + 'Z'

def setup_logging(log_file: str = None, log_level: str = "INFO") -> logging.Logger:
    """Setup logging configuration"""
    logger = logging.getLogger('burmese_scraper')
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def load_existing_ids(output_file: str) -> set:
    """Load existing article IDs from output file for resume functionality"""
    existing_ids = set()
    
    try:
        with open(output_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        article = json.loads(line)
                        if 'id' in article:
                            existing_ids.add(article['id'])
                    except json.JSONDecodeError:
                        continue
    except FileNotFoundError:
        pass
    
    return existing_ids

def is_css_selector(selector: str) -> bool:
    """Check if selector is CSS (vs XPath)"""
    # Simple heuristic: XPath typically starts with / or // or contains xpath functions
    xpath_indicators = ['/', 'text()', 'contains(', 'following-sibling', 'preceding-sibling', '@']
    return not any(indicator in selector for indicator in xpath_indicators)

def validate_selector_format(selector: str) -> bool:
    """Basic validation of selector format"""
    if not selector or not selector.strip():
        return False
    
    # Remove whitespace
    selector = selector.strip()
    
    # Basic checks
    if len(selector) < 1:
        return False
        
    return True

def normalize_slug(slug: str) -> str:
    """
    Normalize slug for file naming
    Remove spaces, convert to lowercase, replace with underscores
    
    Example: "Irrawaddy News" -> "irrawaddy_news"
    """
    if not slug:
        return "scraper_output"
    
    # Convert to lowercase and replace spaces with underscores
    normalized = slug.lower().strip()
    normalized = re.sub(r'\s+', '_', normalized)  # Replace spaces with underscores
    normalized = re.sub(r'[^\w\-_]', '', normalized)  # Remove special characters except - and _
    normalized = re.sub(r'_+', '_', normalized)  # Replace multiple underscores with single
    normalized = normalized.strip('_')  # Remove leading/trailing underscores
    
    # Ensure it's not empty after cleaning
    if not normalized:
        return "scraper_output"
    
    return normalized
