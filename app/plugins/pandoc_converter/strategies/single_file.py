import logging
from .base import ProcessingStrategy
from ..models import ProcessingContext, ProcessingResult, ProcessingMethod, get_output_extension
from ..services import PandocExecutor, MemoryMonitor

# Set up logging
logger = logging.getLogger(__name__)


class SingleFileStrategy(ProcessingStrategy):
    """Strategy for processing single files with pandoc"""
    
    def __init__(self, pandoc_executor: PandocExecutor, memory_monitor: MemoryMonitor):
        self.pandoc_executor = pandoc_executor
        self.memory_monitor = memory_monitor
    
    def process(self, context: ProcessingContext) -> ProcessingResult:
        """Process single file with pandoc"""
        try:
            logger.info(f"Processing single file: {context.input_info.filename} ({context.input_info.size_mb}MB)")
            
            # Check memory before starting
            initial_memory = self.memory_monitor.check_usage()
            logger.info(f"Initial memory status: {initial_memory}")
            
            # Build output path with proper extension mapping
            output_extension = get_output_extension(context.output_format)
            output_filename = f"{context.input_info.path.stem}.{output_extension}"
            output_path = context.temp_dir / output_filename
            
            # Build pandoc command
            command = self.pandoc_executor.build_command(
                context.input_info.path, output_path, context.complete_output_format,
                context.config.advanced_options, context.self_contained
            )
            
            # Execute pandoc command
            success = self.pandoc_executor.execute_with_monitoring(
                command, context.temp_dir, context.config.memory_limit, 
                context.config.timeout * 3  # Longer timeout for full files
            )
            
            if not success:
                return ProcessingResult(
                    success=False,
                    method=ProcessingMethod.SINGLE_FILE,
                    error="Pandoc execution failed"
                )
            
            if not output_path.exists():
                return ProcessingResult(
                    success=False,
                    method=ProcessingMethod.SINGLE_FILE,
                    error="Pandoc completed but output file was not created"
                )
            
            # Final memory check
            final_memory = self.memory_monitor.check_usage()
            
            return ProcessingResult(
                success=True,
                output_path=output_path,
                method=ProcessingMethod.SINGLE_FILE,
                memory_monitoring={
                    "initial": initial_memory,
                    "final": final_memory
                }
            )
            
        except Exception as e:
            logger.error(f"Single file processing failed: {e}")
            return ProcessingResult(
                success=False,
                method=ProcessingMethod.SINGLE_FILE,
                error=str(e)
            ) 