import re
from typing import Dict, Any
from collections import Counter


class Plugin:
    """Text Statistics Plugin - Analyzes text and provides comprehensive statistics"""
    
    def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the text statistics analysis
        
        Args:
            data: Dictionary containing 'text' key with the text to analyze
            
        Returns:
            Dictionary with comprehensive text statistics
        """
        text = data.get('text', '')
        
        if not text:
            return {
                "error": "No text provided for analysis"
            }
        
        # Basic counts
        character_count = len(text)
        character_count_no_spaces = len(text.replace(' ', ''))
        line_count = len(text.splitlines())
        
        # Word analysis
        words = self._extract_words(text)
        word_count = len(words)
        unique_words_set = set(word.lower() for word in words)
        unique_words = len(unique_words_set)
        
        # Character analysis
        unique_characters = len(set(text))
        
        # Frequency analysis
        word_frequency = dict(Counter(word.lower() for word in words))
        character_frequency = dict(Counter(text))
        
        # Advanced statistics
        average_word_length = sum(len(word) for word in words) / word_count if word_count > 0 else 0
        sentence_count = self._count_sentences(text)
        
        return {
            "character_count": character_count,
            "character_count_no_spaces": character_count_no_spaces,
            "word_count": word_count,
            "line_count": line_count,
            "unique_words": unique_words,
            "unique_characters": unique_characters,
            "word_frequency": word_frequency,
            "character_frequency": character_frequency,
            "average_word_length": round(average_word_length, 2),
            "sentence_count": sentence_count
        }
    
    def _extract_words(self, text: str) -> list:
        """Extract words from text using regex"""
        # Match word characters (letters, numbers, apostrophes in contractions)
        words = re.findall(r"\b\w+(?:'\w+)?\b", text)
        return words
    
    def _count_sentences(self, text: str) -> int:
        """Count sentences based on sentence-ending punctuation"""
        # Count sentences by looking for sentence-ending punctuation
        sentence_endings = re.findall(r'[.!?]+', text)
        return len(sentence_endings) if sentence_endings else (1 if text.strip() else 0) 