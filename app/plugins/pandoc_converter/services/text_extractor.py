import logging
from pathlib import Path
from bs4 import BeautifulSoup

# Set up logging
logger = logging.getLogger(__name__)


class TextExtractor:
    """Handles text extraction from HTML without pandoc"""
    
    def extract_from_html(self, input_path: Path, output_format: str, temp_dir: Path) -> Path:
        """Extract text from HTML without pandoc (for large pdf2htmlex files)"""
        logger.info("Extracting text directly from HTML without pandoc")
        
        output_filename = f"{input_path.stem}_extracted.{output_format}"
        output_path = temp_dir / output_filename
        
        try:
            # Read HTML and extract text using BeautifulSoup
            with open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
                html_content = f.read()
            
            # Parse HTML to extract text
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text content
            text_content = soup.get_text()
            
            # Clean up text
            clean_text = self._clean_text(text_content)
            
            # Write output based on format
            self._write_output(output_path, clean_text, output_format, input_path.stem)
            
            logger.info(f"Text extraction successful: {output_filename} ({output_path.stat().st_size / (1024*1024):.1f}MB)")
            return output_path
            
        except Exception as e:
            logger.error(f"Text extraction failed: {e}")
            # Create minimal output file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(f"Text extraction failed for {input_path.name}: {e}")
            return output_path
    
    def _clean_text(self, text_content: str) -> str:
        """Clean up extracted text"""
        lines = (line.strip() for line in text_content.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        return '\n'.join(chunk for chunk in chunks if chunk)
    
    def _write_output(self, output_path: Path, clean_text: str, output_format: str, stem: str):
        """Write output based on format"""
        with open(output_path, 'w', encoding='utf-8') as f:
            if output_format in ['txt', 'plain']:
                f.write(clean_text)
            elif output_format in ['md', 'markdown']:
                # Add basic markdown formatting
                f.write(f"# {stem}\n\n")
                f.write(clean_text.replace('\n\n', '\n\n## '))
            else:
                # Fallback: wrap in basic HTML
                f.write(f"<!DOCTYPE html>\n<html>\n<head>\n<title>{stem}</title>\n</head>\n<body>\n")
                f.write(f"<pre>{clean_text}</pre>\n")
                f.write("</body>\n</html>") 