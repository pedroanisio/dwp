import re
from typing import Dict, Any, List
from collections import Counter
import requests
from bs4 import BeautifulSoup, NavigableString
import nltk
from nltk.tokenize import sent_tokenize
from urllib.parse import urlparse
import logging


class Plugin:
    """Enhanced Web Sentence Analyzer Plugin - Robust web content extraction and analysis"""
    
    def __init__(self):
        """Initialize the plugin with enhanced logging and NLTK setup"""
        # Configure logging
        self.logger = logging.getLogger(__name__)
        
        # Ensure NLTK punkt tokenizer is available
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            self.logger.info("Downloading NLTK punkt tokenizer...")
            nltk.download('punkt', quiet=True)
    
    def _clean_html_content(self, soup: BeautifulSoup) -> str:
        """
        Thoroughly clean HTML content with enhanced extraction
        
        Args:
            soup: BeautifulSoup parsed HTML
        
        Returns:
            Cleaned text content
        """
        # Remove specific unwanted elements
        unwanted_tags = [
            "script", "style", "noscript", "nav", "header", 
            "footer", "aside", "iframe", "svg", "form", 
            "input", "button", "comment"
        ]
        for tag in soup(unwanted_tags):
            tag.decompose()
        
        # Extract main content sections
        content_tags = ['article', 'main', 'div', 'section', 'p']
        text_parts = []
        
        for tag in soup.find_all(content_tags):
            # Only process if tag has text content
            tag_text = tag.get_text(strip=True)
            if tag_text and len(tag_text) > 50:  # Minimum meaningful content
                text_parts.append(tag_text)
        
        # If no substantial content found, fall back to full text extraction
        if not text_parts:
            text_parts = [soup.get_text(separator=' ', strip=True)]
        
        # Combine and clean text
        full_text = ' '.join(text_parts)
        full_text = re.sub(r'\s+', ' ', full_text).strip()
        
        return full_text
    
    def _is_valid_url(self, url: str) -> bool:
        """
        Enhanced URL validation with domain pattern matching
        
        Args:
            url: URL to validate
        
        Returns:
            Boolean indicating URL validity
        """
        try:
            result = urlparse(url)
            return all([
                result.scheme, 
                result.netloc,
                result.scheme in ['http', 'https'],
                re.match(r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', result.netloc)
            ])
        except Exception as e:
            self.logger.warning(f"URL validation error: {e}")
            return False
    
    def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute comprehensive web page sentence analysis with enhanced error handling
        
        Args:
            data: Dictionary containing 'url' and optional parameters
            
        Returns:
            Dictionary with comprehensive sentence analysis results
        """
        # Extract and validate parameters with bounds checking
        url = str(data.get('url', '')).strip()
        max_sentences = min(max(int(data.get('max_sentences', 50)), 10), 500)
        min_sentence_length = min(max(int(data.get('min_sentence_length', 10)), 5), 100)
        
        # Validate URL
        if not url:
            return {"error": "No URL provided for analysis"}
        
        if not self._is_valid_url(url):
            return {"error": "Invalid URL format. Use a valid http/https URL."}
        
        try:
            # Configure robust request with enhanced headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            # Enhanced request configuration with session and retries
            session = requests.Session()
            adapter = requests.adapters.HTTPAdapter(max_retries=3)
            session.mount('http://', adapter)
            session.mount('https://', adapter)
            
            # Fetch webpage with enhanced error handling
            response = session.get(
                url, 
                headers=headers, 
                timeout=(10, 30),  # (connect timeout, read timeout)
                allow_redirects=True
            )
            
            # Enhanced response validation
            response.raise_for_status()
            
            # Check content type
            content_type = response.headers.get('Content-Type', '').lower()
            if 'text/html' not in content_type:
                return {"error": f"Unsupported content type: {content_type}"}
            
            # Parse HTML
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Extract page title with fallback
            page_title = (soup.title.string.strip() if soup.title 
                          else urlparse(url).netloc)
            
            # Clean and extract text using enhanced method
            text = self._clean_html_content(soup)
            
            if not text:
                return {"error": "No meaningful text content found"}
            
            # Tokenize sentences
            sentences = sent_tokenize(text)
            
            # Filter and normalize sentences
            normalized_sentences = [
                sentence.strip().lower() 
                for sentence in sentences 
                if len(sentence.strip()) >= min_sentence_length
            ]
            
            if not normalized_sentences:
                return {
                    "error": f"No sentences found with minimum length of {min_sentence_length} characters"
                }
            
            # Count frequency
            counter = Counter(normalized_sentences)
            
            # Sort by frequency and alphabetically
            sorted_sentences = sorted(
                counter.items(), 
                key=lambda x: (-x[1], x[0])
            )[:max_sentences]
            
            # Format results
            most_common_sentences = [
                {
                    "rank": rank,
                    "sentence": sentence,
                    "frequency": frequency
                }
                for rank, (sentence, frequency) in enumerate(sorted_sentences, 1)
            ]
            
            # Calculate statistics
            return {
                "url": url,
                "page_title": page_title,
                "total_sentences": len(sentences),
                "unique_sentences": len(counter),
                "total_text_length": len(text),
                "average_sentence_length": round(
                    sum(len(s) for s in normalized_sentences) / len(normalized_sentences), 
                    2
                ),
                "most_common_sentences": most_common_sentences
            }
        
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Web request failed: {e}")
            return {"error": f"Failed to fetch webpage: {e}"}
        except Exception as e:
            self.logger.error(f"Analysis failed: {e}")
            return {"error": f"Unexpected error during analysis: {e}"} 