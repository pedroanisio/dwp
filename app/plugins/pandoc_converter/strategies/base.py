from abc import ABC, abstractmethod
from ..models import ProcessingContext, ProcessingResult


class ProcessingStrategy(ABC):
    """Abstract base class for processing strategies"""
    
    @abstractmethod
    def process(self, context: ProcessingContext) -> ProcessingResult:
        """Process the file according to the strategy"""
        pass 