import json
import numpy as np
from typing import List, Dict, Any, Tuple, Set
from dataclasses import dataclass, field, asdict
import networkx as nx
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import spacy
from collections import defaultdict, Counter
import re
from abc import ABC, abstractmethod

# Knowledge representation classes
@dataclass
class Concept:
    """Represents a core concept in the book"""
    id: str
    term: str
    definition: str = ""
    frequency: int = 0
    importance_score: float = 0.0
    related_concepts: List[str] = field(default_factory=list)
    context_examples: List[str] = field(default_factory=list)
    chapter_occurrences: Dict[str, int] = field(default_factory=dict)

@dataclass
class Relationship:
    """Represents relationships between concepts"""
    source_id: str
    target_id: str
    relationship_type: str
    strength: float
    evidence: List[str] = field(default_factory=list)

@dataclass
class KnowledgePattern:
    """Represents recurring patterns or rules in the text"""
    pattern_id: str
    pattern_type: str  # e.g., "cause-effect", "definition", "example"
    template: str
    instances: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0

@dataclass
class SemanticCluster:
    """Groups of related concepts forming a semantic unit"""
    cluster_id: str
    theme: str
    concepts: List[str] = field(default_factory=list)
    central_idea: str = ""
    hierarchy_level: int = 0

@dataclass
class KnowledgeCartridge:
    """The complete knowledge representation of a book"""
    metadata: Dict[str, Any] = field(default_factory=dict)
    concepts: Dict[str, Concept] = field(default_factory=dict)
    relationships: List[Relationship] = field(default_factory=list)
    knowledge_graph: Dict[str, Any] = field(default_factory=dict)
    semantic_clusters: List[SemanticCluster] = field(default_factory=list)
    patterns: List[KnowledgePattern] = field(default_factory=list)
    learning_path: List[str] = field(default_factory=list)
    comprehension_questions: List[Dict[str, str]] = field(default_factory=list)
    key_insights: List[str] = field(default_factory=list)
    mental_models: List[Dict[str, Any]] = field(default_factory=list)

class KnowledgeExtractor(ABC):
    """Abstract base class for knowledge extraction strategies"""
    @abstractmethod
    def extract(self, data: Dict[str, Any]) -> Any:
        pass

class ConceptExtractor(KnowledgeExtractor):
    """Extracts core concepts from the book analysis"""
    def __init__(self):
        self.nlp = spacy.load('en_core_web_sm')
    
    def extract(self, data: Dict[str, Any]) -> Dict[str, Concept]:
        concepts = {}
        
        # Extract from lemmatized bag of words
        lemmatized_bow = data.get('lemmatized_bag_of_words', {})
        
        # Get top concepts based on frequency and TF-IDF
        important_terms = self._identify_important_terms(data)
        
        for term in important_terms:
            concept_id = f"concept_{term}"
            frequency = lemmatized_bow.get(term, 0)
            
            # Find sentences containing this term for context
            context_sentences = self._find_context_sentences(term, data.get('unique_sentences', []))
            
            # Calculate importance score
            importance = self._calculate_importance(term, data)
            
            concept = Concept(
                id=concept_id,
                term=term,
                frequency=frequency,
                importance_score=importance,
                context_examples=context_sentences[:3]  # Top 3 examples
            )
            
            concepts[concept_id] = concept
        
        return concepts
    
    def _identify_important_terms(self, data: Dict[str, Any], top_n: int = 100) -> List[str]:
        """Identify the most important terms from various sources"""
        important_terms = set()
        
        # From lemmatized bag of words (top frequency)
        lemmatized_bow = data.get('lemmatized_bag_of_words', {})
        sorted_terms = sorted(lemmatized_bow.items(), key=lambda x: x[1], reverse=True)
        important_terms.update([term for term, _ in sorted_terms[:top_n]])
        
        # From TF-IDF scores
        tfidf_by_chapter = data.get('tfidf_by_chapter', {})
        for chapter, terms in tfidf_by_chapter.items():
            important_terms.update(list(terms.keys())[:10])
        
        # From bigrams and trigrams (extract individual words)
        for ngram_dict in [data.get('top_bigrams', {}), data.get('top_trigrams', {})]:
            for ngram in ngram_dict.keys():
                important_terms.update(ngram.split('_'))
        
        return list(important_terms)
    
    def _find_context_sentences(self, term: str, sentences: List[str]) -> List[str]:
        """Find sentences containing the term"""
        context = []
        for sentence in sentences:
            if term.lower() in sentence.lower():
                context.append(sentence)
        return context
    
    def _calculate_importance(self, term: str, data: Dict[str, Any]) -> float:
        """Calculate importance score based on multiple factors"""
        score = 0.0
        
        # Frequency score
        lemmatized_bow = data.get('lemmatized_bag_of_words', {})
        max_freq = max(lemmatized_bow.values()) if lemmatized_bow else 1
        freq_score = lemmatized_bow.get(term, 0) / max_freq
        score += freq_score * 0.3
        
        # TF-IDF score
        tfidf_score = 0.0
        tfidf_by_chapter = data.get('tfidf_by_chapter', {})
        for chapter, terms in tfidf_by_chapter.items():
            if term in terms:
                tfidf_score = max(tfidf_score, terms[term])
        score += tfidf_score * 0.4
        
        # N-gram participation score
        ngram_score = 0.0
        for ngram_dict in [data.get('top_bigrams', {}), data.get('top_trigrams', {})]:
            for ngram, count in ngram_dict.items():
                if term in ngram.split('_'):
                    ngram_score += count
        
        max_ngram = max([max(d.values()) for d in [data.get('top_bigrams', {}), data.get('top_trigrams', {})] if d] + [1])
        score += (ngram_score / max_ngram) * 0.3
        
        return min(score, 1.0)

