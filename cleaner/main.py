#!/usr/bin/env python3
"""
Data Cleaner for Burmese Corpus Scraper
Cleans raw scraped data according to cleaning rules configuration
"""

import json
import yaml
import hashlib
import os
import re
import argparse
from pathlib import Path
from typing import Dict, List, Any, Tuple
import logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# Import Myanmar tools for Zawgyi conversion
try:
    from myanmartools import ZawgyiDetector
    from icu import Transliterator
    MYANMAR_TOOLS_AVAILABLE = True
    detector = ZawgyiDetector()
    converter = Transliterator.createInstance('Zawgyi-my')
except ImportError:
    MYANMAR_TOOLS_AVAILABLE = False
    detector = None
    converter = None

# Import Myanmar word library
try:
    from libs.myanmar_word_lib import MyanmarSegmenter
    MYANMAR_WORD_LIB_AVAILABLE = True
    myanmar_segmenter = MyanmarSegmenter()
except ImportError as e:
    MYANMAR_WORD_LIB_AVAILABLE = False
    myanmar_segmenter = None
    logger.warning(f"Myanmar word library not available: {e}")

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataCleaner:
    def __init__(self, config_file: str = "cleaner.yaml"):
        self.config_file = config_file
        self.config = self._load_config()
        self.raw_dir = Path("data/raw")
        self.clean_dir = Path("data/clean")
        self.clean_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_config(self) -> Dict[str, Any]:
        """Load cleaning rules configuration"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {}
    
    def _get_site_config(self, site_name: str) -> Dict[str, Any]:
        """Get configuration for specific site"""
        defaults = self.config.get('defaults', {})
        site_config = self.config.get('sites', {}).get(site_name, {})
        
        # Merge defaults with site-specific config
        config = defaults.copy()
        config.update(site_config)
        return config
    
    def clean_title(self, title: str, removal_keywords: List[str]) -> str:
        """Clean title by removing keywords and converting to Unicode"""
        if not title:
            return title
        
        # 1. Zawgyi to Unicode conversion
        title = self.zawgyi_to_unicode(title)
        
        # 2. Remove keywords
        for keyword in removal_keywords:
            if keyword:
                title = title.replace(keyword, '')
        
        # 3. Apply cleaning functions
        title = self.clean_xinhua_content(title)
        title = self.clean_references_section(title)
        title = self.clean_escaped_quotes(title)
        title = self.clean_botupload_lines(title)
        title = self.clean_continuous_dashes(title)
        
        # 4. Normalize whitespace
        title = re.sub(r'\s+', ' ', title).strip()
        
        return title
    
    def clean_text(self, text: str, removal_keywords: List[str]) -> str:
        """Clean text by removing keywords and converting to Unicode"""
        if not text:
            return text
        
        # 1. Remove HTML tags and unwanted content first
        text = self.remove_html_and_special_content(text)
        
        # 2. Zawgyi to Unicode conversion
        text = self.zawgyi_to_unicode(text)
        
        # 3. Remove keywords
        for keyword in removal_keywords:
            if keyword:
                text = text.replace(keyword, '')
        
        # 4. Remove Zawgyi separators
        separators = ['ZG ', 'Zawgyi ', 'ZAWGYI', '[Zawgyi]', 'ZawGyi']
        for sep in separators:
            sep_index = text.find(sep)
            if sep_index != -1:
                text = text[:sep_index]
                break
        
        # 5. Apply comprehensive cleaning functions
        text = self.clean_xinhua_content(text)
        text = self.clean_references_section(text)
        text = self.clean_escaped_quotes(text)
        text = self.clean_botupload_lines(text)
        text = self.clean_continuous_dashes(text)
        
        # 6. Convert tables and formulas to LaTeX
        text = self.convert_tables_and_formulas(text)
        
        # 7. Normalize text formatting and remove special symbols
        text = self.normalize_text_formatting(text)
        
        return text
    
    def extract_with_selectors(self, html_content: str, site_config: Dict[str, Any], base_url: str = '') -> Tuple[str, str]:
        """Extract content using CSS selectors and format images"""
        if not html_content:
            return '', ''
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract feature image
            feature_image_url = ''
            feature_image_selector = site_config.get('feature_image_selector', '')
            if feature_image_selector:
                img_element = soup.select_one(feature_image_selector)
                if img_element:
                    feature_image_url = img_element.get('src', '') or img_element.get('data-src', '')
                    if feature_image_url and base_url:
                        feature_image_url = urljoin(base_url, feature_image_url)
            
            # Extract main text
            main_text = ''
            main_text_selector = site_config.get('main_text_selector', '')
            if main_text_selector:
                text_elements = soup.select(main_text_selector)
                if text_elements:
                    # Process each text element and preserve image positions
                    text_parts = []
                    for element in text_elements:
                        # Find images within this text element
                        for img in element.find_all('img'):
                            img_src = img.get('src', '') or img.get('data-src', '')
                            if img_src:
                                if base_url:
                                    img_src = urljoin(base_url, img_src)
                                # Replace img tag with formatted image link
                                img_tag = f'[IMAGE : {img_src}]'
                                img.replace_with(img_tag)
                        
                        # Get text content
                        element_text = element.get_text(separator=' ', strip=True)
                        if element_text:
                            text_parts.append(element_text)
                    
                    main_text = ' '.join(text_parts)
            
            # If no selector worked, fall back to full text extraction
            if not main_text:
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                
                # Format images
                for img in soup.find_all('img'):
                    img_src = img.get('src', '') or img.get('data-src', '')
                    if img_src:
                        if base_url:
                            img_src = urljoin(base_url, img_src)
                        img_tag = f'[IMAGE : {img_src}]'
                        img.replace_with(img_tag)
                
                main_text = soup.get_text(separator=' ', strip=True)
            
            return feature_image_url, main_text
            
        except Exception as e:
            logger.warning(f"Error extracting with selectors: {e}")
            return '', html_content
    
    def extract_final_output(self, raw_item: Dict[str, Any], site_config: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and format final output"""
        url = raw_item.get('url', '')
        raw_html = raw_item.get('raw_html_content', '')
        raw_title = raw_item.get('title', '')
        
        # Extract content using selectors
        feature_image_url, extracted_text = self.extract_with_selectors(raw_html, site_config, url)
        
        # Clean title
        cleaned_title = self.clean_title(raw_title, site_config.get('title_removal_keywords', []))
        
        # Clean text
        cleaned_text = self.clean_text(extracted_text, site_config.get('text_removal_keywords', []))
        
        # Combine feature image + text
        final_text = ''
        if feature_image_url:
            final_text += f'[IMAGE : {feature_image_url}] '
        final_text += cleaned_text
        
        # Generate MD5 ID
        md5_id = hashlib.md5(url.encode('utf-8')).hexdigest()
        
        cleaned_item = {
            "id": md5_id,
            "title": cleaned_title,
            "text": final_text.strip(),
            "domain": site_config.get('domain', 'News'),
            "url": url
        }
        
        return cleaned_item
    
    def process_file(self, input_file: Path) -> None:
        """Process a single JSONL file"""
        site_name = input_file.stem
        site_config = self._get_site_config(site_name)
        
        output_file = self.clean_dir / f"{site_name}_cleaned.jsonl"
        
        logger.info(f"Processing {input_file} -> {output_file}")
        
        processed_count = 0
        seen_ids = set()
        
        try:
            with open(input_file, 'r', encoding='utf-8') as infile, \
                 open(output_file, 'w', encoding='utf-8') as outfile:
                
                for line in infile:
                    line = line.strip()
                    if line:
                        try:
                            raw_item = json.loads(line)
                            cleaned_item = self.extract_final_output(raw_item, site_config)
                            
                            # Remove duplicates by ID
                            item_id = cleaned_item.get('id')
                            if item_id in seen_ids:
                                logger.debug(f"Skipping duplicate ID: {item_id}")
                                continue
                            
                            seen_ids.add(item_id)
                            
                            # Validate content quality
                            if self.validate_content_quality(cleaned_item):
                                outfile.write(json.dumps(cleaned_item, ensure_ascii=False) + '\n')
                                processed_count += 1
                            else:
                                # Add more detailed logging to understand rejection reasons
                                text_len = len(cleaned_item.get('text', ''))
                                title_len = len(cleaned_item.get('title', ''))
                                title_content = cleaned_item.get('title', '')[:100]  # First 100 chars of title
                                has_myanmar = self.has_myanmar_characters(cleaned_item.get('text', '')) or self.has_myanmar_characters(cleaned_item.get('title', ''))
                                logger.debug(f"Rejected item {item_id}: text_len={text_len}, title_len={title_len}, has_myanmar={has_myanmar}")
                                logger.debug(f"Title content: '{title_content}'")
                            
                        except json.JSONDecodeError as e:
                            logger.warning(f"Skipping invalid JSON line: {e}")
                            continue
            
            logger.info(f"Processed {processed_count} items for {site_name}")
            
        except Exception as e:
            logger.error(f"Error processing {input_file}: {e}")
    
    def process_all_files(self, site_filter: str = None) -> None:
        """Process all JSONL files in data/raw directory"""
        jsonl_files = list(self.raw_dir.glob("*.jsonl"))
        
        # Filter by site if specified
        if site_filter:
            jsonl_files = [f for f in jsonl_files if f.stem == site_filter]
            if not jsonl_files:
                logger.error(f"No JSONL file found for site: {site_filter}")
                logger.info(f"Available files: {[f.stem for f in self.raw_dir.glob('*.jsonl')]}")
                return
            logger.info(f"Processing only site: {site_filter}")
        
        if not jsonl_files:
            logger.warning("No JSONL files found in data/raw directory")
            return
        
        logger.info(f"Found {len(jsonl_files)} files to process")
        
        for jsonl_file in jsonl_files:
            self.process_file(jsonl_file)
        
        logger.info("All files processed successfully")
    
    def zawgyi_to_unicode(self, text: str) -> str:
        """Convert Zawgyi text to Unicode if needed"""
        if not MYANMAR_TOOLS_AVAILABLE or not text:
            return text
        
        try:
            score = detector.get_zawgyi_probability(text)
            if score > 0.5:
                return converter.transliterate(text)
            return text
        except Exception:
            return text
    
    def normalize_text_for_comparison(self, text: str) -> str:
        """Remove spaces from text for comparison only (original text is preserved)"""
        if not text:
            return ""
        return text.replace(" ", "").replace("\t", "").replace("\n", "")
    
    def has_myanmar_characters(self, text: str) -> bool:
        """Check if text contains Myanmar/Burmese characters"""
        if not text:
            return False
        
        # Myanmar Unicode range: U+1000-U+109F
        myanmar_pattern = r'[\u1000-\u109F]'
        return bool(re.search(myanmar_pattern, text))
    
    def clean_escaped_quotes(self, text: str) -> str:
        """Remove escaped quotes from text"""
        if not text:
            return text
        
        # Remove escaped quotes \"
        text = text.replace('\"', ' ')
        text = text.replace('\\', ' ')
        
        return text

    def clean_botupload_lines(self, text: str) -> str:
        """Remove lines containing 'BotUpload' from text"""
        if not text:
            return text
        
        # Split text into lines
        lines = text.split('\n')
        
        # Filter out lines containing 'BotUpload' (case insensitive)
        cleaned_lines = [line for line in lines if 'BotUpload' not in line and 'botupload' not in line.lower()]
        
        # Rejoin the lines
        cleaned_text = '\n'.join(cleaned_lines)
        
        return cleaned_text.strip()

    def clean_continuous_dashes(self, text: str) -> str:
        """Remove continuous dashes (2 or more consecutive dashes)"""
        if not text:
            return text
        
        # Use regex to find and remove 2 or more consecutive dashes
        # This pattern matches 2 or more consecutive dash characters
        cleaned_text = re.sub(r'-{2,}', ' - ', text)
        
        return cleaned_text.strip()
    
    def clean_xinhua_content(self, text: str) -> str:
        """Clean Xinhua-specific content patterns"""
        if not text:
            return text
        
        # Remove "————" and everything after it
        dash_pattern = r'————.*$'
        text = re.sub(dash_pattern, '', text, flags=re.MULTILINE)
        
        # Remove (Xinhua) and (ဆင်ဟွာ) with misspellings and author names, especially at the end
        # First remove at the end with optional whitespace/punctuation
        xinhua_end_patterns = [
            r'\s*\([Xx][Ii][Nn][Hh][Uu][Aa]/[^)]+\)\s*[.။]*\s*$',  # (Xinhua/Author) at end
            r'\s*\([Xx][Ii][Nn][Hh].*?\)\s*[.။]*\s*$',  # English (Xinh*) - catches misspellings
            r'\s*\([Xx][Ii][Nn][Hh][Uu][Aa]\)\s*[.။]*\s*$',  # English (Xinhua) - exact match
            r'\s*\(ဆင်ဟွာ\)\s*[.။]*\s*$'  # Myanmar (ဆင်ဟွာ)
        ]
        
        for pattern in xinhua_end_patterns:
            text = re.sub(pattern, '', text)
        
        # Then remove any remaining occurrences anywhere in text
        xinhua_patterns = [
            r'\([Xx][Ii][Nn][Hh][Uu][Aa]/[^)]+\)',  # (Xinhua/Author) anywhere
            r'\([Xx][Ii][Nn][Hh].*?\)',  # English (Xinh*) - catches misspellings
            r'\([Xx][Ii][Nn][Hh][Uu][Aa]\)',  # English (Xinhua) - exact match
            r'\(ဆင်ဟွာ\)'  # Myanmar (ဆင်ဟွာ)
        ]
        
        for pattern in xinhua_patterns:
            text = re.sub(pattern, '', text)
        
        # Remove dots separator commonly used in Xinhua articles
        text = re.sub(r'^…+', '', text, flags=re.MULTILINE)
        
        # Find and remove English/Chinese version sections with misspellings
        # Pattern includes non-alphabetic characters before version markers
        version_patterns = [
            # English version patterns (with common misspellings)
            r'[^a-zA-Z\u1000-\u109F]*(?:\()?[Ee]nglish\s*[Vv]ers?i?o?n+(?:\))?.*',
            r'[^a-zA-Z\u1000-\u109F]*(?:\()?[Ee]nglish\s*[Vv]ersi+on+(?:\))?.*',
            r'[^a-zA-Z\u1000-\u109F]*(?:\()?[Ee]nglish\s*[Vv]ersion+(?:\))?.*',
            
            # Chinese version patterns (with common misspellings)  
            r'[^a-zA-Z\u1000-\u109F]*(?:\()?[Cc]hinese\s*[Vv]ers?i?o?n+(?:\))?.*',
            r'[^a-zA-Z\u1000-\u109F]*(?:\()?[Cc]hinese\s*[Vv]ersi+on+(?:\))?.*',
            r'[^a-zA-Z\u1000-\u109F]*(?:\()?[Cc]hinese\s*[Vv]ersion+(?:\))?.*',
            
            # Exact case patterns (fallback)
            r'[^a-zA-Z\u1000-\u109F]*(?:\()?English\s*Version(?:\))?.*',
            r'[^a-zA-Z\u1000-\u109F]*(?:\()?Chinese\s*Version(?:\))?.*'
        ]
        
        for pattern in version_patterns:
            # Find the position where version section starts
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                # Find where the actual alphabetic content ends before the version marker
                before_match = text[:match.start()]
                
                # Look for the last alphabetic character or Myanmar character before the match
                last_alpha_pos = match.start()
                for i in range(match.start() - 1, -1, -1):
                    if text[i].isalpha() or '\u1000' <= text[i] <= '\u109F':
                        last_alpha_pos = i + 1
                        break
                    elif i == 0:
                        last_alpha_pos = 0
                        break
                
                # Check if there's Myanmar content after the version marker
                after_version = text[match.end():]
                if self.has_myanmar_characters(after_version):
                    # Keep the Myanmar content, remove from last alphabetic position
                    text = text[:last_alpha_pos] + after_version
                else:
                    # Remove everything from last alphabetic position onwards
                    text = text[:last_alpha_pos]
                break
        
        return text.strip()
    
    def clean_references_section(self, text: str) -> str:
        """Clean Myanmar references section: == ကိုးကား =="""
        if not text:
            return text
        
        # Pattern to match "== ကိုးကား ==" with optional whitespace
        references_pattern = r'\s*==\s*ကိုးကား\s*==\s*'
        
        # Find the references section
        match = re.search(references_pattern, text)
        if match:
            # Get the text after the references marker
            after_references = text[match.end():].strip()
            
            if not after_references:
                # If nothing after "== ကိုးကား ==", remove the entire marker
                text = text[:match.start()].strip()
            else:
                # If there's content after, replace "== ကိုးကား ==" with "ကိုးကား "
                before_text = text[:match.start()].rstrip()
                text = before_text + " ကိုးကား " + after_references
        
        return text.strip()
    
    def remove_html_and_special_content(self, text: str) -> str:
        """Remove HTML tags, navigation elements, ads, and other unwanted content"""
        if not text:
            return text
        
        # Remove HTML tags completely
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove HTML entities
        html_entities = {
            '&nbsp;': ' ', '&amp;': '&', '&lt;': '<', '&gt;': '>', '&quot;': '"',
            '&apos;': "'", '&copy;': '©', '&reg;': '®', '&trade;': '™',
            '&#39;': "'", '&#34;': '"', '&#8217;': "'", '&#8220;': '"', '&#8221;': '"'
        }
        for entity, replacement in html_entities.items():
            text = text.replace(entity, replacement)
        
        # Remove navigation and menu patterns
        nav_patterns = [
            r'(?i)menu\s*[:：]\s*.*?(?=\n|$)',
            r'(?i)navigation\s*[:：]\s*.*?(?=\n|$)',
            r'(?i)breadcrumb\s*[:：]\s*.*?(?=\n|$)',
            r'(?i)home\s*[>›]\s*.*?(?=\n|$)',
            r'(?i)သင်္ကေတ\s*[:：]\s*.*?(?=\n|$)',  # Myanmar "symbol/menu"
            r'(?i)မူလစာမျက်နှာ\s*[>›]\s*.*?(?=\n|$)',  # Myanmar "home page"
        ]
        
        for pattern in nav_patterns:
            text = re.sub(pattern, '', text, flags=re.MULTILINE)
        
        # Remove advertisement patterns
        ad_patterns = [
            r'(?i)advertisement\s*[:：]?.*?(?=\n|$)',
            r'(?i)sponsored\s*[:：]?.*?(?=\n|$)',
            r'(?i)ads?\s*[:：]?.*?(?=\n|$)',
            r'(?i)ကြော်ငြာ\s*[:：]?.*?(?=\n|$)',  # Myanmar "advertisement"
            r'(?i)click\s+here.*?(?=\n|$)',
            r'(?i)read\s+more.*?(?=\n|$)',
            r'(?i)continue\s+reading.*?(?=\n|$)',
        ]
        
        for pattern in ad_patterns:
            text = re.sub(pattern, '', text, flags=re.MULTILINE)
        
        # Remove copyright and disclaimer patterns
        legal_patterns = [
            r'(?i)copyright\s*[©℗]?\s*\d{4}.*?(?=\n|$)',
            r'(?i)all\s+rights?\s+reserved.*?(?=\n|$)',
            r'(?i)disclaimer\s*[:：]?.*?(?=\n|$)',
            r'(?i)terms?\s+of\s+use.*?(?=\n|$)',
            r'(?i)privacy\s+policy.*?(?=\n|$)',
            r'(?i)မူပိုင်ခွင့်.*?(?=\n|$)',  # Myanmar "copyright"
            r'(?i)တရားဝင်.*?(?=\n|$)',  # Myanmar "legal"
        ]
        
        for pattern in legal_patterns:
            text = re.sub(pattern, '', text, flags=re.MULTILINE)
        
        # Remove webpage buttons and interactive elements
        button_patterns = [
            r'(?i)\[?\s*share\s*\]?',
            r'(?i)\[?\s*like\s*\]?',
            r'(?i)\[?\s*comment\s*\]?',
            r'(?i)\[?\s*subscribe\s*\]?',
            r'(?i)\[?\s*follow\s*\]?',
            r'(?i)\[?\s*tweet\s*\]?',
            r'(?i)\[?\s*facebook\s*\]?',
            r'(?i)\[?\s*twitter\s*\]?',
            r'(?i)\[?\s*download\s*\]?',
            r'(?i)\[?\s*print\s*\]?',
        ]
        
        for pattern in button_patterns:
            text = re.sub(pattern, '', text)
        
        return text.strip()
    
    def normalize_text_formatting(self, text: str) -> str:
        """Normalize text formatting and remove special symbols"""
        if not text:
            return text
        
        # Remove emojis and artistic symbols
        # Unicode ranges for emojis and symbols
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags (iOS)
            "\U00002702-\U000027B0"  # dingbats
            "\U000024C2-\U0001F251"  # enclosed characters
            "\U0001F900-\U0001F9FF"  # supplemental symbols
            "\U0001FA70-\U0001FAFF"  # symbols and pictographs extended-A
            "]+", flags=re.UNICODE
        )
        text = emoji_pattern.sub('', text)
        
        # Remove other special symbols and artistic characters
        special_symbols = [
            '★', '☆', '♪', '♫', '♬', '♩', '♭', '♮', '♯',  # stars and music
            '♠', '♣', '♥', '♦',  # card suits
            '▲', '▼', '◆', '◇', '○', '●', '□', '■',  # geometric shapes
            '→', '←', '↑', '↓', '↔', '↕',  # arrows
            '※', '§', '¶', '†', '‡', '•', '‰', '‱',  # misc symbols
            '℃', '℉', '°', '′', '″', '‴',  # degree and temperature
        ]
        
        for symbol in special_symbols:
            text = text.replace(symbol, '')
        
        # Normalize line breaks - no more than one consecutive line break
        text = re.sub(r'\n{3,}', '\n\n', text)  # Max 2 line breaks
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)  # Clean up spaced line breaks
        
        # Normalize spaces and indentation
        # Remove excessive spaces (more than 2 consecutive spaces)
        text = re.sub(r' {3,}', '  ', text)
        
        # Remove abnormal indentation (tabs and excessive spaces at line start)
        text = re.sub(r'^\s{4,}', '  ', text, flags=re.MULTILINE)  # Max 2 spaces indent
        text = re.sub(r'^\t+', '  ', text, flags=re.MULTILINE)  # Replace tabs with 2 spaces
        
        # Clean up mixed spaces and tabs
        text = re.sub(r'[ \t]+', ' ', text)  # Normalize all whitespace to single spaces
        
        return text.strip()
    
    def convert_tables_and_formulas(self, text: str) -> str:
        """Convert tables and formulas to LaTeX format"""
        if not text:
            return text
        
        # Detect and convert simple table patterns
        # Pattern: data separated by | or multiple spaces/tabs
        table_patterns = [
            r'(\|[^|\n]+\|[^|\n]*\n)+',  # Pipe-separated tables
            r'((?:[^\n\t]{2,}\t[^\n\t]{2,}(?:\t[^\n\t]{2,})*\n){2,})',  # Tab-separated tables
        ]
        
        def convert_table_to_latex(match):
            table_text = match.group(0).strip()
            lines = table_text.split('\n')
            
            if '|' in table_text:
                # Pipe-separated table
                rows = []
                for line in lines:
                    if '|' in line:
                        cells = [cell.strip() for cell in line.split('|') if cell.strip()]
                        if cells:
                            rows.append(' & '.join(cells) + ' \\\\')
                
                if rows:
                    col_count = len(rows[0].split(' & '))
                    latex_table = f"\\begin{{tabular}}{{{('c' * col_count)}}}\n"
                    latex_table += '\n'.join(rows)
                    latex_table += "\n\\end{tabular}"
                    return latex_table
            
            elif '\t' in table_text:
                # Tab-separated table
                rows = []
                for line in lines:
                    if '\t' in line:
                        cells = [cell.strip() for cell in line.split('\t') if cell.strip()]
                        if cells:
                            rows.append(' & '.join(cells) + ' \\\\')
                
                if rows:
                    col_count = len(rows[0].split(' & '))
                    latex_table = f"\\begin{{tabular}}{{{('c' * col_count)}}}\n"
                    latex_table += '\n'.join(rows)
                    latex_table += "\n\\end{tabular}"
                    return latex_table
            
            return match.group(0)  # Return original if conversion fails
        
        for pattern in table_patterns:
            text = re.sub(pattern, convert_table_to_latex, text, flags=re.MULTILINE)
        
        # Convert mathematical expressions to LaTeX (but exclude Myanmar legal/administrative references)
        # Simple patterns for common mathematical expressions
        math_patterns = [
            (r'(\d+)\s*\^\s*(\d+)', r'$\1^{\2}$'),  # Exponents: 2^3 -> $2^{3}$
            (r'sqrt\(([^)]+)\)', r'$\\sqrt{\1}$'),  # Square root: sqrt(x) -> $\sqrt{x}$
        ]
        
        # Only convert fractions that are clearly mathematical (not legal/administrative references)
        # Exclude patterns that contain Myanmar text or legal document patterns
        def convert_fraction(match):
            full_match = match.group(0)
            before_context = text[max(0, match.start()-20):match.start()]
            after_context = text[match.end():match.end()+20]
            
            # Check if this looks like a legal document reference or license plate
            legal_indicators = [
                'ပုဒ်မ', 'ကြီး', 'ယာဉ်', 'လိုင်စင်', 'အမှတ်', 'နံပါတ်',  # Myanmar legal terms
                'section', 'article', 'law', 'act', 'license', 'number',  # English legal terms
                '(က)', '(ခ)', '(ဂ)', '(ပ)', '(ဖ)', '(ဗ)', '(မ)',  # Myanmar subsection markers
                'YGN', 'MDY', 'NPT', 'MGW', 'BGA', 'PGO', 'TNU', 'KYT',  # Myanmar city codes
                'TOYOTA', 'HONDA', 'NISSAN', 'MAZDA', 'HYUNDAI', 'KIA', 'FORD',  # Car brands
                'BUS', 'TRUCK', 'CAR', 'TAXI', 'VAN', 'MOTORCYCLE',  # Vehicle types
            ]
            
            context = before_context + after_context
            for indicator in legal_indicators:
                if indicator in context:
                    return full_match  # Keep original format for legal references
            
            # Check if surrounded by Myanmar numerals (likely administrative reference)
            if re.search(r'[၀-၉]', before_context + after_context):
                return full_match  # Keep original format
            
            # Check for license plate patterns and file paths: XXX-##/##X-XXXX or similar
            license_plate_patterns = [
                r'[A-Z]{2,4}-\d+/\d+[A-Z]?-[A-Z\d]+',  # YGN-40/7N-XXXX
                r'[A-Z]{2,4}\s*-\s*\d+\s*/\s*\d+',     # YGN-40/7 or YGN - 40/7
                r'\d+\s*/\s*\d+[A-Z]',                  # 40/7N
                r'[A-Z]\s*\d+\s*/\s*\d+',              # A40/7
                r'\w+/\d+/\d+\.\w+',                    # file paths like t33/1/16/2705.png
                r'\d+/\d+/\d+\.\w+',                    # numeric paths like 33/1/16/2705.png
                r'[a-zA-Z0-9_-]+/\d+/\d+',             # directory/number/number patterns
            ]
            
            full_context = before_context + full_match + after_context
            for pattern in license_plate_patterns:
                if re.search(pattern, full_context):
                    return full_match  # Keep original format for license plates
            
            # Check if it's part of a dash-separated identifier (common in licenses/IDs)
            if '-' in before_context or '-' in after_context:
                return full_match  # Keep original format
            
            # Check for file extensions in the context (indicates file paths)
            file_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.bmp', '.pdf', '.doc', '.txt']
            context_text = before_context + full_match + after_context
            if any(ext in context_text.lower() for ext in file_extensions):
                return full_match  # Keep original format for file paths
            
            # Check if it's part of a URL or path structure
            if '/' in before_context or '/' in after_context:
                # Look for path-like patterns
                if re.search(r'[a-zA-Z0-9_-]+/', before_context + after_context):
                    return full_match  # Keep original format for paths
            
            # Check for common time/availability expressions
            num1, num2 = match.groups()
            if (num1 == '24' and num2 == '7') or (num1 == '7' and num2 == '24'):
                return full_match  # Keep 24/7 as is (24 hours, 7 days)
            
            # Check if surrounded by parentheses (often indicates service hours, not math)
            if ('(' in before_context and ')' in after_context) or ('（' in before_context and '）' in after_context):
                # Common service hour patterns
                service_patterns = [
                    (num1 == '24' and num2 == '7'),  # 24/7
                    (num1 == '12' and num2 == '7'),  # 12/7
                    (num1 == '8' and num2 == '5'),   # 8/5 (8am-5pm, 5 days)
                ]
                if any(service_patterns):
                    return full_match  # Keep as service hours
            
            # Only convert if it looks like a pure mathematical fraction
            return f'$\\frac{{{num1}}}{{{num2}}}$'
        
        # Apply fraction conversion with context checking
        text = re.sub(r'(\d+)\s*/\s*(\d+)', convert_fraction, text)
        
        # Apply other math patterns
        for pattern, replacement in math_patterns:
            text = re.sub(pattern, replacement, text)
        
        # Only convert equations that are clearly mathematical (not administrative)
        def convert_equation(match):
            var, equation = match.groups()
            # Skip if it contains Myanmar characters (likely not a math equation)
            if re.search(r'[\u1000-\u109F]', equation):
                return match.group(0)
            # Skip if equation is too long (likely not a simple math equation)
            if len(equation.strip()) > 20:
                return match.group(0)
            return f'${var} = {equation.strip()}$'
        
        text = re.sub(r'([a-zA-Z])\s*=\s*([^,\n]+)', convert_equation, text)
        
        return text
    
    def detect_content_issues(self, text: str) -> bool:
        """Detect content quality issues like truncation, multiple topics, garbled text"""
        if not text:
            return False
        
        # Check for paragraph truncation (ends abruptly)
        truncation_patterns = [
            r'[^.။!?]\s*$',  # Doesn't end with proper punctuation
            r'\.\.\.\s*$',   # Ends with ellipsis
            r'[a-zA-Z\u1000-\u109F]\s*$',  # Ends with letter (incomplete word)
        ]
        
        # Check for multiple topics (too many topic changes)
        topic_change_indicators = len(re.findall(r'\n\s*\n', text))
        if topic_change_indicators > 10:  # Too many paragraph breaks suggest multiple topics
            return False
        
        # Check for garbled text (too many non-standard characters)
        total_chars = len(text)
        if total_chars > 0:
            # Count Myanmar, English, numbers, and common punctuation
            valid_chars = len(re.findall(r'[\u1000-\u109F\w\s.,!?;:()"\'-]', text))
            valid_ratio = valid_chars / total_chars
            
            if valid_ratio < 0.8:  # Less than 80% valid characters suggests garbled text
                return False
        
        # Check for incoherent characters (random character sequences)
        incoherent_patterns = [
            r'[a-zA-Z]{20,}',  # Very long English words (likely garbled)
            r'[\u1000-\u109F]{30,}',  # Very long Myanmar sequences without spaces
            r'[0-9]{15,}',  # Very long number sequences
        ]
        
        for pattern in incoherent_patterns:
            if re.search(pattern, text):
                return False
        
        return True
    
    def detect_severe_content_issues(self, text: str) -> bool:
        """Detect only severe content quality issues (more lenient version)"""
        if not text:
            return False
        
        # Only check for severely garbled text (much more lenient)
        total_chars = len(text)
        if total_chars > 0:
            # Count Myanmar, English, numbers, and common punctuation
            valid_chars = len(re.findall(r'[\u1000-\u109F\w\s.,!?;:()"\'-]', text))
            valid_ratio = valid_chars / total_chars
            
            # Only reject if less than 50% valid characters (was 80%)
            if valid_ratio < 0.5:
                return False
        
        # Only check for extremely incoherent patterns
        severe_incoherent_patterns = [
            r'[a-zA-Z]{50,}',  # Extremely long English words (was 20+)
            r'[\u1000-\u109F]{100,}',  # Extremely long Myanmar sequences (was 30+)
            r'[0-9]{30,}',  # Extremely long number sequences (was 15+)
        ]
        
        for pattern in severe_incoherent_patterns:
            if re.search(pattern, text):
                return False
        
        return True
    
    def count_words_myanmar(self, text: str) -> int:
        """Count words in text (Myanmar + English) using fast Myanmar word library"""
        if not text:
            return 0
        
        # Clean text first by removing IMAGE tags, URLs, etc.
        cleaned_text = self.clean_text_for_counting(text)
        
        if not cleaned_text:
            return 0
        
        # Use Myanmar word library if available
        if MYANMAR_WORD_LIB_AVAILABLE and myanmar_segmenter:
            try:
                # Check if text has Myanmar characters
                if self.has_myanmar_characters(cleaned_text):
                    # Use FAST Myanmar segmentation for Myanmar text (4000x+ faster)
                    return myanmar_segmenter.count_words_fast(cleaned_text)
                else:
                    # For English/other languages, use simple word splitting
                    words = cleaned_text.split()
                    return len([w for w in words if w.strip()])
            except Exception as e:
                logger.warning(f"Fast Myanmar word counting failed, falling back to simple count: {e}")
                # Fallback to simple word splitting
                words = cleaned_text.split()
                return len([w for w in words if w.strip()])
        else:
            # Fallback to simple word splitting if Myanmar library not available
            words = cleaned_text.split()
            return len([w for w in words if w.strip()])
    
    def clean_text_for_counting(self, text: str) -> str:
        """Clean text by removing IMAGE tags, URLs, and other non-countable content"""
        if not text:
            return ""
        
        # Remove IMAGE tags (various formats)
        # Remove [IMAGE] tags and variations
        text = re.sub(r'\[IMAGE[^\]]*\]', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\[IMG[^\]]*\]', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\[PHOTO[^\]]*\]', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\[PIC[^\]]*\]', '', text, flags=re.IGNORECASE)
        
        # Remove URLs (http, https, www, ftp)
        url_patterns = [
            r'https?://[^\s]+',  # http/https URLs
            r'www\.[^\s]+',      # www URLs
            r'ftp://[^\s]+',     # ftp URLs
            r'[^\s]+\.[a-z]{2,}(?:/[^\s]*)?'  # domain.com style URLs
        ]
        
        for pattern in url_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # Remove email addresses
        text = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '', text)
        
        # Clean up extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def validate_content_quality(self, item: Dict[str, Any]) -> bool:
        """Validate content quality with reasonable criteria"""
        text = item.get('text', '').strip()
        title = item.get('title', '').strip()
        domain = item.get('domain', '').strip()
        
        # Check for empty content
        if not text or not title:
            return False
        
        # Check for Myanmar content (more lenient - either title OR text needs Myanmar)
        has_myanmar_title = self.has_myanmar_characters(title)
        has_myanmar_text = self.has_myanmar_characters(text)
        
        if not has_myanmar_title and not has_myanmar_text:
            return False
        
        # Use word count instead of character count for better quality assessment
        word_count = self.count_words_myanmar(text)
        if word_count < 200:  # 200 words minimum instead of 1000 characters
            return False
        
        # Clean the text for assessment (but be more lenient in other ways)
        cleaned_text = self.clean_xinhua_content(text)
        
        if not cleaned_text.strip():
            return False
        
        # After cleaning, check word count again
        cleaned_word_count = self.count_words_myanmar(cleaned_text)
        if cleaned_word_count < 150:  # 150 words minimum after cleaning
            return False
        
        # Remove "Unicode" prefix and everything before it (common in scraped content)
        unicode_index = cleaned_text.find('Unicode')
        if unicode_index != -1:
            cleaned_text = cleaned_text[unicode_index + len('Unicode'):].lstrip()
            final_word_count = self.count_words_myanmar(cleaned_text)
            if final_word_count < 100:
                return False
        
        # Remove Zawgyi separators and check remaining content
        separators = ['ZG ', 'Zawgyi ', 'ZAWGYI', '[Zawgyi]', 'ZawGyi']
        for sep in separators:
            sep_index = cleaned_text.find(sep)
            if sep_index != -1:
                cleaned_text = cleaned_text[:sep_index]
                break
        
        # Final check after all cleaning - use word count
        final_word_count = self.count_words_myanmar(cleaned_text.strip())
        if final_word_count < 100:  # 100 words minimum after all cleaning
            return False
        
        # Only check for severe content quality issues (more lenient)
        if not self.detect_severe_content_issues(cleaned_text):
            return False
        
        return True

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Clean Burmese corpus data')
    parser.add_argument('--site', type=str, help='Process only specific site (e.g., duwun_api, bbc_burmese)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging to see rejection reasons')
    
    args = parser.parse_args()
    
    # Set logging level based on verbose flag
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    cleaner = DataCleaner()
    cleaner.process_all_files(site_filter=args.site)

if __name__ == "__main__":
    main()
