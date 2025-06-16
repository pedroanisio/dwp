import logging
from .base import ProcessingStrategy
from ..models import ProcessingContext, ProcessingResult, ProcessingMethod
from ..services import TextExtractor, MemoryMonitor

# Set up logging
logger = logging.getLogger(__name__)


class TextExtractionStrategy(ProcessingStrategy):
    """Strategy for text extraction without pandoc"""
    
    def __init__(self, text_extractor: TextExtractor, memory_monitor: MemoryMonitor):
        self.text_extractor = text_extractor
        self.memory_monitor = memory_monitor
    
    def process(self, context: ProcessingContext) -> ProcessingResult:
        """Process file using text extraction"""
        try:
            logger.info(f"Processing with text extraction: {context.input_info.filename} ({context.input_info.size_mb}MB)")
            
            # Check memory before starting
            initial_memory = self.memory_monitor.check_usage()
            logger.info(f"Initial memory status: {initial_memory}")
            
            # Extract text directly
            output_path = self.text_extractor.extract_from_html(
                context.input_info.path, context.output_format, context.temp_dir
            )
            
            # Final memory check
            final_memory = self.memory_monitor.check_usage()
            
            return ProcessingResult(
                success=True,
                output_path=output_path,
                method=ProcessingMethod.TEXT_EXTRACTION,
                memory_monitoring={
                    "initial": initial_memory,
                    "final": final_memory
                }
            )
            
        except Exception as e:
            logger.error(f"Text extraction processing failed: {e}")
            return ProcessingResult(
                success=False,
                method=ProcessingMethod.TEXT_EXTRACTION,
                error=str(e)
            ) 