class RelationshipExtractor(KnowledgeExtractor):
    """Extracts relationships between concepts"""
    def __init__(self):
        self.nlp = spacy.load('en_core_web_sm')
        self.relation_patterns = [
            (r'(\w+) is a (\w+)', 'is_a'),
            (r'(\w+) causes (\w+)', 'causes'),
            (r'(\w+) leads to (\w+)', 'leads_to'),
            (r'(\w+) consists of (\w+)', 'consists_of'),
            (r'(\w+) requires (\w+)', 'requires'),
        ]
    
    def extract(self, data: Dict[str, Any], concepts: Dict[str, Concept]) -> List[Relationship]:
        relationships = []
        
        # Extract from bigrams and trigrams
        relationships.extend(self._extract_from_ngrams(data, concepts))
        
        # Extract from sentences using patterns
        relationships.extend(self._extract_from_patterns(data, concepts))
        
        # Extract from co-occurrence
        relationships.extend(self._extract_from_cooccurrence(data, concepts))
        
        return relationships
    
    def _extract_from_ngrams(self, data: Dict[str, Any], concepts: Dict[str, Concept]) -> List[Relationship]:
        """Extract relationships from n-grams"""
        relationships = []
        concept_terms = {c.term.lower(): c.id for c in concepts.values()}
        
        # Process bigrams
        for bigram, count in data.get('pos_filtered_bigrams', {}).items():
            words = bigram.split('_')
            if len(words) == 2:
                w1, w2 = words[0].lower(), words[1].lower()
                if w1 in concept_terms and w2 in concept_terms:
                    rel = Relationship(
                        source_id=concept_terms[w1],
                        target_id=concept_terms[w2],
                        relationship_type='adjacent_to',
                        strength=count / 100.0  # Normalize
                    )
                    relationships.append(rel)
        
        return relationships
    
    def _extract_from_patterns(self, data: Dict[str, Any], concepts: Dict[str, Concept]) -> List[Relationship]:
        """Extract relationships using linguistic patterns"""
        relationships = []
        concept_terms = {c.term.lower(): c.id for c in concepts.values()}
        
        for sentence in data.get('unique_sentences', [])[:1000]:  # Process subset for efficiency
            for pattern, rel_type in self.relation_patterns:
                matches = re.findall(pattern, sentence.lower())
                for match in matches:
                    if len(match) == 2:
                        w1, w2 = match[0], match[1]
                        if w1 in concept_terms and w2 in concept_terms:
                            rel = Relationship(
                                source_id=concept_terms[w1],
                                target_id=concept_terms[w2],
                                relationship_type=rel_type,
                                strength=0.8,
                                evidence=[sentence]
                            )
                            relationships.append(rel)
        
        return relationships
    
    def _extract_from_cooccurrence(self, data: Dict[str, Any], concepts: Dict[str, Concept]) -> List[Relationship]:
        """Extract relationships based on co-occurrence in sentences"""
        relationships = []
        concept_terms = {c.term.lower(): c.id for c in concepts.values()}
        cooccurrence_counts = defaultdict(int)
        
        # Count co-occurrences
        for sentence in data.get('unique_sentences', []):
            sentence_lower = sentence.lower()
            present_concepts = []
            
            for term, concept_id in concept_terms.items():
                if term in sentence_lower:
                    present_concepts.append(concept_id)
            
            # Count pairs
            for i in range(len(present_concepts)):
                for j in range(i + 1, len(present_concepts)):
                    pair = tuple(sorted([present_concepts[i], present_concepts[j]]))
                    cooccurrence_counts[pair] += 1
        
        # Create relationships for significant co-occurrences
        threshold = 3
        for (c1, c2), count in cooccurrence_counts.items():
            if count >= threshold:
                rel = Relationship(
                    source_id=c1,
                    target_id=c2,
                    relationship_type='cooccurs_with',
                    strength=min(count / 20.0, 1.0)  # Normalize
                )
                relationships.append(rel)
        
        return relationships

