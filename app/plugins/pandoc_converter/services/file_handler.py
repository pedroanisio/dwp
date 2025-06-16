import tempfile
import shutil
import uuid
import logging
from pathlib import Path
from ..models import InputFileInfo

# Set up logging
logger = logging.getLogger(__name__)


class FileHandler:
    """Handles file operations and validation"""
    
    def __init__(self, downloads_dir: Path = Path("/app/data/downloads")):
        self.downloads_dir = downloads_dir
    
    def validate_input(self, filename: str, file_size: int) -> InputFileInfo:
        """Validate input file and return file info"""
        file_ext = Path(filename).suffix.lower()
        
        # Check for potential issues
        if file_size == 0:
            raise ValueError("Input file is empty")
        if file_size > 2 * 1024 * 1024 * 1024:  # 2GB limit
            size_mb = round(file_size / (1024 * 1024), 2)
            raise ValueError(f"Input file too large: {size_mb}MB (max 2048MB)")
        
        return InputFileInfo(
            filename=filename,
            size=file_size,
            path=Path(),  # Will be set later
            extension=file_ext
        )
    
    def setup_temp_directory(self) -> Path:
        """Create and return temporary directory"""
        temp_dir = Path(tempfile.mkdtemp())
        logger.info(f"Created temporary directory: {temp_dir}")
        return temp_dir
    
    def move_to_downloads(self, temp_file_path: Path, filename: str) -> Path:
        """Move file from temp directory to permanent downloads directory"""
        self.downloads_dir.mkdir(parents=True, exist_ok=True)
        
        # Create unique filename to avoid conflicts
        unique_id = str(uuid.uuid4())[:8]
        file_stem = temp_file_path.stem
        file_suffix = temp_file_path.suffix
        safe_filename = f"{file_stem}_{unique_id}{file_suffix}"
        
        permanent_path = self.downloads_dir / safe_filename
        
        # Move the file
        shutil.move(str(temp_file_path), str(permanent_path))
        logger.info(f"Moved output file to permanent location: {permanent_path}")
        
        return permanent_path
    
    def cleanup(self, temp_dir: Path):
        """Clean up temporary directory"""
        if temp_dir and temp_dir.exists():
            try:
                shutil.rmtree(temp_dir)
                logger.info(f"Cleaned up temporary directory: {temp_dir}")
            except Exception as cleanup_error:
                logger.warning(f"Failed to clean up temporary directory {temp_dir}: {cleanup_error}") 