from typing import List, Dict
from pydantic import BaseModel, Field
from ...models.plugin import BasePluginResponse


class WordInfo(BaseModel):
    """Model for word information with POS tag and reason"""
    word: str = Field(..., description="The word")
    pos_tag: str = Field(..., description="Part-of-speech tag")
    reason: str = Field(..., description="Reason for removal or preservation")


class ProcessingStatistics(BaseModel):
    """Model for processing statistics"""
    original_word_count: int = Field(..., description="Number of words in original text")
    processed_word_count: int = Field(..., description="Number of words after processing")
    words_removed_count: int = Field(..., description="Number of words removed")
    words_preserved_count: int = Field(..., description="Number of potential stopwords preserved")
    stopword_removal_rate: float = Field(..., description="Percentage of words removed as stopwords")


class ContextAwareStopwordsResponse(BasePluginResponse):
    """Pydantic model for context-aware stopwords plugin response"""
    original_text: str = Field(..., description="The original input text")
    processed_text: str = Field(..., description="Text after stopword removal")
    method_used: str = Field(..., description="The stopword removal method that was applied")
    words_removed: List[WordInfo] = Field(..., description="List of words that were removed as stopwords")
    words_preserved: List[WordInfo] = Field(..., description="List of potential stopwords that were preserved due to context")
    statistics: ProcessingStatistics = Field(..., description="Processing statistics")