class PatternExtractor(KnowledgeExtractor):
    """Extracts knowledge patterns from the text"""
    def extract(self, data: Dict[str, Any]) -> List[KnowledgePattern]:
        patterns = []
        
        # Extract definition patterns
        patterns.extend(self._extract_definition_patterns(data))
        
        # Extract cause-effect patterns
        patterns.extend(self._extract_cause_effect_patterns(data))
        
        # Extract example patterns
        patterns.extend(self._extract_example_patterns(data))
        
        return patterns
    
    def _extract_definition_patterns(self, data: Dict[str, Any]) -> List[KnowledgePattern]:
        """Extract definition patterns"""
        patterns = []
        definition_regex = [
            r'(\w+) is defined as (.+)',
            r'(\w+) means (.+)',
            r'(\w+), which is (.+)',
        ]
        
        instances = []
        for sentence in data.get('unique_sentences', [])[:500]:
            for regex in definition_regex:
                match = re.search(regex, sentence)
                if match:
                    instances.append({
                        'term': match.group(1),
                        'definition': match.group(2),
                        'sentence': sentence
                    })
        
        if instances:
            pattern = KnowledgePattern(
                pattern_id='definition_pattern',
                pattern_type='definition',
                template='{term} is defined as {definition}',
                instances=instances,
                confidence=0.8
            )
            patterns.append(pattern)
        
        return patterns
    
    def _extract_cause_effect_patterns(self, data: Dict[str, Any]) -> List[KnowledgePattern]:
        """Extract cause-effect patterns"""
        patterns = []
        cause_effect_regex = [
            r'(.+) causes (.+)',
            r'(.+) leads to (.+)',
            r'(.+) results in (.+)',
            r'because of (.+), (.+)',
        ]
        
        instances = []
        for sentence in data.get('unique_sentences', [])[:500]:
            for regex in cause_effect_regex:
                match = re.search(regex, sentence)
                if match:
                    instances.append({
                        'cause': match.group(1),
                        'effect': match.group(2) if len(match.groups()) > 1 else match.group(1),
                        'sentence': sentence
                    })
        
        if instances:
            pattern = KnowledgePattern(
                pattern_id='cause_effect_pattern',
                pattern_type='cause-effect',
                template='{cause} leads to {effect}',
                instances=instances[:20],  # Limit instances
                confidence=0.75
            )
            patterns.append(pattern)
        
        return patterns
    
    def _extract_example_patterns(self, data: Dict[str, Any]) -> List[KnowledgePattern]:
        """Extract example patterns"""
        patterns = []
        example_regex = [
            r'for example, (.+)',
            r'such as (.+)',
            r'including (.+)',
            r'(.+), for instance',
        ]
        
        instances = []
        for sentence in data.get('unique_sentences', [])[:500]:
            for regex in example_regex:
                match = re.search(regex, sentence, re.IGNORECASE)
                if match:
                    instances.append({
                        'example': match.group(1).strip(),
                        'sentence': sentence
                    })
        
        if instances:
            pattern = KnowledgePattern(
                pattern_id='example_pattern',
                pattern_type='example',
                template='Example: {example}',
                instances=instances[:20],
                confidence=0.9
            )
            patterns.append(pattern)
        
        return patterns

