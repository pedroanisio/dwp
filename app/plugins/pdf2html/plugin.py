from pathlib import Path
import subprocess
import tempfile
from typing import Dict, Any, Type, List
import os
import shutil
import logging
import uuid
import time
from pydantic import BaseModel, Field
from ...models.plugin import BasePlugin, BasePluginResponse

# Set up logging
logger = logging.getLogger(__name__)

class Pdf2HtmlResponse(BasePluginResponse):
    """Pydantic model for PDF to HTML converter plugin response"""
    file_path: str = Field(..., description="Path to the converted HTML file")
    file_name: str = Field(..., description="Name of the converted HTML file")
    conversion_details: Dict[str, Any] = Field(default={}, description="Details about the conversion process")
    docker_info: Dict[str, Any] = Field(default={}, description="Information about Docker container execution")


class Plugin(BasePlugin):
    """PDF to HTML Converter Plugin - Converts PDF files to HTML using pdf2htmlEX in Docker"""
    
    @classmethod
    def get_response_model(cls) -> Type[BasePluginResponse]:
        """Return the Pydantic model for this plugin's response"""
        return Pdf2HtmlResponse
    
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
    
    def _validate_input_file(self, filename: str, content: bytes) -> Dict[str, Any]:
        """Validate input PDF file and return diagnostics"""
        file_size = len(content)
        file_ext = Path(filename).suffix.lower()
        
        diagnostics = {
            "filename": filename,
            "file_size": file_size,
            "file_extension": file_ext,
            "size_mb": round(file_size / (1024 * 1024), 2)
        }
        
        # Check for potential issues
        if file_size == 0:
            raise ValueError("Input PDF file is empty")
        if file_size > 500 * 1024 * 1024:  # 500MB limit for PDFs
            raise ValueError(f"Input PDF file too large: {diagnostics['size_mb']}MB (max 500MB)")
        if file_ext != '.pdf':
            raise ValueError(f"Invalid file extension: {file_ext}. Only PDF files are supported.")
            
        return diagnostics
    
    def _check_docker_availability(self) -> Dict[str, Any]:
        """Check if Docker is available and accessible"""
        docker_info = {
            "docker_available": False,
            "docker_version": None,
            "error_message": None
        }
        
        try:
            # Check if Docker is available
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                docker_info["docker_available"] = True
                docker_info["docker_version"] = result.stdout.strip()
                logger.info(f"Docker available: {docker_info['docker_version']}")
            else:
                docker_info["error_message"] = f"Docker command failed: {result.stderr}"
                
        except FileNotFoundError:
            docker_info["error_message"] = "Docker command not found. Please install Docker."
        except subprocess.TimeoutExpired:
            docker_info["error_message"] = "Docker command timed out. Docker daemon may not be running."
        except Exception as e:
            docker_info["error_message"] = f"Error checking Docker: {e}"
        
        return docker_info
    
    def _check_pdf2htmlex_image(self) -> Dict[str, Any]:
        """Check if pdf2htmlEX Docker image is available or can be pulled"""
        image_info = {
            "image_available": False,
            "image_pulled": False,
            "error_message": None
        }
        
        image_name = "pdf2htmlex/pdf2htmlex"
        
        try:
            # Check if image exists locally
            result = subprocess.run(
                ["docker", "image", "inspect", image_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                image_info["image_available"] = True
                logger.info(f"Docker image {image_name} is available locally")
                return image_info
            
            # Try to pull the image if not available locally
            logger.info(f"Pulling Docker image {image_name}...")
            pull_result = subprocess.run(
                ["docker", "pull", image_name],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout for pulling
            )
            
            if pull_result.returncode == 0:
                image_info["image_available"] = True
                image_info["image_pulled"] = True
                logger.info(f"Successfully pulled Docker image {image_name}")
            else:
                image_info["error_message"] = f"Failed to pull image: {pull_result.stderr}"
                
        except subprocess.TimeoutExpired:
            image_info["error_message"] = "Timeout while pulling Docker image. Check internet connection."
        except Exception as e:
            image_info["error_message"] = f"Error checking/pulling Docker image: {e}"
        
        return image_info
    
    def _build_pdf2htmlex_command(self, input_filename: str, output_filename: str, zoom: float, 
                                 embed_css: bool, embed_javascript: bool, embed_images: bool) -> List[str]:
        """Build the Docker command for pdf2htmlEX conversion"""
        
        # Base Docker command
        command = [
            "docker", "run",
            "--rm",  # Remove container after execution
            "-v", "/pdf:/pdf",  # Mount the volume (will be set up by caller)
            "-w", "/pdf",  # Set working directory
            "pdf2htmlex/pdf2htmlex"
        ]
        
        # Add pdf2htmlEX options
        pdf2htmlex_options = []
        
        # Zoom level
        if zoom and zoom > 0:
            pdf2htmlex_options.extend(["--zoom", str(zoom)])
        
        # Embedding options
        if embed_css:
            pdf2htmlex_options.append("--embed-css=1")
        else:
            pdf2htmlex_options.append("--embed-css=0")
            
        if embed_javascript:
            pdf2htmlex_options.append("--embed-javascript=1")
        else:
            pdf2htmlex_options.append("--embed-javascript=0")
            
        if embed_images:
            pdf2htmlex_options.append("--embed-image=1")
        else:
            pdf2htmlex_options.append("--embed-image=0")
        
        # Output filename
        if output_filename:
            pdf2htmlex_options.extend(["--dest-dir", ".", "--page-filename", output_filename])
        
        # Input file
        pdf2htmlex_options.append(input_filename)
        
        # Add pdf2htmlEX options to Docker command
        command.extend(pdf2htmlex_options)
        
        return command
    
    def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        input_file_info = data.get("input_file")
        zoom = data.get("zoom", 1.3)
        embed_css = data.get("embed_css", True)
        embed_javascript = data.get("embed_javascript", True)
        embed_images = data.get("embed_images", True)
        output_filename = data.get("output_filename", "").strip()

        if not input_file_info:
            raise ValueError("Missing input PDF file")

        temp_dir = None
        
        try:
            # Check Docker availability first
            docker_info = self._check_docker_availability()
            if not docker_info["docker_available"]:
                error_msg = "Docker is not available or not running."
                if docker_info["error_message"]:
                    error_msg += f"\n\nError: {docker_info['error_message']}"
                error_msg += "\n\n🔧 Solutions:"
                error_msg += "\n  • Install Docker from docker.com"
                error_msg += "\n  • Start the Docker daemon"
                error_msg += "\n  • Ensure current user has Docker permissions"
                raise RuntimeError(error_msg)
            
            # Check pdf2htmlEX Docker image
            image_info = self._check_pdf2htmlex_image()
            if not image_info["image_available"]:
                error_msg = "pdf2htmlEX Docker image is not available."
                if image_info["error_message"]:
                    error_msg += f"\n\nError: {image_info['error_message']}"
                error_msg += "\n\n🔧 Solutions:"
                error_msg += "\n  • Ensure Docker has internet access"
                error_msg += "\n  • Try manually: docker pull pdf2htmlex/pdf2htmlex"
                error_msg += "\n  • Check Docker Hub availability"
                raise RuntimeError(error_msg)
            
            # Create temporary directory
            temp_dir = tempfile.mkdtemp()
            logger.info(f"Created temporary directory: {temp_dir}")
            
            # Validate and analyze input file
            input_filename = input_file_info["filename"]
            input_file_content = input_file_info["content"]
            
            file_diagnostics = self._validate_input_file(input_filename, input_file_content)
            logger.info(f"Input PDF file diagnostics: {file_diagnostics}")

            # Write input file to temp directory
            input_path = Path(temp_dir) / input_filename
            with open(input_path, "wb") as f:
                f.write(input_file_content)

            # Determine output filename
            if not output_filename:
                output_filename = f"{input_path.stem}.html"
            elif not output_filename.endswith('.html'):
                output_filename += '.html'
            
            output_path = Path(temp_dir) / output_filename
            
            # Build Docker command with corrected volume mounting
            # Mount the temp directory to /pdf in the container
            command = [
                "docker", "run",
                "--rm",  # Remove container after execution
                "-v", f"{temp_dir}:/pdf",  # Mount the temp directory
                "-w", "/pdf",  # Set working directory
                "pdf2htmlex/pdf2htmlex"
            ]
            
            # Add pdf2htmlEX options
            pdf2htmlex_options = []
            
            # Zoom level
            if zoom and zoom > 0:
                pdf2htmlex_options.extend(["--zoom", str(zoom)])
            
            # Embedding options
            if embed_css:
                pdf2htmlex_options.append("--embed-css=1")
            else:
                pdf2htmlex_options.append("--embed-css=0")
                
            if embed_javascript:
                pdf2htmlex_options.append("--embed-javascript=1")  
            else:
                pdf2htmlex_options.append("--embed-javascript=0")
                
            if embed_images:
                pdf2htmlex_options.append("--embed-image=1")
            else:
                pdf2htmlex_options.append("--embed-image=0")
            
            # Output settings
            pdf2htmlex_options.extend(["--dest-dir", "."])
            
            # Input file (just the filename, since we're in the mounted directory)
            pdf2htmlex_options.append(input_filename)
            
            # Add pdf2htmlEX options to Docker command
            command.extend(pdf2htmlex_options)
            
            # Log command being executed (hide sensitive paths)
            safe_command = command.copy()
            for i, arg in enumerate(safe_command):
                if temp_dir in arg:
                    safe_command[i] = arg.replace(temp_dir, "/tmp/***")
            logger.info(f"Executing Docker command: {' '.join(safe_command)}")
            
            # Execute Docker command
            start_time = time.time()
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=600,  # 10 minute timeout
                check=False  # Don't raise exception immediately
            )
            execution_time = time.time() - start_time
            
            # Check if conversion was successful
            if result.returncode != 0:
                # Prepare detailed error information
                error_details = {
                    "command": ' '.join(safe_command),
                    "exit_code": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "execution_time": execution_time,
                    "docker_info": docker_info,
                    "image_info": image_info,
                    "input_file": file_diagnostics
                }
                
                # Create user-friendly error message
                error_msg = f"pdf2htmlEX conversion failed with exit code {result.returncode}"
                
                if result.stderr:
                    error_msg += f"\n\nError Details:\n{result.stderr}"
                
                if result.stdout:
                    error_msg += f"\n\nOutput:\n{result.stdout}"
                
                # Add specific guidance based on common issues
                if "Permission denied" in result.stderr:
                    error_msg += "\n\n💡 Permission issues detected:"
                    error_msg += "\n  • Docker may not have access to the mounted directory"
                    error_msg += "\n  • Try restarting the Docker daemon"
                    error_msg += "\n  • Check file permissions"
                
                if "No such file or directory" in result.stderr:
                    error_msg += "\n\n💡 File not found issues:"
                    error_msg += "\n  • PDF file may be corrupted"
                    error_msg += "\n  • Check if the PDF can be opened normally"
                
                # Log detailed error for debugging
                logger.error(f"pdf2htmlEX conversion failed: {error_details}")
                
                raise RuntimeError(error_msg)
            
            # Find the generated HTML file (pdf2htmlEX may create different filename)
            html_files = list(Path(temp_dir).glob("*.html"))
            if not html_files:
                raise RuntimeError("pdf2htmlEX completed successfully but no HTML file was created")
            
            # Use the first HTML file found (should be only one)
            generated_html_path = html_files[0]
            final_output_filename = output_filename if output_filename else generated_html_path.name
            
            # Get output file size for diagnostics
            output_size = generated_html_path.stat().st_size
            
            # Move file to permanent downloads directory BEFORE cleanup
            permanent_file_path = self._move_to_downloads(generated_html_path, final_output_filename)
            
            # Prepare conversion details
            conversion_details = {
                "input_file": file_diagnostics,
                "output_file": {
                    "filename": final_output_filename,
                    "size_bytes": output_size,
                    "size_mb": round(output_size / (1024 * 1024), 2)
                },
                "conversion_settings": {
                    "zoom": zoom,
                    "embed_css": embed_css,
                    "embed_javascript": embed_javascript,
                    "embed_images": embed_images
                },
                "execution_time_seconds": round(execution_time, 2),
                "conversion_successful": True,
                "temp_directory": temp_dir,
                "permanent_location": str(permanent_file_path)
            }
            
            # Add Docker and image info to response
            docker_response_info = {
                "docker_version": docker_info.get("docker_version"),
                "image_pulled": image_info.get("image_pulled", False),
                "execution_time": execution_time,
                "exit_code": result.returncode
            }
            
            logger.info(f"PDF to HTML conversion successful: {conversion_details}")
            
            return {
                "file_path": str(permanent_file_path),
                "file_name": final_output_filename,
                "conversion_details": conversion_details,
                "docker_info": docker_response_info
            }
            
        except subprocess.TimeoutExpired:
            error_msg = "pdf2htmlEX conversion timed out (10 minutes). The PDF file may be too large or complex."
            logger.error(error_msg)
            raise RuntimeError(error_msg)
            
        except Exception as e:
            logger.error(f"Unexpected error in pdf2htmlEX conversion: {e}")
            raise RuntimeError(f"An unexpected error occurred during conversion: {e}")
            
        finally:
            # Clean up temporary directory
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                    logger.info(f"Cleaned up temporary directory: {temp_dir}")
                except Exception as cleanup_error:
                    logger.warning(f"Failed to clean up temporary directory {temp_dir}: {cleanup_error}") 