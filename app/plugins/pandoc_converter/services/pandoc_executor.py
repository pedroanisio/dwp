import subprocess
import threading
import time
import logging
from pathlib import Path
from typing import List, Optional
from .memory import MemoryMonitor

# Set up logging
logger = logging.getLogger(__name__)


class PandocExecutor:
    """Handles pandoc command execution with memory monitoring"""
    
    def __init__(self, memory_monitor: MemoryMonitor):
        self.memory_monitor = memory_monitor
    
    def build_command(self, input_path: Path, output_path: Path, output_format: str, 
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
    
    def execute_with_monitoring(self, command: List[str], temp_dir: Path, 
                              memory_limit_mb: int, timeout: int, 
                              chunk_num: Optional[int] = None) -> bool:
        """Execute pandoc command with memory monitoring and limits"""
        try:
            chunk_suffix = f"_chunk_{chunk_num}" if chunk_num else ""
            stdout_log = temp_dir / f"pandoc_stdout{chunk_suffix}.log"
            stderr_log = temp_dir / f"pandoc_stderr{chunk_suffix}.log"
            
            logger.info(f"Executing pandoc{' for chunk ' + str(chunk_num) if chunk_num else ''}: {' '.join(command)}")
            
            with open(stdout_log, 'w') as stdout_f, open(stderr_log, 'w') as stderr_f:
                # Start process
                process = subprocess.Popen(
                    command,
                    stdout=stdout_f,
                    stderr=stderr_f
                )
                
                # Start memory monitoring in background
                monitor_thread = threading.Thread(
                    target=self.memory_monitor.monitor_process,
                    args=(process, memory_limit_mb),
                    daemon=True
                )
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
    
    def get_version(self) -> str:
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