from pathlib import Path
import subprocess
import tempfile
from typing import Dict, Any, Type, List, Union
import os
import shutil
import logging
import uuid
import re
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
            
            # Validate and analyze input file
            input_filename = input_file_info["filename"]
            input_file_content = input_file_info["content"]
            
            file_diagnostics = self._validate_input_file(input_filename, input_file_content)
            logger.info(f"Input file diagnostics: {file_diagnostics}")

            # Write input file to temp directory
            input_path = Path(temp_dir) / input_filename
            with open(input_path, "wb") as f:
                f.write(input_file_content)

            # Prepare output file path (use base format for filename)
            output_filename = f"{input_path.stem}.{output_format}"
            output_path = Path(temp_dir) / output_filename
            
            # Build complete format string with features for pandoc command
            complete_output_format = self._build_output_format_with_features(output_format, validated_features)
            
            # Build pandoc command with advanced options
            command = ["pandoc"]
            
            # Add advanced options first (before input file)
            if validated_advanced_options:
                command.extend(validated_advanced_options)
                logger.info(f"Added advanced options: {validated_advanced_options}")
            
            # Add input file
            command.append(str(input_path))
            
            # Add output format with features
            command.extend(["-t", complete_output_format])
            
            # Add output file
            command.extend(["-o", str(output_path)])
            
            # Add self-contained flag if requested
            if self_contained:
                command.append("--self-contained")
            
            # Get pandoc version for diagnostics
            pandoc_version = self._get_pandoc_version()
            
            # Log command being executed
            logger.info(f"Executing pandoc command: {' '.join(command)}")
            logger.info(f"Pandoc version: {pandoc_version}")
            if validated_features:
                logger.info(f"Using output format with features: {complete_output_format}")
            
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
                    "output_format": output_format,
                    "complete_output_format": complete_output_format,
                    "advanced_options": validated_advanced_options,
                    "features": validated_features,
                    "data_files_check": data_files_check
                }
                
                # Create user-friendly error message
                error_msg = f"Pandoc conversion failed with exit code {result.returncode}"
                
                if result.stderr:
                    error_msg += f"\n\nPandoc Error Details:\n{result.stderr}"
                
                if result.stdout:
                    error_msg += f"\n\nPandoc Output:\n{result.stdout}"
                
                # Add specific guidance based on exit code and error content
                if result.returncode == 97:
                    if "Could not find data file" in result.stderr:
                        error_msg += "\n\n💡 Exit code 97 with 'Could not find data file' indicates:"
                        error_msg += "\n  • Incomplete pandoc installation missing data files"
                        error_msg += "\n  • Data files not accessible in expected location"
                        error_msg += "\n  • Container may need to be rebuilt with proper pandoc setup"
                        error_msg += "\n\n🔧 Quick fix: Restart the container or reinstall pandoc"
                    else:
                        error_msg += "\n\n💡 Exit code 97 usually indicates:"
                        error_msg += "\n  • Input file format issues or corruption"
                        error_msg += "\n  • Unsupported conversion combination"
                        error_msg += "\n  • Complex document structure that pandoc can't handle"
                        error_msg += f"\n  • Try converting {file_diagnostics['file_extension']} to a simpler format first (e.g., markdown)"
                
                if validated_advanced_options:
                    error_msg += f"\n\n⚙️ Advanced options used: {' '.join(validated_advanced_options)}"
                    error_msg += "\n  • Double-check the advanced options syntax"
                    error_msg += "\n  • Some options may conflict with the conversion"
                    error_msg += "\n  • Try running without advanced options first"
                
                if validated_features:
                    error_msg += f"\n\n🔧 Features used: {' '.join(validated_features)}"
                    error_msg += "\n  • Double-check the features syntax"
                    error_msg += "\n  • Some features may conflict with the conversion"
                    error_msg += "\n  • Try running without features first"
                
                # Log detailed error for debugging
                logger.error(f"Pandoc conversion failed: {error_details}")
                
                raise RuntimeError(error_msg)
            
            # Verify output file was created
            if not output_path.exists():
                raise RuntimeError("Pandoc completed successfully but output file was not created")
            
            # Get output file size for diagnostics
            output_size = output_path.stat().st_size
            
            # Move file to permanent downloads directory BEFORE cleanup
            permanent_file_path = self._move_to_downloads(output_path, output_filename)
            
            # Prepare conversion details
            conversion_details = {
                "pandoc_version": pandoc_version,
                "command_executed": " ".join(command),
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
                "data_files_check": data_files_check
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