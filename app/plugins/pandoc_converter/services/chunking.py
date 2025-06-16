import logging
from pathlib import Path
from typing import List
from bs4 import BeautifulSoup

# Set up logging
logger = logging.getLogger(__name__)


class ChunkingService:
    """Handles HTML file chunking operations"""
    
    def should_chunk(self, file_size: int, file_ext: str, threshold: int) -> bool:
        """Determine if file should be chunked based on size and type"""
        return file_ext.lower() == '.html' and file_size > threshold
    
    def split_html_content(self, input_path: Path, temp_dir: Path, max_chunk_size: int) -> List[Path]:
        """Split large HTML file into smaller chunks at logical boundaries"""
        try:
            logger.info(f"Splitting large HTML file: {input_path} (target chunk size: {max_chunk_size / (1024*1024):.1f}MB)")
            
            # First try simple text-based chunking for very large files
            file_size = input_path.stat().st_size
            if file_size > 200 * 1024 * 1024:  # > 200MB, use simple text chunking
                return self._split_html_by_text(input_path, temp_dir, max_chunk_size)
            
            # Read and parse HTML for smaller files
            try:
                with open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Parse with BeautifulSoup (memory intensive)
                soup = BeautifulSoup(content, 'html.parser')
            except MemoryError:
                logger.warning("BeautifulSoup parsing failed due to memory, falling back to text chunking")
                return self._split_html_by_text(input_path, temp_dir, max_chunk_size)
            
            return self._split_with_beautifulsoup(soup, input_path, temp_dir, max_chunk_size)
            
        except Exception as e:
            logger.error(f"Failed to split HTML file: {e}")
            # Return original file if chunking fails
            return [input_path]
    
    def _split_html_by_text(self, input_path: Path, temp_dir: Path, max_chunk_size: int) -> List[Path]:
        """Fallback method: split HTML by text without parsing (memory efficient)"""
        logger.info("Using text-based HTML chunking for very large file")
        
        chunks = []
        chunk_num = 0
        
        try:
            with open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
                current_chunk = ""
                chunk_size = 0
                
                # Read line by line to manage memory
                for line in f:
                    line_size = len(line.encode('utf-8'))
                    
                    # Check if adding this line exceeds chunk size
                    if chunk_size + line_size > max_chunk_size and current_chunk:
                        # Save current chunk
                        chunk_path = self._create_text_chunk(temp_dir, chunk_num, current_chunk, input_path.stem)
                        chunks.append(chunk_path)
                        chunk_num += 1
                        
                        # Start new chunk
                        current_chunk = line
                        chunk_size = line_size
                    else:
                        current_chunk += line
                        chunk_size += line_size
                
                # Save final chunk
                if current_chunk:
                    chunk_path = self._create_text_chunk(temp_dir, chunk_num, current_chunk, input_path.stem)
                    chunks.append(chunk_path)
            
            logger.info(f"Split HTML into {len(chunks)} chunks using text-based chunking")
            return chunks
            
        except Exception as e:
            logger.error(f"Text-based chunking failed: {e}")
            return [input_path]
    
    def _split_with_beautifulsoup(self, soup: BeautifulSoup, input_path: Path, temp_dir: Path, max_chunk_size: int) -> List[Path]:
        """Split HTML using BeautifulSoup parsing"""
        # Extract document structure
        head = soup.find('head')
        body = soup.find('body')
        
        if not body:
            body_elements = list(soup.children)
        else:
            body_elements = list(body.children)
        
        chunks = []
        current_chunk_elements = []
        current_chunk_size = 0
        chunk_num = 0
        
        # Estimate header size
        head_size = len(str(head)) if head else 1000
        base_html_size = head_size + 200  # <html>, <body> tags etc.
        
        for element in body_elements:
            element_size = len(str(element))
            
            # If single element is too large, try to split it further
            if element_size > max_chunk_size:
                logger.warning(f"Large element ({element_size / (1024*1024):.1f}MB) detected, attempting sub-chunking")
                sub_chunks = self._split_large_element(element, temp_dir, chunk_num, head, input_path.stem, max_chunk_size)
                chunks.extend(sub_chunks)
                chunk_num += len(sub_chunks)
                continue
            
            # Check if adding this element would exceed chunk size
            if (current_chunk_size + element_size + base_html_size > max_chunk_size and 
                current_chunk_elements):
                
                # Save current chunk
                chunk_path = self._create_html_chunk(
                    temp_dir, chunk_num, head, current_chunk_elements, input_path.stem
                )
                chunks.append(chunk_path)
                chunk_num += 1
                
                # Start new chunk
                current_chunk_elements = [element]
                current_chunk_size = element_size
            else:
                current_chunk_elements.append(element)
                current_chunk_size += element_size
        
        # Save final chunk if there are remaining elements
        if current_chunk_elements:
            chunk_path = self._create_html_chunk(
                temp_dir, chunk_num, head, current_chunk_elements, input_path.stem
            )
            chunks.append(chunk_path)
        
        logger.info(f"Split HTML into {len(chunks)} chunks using structured parsing")
        return chunks
    
    def _create_text_chunk(self, temp_dir: Path, chunk_num: int, content: str, original_stem: str) -> Path:
        """Create a simple text chunk (minimal HTML structure)"""
        chunk_filename = f"{original_stem}_textchunk_{chunk_num:03d}.html"
        chunk_path = temp_dir / chunk_filename
        
        # Wrap content in minimal HTML
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>{original_stem} - Text Chunk {chunk_num + 1}</title>
    <meta charset="utf-8">
