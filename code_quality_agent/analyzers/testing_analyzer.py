"""Testing analyzer for detecting testing gaps and test quality issues."""

import re
import ast
from typing import List, Dict, Any, Set, Optional, Tuple
from pathlib import Path
import logging

from .base import QualityAnalyzer, IssueCategory, Severity
from .issue_factory import IssueFactory
from .analyzer_utils import AnalyzerUtils
from ..core.models import ParsedFile, AnalysisContext, Issue, Function, Class

logger = logging.getLogger(__name__)


class TestingAnalyzer(QualityAnalyzer):
    """Analyzer for detecting testing gaps and test quality issues."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the testing analyzer."""
        super().__init__(config)
        self.supported_languages = ["python", "javascript", "typescript"]
        
        # Testing analysis thresholds (configurable)
        self.thresholds = {
            'min_test_coverage': config.get('min_test_coverage', 0.8) if config else 0.8,
            'critical_function_coverage': config.get('critical_function_coverage', 0.9) if config else 0.9,
            'max_test_complexity': config.get('max_test_complexity', 5) if config else 5,
            'min_assertions_per_test': config.get('min_assertions_per_test', 1) if config else 1,
            'max_test_length': config.get('max_test_length', 50) if config else 50
        }
        
        # Define analyzer categories
        self.categories = [IssueCategory.TESTING]
        
        # Test file patterns - FIXED
        self.test_patterns = {
            'python': [
                r'/test_[^/]*\.py$',  # Files starting with test_ (filename only)
                r'.*_test\.py$',      # Files ending with _test.py
                r'/tests?\.py$',      # Files named test.py or tests.py (filename only)
                r'.*/tests?/.*\.py$'  # Files in test or tests directories
            ],
            'javascript': [
                r'.*\.test\.js$',
                r'.*\.spec\.js$',
                r'.*/tests?/.*\.js$',
                r'.*/__tests__/.*\.js$'
            ],
            'typescript': [
                r'.*\.test\.ts$',
                r'.*\.spec\.ts$',
                r'.*/tests?/.*\.ts$',
                r'.*/__tests__/.*\.ts$'
            ]
        }
    
    def get_supported_languages(self) -> List[str]:
        """Return list of supported languages."""
        return self.supported_languages
    
    def get_category(self) -> IssueCategory:
        """Return the category of issues this analyzer detects."""
        return IssueCategory.TESTING
    
    def analyze(self, parsed_files: List[ParsedFile], context: AnalysisContext) -> List[Issue]:
        """
        Analyze parsed files for testing issues.
        
        Args:
            parsed_files: List of parsed files to analyze
            context: Analysis context
            
        Returns:
            List of testing issues found
        """
        issues = []
        
        try:
            # Separate test files from source files
            test_files, source_files = self._separate_test_and_source_files(parsed_files)
            
            # Debug logging
            logger.info(f"Testing analyzer: Found {len(test_files)} test files and {len(source_files)} source files")
            
            # Analyze test coverage
            issues.extend(self._analyze_test_coverage(source_files, test_files))
            
        except Exception as e:
            logger.error(f"Testing analysis failed: {e}")
        
        return issues
    
    def _separate_test_and_source_files(self, parsed_files: List[ParsedFile]) -> Tuple[List[ParsedFile], List[ParsedFile]]:
        """Separate test files from source files."""
        test_files = []
        source_files = []
        
        for parsed_file in parsed_files:
            if self._is_test_file(parsed_file):
                test_files.append(parsed_file)
                logger.debug(f"Identified as test file: {parsed_file.path}")
            else:
                source_files.append(parsed_file)
                logger.debug(f"Identified as source file: {parsed_file.path}")
        
        return test_files, source_files
    
    def _is_test_file(self, parsed_file: ParsedFile) -> bool:
        """Check if a file is a test file based on naming patterns."""
        file_path = parsed_file.path.lower()
        language = parsed_file.language
        
        if language in self.test_patterns:
            for pattern in self.test_patterns[language]:
                if re.search(pattern, file_path):
                    return True
        
        return False
    
    def _analyze_test_coverage(self, source_files: List[ParsedFile], test_files: List[ParsedFile]) -> List[Issue]:
        """Analyze test coverage for source files."""
        issues = []
        
        # Only flag missing tests for substantial files with complex logic
        if not test_files:
            logger.info(f"No test files found, analyzing {len(source_files)} source files for testing needs")
            for source_file in source_files:
                # Only flag files that have substantial logic worth testing
                function_count = len(source_file.functions)
                class_count = len(source_file.classes)
                line_count = source_file.metadata.line_count if source_file.metadata else 0
                
                # Only create testing issues for files with significant complexity
                if (function_count >= 3 or class_count >= 2 or line_count >= 50) and (function_count > 0 or class_count > 0):
                    issues.append(IssueFactory.create_testing_issue(
                        title="Missing Test Coverage",
                        description=f"Source file {source_file.path} contains substantial logic "
                                  f"({function_count} functions, {class_count} classes) but no test files found. "
                                  f"Consider adding tests for critical functionality.",
                        file_path=source_file.path,
                        line_start=1,
                        line_end=source_file.metadata.line_count if source_file.metadata else 100,
                        suggestion="Create test files for complex functions and classes. "
                                 "Focus on testing critical business logic and edge cases.",
                        confidence=0.7,
                        testing_gap_type="no_tests",
                        severity=Severity.MEDIUM  # Reduced from HIGH to MEDIUM
                    ))
        
        return issues