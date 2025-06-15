from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from ...models.plugin import BasePluginResponse


class SentenceCluster(BaseModel):
    """Model for a cluster of similar sentences"""
    cluster_id: int = Field(..., description="Unique identifier for the cluster")
    sentences: List[str] = Field(..., description="Original sentences in this cluster")
    merged_sentence: str = Field(..., description="The merged sentence result")
    similarity_score: float = Field(..., description="Average similarity score within the cluster")
    key_phrases: List[str] = Field(..., description="Key phrases extracted from the cluster")


class SentenceMergerResponse(BasePluginResponse):
    """Pydantic model for sentence merger plugin response"""
    original_sentence_count: int = Field(..., description="Number of original sentences")
    merged_sentence_count: int = Field(..., description="Number of merged sentences")
    reduction_percentage: float = Field(..., description="Percentage reduction in sentence count")
    similarity_threshold: float = Field(..., description="Similarity threshold used for clustering")
    clusters: List[SentenceCluster] = Field(..., description="Details of each sentence cluster")
    merged_sentences: List[str] = Field(..., description="Final list of merged sentences")
    processing_stats: Dict[str, float] = Field(..., description="Processing statistics and timing") 