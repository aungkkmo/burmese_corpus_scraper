#!/usr/bin/env python3
"""
Storage module for the Burmese corpus scraper
Handles saving scraped data in various formats
"""

import json
import logging
import os
from typing import Dict, List, Any, Optional
from pathlib import Path

class DataStorage:
    """Handle storage of scraped article data"""
    
    def __init__(self, output_file: str, format_type: str = 'ndjson'):
        self.output_file = output_file
        self.format_type = format_type.lower()
        self.logger = logging.getLogger('burmese_scraper.storage')
        
        # Ensure output directory exists
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize storage based on format
        if self.format_type == 'ndjson':
            self._init_ndjson()
        elif self.format_type == 'json':
            self._init_json()
        else:
            raise ValueError(f"Unsupported format: {format_type}")
    
    def _init_ndjson(self):
        """Initialize NDJSON storage"""
        # NDJSON files can be appended to directly
        pass
    
    def _init_json(self):
        """Initialize JSON array storage"""
        # For JSON array, we need to manage the structure
        self._json_articles = []
        
        # Load existing data if file exists
        if os.path.exists(self.output_file):
            try:
                with open(self.output_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                    if isinstance(existing_data, list):
                        self._json_articles = existing_data
                        self.logger.info(f"Loaded {len(self._json_articles)} existing articles")
            except Exception as e:
                self.logger.warning(f"Could not load existing JSON file: {e}")
    
    def save_article(self, article: Dict[str, Any]) -> bool:
        """
        Save a single article
        
        Args:
            article: Article data dictionary
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            if self.format_type == 'ndjson':
                return self._save_article_ndjson(article)
            elif self.format_type == 'json':
                return self._save_article_json(article)
            else:
                self.logger.error(f"Unsupported format: {self.format_type}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error saving article {article.get('id', 'unknown')}: {e}")
            return False
    
    def _save_article_ndjson(self, article: Dict[str, Any]) -> bool:
        """Save article in NDJSON format"""
        try:
            with open(self.output_file, 'a', encoding='utf-8') as f:
                json.dump(article, f, ensure_ascii=False, separators=(',', ':'))
                f.write('\n')
            return True
        except Exception as e:
            self.logger.error(f"Error saving NDJSON article: {e}")
            return False
    
    def _save_article_json(self, article: Dict[str, Any]) -> bool:
        """Save article in JSON array format"""
        try:
            # Add to in-memory list
            self._json_articles.append(article)
            
            # Write entire array to file
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(self._json_articles, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            self.logger.error(f"Error saving JSON article: {e}")
            return False
    
    def save_batch(self, articles: List[Dict[str, Any]]) -> int:
        """
        Save multiple articles
        
        Args:
            articles: List of article data dictionaries
            
        Returns:
            Number of articles saved successfully
        """
        saved_count = 0
        
        for article in articles:
            if self.save_article(article):
                saved_count += 1
        
        self.logger.info(f"Saved {saved_count}/{len(articles)} articles")
        return saved_count
    
    def get_existing_ids(self) -> set:
        """
        Get set of existing article IDs from output file
        
        Returns:
            Set of existing article IDs
        """
        existing_ids = set()
        
        if not os.path.exists(self.output_file):
            return existing_ids
        
        try:
            if self.format_type == 'ndjson':
                with open(self.output_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                article = json.loads(line)
                                if 'id' in article:
                                    existing_ids.add(article['id'])
                            except json.JSONDecodeError:
                                continue
            
            elif self.format_type == 'json':
                with open(self.output_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        for article in data:
                            if isinstance(article, dict) and 'id' in article:
                                existing_ids.add(article['id'])
            
            self.logger.info(f"Found {len(existing_ids)} existing article IDs")
            
        except Exception as e:
            self.logger.warning(f"Error reading existing IDs: {e}")
        
        return existing_ids
    
    def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        stats = {
            'output_file': self.output_file,
            'format_type': self.format_type,
            'file_exists': os.path.exists(self.output_file),
            'file_size': 0,
            'article_count': 0
        }
        
        if stats['file_exists']:
            try:
                stats['file_size'] = os.path.getsize(self.output_file)
                
                if self.format_type == 'ndjson':
                    with open(self.output_file, 'r', encoding='utf-8') as f:
                        stats['article_count'] = sum(1 for line in f if line.strip())
                
                elif self.format_type == 'json':
                    with open(self.output_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            stats['article_count'] = len(data)
                
            except Exception as e:
                self.logger.warning(f"Error getting stats: {e}")
        
        return stats
    
    def backup_existing(self) -> Optional[str]:
        """
        Create backup of existing output file
        
        Returns:
            Path to backup file or None if no backup created
        """
        if not os.path.exists(self.output_file):
            return None
        
        try:
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = f"{self.output_file}.backup_{timestamp}"
            
            import shutil
            shutil.copy2(self.output_file, backup_path)
            
            self.logger.info(f"Created backup: {backup_path}")
            return backup_path
            
        except Exception as e:
            self.logger.error(f"Error creating backup: {e}")
            return None
    
    def validate_output(self) -> Dict[str, Any]:
        """
        Validate output file format and content
        
        Returns:
            Validation results dictionary
        """
        results = {
            'valid': False,
            'errors': [],
            'warnings': [],
            'article_count': 0,
            'valid_articles': 0,
            'invalid_articles': 0
        }
        
        if not os.path.exists(self.output_file):
            results['errors'].append("Output file does not exist")
            return results
        
        try:
            if self.format_type == 'ndjson':
                results.update(self._validate_ndjson())
            elif self.format_type == 'json':
                results.update(self._validate_json())
            
            results['valid'] = len(results['errors']) == 0
            
        except Exception as e:
            results['errors'].append(f"Validation error: {e}")
        
        return results
    
    def _validate_ndjson(self) -> Dict[str, Any]:
        """Validate NDJSON format"""
        results = {
            'errors': [],
            'warnings': [],
            'article_count': 0,
            'valid_articles': 0,
            'invalid_articles': 0
        }
        
        with open(self.output_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                
                results['article_count'] += 1
                
                try:
                    article = json.loads(line)
                    if self._validate_article_structure(article):
                        results['valid_articles'] += 1
                    else:
                        results['invalid_articles'] += 1
                        results['warnings'].append(f"Line {line_num}: Invalid article structure")
                        
                except json.JSONDecodeError as e:
                    results['invalid_articles'] += 1
                    results['errors'].append(f"Line {line_num}: JSON decode error: {e}")
        
        return results
    
    def _validate_json(self) -> Dict[str, Any]:
        """Validate JSON array format"""
        results = {
            'errors': [],
            'warnings': [],
            'article_count': 0,
            'valid_articles': 0,
            'invalid_articles': 0
        }
        
        with open(self.output_file, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                
                if not isinstance(data, list):
                    results['errors'].append("JSON root is not an array")
                    return results
                
                results['article_count'] = len(data)
                
                for i, article in enumerate(data):
                    if not isinstance(article, dict):
                        results['invalid_articles'] += 1
                        results['errors'].append(f"Article {i}: Not a dictionary")
                        continue
                    
                    if self._validate_article_structure(article):
                        results['valid_articles'] += 1
                    else:
                        results['invalid_articles'] += 1
                        results['warnings'].append(f"Article {i}: Invalid structure")
                
            except json.JSONDecodeError as e:
                results['errors'].append(f"JSON decode error: {e}")
        
        return results
    
    def _validate_article_structure(self, article: Dict[str, Any]) -> bool:
        """Validate individual article structure"""
        required_fields = ['id', 'url', 'scraped_at']
        
        for field in required_fields:
            if field not in article:
                return False
        
        return True
