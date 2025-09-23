#!/usr/bin/env python3
"""
Utility functions for the Burmese corpus scraper
"""

import hashlib
import re
import logging
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Set, Dict, Any, Optional
from urllib.parse import urljoin, urlparse

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

def load_sites_config() -> Optional[Dict[str, Any]]:
    """
    Load multi-site configuration from sites.yaml
    Returns None if no sites.yaml file exists
    """
    sites_file = Path('sites.yaml')
    if not sites_file.exists():
        return None
    
    try:
        import yaml
        with open(sites_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config
    except ImportError:
        print("Warning: PyYAML not installed. Install with: pip install pyyaml")
        return None
    except Exception as e:
        print(f"Error loading sites.yaml: {e}")
        return None

def convert_pagination_type(pagination_type) -> str:
    """
    Convert numeric pagination type to string
    0 = none, 1 = queryparam, 2 = click, 3 = scroll
    """
    if isinstance(pagination_type, int):
        pagination_map = {
            0: 'none',
            1: 'queryparam', 
            2: 'click',
            3: 'scroll'
        }
        return pagination_map.get(pagination_type, 'none')
    elif isinstance(pagination_type, str):
        # Already a string, return as-is for backwards compatibility
        return pagination_type
    else:
        return 'none'

def get_site_config(sites_config: Dict[str, Any], site_key: str, category: str = None) -> Optional[Dict[str, Any]]:
    """
    Get configuration for a specific site, merging with defaults
    """
    if not sites_config or 'sites' not in sites_config:
        return None
    
    if site_key not in sites_config['sites']:
        return None
    
    # Start with defaults
    config = sites_config.get('defaults', {}).copy()
    
    # Override with site-specific settings
    site_config = sites_config['sites'][site_key].copy()
    config.update(site_config)
    
    # Handle multiple archive URLs
    if 'archive_urls' in config:
        archive_urls = config['archive_urls']
        
        if category and category in archive_urls:
            # Use specific category URL
            config['archive_url'] = archive_urls[category]
            config['category'] = category
        else:
            # Use first URL as default or show available categories
            if isinstance(archive_urls, dict):
                if not category:
                    # Return config with available categories for selection
                    config['available_categories'] = list(archive_urls.keys())
                    config['archive_url'] = list(archive_urls.values())[0]  # Default to first
                    config['category'] = list(archive_urls.keys())[0]
                else:
                    # Category not found
                    return None
        
        # Remove archive_urls from final config to avoid confusion
        del config['archive_urls']
    
    # Convert numeric pagination type to string
    if 'pagination_type' in config:
        config['pagination_type'] = convert_pagination_type(config['pagination_type'])
    
    # Add the site key as slug if not specified
    if 'slug' not in config:
        base_slug = site_key
        if category:
            base_slug = f"{site_key}_{category}"
        config['slug'] = base_slug
    
    return config

def get_site_categories(sites_config: Dict[str, Any], site_key: str) -> Optional[Dict[str, str]]:
    """
    Get available categories for a site
    """
    if not sites_config or 'sites' not in sites_config:
        return None
    
    if site_key not in sites_config['sites']:
        return None
    
    site_config = sites_config['sites'][site_key]
    
    if 'archive_urls' in site_config:
        return site_config['archive_urls']
    elif 'archive_url' in site_config:
        # Single URL site
        return {'main': site_config['archive_url']}
    
    return None

def load_env_config() -> Optional[Dict[str, Any]]:
    """
    Load scraper configuration from .env file
    Returns None if no .env file or if required fields are missing
    """
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        return None
    
    # Check if .env file exists
    if not Path('.env').exists():
        return None
    
    # Required fields
    required_fields = [
        'SCRAPER_SLUG',
        'SCRAPER_ARCHIVE_URL', 
        'SCRAPER_ARCHIVE_SELECTOR',
        'SCRAPER_CONTENT_SELECTOR'
    ]
    
    # Check if all required fields are present
    config = {}
    for field in required_fields:
        value = os.getenv(field)
        if not value:
            return None  # Missing required field
        config[field.lower().replace('scraper_', '')] = value
    
    # Optional fields with defaults
    optional_fields = {
        'SCRAPER_PAGINATION_TYPE': 'none',
        'SCRAPER_PAGINATION_PARAM': None,
        'SCRAPER_THUMBNAIL_SELECTOR': 'img',
        'SCRAPER_DELAY': '1.0',
        'SCRAPER_TIMEOUT': '30',
        'SCRAPER_MAX_PAGES': None,
        'SCRAPER_USE_PROXY': 'false',
        'SCRAPER_FORCE_ENGINE': None,
        'SCRAPER_LOG_LEVEL': 'INFO',
        'SCRAPER_OUTPUT_FORMAT': 'ndjson',
        'SCRAPER_RESUME': 'false'
    }
    
    for field, default in optional_fields.items():
        value = os.getenv(field, default)
        key = field.lower().replace('scraper_', '')
        
        # Convert string values to appropriate types
        if key in ['delay', 'timeout']:
            config[key] = float(value) if value else None
        elif key in ['max_pages']:
            config[key] = int(value) if value and value.isdigit() else None
        elif key in ['use_proxy', 'resume']:
            config[key] = value.lower() in ('true', '1', 'yes', 'on')
        else:
            config[key] = value if value else None
    
    return config

