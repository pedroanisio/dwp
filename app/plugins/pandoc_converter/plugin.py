from pathlib import Path
import subprocess
import tempfile
from typing import Dict, Any, Type
import os
import shutil
import logging
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
    
    def _validate_input_file(self, filename: str, content: bytes) -> Dict[str, Any]:
        """Validate input file and return diagnostics"""
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
            raise ValueError("Input file is empty")
        if file_size > 100 * 1024 * 1024:  # 100MB limit
            raise ValueError(f"Input file too large: {diagnostics['size_mb']}MB (max 100MB)")
            
        return diagnostics
    
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
    
    def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        input_file_info = data.get("input_file")
        output_format = data.get("output_format")
        self_contained = data.get("self_contained", False)

        if not input_file_info or not output_format:
            raise ValueError("Missing input file or output format")

        temp_dir = None
        
        try:
            # Create temporary directory
            temp_dir = tempfile.mkdtemp()
            logger.info(f"Created temporary directory: {temp_dir}")
            
            # Validate and analyze input file
            input_filename = input_file_info["filename"]
            input_file_content = input_file_info["content"]
            
            file_diagnostics = self._validate_input_file(input_filename, input_file_content)
            logger.info(f"Input file diagnostics: {file_diagnostics}")

            # Write input file to temp directory
            input_path = Path(temp_dir) / input_filename
            with open(input_path, "wb") as f:
                f.write(input_file_content)

            # Prepare output file path
            output_filename = f"{input_path.stem}.{output_format}"
            output_path = Path(temp_dir) / output_filename
            
            # Build pandoc command
            command = ["pandoc", str(input_path), "-o", str(output_path)]
            if self_contained:
                command.append("--self-contained")
            
            # Get pandoc version for diagnostics
            pandoc_version = self._get_pandoc_version()
            
            # Log command being executed
            logger.info(f"Executing pandoc command: {' '.join(command)}")
            logger.info(f"Pandoc version: {pandoc_version}")
            
            # Execute pandoc with detailed error capture
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                check=False  # Don't raise exception immediately
            )
            
            # Check if conversion was successful
            if result.returncode != 0:
                # Prepare detailed error information
                error_details = {
                    "command": " ".join(command),
                    "exit_code": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "pandoc_version": pandoc_version,
                    "input_file": file_diagnostics,
                    "output_format": output_format
                }
                
                # Create user-friendly error message
                error_msg = f"Pandoc conversion failed with exit code {result.returncode}"
                
                if result.stderr:
                    error_msg += f"\n\nPandoc Error Details:\n{result.stderr}"
                
                if result.stdout:
                    error_msg += f"\n\nPandoc Output:\n{result.stdout}"
                
                # Add specific guidance based on exit code
                if result.returncode == 97:
                    error_msg += "\n\n💡 Exit code 97 usually indicates:"
                    error_msg += "\n  • Input file format issues or corruption"
                    error_msg += "\n  • Unsupported conversion combination"
                    error_msg += "\n  • Complex document structure that pandoc can't handle"
                    error_msg += f"\n  • Try converting {file_diagnostics['file_extension']} to a simpler format first (e.g., markdown)"
                
                # Log detailed error for debugging
                logger.error(f"Pandoc conversion failed: {error_details}")
                
                raise RuntimeError(error_msg)
            
            # Verify output file was created
            if not output_path.exists():
                raise RuntimeError("Pandoc completed successfully but output file was not created")
            
            # Get output file size for diagnostics
            output_size = output_path.stat().st_size
            
            # Prepare conversion details
            conversion_details = {
                "pandoc_version": pandoc_version,
                "command_executed": " ".join(command),
                "input_file": file_diagnostics,
                "output_file": {
                    "filename": output_filename,
                    "size_bytes": output_size,
                    "size_mb": round(output_size / (1024 * 1024), 2)
                },
                "conversion_successful": True,
                "temp_directory": temp_dir
            }
            
            logger.info(f"Conversion successful: {conversion_details}")
            
            return {
                "file_path": str(output_path),
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