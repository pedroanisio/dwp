#!/usr/bin/env python3
"""
Deep structure analyzer for nested Principia documents.
This script analyzes the nested content within div blocks.
"""

import json
import sys
from collections import Counter, defaultdict
from typing import Dict, List, Any, Tuple

class NestedContentAnalyzer:
    def __init__(self):
        self.content_depth = 0
        self.max_text_length = 0
        self.text_samples = []
        self.nested_structure_map = defaultdict(int)
        
    def analyze_file(self, filename: str):
        """Main analysis function."""
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print("=== NESTED CONTENT ANALYSIS ===\n")
        
        body = data.get('body', [])
        
        # Separate top-level blocks
        top_level_paragraphs = [b for b in body if b.get('type') == 'paragraph']
        top_level_divs = [b for b in body if b.get('type') == 'div']
        
        print(f"TOP LEVEL STRUCTURE:")
        print(f"  Empty Paragraphs: {len(top_level_paragraphs)}")
        print(f"  Div Containers: {len(top_level_divs)}")
        
        # Analyze div contents
        print("\n=== ANALYZING DIV CONTENTS ===\n")
        
        all_nested_content = []
        div_structures = Counter()
        
        for i, div_block in enumerate(top_level_divs):
            content = div_block.get('content', [])
            structure = self._analyze_div_content(content, f"div[{i}]")
            div_structures[structure] += 1
            all_nested_content.extend(content)
        
        # Print div structure patterns
        print("\nDIV STRUCTURE PATTERNS:")
        for pattern, count in div_structures.most_common(10):
            print(f"  {pattern}: {count} divs")
        
        # Analyze all nested content
        self._analyze_nested_content(all_nested_content)
        
        # Print findings
        print("\nNESTED CONTENT STATISTICS:")
        print(f"  Maximum nesting depth: {self.content_depth}")
        print(f"  Longest text content: {self.max_text_length} characters")
        
        print("\nNESTED STRUCTURE FREQUENCY:")
        for structure, count in sorted(self.nested_structure_map.items(), 
                                     key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {structure}: {count}")
        
        # Show text samples
        if self.text_samples:
            print("\nTEXT CONTENT SAMPLES:")
            for i, (path, text) in enumerate(self.text_samples[:5]):
                preview = text[:100] + "..." if len(text) > 100 else text
                print(f"\n  Sample {i+1} from {path}:")
                print(f"    \"{preview}\"")
    
    def _analyze_div_content(self, content: List[Dict], path: str) -> str:
        """Analyze content of a single div and return its structure signature."""
        if not content:
            return "empty"
        
        # Count content types
        type_counts = Counter()
        for item in content:
            if isinstance(item, dict):
                item_type = item.get('type', 'unknown')
                type_counts[item_type] += 1
        
        # Create structure signature
        signature_parts = []
        for content_type, count in sorted(type_counts.items()):
            signature_parts.append(f"{count}{content_type[0]}")  # e.g., "2p" for 2 paragraphs
        
        return "-".join(signature_parts) if signature_parts else "empty"
    
    def _analyze_nested_content(self, content_list: List[Any], depth: int = 1, path: str = ""):
        """Recursively analyze nested content."""
        self.content_depth = max(self.content_depth, depth)
        
        for i, item in enumerate(content_list):
            current_path = f"{path}[{i}]" if path else f"item[{i}]"
            
            if isinstance(item, dict):
                item_type = item.get('type', 'unknown')
                
                # Track structure patterns
                structure_key = f"level{depth}_{item_type}"
                self.nested_structure_map[structure_key] += 1
                
                # Analyze based on type
                if item_type == 'paragraph':
                    self._analyze_paragraph(item, current_path)
                elif item_type == 'div':
                    nested_content = item.get('content', [])
                    self._analyze_nested_content(nested_content, depth + 1, f"{current_path}.div")
                elif item_type == 'heading':
                    self._analyze_heading(item, current_path)
                elif item_type in ['text', 'emphasis']:
                    self._analyze_text_content(item, current_path)
    
    def _analyze_paragraph(self, para: Dict, path: str):
        """Analyze paragraph content."""
        content = para.get('content', [])
        semantic_label = para.get('semantic_label')
        
        if semantic_label:
            self.nested_structure_map[f"semantic_{semantic_label}"] += 1
        
        # Extract text
        full_text = self._extract_text_from_content(content)
        if full_text:
            self.max_text_length = max(self.max_text_length, len(full_text))
            if len(self.text_samples) < 10:
                self.text_samples.append((f"{path}[{semantic_label or 'para'}]", full_text))
        
        # Continue analyzing nested content
        self._analyze_nested_content(content, 999, f"{path}.para")  # 999 indicates inline content
    
    def _analyze_heading(self, heading: Dict, path: str):
        """Analyze heading content."""
        level = heading.get('level', 0)
        content = heading.get('content', [])
        
        self.nested_structure_map[f"heading_level_{level}"] += 1
        
        # Extract heading text
        heading_text = self._extract_text_from_content(content)
        if heading_text and len(self.text_samples) < 10:
            self.text_samples.append((f"{path}[h{level}]", heading_text))
    
    def _analyze_text_content(self, text_item: Dict, path: str):
        """Analyze text or emphasis content."""
        content = text_item.get('content', '')
        if content:
            self.max_text_length = max(self.max_text_length, len(content))
    
    def _extract_text_from_content(self, content_list: List[Dict]) -> str:
        """Extract all text from a content list."""
        texts = []
        for item in content_list:
            if isinstance(item, dict):
                if item.get('type') in ['text', 'emphasis']:
                    text = item.get('content', '')
                    if text:
                        texts.append(text)
        return ' '.join(texts)

def analyze_nested_structure(filename: str):
    """Analyze nested structure and find unique patterns."""
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print("\n=== UNIQUE NESTED PATTERNS ===\n")
    
    # Find unique div structures
    unique_patterns = defaultdict(list)
    body = data.get('body', [])
    
    for i, block in enumerate(body):
        if block.get('type') == 'div':
            pattern = extract_pattern(block)
            unique_patterns[pattern].append(i)
    
    # Show unique patterns
    print("UNIQUE DIV PATTERNS FOUND:")
    for pattern, indices in sorted(unique_patterns.items(), 
                                 key=lambda x: len(x[1]), reverse=True)[:10]:
        print(f"\n  Pattern: {pattern}")
        print(f"  Occurrences: {len(indices)}")
        print(f"  First at index: {indices[0]}")
        
        # Show example structure
        if indices:
            example = body[indices[0]]
            print("  Example structure:")
            print_structure(example, indent=4)

def extract_pattern(block: Dict, max_depth: int = 3) -> str:
    """Extract a pattern signature from a block."""
    def _extract(item: Any, depth: int) -> str:
        if depth > max_depth:
            return "..."
        
        if isinstance(item, dict):
            item_type = item.get('type', 'unknown')
            if 'content' in item and isinstance(item['content'], list):
                content_pattern = [_extract(c, depth + 1) for c in item['content'][:3]]
                return f"{item_type}[{','.join(content_pattern)}]"
            return item_type
        elif isinstance(item, list):
            patterns = [_extract(i, depth + 1) for i in item[:3]]
            return f"[{','.join(patterns)}]"
        else:
            return type(item).__name__
    
    return _extract(block, 0)

def print_structure(block: Dict, indent: int = 0, max_depth: int = 4):
    """Print structure with indentation."""
    if indent // 2 > max_depth:
        print(" " * indent + "...")
        return
    
    prefix = " " * indent
    
    if isinstance(block, dict):
        block_type = block.get('type', 'unknown')
        print(f"{prefix}{block_type}:")
        
        for key, value in block.items():
            if key == 'content':
                if isinstance(value, list):
                    print(f"{prefix}  content: [{len(value)} items]")
                    for i, item in enumerate(value[:2]):  # Show first 2 items
                        print(f"{prefix}    [{i}]:")
                        print_structure(item, indent + 6, max_depth)
                    if len(value) > 2:
                        print(f"{prefix}    ... and {len(value) - 2} more")
                else:
                    print(f"{prefix}  {key}: {type(value).__name__}")
            elif key not in ['type']:
                value_repr = repr(value)[:50] + "..." if len(repr(value)) > 50 else repr(value)
                print(f"{prefix}  {key}: {value_repr}")

def extract_all_text(filename: str, output_file: str = None):
    """Extract all text content from the document."""
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    all_text = []
    
    def extract_text(item: Any, path: str = ""):
        if isinstance(item, dict):
            if item.get('type') == 'text':
                content = item.get('content', '')
                if content:
                    all_text.append({
                        'path': path,
                        'text': content,
                        'type': 'text'
                    })
            elif item.get('type') == 'emphasis':
                content = item.get('content', '')
                if content:
                    all_text.append({
                        'path': path,
                        'text': content,
                        'type': 'emphasis'
                    })
            elif 'content' in item:
                for i, nested in enumerate(item.get('content', [])):
                    extract_text(nested, f"{path}/{item.get('type', 'unknown')}[{i}]")
        elif isinstance(item, list):
            for i, nested in enumerate(item):
                extract_text(nested, f"{path}[{i}]")
    
    # Extract from body
    body = data.get('body', [])
    for i, block in enumerate(body):
        extract_text(block, f"body[{i}]")
    
    print(f"\nTotal text segments found: {len(all_text)}")
    
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            for item in all_text:
                f.write(f"=== {item['path']} ({item['type']}) ===\n")
                f.write(item['text'])
                f.write("\n\n")
        print(f"All text extracted to: {output_file}")
    
    return all_text

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python nested_analyzer.py <json_file> [command]")
        print("Commands:")
        print("  analyze - Deep nested content analysis (default)")
        print("  patterns - Show unique structural patterns")
        print("  extract - Extract all text to file")
        sys.exit(1)
    
    filename = sys.argv[1]
    command = sys.argv[2] if len(sys.argv) > 2 else "analyze"
    
    try:
        if command == "analyze":
            analyzer = NestedContentAnalyzer()
            analyzer.analyze_file(filename)
        elif command == "patterns":
            analyze_nested_structure(filename)
        elif command == "extract":
            output = filename.replace('.json', '_text.txt')
            extract_all_text(filename, output)
        else:
            print(f"Unknown command: {command}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()