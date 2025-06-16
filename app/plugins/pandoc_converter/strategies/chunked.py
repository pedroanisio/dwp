import logging
from .base import ProcessingStrategy
from ..models import ProcessingContext, ProcessingResult, ProcessingMethod, ChunkResult
from ..services import PandocExecutor, MemoryMonitor, ChunkingService, TextExtractor

# Set up logging
logger = logging.getLogger(__name__)


class ChunkedStrategy(ProcessingStrategy):
    """Strategy for processing files by chunking"""
    
    def __init__(self, pandoc_executor: PandocExecutor, memory_monitor: MemoryMonitor, 
                 chunking_service: ChunkingService, text_extractor: TextExtractor):
        self.pandoc_executor = pandoc_executor
        self.memory_monitor = memory_monitor
        self.chunking_service = chunking_service
        self.text_extractor = text_extractor
    
    def process(self, context: ProcessingContext) -> ProcessingResult:
        """Process file using chunking strategy"""
        try:
            logger.info(f"Processing chunked file: {context.input_info.filename} ({context.input_info.size_mb}MB)")
            
            # Check memory before starting
            initial_memory = self.memory_monitor.check_usage()
            logger.info(f"Initial memory status: {initial_memory}")
            
            # Split into chunks
            chunk_paths = self.chunking_service.split_html_content(
                context.input_info.path, context.temp_dir, context.config.chunk_size
            )
            
            # Process each chunk
            processed_chunks = []
            chunk_results = []
            
            for i, chunk_path in enumerate(chunk_paths):
                try:
                    logger.info(f"Processing chunk {i+1}/{len(chunk_paths)}: {chunk_path.name}")
                    
                    # Process individual chunk
                    chunk_output_filename = f"{chunk_path.stem}.{context.output_format}"
                    chunk_output_path = context.temp_dir / chunk_output_filename
                    
                    # Build pandoc command for chunk
                    chunk_command = self.pandoc_executor.build_command(
                        chunk_path, chunk_output_path, context.complete_output_format,
                        context.config.advanced_options, context.self_contained
                    )
                    
                    # Execute pandoc on chunk
                    chunk_success = self.pandoc_executor.execute_with_monitoring(
                        chunk_command, context.temp_dir, context.config.memory_limit, 
                        context.config.timeout, i+1
                    )
                    
                    chunk_result = ChunkResult(
                        chunk_id=i+1,
                        success=chunk_success,
                        output_path=chunk_output_path if chunk_success else None
                    )
                    chunk_results.append(chunk_result)
                    
                    if chunk_success and chunk_output_path.exists():
                        processed_chunks.append(chunk_output_path)
                        logger.info(f"Successfully processed chunk {i+1}")
                    else:
                        logger.warning(f"Failed to process chunk {i+1}")
                        
                except Exception as chunk_error:
                    logger.error(f"Error processing chunk {i+1}: {chunk_error}")
                    chunk_results.append(ChunkResult(
                        chunk_id=i+1,
                        success=False,
                        error=str(chunk_error)
                    ))
                    continue
            
            success_rate = len(processed_chunks) / len(chunk_paths)
            logger.info(f"Chunk processing success rate: {success_rate:.1%} ({len(processed_chunks)}/{len(chunk_paths)})")
            
            if not processed_chunks:
                # All chunks failed - try text extraction fallback
                logger.warning("All chunks failed, attempting text extraction fallback")
                output_path = self.text_extractor.extract_from_html(
                    context.input_info.path, context.output_format, context.temp_dir
                )
                return ProcessingResult(
                    success=True,
                    output_path=output_path,
                    method=ProcessingMethod.TEXT_EXTRACTION,
                    chunk_count=len(chunk_paths),
                    success_rate=0.0
                )
            elif success_rate < context.config.success_rate_threshold:
                # Low success rate - try text extraction fallback
                logger.warning(f"Low success rate ({success_rate:.1%}), trying text extraction fallback")
                output_path = self.text_extractor.extract_from_html(
                    context.input_info.path, context.output_format, context.temp_dir
                )
                return ProcessingResult(
                    success=True,
                    output_path=output_path,
                    method=ProcessingMethod.TEXT_EXTRACTION,
                    chunk_count=len(chunk_paths),
                    success_rate=success_rate
                )
            else:
                # Merge successful chunks
                logger.info(f"Merging {len(processed_chunks)} successfully processed chunks")
                output_path = self.chunking_service.merge_chunks(
                    processed_chunks, context.output_format, context.temp_dir, context.input_info.path.stem
                )
                
                # Final memory check
                final_memory = self.memory_monitor.check_usage()
                
                return ProcessingResult(
                    success=True,
                    output_path=output_path,
                    method=ProcessingMethod.CHUNKED,
                    chunk_count=len(chunk_paths),
                    success_rate=success_rate,
                    memory_monitoring={
                        "initial": initial_memory,
                        "final": final_memory
                    }
                )
            
        except Exception as e:
            logger.error(f"Chunked processing failed: {e}")
            return ProcessingResult(
                success=False,
                method=ProcessingMethod.CHUNKED,
                error=str(e)
            ) 