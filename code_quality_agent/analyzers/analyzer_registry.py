"""Registry for managing quality analyzers."""

import logging
from typing import Dict, List, Type, Optional, Any
from enum import Enum

from .base import QualityAnalyzer, IssueCategory
from ..core.models import ParsedFile, AnalysisContext, Issue

logger = logging.getLogger(__name__)


class AnalyzerPriority(Enum):
    """Priority levels for analyzer execution."""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


class AnalyzerRegistry:
    """Registry for managing and coordinating quality analyzers."""
    
    def __init__(self):
        """Initialize the analyzer registry."""
        self._analyzers: Dict[str, QualityAnalyzer] = {}
        self._analyzer_priorities: Dict[str, AnalyzerPriority] = {}
        self._category_analyzers: Dict[IssueCategory, List[str]] = {}
        self._language_analyzers: Dict[str, List[str]] = {}
    
    def register_analyzer(
        self, 
        analyzer: QualityAnalyzer, 
        priority: AnalyzerPriority = AnalyzerPriority.MEDIUM
    ) -> None:
        """
        Register a quality analyzer.
        
        Args:
            analyzer: The analyzer instance to register
            priority: Execution priority for the analyzer
        """
        analyzer_name = analyzer.get_name()
        
        if analyzer_name in self._analyzers:
            logger.warning(f"Analyzer {analyzer_name} is already registered, replacing")
        
        self._analyzers[analyzer_name] = analyzer
        self._analyzer_priorities[analyzer_name] = priority
        
        # Index by category
        category = analyzer.get_category()
        if category not in self._category_analyzers:
            self._category_analyzers[category] = []
        self._category_analyzers[category].append(analyzer_name)
        
        # Index by supported languages
        for language in analyzer.get_supported_languages():
            if language not in self._language_analyzers:
                self._language_analyzers[language] = []
            self._language_analyzers[language].append(analyzer_name)
        
        logger.info(f"Registered analyzer: {analyzer_name} (priority: {priority.name})")
    
    def unregister_analyzer(self, analyzer_name: str) -> bool:
        """
        Unregister an analyzer.
        
        Args:
            analyzer_name: Name of the analyzer to unregister
            
        Returns:
            True if analyzer was found and removed
        """
        if analyzer_name not in self._analyzers:
            return False
        
        analyzer = self._analyzers[analyzer_name]
        
        # Remove from main registry
        del self._analyzers[analyzer_name]
        del self._analyzer_priorities[analyzer_name]
        
        # Remove from category index
        category = analyzer.get_category()
        if category in self._category_analyzers:
            self._category_analyzers[category].remove(analyzer_name)
            if not self._category_analyzers[category]:
                del self._category_analyzers[category]
        
        # Remove from language index
        for language in analyzer.get_supported_languages():
            if language in self._language_analyzers:
                self._language_analyzers[language].remove(analyzer_name)
                if not self._language_analyzers[language]:
                    del self._language_analyzers[language]
        
        logger.info(f"Unregistered analyzer: {analyzer_name}")
        return True
    
    def get_analyzer(self, analyzer_name: str) -> Optional[QualityAnalyzer]:
        """Get an analyzer by name."""
        return self._analyzers.get(analyzer_name)
    
    def get_analyzers_for_category(self, category: IssueCategory) -> List[QualityAnalyzer]:
        """Get all analyzers for a specific issue category."""
        analyzer_names = self._category_analyzers.get(category, [])
        return [self._analyzers[name] for name in analyzer_names if name in self._analyzers]
    
    def get_analyzers_for_language(self, language: str) -> List[QualityAnalyzer]:
        """Get all analyzers that support a specific language."""
        analyzer_names = self._language_analyzers.get(language, [])
        return [self._analyzers[name] for name in analyzer_names if name in self._analyzers]
    
    def get_all_analyzers(self) -> List[QualityAnalyzer]:
        """Get all registered analyzers."""
        return list(self._analyzers.values())
    
    def get_enabled_analyzers(self) -> List[QualityAnalyzer]:
        """Get all enabled analyzers."""
        return [analyzer for analyzer in self._analyzers.values() if analyzer.is_enabled()]
    
    def get_analyzers_by_priority(self, priority: AnalyzerPriority) -> List[QualityAnalyzer]:
        """Get all analyzers with a specific priority."""
        return [
            self._analyzers[name] for name, p in self._analyzer_priorities.items()
            if p == priority and name in self._analyzers
        ]
    
    def get_sorted_analyzers(self) -> List[QualityAnalyzer]:
        """Get all enabled analyzers sorted by priority (highest first)."""
        enabled_analyzers = self.get_enabled_analyzers()
        
        def get_priority_value(analyzer):
            return self._analyzer_priorities.get(analyzer.get_name(), AnalyzerPriority.MEDIUM).value
        
        return sorted(enabled_analyzers, key=get_priority_value)
    
    def run_analyzers(
        self, 
        parsed_files: List[ParsedFile], 
        context: AnalysisContext,
        categories: Optional[List[IssueCategory]] = None,
        languages: Optional[List[str]] = None
    ) -> List[Issue]:
        """
        Run analyzers on parsed files with optional filtering.
        
        Args:
            parsed_files: Files to analyze
            context: Analysis context
            categories: Optional list of categories to analyze
            languages: Optional list of languages to analyze
            
        Returns:
            List of all issues found
        """
        all_issues = []
        
        # Get analyzers to run
        analyzers_to_run = self._get_filtered_analyzers(categories, languages)
        
        # Sort by priority
        sorted_analyzers = sorted(
            analyzers_to_run,
            key=lambda a: self._analyzer_priorities.get(a.get_name(), AnalyzerPriority.MEDIUM).value
        )
        
        for analyzer in sorted_analyzers:
            try:
                # Filter files by supported languages
                supported_languages = analyzer.get_supported_languages()
                relevant_files = [
                    f for f in parsed_files 
                    if f.language in supported_languages
                ]
                
                if relevant_files:
                    logger.debug(f"Running {analyzer.get_name()} on {len(relevant_files)} files")
                    issues = analyzer.analyze(relevant_files, context)
                    
                    # Filter issues by confidence threshold
                    filtered_issues = [
                        issue for issue in issues
                        if issue.confidence >= analyzer.get_confidence_threshold()
                    ]
                    
                    all_issues.extend(filtered_issues)
                    logger.debug(f"{analyzer.get_name()} found {len(filtered_issues)} issues")
                
            except Exception as e:
                logger.error(f"Analyzer {analyzer.get_name()} failed: {e}")
                # Continue with other analyzers
        
        return all_issues
    
    def _get_filtered_analyzers(
        self, 
        categories: Optional[List[IssueCategory]], 
        languages: Optional[List[str]]
    ) -> List[QualityAnalyzer]:
        """Get analyzers filtered by categories and languages."""
        analyzers = set()
        
        # Filter by categories
        if categories:
            for category in categories:
                analyzers.update(self.get_analyzers_for_category(category))
        else:
            analyzers.update(self.get_enabled_analyzers())
        
        # Filter by languages
        if languages:
            language_analyzers = set()
            for language in languages:
                language_analyzers.update(self.get_analyzers_for_language(language))
            analyzers = analyzers.intersection(language_analyzers)
        
        return list(analyzers)
    
    def get_registry_statistics(self) -> Dict[str, Any]:
        """Get statistics about the analyzer registry."""
        total_analyzers = len(self._analyzers)
        enabled_analyzers = len(self.get_enabled_analyzers())
        
        category_counts = {}
        for category, analyzer_names in self._category_analyzers.items():
            category_counts[category.value] = len(analyzer_names)
        
        language_counts = {}
        for language, analyzer_names in self._language_analyzers.items():
            language_counts[language] = len(analyzer_names)
        
        priority_counts = {}
        for priority in AnalyzerPriority:
            count = len(self.get_analyzers_by_priority(priority))
            if count > 0:
                priority_counts[priority.name] = count
        
        return {
            'total_analyzers': total_analyzers,
            'enabled_analyzers': enabled_analyzers,
            'disabled_analyzers': total_analyzers - enabled_analyzers,
            'categories': category_counts,
            'languages': language_counts,
            'priorities': priority_counts
        }
    
    def validate_analyzers(self) -> Dict[str, List[str]]:
        """
        Validate all registered analyzers.
        
        Returns:
            Dictionary with validation results
        """
        validation_results = {
            'valid': [],
            'invalid': [],
            'warnings': []
        }
        
        for name, analyzer in self._analyzers.items():
            try:
                # Check if analyzer has required methods
                if not hasattr(analyzer, 'analyze'):
                    validation_results['invalid'].append(f"{name}: Missing analyze method")
                    continue
                
                if not hasattr(analyzer, 'get_supported_languages'):
                    validation_results['invalid'].append(f"{name}: Missing get_supported_languages method")
                    continue
                
                if not hasattr(analyzer, 'get_category'):
                    validation_results['invalid'].append(f"{name}: Missing get_category method")
                    continue
                
                # Check if analyzer supports any languages
                languages = analyzer.get_supported_languages()
                if not languages:
                    validation_results['warnings'].append(f"{name}: No supported languages")
                
                # Check confidence threshold
                threshold = analyzer.get_confidence_threshold()
                if not (0.0 <= threshold <= 1.0):
                    validation_results['warnings'].append(f"{name}: Invalid confidence threshold: {threshold}")
                
                validation_results['valid'].append(name)
                
            except Exception as e:
                validation_results['invalid'].append(f"{name}: Validation error - {e}")
        
        return validation_results
    
    def clear_registry(self) -> None:
        """Clear all registered analyzers."""
        self._analyzers.clear()
        self._analyzer_priorities.clear()
        self._category_analyzers.clear()
        self._language_analyzers.clear()
        logger.info("Cleared analyzer registry")


# Global analyzer registry instance
analyzer_registry = AnalyzerRegistry()