</head>
<body>
{content}
</body>
</html>"""
        
        with open(chunk_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"Created text chunk: {chunk_filename} ({chunk_path.stat().st_size / (1024*1024):.1f}MB)")
        return chunk_path
    
    def _create_html_chunk(self, temp_dir: Path, chunk_num: int, head, body_elements: List, original_stem: str) -> Path:
        """Create a valid HTML chunk file"""
        chunk_filename = f"{original_stem}_chunk_{chunk_num:03d}.html"
        chunk_path = temp_dir / chunk_filename
        
        # Create new HTML document
        new_soup = BeautifulSoup("", 'html.parser')
        
        # Add DOCTYPE
        doctype = "<!DOCTYPE html>"
        
        # Create HTML structure
        html_tag = new_soup.new_tag('html')
        new_soup.append(html_tag)
        
        # Add head (if exists)
        if head:
            html_tag.append(head)
        else:
            # Create minimal head
            head_tag = new_soup.new_tag('head')
            title_tag = new_soup.new_tag('title')
            title_tag.string = f"{original_stem} - Chunk {chunk_num + 1}"
            head_tag.append(title_tag)
            html_tag.append(head_tag)
        
        # Add body with elements
        body_tag = new_soup.new_tag('body')
        for element in body_elements:
            if element.name:  # Skip text nodes without tags
                body_tag.append(element)
        html_tag.append(body_tag)
        
        # Write chunk to file
        with open(chunk_path, 'w', encoding='utf-8') as f:
            f.write(doctype + '\n')
            f.write(str(new_soup))
        
        logger.info(f"Created chunk: {chunk_filename} ({chunk_path.stat().st_size / (1024*1024):.1f}MB)")
        return chunk_path
    
    def _split_large_element(self, element, temp_dir: Path, base_chunk_num: int, head, original_stem: str, max_size: int) -> List[Path]:
        """Split a single large HTML element into smaller pieces"""
        chunks = []
        
        try:
            # Convert element to string and split by common boundaries
            element_str = str(element)
            
            # Try to split on common HTML boundaries
            split_patterns = [
                '</div>',  # div boundaries
                '</p>',    # paragraph boundaries
                '</span>', # span boundaries
                '</li>',   # list item boundaries
                '\n\n'     # double newlines
            ]
            
            best_chunks = [element_str]  # Start with whole element
            
            for pattern in split_patterns:
                if len(best_chunks) == 1 and len(best_chunks[0]) > max_size:
                    # Try splitting on this pattern
                    new_chunks = []
                    for chunk in best_chunks:
                        if len(chunk) > max_size:
                            parts = chunk.split(pattern)
                            # Rejoin the pattern except for last part
                            rejoined = [parts[0]]
                            for i in range(1, len(parts)):
                                if len(rejoined[-1]) + len(pattern) + len(parts[i]) < max_size:
                                    rejoined[-1] += pattern + parts[i]
                                else:
                                    rejoined.append(parts[i])
                            new_chunks.extend(rejoined)
                        else:
                            new_chunks.append(chunk)
                    best_chunks = new_chunks
            
            # Create chunk files
            for i, chunk_content in enumerate(best_chunks):
                if chunk_content.strip():  # Skip empty chunks
                    chunk_path = self._create_text_chunk(temp_dir, base_chunk_num + i, chunk_content, f"{original_stem}_subelement")
                    chunks.append(chunk_path)
            
            return chunks
            
        except Exception as e:
            logger.error(f"Large element splitting failed: {e}")
            # Create single chunk with the element
            chunk_path = self._create_text_chunk(temp_dir, base_chunk_num, str(element), f"{original_stem}_large")
            return [chunk_path]
    
    def merge_chunks(self, chunk_results: List[Path], output_format: str, temp_dir: Path, original_stem: str) -> Path:
        """Merge converted chunks back into single output file"""
        merged_filename = f"{original_stem}_merged.{output_format}"
        merged_path = temp_dir / merged_filename
        
        try:
            with open(merged_path, 'w', encoding='utf-8') as merged_file:
                for i, chunk_path in enumerate(chunk_results):
                    if chunk_path.exists():
                        with open(chunk_path, 'r', encoding='utf-8') as chunk_file:
                            content = chunk_file.read()
                            
                            # Add separator between chunks (except for first chunk)
                            if i > 0:
                                if output_format in ['md', 'markdown']:
                                    merged_file.write("\n\n---\n\n")  # Markdown separator
                                elif output_format in ['txt', 'plain']:
                                    merged_file.write("\n\n" + "="*50 + "\n\n")  # Text separator
                                else:
                                    merged_file.write("\n\n")  # Simple separator
                            
                            merged_file.write(content)
                    else:
                        logger.warning(f"Chunk file not found: {chunk_path}")
            
            logger.info(f"Merged {len(chunk_results)} chunks into: {merged_filename}")
            return merged_path
            
        except Exception as e:
            logger.error(f"Failed to merge chunks: {e}")
            # Return first successful chunk if merging fails
            for chunk_path in chunk_results:
                if chunk_path.exists():
                    return chunk_path
            raise RuntimeError(f"No successful chunks to merge: {e}") 