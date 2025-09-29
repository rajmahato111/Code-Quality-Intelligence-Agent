"""Base classes and interfaces for quality analyzers."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from enum import Enum

from ..core.models import Issue, ParsedFile, AnalysisContext, IssueCategory, Severity


class QualityAnalyzer(ABC):
    """Abstract base class for all quality analyzers."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the analyzer with optional configuration."""
        self.config = config or {}
    
    @abstractmethod
    def analyze(self, parsed_files: List[ParsedFile], context: AnalysisContext) -> List[Issue]:
        """
        Analyze parsed files and return a list of quality issues.
        
        Args:
            parsed_files: List of parsed code files
            context: Analysis context with additional information
            
        Returns:
            List of identified issues
        """
        pass
    
    @abstractmethod
    def get_supported_languages(self) -> List[str]:
        """Return list of programming languages this analyzer supports."""
        pass
    
    @abstractmethod
    def get_category(self) -> IssueCategory:
        """Return the category of issues this analyzer detects."""
        pass
    
    def get_name(self) -> str:
        """Return the name of this analyzer."""
        return self.__class__.__name__
    
    def is_enabled(self) -> bool:
        """Check if this analyzer is enabled in the configuration."""
        return self.config.get("enabled", True)
    
    def get_confidence_threshold(self) -> float:
        """Get the minimum confidence threshold for reporting issues."""
        return self.config.get("confidence_threshold", 0.7)