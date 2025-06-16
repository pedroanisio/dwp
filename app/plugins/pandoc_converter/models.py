from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
from pydantic import BaseModel, Field
from ...models.plugin import BasePluginResponse


def get_output_extension(output_format: str) -> str:
    """Map output format to file extension"""
    format_to_extension = {
        'plain': 'txt',
        'markdown': 'md', 
        'html': 'html',
        'html5': 'html',
        'latex': 'tex',
        'pdf': 'pdf',
        'docx': 'docx',
        'odt': 'odt',
        'rtf': 'rtf',
        'epub': 'epub',
        'json': 'json',
        'txt': 'txt',
        'md': 'md'
    }
    return format_to_extension.get(output_format.lower(), output_format)


class ProcessingMethod(Enum):
    """Enumeration of processing methods"""
    SINGLE_FILE = "single_file"
    CHUNKED = "chunked"
    TEXT_EXTRACTION = "text_extraction"


@dataclass
class ProcessingConfig:
    """Configuration for pandoc processing"""
    chunk_size: int = 10 * 1024 * 1024  # 10MB
    memory_limit: int = 4096  # 4GB in MB
    timeout: int = 600  # 10 minutes
    chunking_threshold: int = 50 * 1024 * 1024  # 50MB
    text_extraction_threshold: int = 200 * 1024 * 1024  # 200MB
    success_rate_threshold: float = 0.5  # 50%
    advanced_options: List[str] = None
    features: List[str] = None
    
    def __post_init__(self):
        if self.advanced_options is None:
            self.advanced_options = []
        if self.features is None:
            self.features = []


@dataclass
class InputFileInfo:
    """Information about input file"""
    filename: str
    size: int
    path: Path
    extension: str
    
    @property
    def size_mb(self) -> float:
        return round(self.size / (1024 * 1024), 2)


@dataclass
class MemoryStatus:
    """Memory usage information"""
    process_memory_mb: float
    system_memory_gb: float
    available_memory_gb: float
    memory_usage_percent: float


@dataclass
class ChunkResult:
    """Result of processing a single chunk"""
    chunk_id: int
    success: bool
    output_path: Optional[Path] = None
    memory_used: float = 0.0
    processing_time: float = 0.0
    error: Optional[str] = None


@dataclass
class ProcessingResult:
    """Result of processing operation"""
    success: bool
    output_path: Optional[Path] = None
    method: ProcessingMethod = ProcessingMethod.SINGLE_FILE
    chunk_count: int = 0
    success_rate: float = 1.0
    memory_monitoring: Dict[str, Any] = None
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.memory_monitoring is None:
            self.memory_monitoring = {}


@dataclass
class ProcessingContext:
    """Context for processing operations"""
    input_info: InputFileInfo
    config: ProcessingConfig
    temp_dir: Path
    output_format: str
    complete_output_format: str
    self_contained: bool = False


class PandocConverterResponse(BasePluginResponse):
    """Pydantic model for pandoc converter plugin response"""
    file_path: str = Field(..., description="Path to the converted file")
    file_name: str = Field(..., description="Name of the converted file")
    conversion_details: Dict[str, Any] = Field(default={}, description="Details about the conversion process") 