# Sentence Merger Plugin

## Overview

The Sentence Merger plugin uses advanced NLP techniques to identify and merge semantically similar sentences. It employs sentence transformers for generating embeddings and hierarchical clustering to group similar sentences, then intelligently merges them while preserving unique information.

## Features

- **Semantic Similarity Detection**: Uses pre-trained sentence transformer models to identify similar sentences
- **Intelligent Clustering**: Hierarchical clustering groups sentences based on semantic similarity
- **Smart Merging**: Preserves unique information when combining similar sentences
- **Flexible Input**: Accepts either raw text or pre-split sentences
- **Detailed Analytics**: Provides clustering details, similarity scores, and processing statistics

## Dependencies

The plugin requires the following Python packages:
- `sentence-transformers==2.2.2` - For generating sentence embeddings
- `scikit-learn==1.3.0` - For clustering algorithms
- `spacy==3.7.2` - For advanced NLP features
- `numpy` - For numerical operations

### Installation

```bash
pip install sentence-transformers scikit-learn spacy numpy
python -m spacy download en_core_web_sm
```

## Input Parameters

- **text** (optional): Raw text that will be automatically split into sentences
- **sentences** (optional): Pre-split sentences as a JSON array
- **similarity_threshold** (optional, default: 0.75): Similarity threshold for clustering (0.1-0.99)

## Output

The plugin returns:
- Original and merged sentence counts
- Reduction percentage
- Detailed cluster information including similarity scores and key phrases
- Final list of merged sentences
- Processing statistics

## Example Usage

### Input Text
```
"Climate change is affecting global temperatures. Global warming is impacting weather patterns worldwide. The economy is growing steadily this year. Economic growth has been consistent throughout the year. Rising sea levels threaten coastal cities."
```

### Expected Output
The plugin would identify that:
- "Climate change is affecting global temperatures" and "Global warming is impacting weather patterns worldwide" are similar
- "The economy is growing steadily this year" and "Economic growth has been consistent throughout the year" are similar
- "Rising sea levels threaten coastal cities" stands alone

And merge the similar sentences while preserving unique information.

## Technical Details

The plugin uses:
- **all-MiniLM-L6-v2** sentence transformer model for embeddings
- **Agglomerative Clustering** with cosine similarity for grouping
- **spaCy** for key phrase extraction and advanced text processing
- **Intelligent merging** that combines sentences while preserving unique content

## Performance

Processing time depends on:
- Number of sentences
- Complexity of text
- Similarity threshold (lower thresholds = more merging = longer processing)

The plugin provides detailed timing statistics for embedding generation and clustering phases. 