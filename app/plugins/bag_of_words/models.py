from typing import List, Dict
from pydantic import BaseModel, Field
from ...models.plugin import BasePluginResponse


class WordItem(BaseModel):
    """Model for individual word items with frequency"""
    word: str = Field(..., description="The word")
    frequency: int = Field(..., description="Frequency count of the word")


class FrequencyHistogram(BaseModel):
    """Model for frequency histogram data"""
    bins: List[str] = Field(..., description="Frequency bins (e.g., [1, 2, 3, 4, 5+])")
    counts: List[int] = Field(..., description="Number of words in each frequency bin")
    labels: List[str] = Field(..., description="Human-readable labels for histogram bins")


class BagOfWordsResponse(BasePluginResponse):
    """Pydantic model for bag of words plugin response"""
    total_words: int = Field(..., description="Total number of words in the text")
    unique_words: int = Field(..., description="Number of unique words in the text")
    filtered_words: int = Field(..., description="Number of words that meet the cutoff threshold")
    cutoff_threshold: int = Field(..., description="The cutoff threshold that was applied")
    word_frequencies: Dict[str, int] = Field(..., description="Word frequencies that meet the cutoff threshold")
    word_list: List[WordItem] = Field(..., description="List of words sorted by frequency (descending)")
    frequency_histogram: FrequencyHistogram = Field(..., description="Histogram data showing distribution of word frequencies")