class KnowledgeGraphBuilder:
    """Builds a knowledge graph from concepts and relationships"""
    def build(self, concepts: Dict[str, Concept], relationships: List[Relationship]) -> Dict[str, Any]:
        G = nx.DiGraph()
        
        # Add nodes
        for concept_id, concept in concepts.items():
            G.add_node(concept_id, 
                      term=concept.term,
                      importance=concept.importance_score,
                      frequency=concept.frequency)
        
        # Add edges
        for rel in relationships:
            G.add_edge(rel.source_id, rel.target_id,
                      relationship=rel.relationship_type,
                      weight=rel.strength)
        
        # Calculate centrality measures
        pagerank = nx.pagerank(G) if len(G) > 0 else {}
        betweenness = nx.betweenness_centrality(G) if len(G) > 0 else {}
        
        # Create graph representation
        graph_data = {
            'nodes': [
                {
                    'id': node,
                    'term': G.nodes[node].get('term', ''),
                    'importance': G.nodes[node].get('importance', 0),
                    'pagerank': pagerank.get(node, 0),
                    'betweenness': betweenness.get(node, 0)
                }
                for node in G.nodes()
            ],
            'edges': [
                {
                    'source': edge[0],
                    'target': edge[1],
                    'relationship': G.edges[edge].get('relationship', ''),
                    'weight': G.edges[edge].get('weight', 0)
                }
                for edge in G.edges()
            ],
            'statistics': {
                'num_nodes': G.number_of_nodes(),
                'num_edges': G.number_of_edges(),
                'density': nx.density(G) if len(G) > 0 else 0,
                'is_connected': nx.is_weakly_connected(G) if len(G) > 0 else False
            }
        }
        
        return graph_data

class SemanticClusterer:
    """Clusters concepts into semantic groups based on the knowledge graph structure"""
    
    def cluster(self, concepts: Dict[str, Concept], graph_data: Dict[str, Any]) -> List[SemanticCluster]:
        """Clusters concepts by finding connected components in the knowledge graph."""
        if not concepts or not graph_data['nodes']:
            return []

        G = nx.Graph()  # Use undirected graph to find connected components
        for edge in graph_data['edges']:
            G.add_edge(edge['source'], edge['target'])

        # Add nodes that might not have edges
        for node in graph_data['nodes']:
            G.add_node(node['id'])

        connected_components = list(nx.connected_components(G))
        
        semantic_clusters = []
        for i, component in enumerate(connected_components):
            concept_list = list(component)
            
            if len(concept_list) < 2:  # Optional: filter out small clusters
                continue

            cluster_terms = [concepts[cid].term for cid in concept_list if cid in concepts]
            theme = self._generate_theme(cluster_terms)
            
            semantic_cluster = SemanticCluster(
                cluster_id=f'cluster_{i}',
                theme=theme,
                concepts=concept_list,
                hierarchy_level=0
            )
            semantic_clusters.append(semantic_cluster)
        
        return semantic_clusters

    def _generate_theme(self, terms: List[str]) -> str:
        """Generate a theme name for a cluster of terms."""
        if not terms:
            return "Untitled Cluster"
        
        word_freq = Counter()
        # A simple list of stopwords to ignore
        stopwords = {'the', 'a', 'an', 'is', 'of', 'in', 'and', 'to', 'for'}
        for term in terms:
            words = [w for w in term.lower().split() if w not in stopwords]
            word_freq.update(words)
        
        common_words = [word for word, _ in word_freq.most_common(3)]
        return ' '.join(common_words) if common_words else terms[0]

