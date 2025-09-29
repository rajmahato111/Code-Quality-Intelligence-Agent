"""Unified parser interface that coordinates multiple language parsers."""

import logging
from pathlib import Path
from typing import List, Optional, Dict, Any, Set
from concurrent.futures import ThreadPoolExecutor, as_completed

from .base import CodeParser
from .python_parser import PythonParser
from .javascript_parser import JavaScriptParser
from ..core.models import ParsedFile, DependencyGraph, AnalysisOptions
from ..utils.file_utils import discover_files, detect_language, get_file_size_mb

logger = logging.getLogger(__name__)


class UnifiedCodeParser:
    """
    Unified parser that coordinates multiple language-specific parsers.
    
    This class provides a single interface for parsing files in multiple
    programming languages, automatically routing files to the appropriate
    parser based on file extension and content.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the unified parser with language-specific parsers."""
        self.config = config or {}
        self.parsers: Dict[str, CodeParser] = {}
        self.language_to_extensions: Dict[str, List[str]] = {}
        
        # Initialize language-specific parsers
        self._initialize_parsers()
    
    def _initialize_parsers(self) -> None:
        """Initialize all available language parsers."""
        # Initialize Python parser
        python_parser = PythonParser(self.config.get('python', {}))
        for lang in python_parser.get_supported_languages():
            self.parsers[lang] = python_parser
            self.language_to_extensions[lang] = python_parser.get_file_extensions()
        
        # Initialize JavaScript/TypeScript parser
        js_parser = JavaScriptParser(self.config.get('javascript', {}))
        for lang in js_parser.get_supported_languages():
            self.parsers[lang] = js_parser
            self.language_to_extensions[lang] = js_parser.get_file_extensions()
        
        logger.info(f"Initialized parsers for languages: {list(self.parsers.keys())}")
    
    def get_supported_languages(self) -> List[str]:
        """Get all supported programming languages."""
        return list(self.parsers.keys())
    
    def get_supported_extensions(self) -> List[str]:
        """Get all supported file extensions."""
        extensions = []
        for ext_list in self.language_to_extensions.values():
            extensions.extend(ext_list)
        return list(set(extensions))  # Remove duplicates
    
    def can_parse_file(self, file_path: Path) -> bool:
        """Check if any parser can handle the given file."""
        language = detect_language(file_path)
        return language is not None and language in self.parsers
    
    def parse_file(self, file_path: Path) -> Optional[ParsedFile]:
        """
        Parse a single file using the appropriate language parser.
        
        Args:
            file_path: Path to the file to parse
            
        Returns:
            ParsedFile object or None if parsing failed
        """
        # Detect language
        language = detect_language(file_path)
        if not language or language not in self.parsers:
            logger.debug(f"No parser available for {file_path} (language: {language})")
            return None
        
        # Check file size
        max_size_mb = self.config.get('max_file_size_mb', 10)
        if get_file_size_mb(file_path) > max_size_mb:
            logger.warning(f"File too large to parse: {file_path}")
            return None
        
        # Parse with appropriate parser
        parser = self.parsers[language]
        try:
            return parser.parse_file(file_path)
        except Exception as e:
            logger.error(f"Failed to parse {file_path} with {parser.__class__.__name__}: {e}")
            return None
    
    def parse_directory(
        self, 
        directory_path: Path, 
        options: AnalysisOptions = None
    ) -> List[ParsedFile]:
        """
        Parse all supported files in a directory.
        
        Args:
            directory_path: Path to the directory to parse
            options: Analysis options for filtering and configuration
            
        Returns:
            List of successfully parsed files
        """
        if options is None:
            options = AnalysisOptions()
        
        # Discover files
        files_to_parse = discover_files(
            directory_path,
            options.include_patterns,
            options.exclude_patterns
        )
        
        # Filter to only supported files
        supported_files = [f for f in files_to_parse if self.can_parse_file(f)]
        
        logger.info(f"Found {len(supported_files)} supported files to parse")
        
        # Parse files
        if options.parallel_processing:
            return self._parse_files_parallel(supported_files, options.max_workers)
        else:
            return self._parse_files_sequential(supported_files)
    
    def _parse_files_sequential(self, files: List[Path]) -> List[ParsedFile]:
        """Parse files sequentially."""
        parsed_files = []
        
        for file_path in files:
            try:
                parsed_file = self.parse_file(file_path)
                if parsed_file:
                    parsed_files.append(parsed_file)
                    logger.debug(f"Successfully parsed: {file_path}")
                else:
                    logger.debug(f"Failed to parse: {file_path}")
            except Exception as e:
                logger.error(f"Error parsing {file_path}: {e}")
        
        return parsed_files
    
    def _parse_files_parallel(self, files: List[Path], max_workers: int = 4) -> List[ParsedFile]:
        """Parse files in parallel using ThreadPoolExecutor."""
        parsed_files = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all parsing tasks
            future_to_file = {
                executor.submit(self.parse_file, file_path): file_path 
                for file_path in files
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    parsed_file = future.result()
                    if parsed_file:
                        parsed_files.append(parsed_file)
                        logger.debug(f"Successfully parsed: {file_path}")
                    else:
                        logger.debug(f"Failed to parse: {file_path}")
                except Exception as e:
                    logger.error(f"Error parsing {file_path}: {e}")
        
        return parsed_files
    
    def build_dependency_graph(self, parsed_files: List[ParsedFile]) -> DependencyGraph:
        """
        Build a unified dependency graph from all parsed files.
        
        Args:
            parsed_files: List of parsed files
            
        Returns:
            Unified dependency graph
        """
        unified_graph = DependencyGraph()
        
        # Group files by language
        files_by_language = {}
        for parsed_file in parsed_files:
            language = parsed_file.language
            if language not in files_by_language:
                files_by_language[language] = []
            files_by_language[language].append(parsed_file)
        
        # Build language-specific dependency graphs
        for language, files in files_by_language.items():
            if language in self.parsers:
                parser = self.parsers[language]
                try:
                    lang_graph = parser.extract_dependencies(files)
                    
                    # Merge into unified graph
                    unified_graph.nodes.update(lang_graph.nodes)
                    unified_graph.edges.extend(lang_graph.edges)
                    
                    logger.debug(f"Added {len(lang_graph.edges)} dependencies from {language} files")
                    
                except Exception as e:
                    logger.error(f"Failed to extract dependencies for {language}: {e}")
        
        # Add cross-language dependencies (if any)
        self._add_cross_language_dependencies(parsed_files, unified_graph)
        
        return unified_graph
    
    def _add_cross_language_dependencies(
        self, 
        parsed_files: List[ParsedFile], 
        graph: DependencyGraph
    ) -> None:
        """Add dependencies between different programming languages."""
        # This is a simplified implementation
        # In practice, you might want to detect:
        # - Python calling JavaScript (e.g., via subprocess)
        # - JavaScript importing Python modules (e.g., via PyScript)
        # - Configuration files referenced by code
        
        file_paths = {pf.path for pf in parsed_files}
        
        for parsed_file in parsed_files:
            # Look for potential cross-language references in imports
            for import_stmt in parsed_file.imports:
                module_path = import_stmt.module
                
                # Check if the import might reference a file in our codebase
                # This is a basic heuristic - could be made more sophisticated
                for file_path in file_paths:
                    file_name = Path(file_path).stem
                    if (file_name == module_path or 
                        module_path in file_path or
                        file_path.endswith(f"/{module_path}")):
                        
                        # Add cross-language dependency
                        graph.add_dependency(parsed_file.path, file_path)
                        logger.debug(f"Added cross-language dependency: {parsed_file.path} -> {file_path}")
    
    def get_parsing_statistics(self, parsed_files: List[ParsedFile]) -> Dict[str, Any]:
        """
        Generate statistics about the parsing results.
        
        Args:
            parsed_files: List of parsed files
            
        Returns:
            Dictionary with parsing statistics
        """
        stats = {
            'total_files': len(parsed_files),
            'languages': {},
            'total_functions': 0,
            'total_classes': 0,
            'total_imports': 0,
            'total_lines': 0,
            'average_complexity': 0.0,
            'files_by_extension': {}
        }
        
        total_complexity = 0
        function_count = 0
        
        for parsed_file in parsed_files:
            language = parsed_file.language
            
            # Language statistics
            if language not in stats['languages']:
                stats['languages'][language] = {
                    'files': 0,
                    'functions': 0,
                    'classes': 0,
                    'imports': 0,
                    'lines': 0
                }
            
            lang_stats = stats['languages'][language]
            lang_stats['files'] += 1
            lang_stats['functions'] += len(parsed_file.functions)
            lang_stats['classes'] += len(parsed_file.classes)
            lang_stats['imports'] += len(parsed_file.imports)
            lang_stats['lines'] += parsed_file.metadata.line_count if parsed_file.metadata else 0
            
            # Overall statistics
            stats['total_functions'] += len(parsed_file.functions)
            stats['total_classes'] += len(parsed_file.classes)
            stats['total_imports'] += len(parsed_file.imports)
            stats['total_lines'] += parsed_file.metadata.line_count if parsed_file.metadata else 0
            
            # Complexity statistics
            for func in parsed_file.functions:
                total_complexity += func.complexity
                function_count += 1
            
            # File extension statistics
            extension = Path(parsed_file.path).suffix
            if extension not in stats['files_by_extension']:
                stats['files_by_extension'][extension] = 0
            stats['files_by_extension'][extension] += 1
        
        # Calculate average complexity
        if function_count > 0:
            stats['average_complexity'] = total_complexity / function_count
        
        return stats
    
    def validate_parsing_results(self, parsed_files: List[ParsedFile]) -> Dict[str, Any]:
        """
        Validate parsing results and identify potential issues.
        
        Args:
            parsed_files: List of parsed files
            
        Returns:
            Dictionary with validation results
        """
        validation_results = {
            'valid_files': 0,
            'files_with_issues': 0,
            'issues': [],
            'warnings': [],
            'language_coverage': {}
        }
        
        for parsed_file in parsed_files:
            has_issues = False
            
            # Check for basic parsing completeness
            if not parsed_file.functions and not parsed_file.classes and not parsed_file.imports:
                # File might be empty or parsing might have failed partially
                if parsed_file.metadata and parsed_file.metadata.line_count > 10:
                    validation_results['warnings'].append(
                        f"Large file with no extracted elements: {parsed_file.path}"
                    )
                    has_issues = True
            
            # Check for extremely high complexity functions
            for func in parsed_file.functions:
                if func.complexity > 20:
                    validation_results['issues'].append(
                        f"Very high complexity function '{func.name}' in {parsed_file.path}: {func.complexity}"
                    )
                    has_issues = True
            
            # Check for missing docstrings in large functions
            for func in parsed_file.functions:
                if not func.docstring and func.line_end - func.line_start > 20:
                    validation_results['warnings'].append(
                        f"Large function without docstring: '{func.name}' in {parsed_file.path}"
                    )
            
            # Update counters
            if has_issues:
                validation_results['files_with_issues'] += 1
            else:
                validation_results['valid_files'] += 1
            
            # Language coverage
            language = parsed_file.language
            if language not in validation_results['language_coverage']:
                validation_results['language_coverage'][language] = 0
            validation_results['language_coverage'][language] += 1
        
        return validation_results
    
    def get_parser_for_language(self, language: str) -> Optional[CodeParser]:
        """Get the parser instance for a specific language."""
        return self.parsers.get(language)
    
    def register_parser(self, parser: CodeParser) -> None:
        """
        Register a new language parser.
        
        Args:
            parser: CodeParser instance to register
        """
        for language in parser.get_supported_languages():
            self.parsers[language] = parser
            self.language_to_extensions[language] = parser.get_file_extensions()
            logger.info(f"Registered parser for {language}: {parser.__class__.__name__}")
    
    def get_file_language_distribution(self, directory_path: Path) -> Dict[str, int]:
        """
        Get the distribution of programming languages in a directory.
        
        Args:
            directory_path: Path to analyze
            
        Returns:
            Dictionary mapping languages to file counts
        """
        files = discover_files(directory_path)
        language_counts = {}
        
        for file_path in files:
            language = detect_language(file_path)
            if language and language in self.parsers:
                language_counts[language] = language_counts.get(language, 0) + 1
        
        return language_counts