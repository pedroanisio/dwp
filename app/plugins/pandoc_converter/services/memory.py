import logging
import time
import threading
import subprocess
import psutil
from ..models import MemoryStatus

# Set up logging
logger = logging.getLogger(__name__)


class MemoryMonitor:
    """Handles memory monitoring and limits"""
    
    def check_usage(self) -> MemoryStatus:
        """Monitor current memory usage"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)
            
            # Get system memory info
            system_memory = psutil.virtual_memory()
            system_memory_gb = system_memory.total / (1024 * 1024 * 1024)
            available_memory_gb = system_memory.available / (1024 * 1024 * 1024)
            
            status = MemoryStatus(
                process_memory_mb=round(memory_mb, 2),
                system_memory_gb=round(system_memory_gb, 2),
                available_memory_gb=round(available_memory_gb, 2),
                memory_usage_percent=system_memory.percent
            )
            
            # Warn if memory usage is high
            if memory_mb > 1024:  # 1GB warning threshold
                logger.warning(f"High memory usage: {memory_mb:.1f}MB")
            
            if available_memory_gb < 1.0:  # Less than 1GB available
                logger.warning(f"Low system memory available: {available_memory_gb:.1f}GB")
                
            return status
            
        except Exception as e:
            logger.error(f"Failed to check memory usage: {e}")
            return MemoryStatus(0, 0, 0, 0)
    
    def monitor_process(self, process: subprocess.Popen, memory_limit_mb: int) -> bool:
        """Monitor process memory usage and terminate if exceeding limit"""
        try:
            proc = psutil.Process(process.pid)
            while process.poll() is None:
                try:
                    memory_mb = proc.memory_info().rss / (1024 * 1024)
                    if memory_mb > memory_limit_mb:
                        logger.warning(f"Process exceeding memory limit: {memory_mb:.1f}MB > {memory_limit_mb}MB")
                        logger.warning("Terminating process to prevent OOM")
                        process.terminate()
                        time.sleep(2)
                        if process.poll() is None:
                            process.kill()  # Force kill if terminate didn't work
                        return False
                    
                    time.sleep(1)  # Check every second
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    break
            return True
        except Exception as e:
            logger.warning(f"Memory monitoring error: {e}")
            return True 