class LearningPathGenerator:
    """Generates an optimal learning path through the concepts"""
    def generate(self, concepts: Dict[str, Concept], relationships: List[Relationship], 
                 graph_data: Dict[str, Any]) -> List[str]:
        # Build dependency graph
        G = nx.DiGraph()
        
        # Add edges based on certain relationship types
        dependency_types = ['requires', 'is_a', 'consists_of']
        for rel in relationships:
            if rel.relationship_type in dependency_types:
                G.add_edge(rel.target_id, rel.source_id)  # Reverse for dependencies
        
        # Topological sort if possible
        if nx.is_directed_acyclic_graph(G):
            path = list(nx.topological_sort(G))
        else:
            # Use PageRank for cyclic graphs
            pagerank_scores = {node['id']: node['pagerank'] 
                             for node in graph_data['nodes']}
            path = sorted(concepts.keys(), 
                         key=lambda x: pagerank_scores.get(x, 0), 
                         reverse=True)
        
        # Ensure all concepts are included
        all_concepts = set(concepts.keys())
        path_set = set(path)
        missing = all_concepts - path_set
        path.extend(list(missing))
        
        return path[:50]  # Return top 50 concepts

class QuestionGenerator:
    """Generates comprehension questions"""
    def generate(self, concepts: Dict[str, Concept], patterns: List[KnowledgePattern]) -> List[Dict[str, str]]:
        questions = []
        
        # Generate definition questions
        for concept in list(concepts.values())[:20]:
            if concept.context_examples:
                question = {
                    'type': 'definition',
                    'question': f"What is {concept.term}?",
                    'answer': concept.context_examples[0] if concept.context_examples else "",
                    'concept_id': concept.id
                }
                questions.append(question)
        
        # Generate pattern-based questions
        for pattern in patterns:
            if pattern.pattern_type == 'cause-effect' and pattern.instances:
                instance = pattern.instances[0]
                question = {
                    'type': 'cause-effect',
                    'question': f"What causes {instance.get('effect', '')}?",
                    'answer': instance.get('cause', ''),
                    'pattern_id': pattern.pattern_id
                }
                questions.append(question)
        
        return questions[:30]  # Limit to 30 questions

class InsightExtractor:
    """Extracts key insights from the analysis"""
    def extract(self, data: Dict[str, Any], concepts: Dict[str, Concept], 
                clusters: List[SemanticCluster]) -> List[str]:
        insights = []
        
        # Topic-based insights
        topics = data.get('topics_lda', {})
        for topic_name, words in list(topics.items())[:5]:
            insight = f"Major theme: {' '.join(words[:5])}"
            insights.append(insight)
        
        # High-importance concept insights
        top_concepts = sorted(concepts.values(), 
                            key=lambda x: x.importance_score, 
                            reverse=True)[:10]
        for concept in top_concepts[:5]:
            if concept.frequency > 10:
                insight = f"Core concept '{concept.term}' appears {concept.frequency} times"
                insights.append(insight)
        
        # Cluster insights
        for cluster in clusters[:3]:
            if len(cluster.concepts) > 5:
                insight = f"Semantic group around '{cluster.theme}' contains {len(cluster.concepts)} related concepts"
                insights.append(insight)
        
        return insights

