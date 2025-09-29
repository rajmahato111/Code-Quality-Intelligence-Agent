"""Base classes and interfaces for code parsers."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pathlib import Path

from ..core.models import ParsedFile, DependencyGraph, FileMetadata


class CodeParser(ABC):
    """Abstract base class for all code parsers."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the parser with optional configuration."""
        self.config = config or {}
    
    @abstractmethod
    def parse_file(self, file_path: Path) -> Optional[ParsedFile]:
        """
        Parse a single file and extract structured information.
        
        Args:
            file_path: Path to the file to parse
            
        Returns:
            ParsedFile object or None if parsing failed
        """
        pass
    
    @abstractmethod
    def get_supported_languages(self) -> List[str]:
        """Return list of programming languages this parser supports."""
        pass
    
    @abstractmethod
    def get_file_extensions(self) -> List[str]:
        """Return list of file extensions this parser handles."""
        pass
    
    def can_parse_file(self, file_path: Path) -> bool:
        """Check if this parser can handle the given file."""
        return file_path.suffix.lower() in self.get_file_extensions()
    
    def extract_dependencies(self, parsed_files: List[ParsedFile]) -> DependencyGraph:
        """
        Extract dependencies between parsed files.
        
        Args:
            parsed_files: List of parsed files
            
        Returns:
            Dependency graph showing relationships
        """
        # Default implementation - can be overridden by specific parsers
        return DependencyGraph()
    
    def get_language_from_file(self, file_path: Path) -> Optional[str]:
        """Determine the programming language from file extension."""
        extension_map = {
            ".py": "python",
            ".js": "javascript", 
            ".ts": "typescript",
            ".jsx": "javascript",
            ".tsx": "typescript",
        }
        return extension_map.get(file_path.suffix.lower())