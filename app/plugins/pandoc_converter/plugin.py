from pathlib import Path
import subprocess
import tempfile
from typing import Dict, Any, Type, List, Union
import os
import shutil
import logging
import uuid
import re
import psutil
from pathlib import Path
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field
from ...models.plugin import BasePlugin, BasePluginResponse

# Set up logging
logger = logging.getLogger(__name__)

class PandocConverterResponse(BasePluginResponse):
    """Pydantic model for pandoc converter plugin response"""
    file_path: str = Field(..., description="Path to the converted file")
    file_name: str = Field(..., description="Name of the converted file")
    conversion_details: Dict[str, Any] = Field(default={}, description="Details about the conversion process")


class Plugin(BasePlugin):
    """Pandoc File Converter Plugin - Converts files between markup formats using Pandoc"""
    
    @classmethod
    def get_response_model(cls) -> Type[BasePluginResponse]:
        """Return the Pydantic model for this plugin's response"""
        return PandocConverterResponse
    
    def _ensure_downloads_directory(self) -> Path:
        """Ensure downloads directory exists and return its path"""
        downloads_dir = Path("/app/data/downloads")
        downloads_dir.mkdir(parents=True, exist_ok=True)
        return downloads_dir
    
    def _move_to_downloads(self, temp_file_path: Path, original_filename: str) -> Path:
        """Move file from temp directory to permanent downloads directory"""
        downloads_dir = self._ensure_downloads_directory()
        
        # Create unique filename to avoid conflicts
        unique_id = str(uuid.uuid4())[:8]
        file_stem = temp_file_path.stem
        file_suffix = temp_file_path.suffix
        safe_filename = f"{file_stem}_{unique_id}{file_suffix}"
        
        permanent_path = downloads_dir / safe_filename
        
        # Move the file
        shutil.move(str(temp_file_path), str(permanent_path))
        logger.info(f"Moved output file to permanent location: {permanent_path}")
        
        return permanent_path
    
    def _validate_input_file(self, filename: str, file_size: int) -> Dict[str, Any]:
        """Validate input file and return diagnostics"""
        file_ext = Path(filename).suffix.lower()
        
        diagnostics = {
            "filename": filename,
            "file_size": file_size,
            "file_extension": file_ext,
            "size_mb": round(file_size / (1024 * 1024), 2)
        }
        
        # Check for potential issues
        if file_size == 0:
            raise ValueError("Input file is empty")
        if file_size > 2 * 1024 * 1024 * 1024:  # 2GB limit instead of 500MB
            raise ValueError(f"Input file too large: {diagnostics['size_mb']}MB (max 2048MB)")
            
        return diagnostics
    
    def _validate_advanced_options(self, advanced_options: Union[str, List[str], None]) -> List[str]:
        """Validate and parse advanced pandoc options"""
        if not advanced_options:
            return []
        
        # Convert to list if string
        if isinstance(advanced_options, str):
            # Split by spaces, but preserve quoted arguments
            import shlex
            try:
                options_list = shlex.split(advanced_options)
            except ValueError as e:
                raise ValueError(f"Invalid advanced_options format: {e}")
        else:
            options_list = advanced_options.copy()
        
        # Security validation: check for dangerous patterns
        dangerous_patterns = [
            r'[;&|`$]',  # Shell metacharacters
            r'\.\./',     # Directory traversal
            r'--?[io]$',  # Input/output flags that could override our files
            r'--input',
            r'--output',
        ]
        
        validated_options = []
        for option in options_list:
            if not isinstance(option, str):
                raise ValueError(f"All advanced options must be strings, got: {type(option)}")
            
            # Check for dangerous patterns
            for pattern in dangerous_patterns:
                if re.search(pattern, option):
                    raise ValueError(f"Advanced option contains potentially dangerous content: '{option}'")
            
            # Don't allow overriding critical options
            if option.startswith(('-o', '--output')):
                raise ValueError(f"Cannot override output option: '{option}'")
            
            validated_options.append(option.strip())
        
        return validated_options
    
    def _validate_and_process_features(self, features: Union[str, List[str], None]) -> List[str]:
        """Validate and process pandoc features (e.g., +smart, -raw_html)"""
        if not features:
            return []
        
        # Convert to list if string
        if isinstance(features, str):
            # Split by commas or spaces
            features_list = [f.strip() for f in re.split(r'[,\s]+', features) if f.strip()]
        else:
            features_list = features.copy()
        
        validated_features = []
        for feature in features_list:
            if not isinstance(feature, str):
                raise ValueError(f"All features must be strings, got: {type(feature)}")
            
            feature = feature.strip()
            if not feature:
                continue
            
            # Validate feature format
            if not re.match(r'^[+-]?[a-zA-Z_][a-zA-Z0-9_]*$', feature):
                raise ValueError(f"Invalid feature format: '{feature}'. Features should be alphanumeric with optional +/- prefix")
            
            # Ensure feature has +/- prefix
            if not feature.startswith(('+', '-')):
                # Default to enabling the feature
                feature = '+' + feature
            
            validated_features.append(feature)
        
        return validated_features
    
    def _build_output_format_with_features(self, base_format: str, features: List[str]) -> str:
        """Build the complete output format string with features"""
        if not features:
            return base_format
        
        # Combine base format with features
        format_with_features = base_format + ''.join(features)
        return format_with_features
    
    def _get_pandoc_version(self) -> str:
        """Get pandoc version for diagnostics"""
        try:
            result = subprocess.run(
                ["pandoc", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.stdout.split('\n')[0] if result.returncode == 0 else "unknown"
        except Exception:
            return "unknown"
    
    def _check_memory_usage(self) -> Dict[str, Any]:
        """Monitor current memory usage"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)
            
            # Get system memory info
            system_memory = psutil.virtual_memory()
            system_memory_gb = system_memory.total / (1024 * 1024 * 1024)
            available_memory_gb = system_memory.available / (1024 * 1024 * 1024)
            
            memory_status = {
                "process_memory_mb": round(memory_mb, 2),
                "system_memory_gb": round(system_memory_gb, 2),
                "available_memory_gb": round(available_memory_gb, 2),
                "memory_usage_percent": system_memory.percent
            }
            
            # Warn if memory usage is high
            if memory_mb > 1024:  # 1GB warning threshold
                logger.warning(f"High memory usage: {memory_mb:.1f}MB")
            
            if available_memory_gb < 1.0:  # Less than 1GB available
                logger.warning(f"Low system memory available: {available_memory_gb:.1f}GB")
                
            return memory_status
            
        except Exception as e:
            logger.error(f"Failed to check memory usage: {e}")
            return {"error": f"Memory check failed: {e}"}
    
    def _should_chunk_file(self, file_size: int, file_ext: str) -> bool:
        """Determine if file should be chunked based on size and type"""
        # Chunk HTML files larger than 50MB (more aggressive for pdf2htmlex output)
        if file_ext.lower() == '.html' and file_size > 50 * 1024 * 1024:
            return True
        return False
    
    def _split_html_content(self, input_path: Path, temp_dir: Path, max_chunk_size: int = 10 * 1024 * 1024) -> List[Path]:
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
            
            # Extract document structure
            html_tag = soup.find('html') or soup
            head = soup.find('head')
            body = soup.find('body')
            
            if not body:
                # No body tag found, treat entire content as body
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
    
    def _merge_converted_chunks(self, chunk_results: List[Path], output_format: str, temp_dir: Path, original_stem: str) -> Path:
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
    
    def _build_pandoc_command(self, input_path: Path, output_path: Path, output_format: str, 
                             advanced_options: List[str], self_contained: bool) -> List[str]:
        """Build pandoc command for execution"""
        command = ["pandoc"]
        
        # Add advanced options first
        if advanced_options:
            command.extend(advanced_options)
        
        # Add input file
        command.append(str(input_path))
        
        # Add output format
        command.extend(["-t", output_format])
        
        # Add output file
        command.extend(["-o", str(output_path)])
        
        # Add self-contained flag if requested
        if self_contained:
            command.append("--self-contained")
        
        return command
    
    def _execute_pandoc_command(self, command: List[str], temp_dir: str, chunk_num: int = None) -> bool:
        """Execute pandoc command with memory monitoring and limits"""
        import threading
        import time
        
        try:
            chunk_suffix = f"_chunk_{chunk_num}" if chunk_num else ""
            stdout_log = Path(temp_dir) / f"pandoc_stdout{chunk_suffix}.log"
            stderr_log = Path(temp_dir) / f"pandoc_stderr{chunk_suffix}.log"
            
            logger.info(f"Executing pandoc{' for chunk ' + str(chunk_num) if chunk_num else ''}: {' '.join(command)}")
            
            # Execute with shorter timeout for chunks
            timeout = 300 if chunk_num else 1800  # 5 min for chunks, 30 min for full files
            memory_limit_mb = 2048  # 2GB memory limit per process (more aggressive)
            
            with open(stdout_log, 'w') as stdout_f, open(stderr_log, 'w') as stderr_f:
                # Start process
                process = subprocess.Popen(
                    command,
                    stdout=stdout_f,
                    stderr=stderr_f
                )
                
                # Memory monitoring thread
                def monitor_memory():
                    try:
                        proc = psutil.Process(process.pid)
                        while process.poll() is None:
                            try:
                                memory_mb = proc.memory_info().rss / (1024 * 1024)
                                if memory_mb > memory_limit_mb:
                                    logger.warning(f"Pandoc process exceeding memory limit: {memory_mb:.1f}MB > {memory_limit_mb}MB")
                                    logger.warning("Terminating pandoc process to prevent OOM")
                                    process.terminate()
                                    time.sleep(2)
                                    if process.poll() is None:
                                        process.kill()  # Force kill if terminate didn't work
                                    break
                                
                                time.sleep(1)  # Check every second
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                break
                    except Exception as e:
                        logger.warning(f"Memory monitoring error: {e}")
                
                # Start memory monitoring in background
                monitor_thread = threading.Thread(target=monitor_memory, daemon=True)
                monitor_thread.start()
                
                # Wait for process completion with timeout
                try:
                    result = process.wait(timeout=timeout)
                except subprocess.TimeoutExpired:
                    logger.error(f"Pandoc timeout{' for chunk ' + str(chunk_num) if chunk_num else ''}, terminating process")
                    process.terminate()
                    time.sleep(2)
                    if process.poll() is None:
                        process.kill()
                    return False
            
            if result == 0:
                logger.info(f"Pandoc command successful{' for chunk ' + str(chunk_num) if chunk_num else ''}")
                return True
            elif result == -9:  # SIGKILL (OOM killer)
                logger.error(f"Pandoc killed by OOM killer{' for chunk ' + str(chunk_num) if chunk_num else ''}")
                return False
            elif result == -15:  # SIGTERM (our memory limit)
                logger.error(f"Pandoc terminated due to memory limit{' for chunk ' + str(chunk_num) if chunk_num else ''}")
                return False
            else:
                # Read limited error output
                stderr_content = ""
                if stderr_log.exists():
                    with open(stderr_log, 'r') as f:
                        stderr_content = f.read(5000)  # Limit to 5KB
                
                logger.error(f"Pandoc failed{' for chunk ' + str(chunk_num) if chunk_num else ''} "
                           f"with exit code {result}: {stderr_content[:500]}")
                return False
                
        except Exception as e:
            logger.error(f"Pandoc execution error{' for chunk ' + str(chunk_num) if chunk_num else ''}: {e}")
            return False
    
    def _check_pandoc_data_files(self) -> Dict[str, Any]:
        """Check if pandoc data files are accessible"""
        data_check = {
            "data_files_accessible": False,
            "missing_files": [],
            "error_message": None
        }
        
        try:
            # Test access to common data files
            test_files = ["abbreviations", "default.csl"]
            for file_name in test_files:
                result = subprocess.run(
                    ["pandoc", "--print-default-data-file", file_name],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode != 0:
                    data_check["missing_files"].append(file_name)
                    if "Could not find data file" in result.stderr:
                        data_check["error_message"] = result.stderr.strip()
            
            data_check["data_files_accessible"] = len(data_check["missing_files"]) == 0
            return data_check
            
        except Exception as e:
            data_check["error_message"] = f"Error checking data files: {e}"
            return data_check
    
    def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        input_file_info = data.get("input_file")
        output_format = data.get("output_format")
        self_contained = data.get("self_contained", False)
        advanced_options = data.get("advanced_options")  # New parameter for advanced pandoc options
        features = data.get("features")  # New parameter for pandoc features

        if not input_file_info or not output_format:
            raise ValueError("Missing input file or output format")

        temp_dir = None
        
        try:
            # Check memory usage before starting
            initial_memory = self._check_memory_usage()
            logger.info(f"Initial memory status: {initial_memory}")
            
            # Create temporary directory
            temp_dir = tempfile.mkdtemp()
            logger.info(f"Created temporary directory: {temp_dir}")
            
            # Check pandoc data files first
            data_files_check = self._check_pandoc_data_files()
            if not data_files_check["data_files_accessible"]:
                error_msg = "Pandoc data files are not accessible. This indicates an incomplete pandoc installation."
                if data_files_check["error_message"]:
                    error_msg += f"\n\nDetailed Error: {data_files_check['error_message']}"
                error_msg += f"\n\nMissing files: {', '.join(data_files_check['missing_files'])}"
                error_msg += "\n\n🔧 Solutions:"
                error_msg += "\n  • Reinstall pandoc with: apt-get install pandoc"
                error_msg += "\n  • Or rebuild Docker container with proper data files"
                error_msg += "\n  • Check if pandoc data directory exists and is accessible"
                raise RuntimeError(error_msg)
            
            # Validate and parse advanced options
            validated_advanced_options = self._validate_advanced_options(advanced_options)
            
            # Validate and process features
            validated_features = self._validate_and_process_features(features)
            
            # Build complete format string with features for pandoc command
            complete_output_format = self._build_output_format_with_features(output_format, validated_features)
            
            # Handle both streaming (temp_path) and legacy (content) input formats
            input_filename = input_file_info["filename"]
            
            if "temp_path" in input_file_info:
                # New streaming format - file already on disk
                temp_input_path = Path(input_file_info["temp_path"])
                file_size = input_file_info["size"]
                
                # Move to our temp directory for processing
                input_path = Path(temp_dir) / input_filename
                shutil.move(str(temp_input_path), str(input_path))
                logger.info(f"Moved streamed file to processing directory: {input_path}")
            else:
                # Legacy format - content in memory
                input_file_content = input_file_info["content"]
                file_size = len(input_file_content)
                
                # Write input file to temp directory
                input_path = Path(temp_dir) / input_filename
                with open(input_path, "wb") as f:
                    f.write(input_file_content)
                logger.info(f"Wrote legacy content to processing directory: {input_path}")
                
            file_diagnostics = self._validate_input_file(input_filename, file_size)
            logger.info(f"Input file diagnostics: {file_diagnostics}")

            # Check if file should be chunked for large HTML files
            should_chunk = self._should_chunk_file(file_size, file_diagnostics["file_extension"])
            chunk_info = {"chunked": should_chunk, "chunk_count": 0}
            
            if should_chunk:
                logger.info(f"Large file detected ({file_diagnostics['size_mb']}MB), enabling chunked processing")
                
                # Split HTML into manageable chunks
                chunk_paths = self._split_html_content(input_path, Path(temp_dir))
                chunk_info["chunk_count"] = len(chunk_paths)
                
                # Process each chunk separately
                processed_chunks = []
                
                for i, chunk_path in enumerate(chunk_paths):
                    try:
                        logger.info(f"Processing chunk {i+1}/{len(chunk_paths)}: {chunk_path.name}")
                        
                        # Check memory before processing chunk
                        chunk_memory = self._check_memory_usage()
                        logger.info(f"Memory before chunk {i+1}: {chunk_memory}")
                        
                        # Process individual chunk
                        chunk_output_filename = f"{chunk_path.stem}.{output_format}"
                        chunk_output_path = Path(temp_dir) / chunk_output_filename
                        
                        # Build pandoc command for chunk
                        chunk_command = self._build_pandoc_command(
                            chunk_path, chunk_output_path, complete_output_format, 
                            validated_advanced_options, self_contained
                        )
                        
                        # Execute pandoc on chunk
                        chunk_success = self._execute_pandoc_command(chunk_command, temp_dir, i+1)
                        
                        if chunk_success and chunk_output_path.exists():
                            processed_chunks.append(chunk_output_path)
                            logger.info(f"Successfully processed chunk {i+1}")
                        else:
                            logger.warning(f"Failed to process chunk {i+1}")
                            
                    except Exception as chunk_error:
                        logger.error(f"Error processing chunk {i+1}: {chunk_error}")
                        continue
                
                if not processed_chunks:
                    raise RuntimeError("All chunks failed to process")
                    
                # Merge processed chunks
                logger.info(f"Merging {len(processed_chunks)} successfully processed chunks")
                output_path = self._merge_converted_chunks(
                    processed_chunks, output_format, Path(temp_dir), input_path.stem
                )
                output_filename = output_path.name
                
            else:
                # Standard single-file processing
                output_filename = f"{input_path.stem}.{output_format}"
                output_path = Path(temp_dir) / output_filename
                
                # Build pandoc command
                command = self._build_pandoc_command(
                    input_path, output_path, complete_output_format, 
                    validated_advanced_options, self_contained
                )
                
                # Execute pandoc command
                success = self._execute_pandoc_command(command, temp_dir)
                if not success:
                    raise RuntimeError("Pandoc conversion failed")
                
                if not output_path.exists():
                    raise RuntimeError("Pandoc completed but output file was not created")
            
            # Get pandoc version for diagnostics
            pandoc_version = self._get_pandoc_version()
            
            # Get output file size for diagnostics
            output_size = output_path.stat().st_size
            
            # Move file to permanent downloads directory BEFORE cleanup
            permanent_file_path = self._move_to_downloads(output_path, output_filename)
            
            # Final memory check
            final_memory = self._check_memory_usage()
            logger.info(f"Final memory status: {final_memory}")
            
            # Prepare conversion details
            conversion_details = {
                "pandoc_version": pandoc_version,
                "input_file": file_diagnostics,
                "output_format": output_format,
                "complete_output_format": complete_output_format,
                "output_file": {
                    "filename": output_filename,
                    "size_bytes": output_size,
                    "size_mb": round(output_size / (1024 * 1024), 2)
                },
                "advanced_options_used": validated_advanced_options,
                "features_used": validated_features,
                "conversion_successful": True,
                "temp_directory": temp_dir,
                "permanent_location": str(permanent_file_path),
                "data_files_check": data_files_check,
                "chunking_info": chunk_info,
                "memory_monitoring": {
                    "initial": initial_memory,
                    "final": final_memory
                },
                "processing_strategy": "chunked" if chunk_info["chunked"] else "single_file",
                "pdf2htmlex_optimized": chunk_info["chunked"]  # Note that this handles pdf2htmlex output
            }
            
            logger.info(f"Conversion successful: {conversion_details}")
            
            return {
                "file_path": str(permanent_file_path),
                "file_name": output_filename,
                "conversion_details": conversion_details
            }
            
        except subprocess.TimeoutExpired:
            error_msg = "Pandoc conversion timed out (5 minutes). The file may be too large or complex."
            logger.error(error_msg)
            raise RuntimeError(error_msg)
            
        except Exception as e:
            logger.error(f"Unexpected error in pandoc conversion: {e}")
            raise RuntimeError(f"An unexpected error occurred during conversion: {e}")
            
        finally:
            # Clean up temporary directory
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                    logger.info(f"Cleaned up temporary directory: {temp_dir}")
                except Exception as cleanup_error:
                    logger.warning(f"Failed to clean up temporary directory {temp_dir}: {cleanup_error}") 