class KnowledgeCartridgeBuilder:
    """Main builder that orchestrates the knowledge extraction process"""
    def __init__(self):
        self.concept_extractor = ConceptExtractor()
        self.relationship_extractor = RelationshipExtractor()
        self.pattern_extractor = PatternExtractor()
        self.graph_builder = KnowledgeGraphBuilder()
        self.clusterer = SemanticClusterer()
        self.path_generator = LearningPathGenerator()
        self.question_generator = QuestionGenerator()
        self.insight_extractor = InsightExtractor()
    
    def build(self, analysis_file: str) -> KnowledgeCartridge:
        """Build a complete knowledge cartridge from book analysis"""
        print("Loading book analysis...")
        with open(analysis_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print("Extracting concepts...")
        concepts = self.concept_extractor.extract(data)
        print(f"  Found {len(concepts)} concepts")
        
        print("Extracting relationships...")
        relationships = self.relationship_extractor.extract(data, concepts)
        print(f"  Found {len(relationships)} relationships")
        
        print("Extracting patterns...")
        patterns = self.pattern_extractor.extract(data)
        print(f"  Found {len(patterns)} patterns")
        
        print("Building knowledge graph...")
        graph_data = self.graph_builder.build(concepts, relationships)
        
        print("Clustering concepts symbolically...")
        clusters = self.clusterer.cluster(concepts, graph_data)
        print(f"  Created {len(clusters)} semantic clusters")
        
        print("Generating learning path...")
        learning_path = self.path_generator.generate(concepts, relationships, graph_data)
        
        print("Generating questions...")
        questions = self.question_generator.generate(concepts, patterns)
        
        print("Extracting insights...")
        insights = self.insight_extractor.extract(data, concepts, clusters)
        
        # Create metadata
        metadata = {
            'source': 'book_analysis.json',
            'num_sentences': len(data.get('unique_sentences', [])),
            'num_unique_words': len(data.get('lemmatized_bag_of_words', {})),
            'num_chapters': len(data.get('tfidf_by_chapter', {})),
            'extraction_version': '1.0'
        }
        
        # Build the cartridge
        cartridge = KnowledgeCartridge(
            metadata=metadata,
            concepts=concepts,
            relationships=relationships,
            knowledge_graph=graph_data,
            semantic_clusters=clusters,
            patterns=patterns,
            learning_path=learning_path,
            comprehension_questions=questions,
            key_insights=insights
        )
        
        return cartridge

def save_cartridge(cartridge: KnowledgeCartridge, output_file: str):
    """Save the knowledge cartridge to JSON"""
    # Convert dataclasses to dicts
    cartridge_dict = {
        'metadata': cartridge.metadata,
        'concepts': {k: asdict(v) for k, v in cartridge.concepts.items()},
        'relationships': [asdict(r) for r in cartridge.relationships],
        'knowledge_graph': cartridge.knowledge_graph,
        'semantic_clusters': [asdict(c) for c in cartridge.semantic_clusters],
        'patterns': [asdict(p) for p in cartridge.patterns],
        'learning_path': cartridge.learning_path,
        'comprehension_questions': cartridge.comprehension_questions,
        'key_insights': cartridge.key_insights,
        'mental_models': cartridge.mental_models
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(cartridge_dict, f, indent=2, ensure_ascii=False)

def main():
    """Main execution function"""
    analysis_file = 'pci_analysis.json'
    output_file = 'pci_cartridge.json'
    
    print("=== Knowledge Cartridge Generator ===")
    print("Creating knowledge representation...")
    
    builder = KnowledgeCartridgeBuilder()
    cartridge = builder.build(analysis_file)
    
    print("\nSaving cartridge...")
    save_cartridge(cartridge, output_file)
    
    print(f"\n✓ Knowledge cartridge saved to {output_file}")
    print("\nCartridge Statistics:")
    print(f"  - Concepts: {len(cartridge.concepts)}")
    print(f"  - Relationships: {len(cartridge.relationships)}")
    print(f"  - Semantic Clusters: {len(cartridge.semantic_clusters)}")
    print(f"  - Knowledge Patterns: {len(cartridge.patterns)}")
    print(f"  - Learning Path Steps: {len(cartridge.learning_path)}")
    print(f"  - Comprehension Questions: {len(cartridge.comprehension_questions)}")
    print(f"  - Key Insights: {len(cartridge.key_insights)}")
    
    print("\nThe machine can now 'learn' this book instantly! 🧠⚡")

if __name__ == "__main__":
    main()