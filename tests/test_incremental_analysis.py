"""Integration tests for incremental analysis functionality."""

import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch

from code_quality_agent.core.orchestrator import AnalysisOrchestrator
from code_quality_agent.core.models import AnalysisOptions
from code_quality_agent.analyzers.base import QualityAnalyzer
from code_quality_agent.analyzers.analyzer_registry import AnalyzerPriority
from code_quality_agent.core.models import (
    Issue, IssueCategory, Severity, CodeLocation, ParsedFile
)


class MockIncrementalAnalyzer(QualityAnalyzer):
    """Mock analyzer that tracks which files it analyzes."""
    
    def __init__(self, name: str = "MockIncrementalAnalyzer"):
        self.name = name
        self.analyzed_files = []
        self.call_count = 0
    
    def get_name(self) -> str:
        return self.name
    
    def get_category(self) -> IssueCategory:
        return IssueCategory.SECURITY
    
    def get_supported_languages(self) -> list:
        return ["python", "javascript"]
    
    def is_enabled(self) -> bool:
        return True
    
    def get_confidence_threshold(self) -> float:
        return 0.7
    
    def analyze(self, parsed_files, context):
        """Track which files are analyzed and return mock issues."""
        self.call_count += 1
        self.analyzed_files.extend([f.path for f in parsed_files])
        
        issues = []
        for file in parsed_files:
            issue = Issue(
                id=f"mock-{file.path}-{self.call_count}",
                category=self.get_category(),
                severity=Severity.MEDIUM,
                title=f"Mock issue in {Path(file.path).name}",
                description="Mock issue for incremental testing",
                location=CodeLocation(file.path, 1, 1),
                affected_files=[file.path],
                suggestion="Fix this mock issue",
                confidence=0.8
            )
            issues.append(issue)
        return issues
    
    def reset_tracking(self):
        """Reset tracking for new test."""
        self.analyzed_files = []
        self.call_count = 0


class TestIncrementalAnalysis:
    """Test cases for incremental analysis functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.orchestrator = AnalysisOrchestrator(
            enable_caching=True,
            cache_dir=self.temp_dir / "cache",
            cache_ttl_hours=1,
            enable_incremental_analysis=True
        )
        self.mock_analyzer = MockIncrementalAnalyzer()
        self.orchestrator.register_analyzer(self.mock_analyzer, AnalyzerPriority.HIGH)
        
        # Mock the unified parser to avoid parsing issues
        self.orchestrator.unified_parser.parse_file = Mock()
        self.orchestrator.unified_parser.build_dependency_graph = Mock()
        self.orchestrator.unified_parser.build_dependency_graph.return_value = Mock()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _create_test_files(self, count: int = 3) -> list:
        """Create test files for analysis."""
        files = []
        for i in range(count):
            file_path = self.temp_dir / f"test{i}.py"
            file_path.write_text(f"print('test file {i}')")
            files.append(file_path)
        return files
    
    def _mock_parse_file(self, file_path):
        """Mock parse file function."""
        return ParsedFile(
            path=str(file_path),
            language="python",
            content=file_path.read_text()
        )
    
    def test_first_analysis_processes_all_files(self):
        """Test that first analysis processes all files."""
        files = self._create_test_files(3)
        self.orchestrator.unified_parser.parse_file.side_effect = self._mock_parse_file
        
        # First analysis should process all files
        options = AnalysisOptions(parallel_processing=False)
        result = self.orchestrator.analyze_codebase(str(self.temp_dir), options)
        
        # Verify all files were analyzed
        assert len(self.mock_analyzer.analyzed_files) == 3
        assert len(result.issues) == 3
        
        # Verify cache statistics
        stats = self.orchestrator.get_cache_statistics()
        assert stats['file_cache_entries'] == 3
    
    def test_second_analysis_uses_cache(self):
        """Test that second analysis uses cached results."""
        files = self._create_test_files(3)
        self.orchestrator.unified_parser.parse_file.side_effect = self._mock_parse_file
        
        options = AnalysisOptions(parallel_processing=False)
        
        # First analysis
        result1 = self.orchestrator.analyze_codebase(str(self.temp_dir), options)
        first_call_count = self.mock_analyzer.call_count
        
        # Reset analyzer tracking
        self.mock_analyzer.reset_tracking()
        
        # Second analysis should use cache
        result2 = self.orchestrator.analyze_codebase(str(self.temp_dir), options)
        
        # Analyzer should not be called again (files cached)
        assert self.mock_analyzer.call_count == 0
        assert len(self.mock_analyzer.analyzed_files) == 0
        
        # Results should be the same
        assert len(result1.issues) == len(result2.issues)
        
        # Cache statistics should show hits
        stats = self.orchestrator.get_cache_statistics()
        assert stats['cache_hits'] > 0
    
    def test_modified_file_triggers_reanalysis(self):
        """Test that modifying a file triggers reanalysis of that file."""
        files = self._create_test_files(3)
        self.orchestrator.unified_parser.parse_file.side_effect = self._mock_parse_file
        
        options = AnalysisOptions(parallel_processing=False)
        
        # First analysis
        result1 = self.orchestrator.analyze_codebase(str(self.temp_dir), options)
        
        # Reset analyzer tracking
        self.mock_analyzer.reset_tracking()
        
        # Modify one file
        time.sleep(0.1)  # Ensure different timestamp
        files[1].write_text("print('modified file 1')")
        
        # Second analysis
        result2 = self.orchestrator.analyze_codebase(str(self.temp_dir), options)
        
        # Only the modified file should be reanalyzed
        assert self.mock_analyzer.call_count == 1
        assert len(self.mock_analyzer.analyzed_files) == 1
        assert str(files[1]) in self.mock_analyzer.analyzed_files
    
    def test_new_file_triggers_analysis(self):
        """Test that adding a new file triggers analysis of that file."""
        files = self._create_test_files(2)
        self.orchestrator.unified_parser.parse_file.side_effect = self._mock_parse_file
        
        options = AnalysisOptions(parallel_processing=False)
        
        # First analysis
        result1 = self.orchestrator.analyze_codebase(str(self.temp_dir), options)
        assert len(result1.issues) == 2
        
        # Reset analyzer tracking
        self.mock_analyzer.reset_tracking()
        
        # Add a new file
        new_file = self.temp_dir / "new_test.py"
        new_file.write_text("print('new file')")
        
        # Second analysis
        result2 = self.orchestrator.analyze_codebase(str(self.temp_dir), options)
        
        # Only the new file should be analyzed
        assert self.mock_analyzer.call_count == 1
        assert len(self.mock_analyzer.analyzed_files) == 1
        assert str(new_file) in self.mock_analyzer.analyzed_files
        
        # Total issues should increase
        assert len(result2.issues) == 3
    
    def test_deleted_file_removes_from_cache(self):
        """Test that deleting a file removes it from results."""
        files = self._create_test_files(3)
        self.orchestrator.unified_parser.parse_file.side_effect = self._mock_parse_file
        
        options = AnalysisOptions(parallel_processing=False)
        
        # First analysis
        result1 = self.orchestrator.analyze_codebase(str(self.temp_dir), options)
        assert len(result1.issues) == 3
        
        # Reset analyzer tracking
        self.mock_analyzer.reset_tracking()
        
        # Delete one file
        files[1].unlink()
        
        # Second analysis
        result2 = self.orchestrator.analyze_codebase(str(self.temp_dir), options)
        
        # No files should be reanalyzed (remaining files unchanged)
        assert self.mock_analyzer.call_count == 0
        
        # Total issues should decrease (deleted file's issues removed)
        assert len(result2.issues) == 2
    
    def test_force_full_analysis_bypasses_cache(self):
        """Test that force_full_analysis bypasses all caching."""
        files = self._create_test_files(3)
        self.orchestrator.unified_parser.parse_file.side_effect = self._mock_parse_file
        
        options = AnalysisOptions(parallel_processing=False)
        
        # First analysis
        result1 = self.orchestrator.analyze_codebase(str(self.temp_dir), options)
        
        # Reset analyzer tracking
        self.mock_analyzer.reset_tracking()
        
        # Force full analysis
        result2 = self.orchestrator.force_full_analysis(str(self.temp_dir), options)
        
        # All files should be reanalyzed
        assert self.mock_analyzer.call_count == 1
        assert len(self.mock_analyzer.analyzed_files) == 3
    
    def test_incremental_analysis_disabled(self):
        """Test behavior when incremental analysis is disabled."""
        # Create orchestrator with incremental analysis disabled
        orchestrator = AnalysisOrchestrator(
            enable_caching=True,
            enable_incremental_analysis=False
        )
        
        mock_analyzer = MockIncrementalAnalyzer("DisabledIncrementalAnalyzer")
        orchestrator.register_analyzer(mock_analyzer, AnalyzerPriority.HIGH)
        orchestrator.unified_parser.parse_file = Mock(side_effect=self._mock_parse_file)
        orchestrator.unified_parser.build_dependency_graph = Mock()
        orchestrator.unified_parser.build_dependency_graph.return_value = Mock()
        
        files = self._create_test_files(3)
        options = AnalysisOptions(parallel_processing=False)
        
        # First analysis
        result1 = orchestrator.analyze_codebase(str(self.temp_dir), options)
        first_call_count = mock_analyzer.call_count
        
        # Reset tracking
        mock_analyzer.reset_tracking()
        
        # Second analysis should reanalyze all files
        result2 = orchestrator.analyze_codebase(str(self.temp_dir), options)
        
        # All files should be reanalyzed
        assert mock_analyzer.call_count == 1
        assert len(mock_analyzer.analyzed_files) == 3
    
    def test_cache_cleanup_integration(self):
        """Test cache cleanup integration with orchestrator."""
        files = self._create_test_files(2)
        self.orchestrator.unified_parser.parse_file.side_effect = self._mock_parse_file
        
        # Perform analysis to populate cache
        options = AnalysisOptions(parallel_processing=False)
        result = self.orchestrator.analyze_codebase(str(self.temp_dir), options)
        
        # Verify cache has entries
        stats_before = self.orchestrator.get_cache_statistics()
        assert stats_before['file_cache_entries'] > 0
        
        # Manually expire cache entries by setting short TTL
        self.orchestrator.cache_manager.ttl_hours = 0.001  # Very short TTL
        time.sleep(0.1)
        
        # Run cleanup
        removed_count = self.orchestrator.cleanup_cache()
        
        # Verify entries were removed
        assert removed_count > 0
        stats_after = self.orchestrator.get_cache_statistics()
        assert stats_after['file_cache_entries'] == 0
    
    def test_cache_statistics_integration(self):
        """Test cache statistics integration."""
        files = self._create_test_files(2)
        self.orchestrator.unified_parser.parse_file.side_effect = self._mock_parse_file
        
        # Initial statistics
        stats = self.orchestrator.get_cache_statistics()
        assert stats['incremental_analysis_enabled'] is True
        assert stats['file_cache_entries'] == 0
        assert stats['cache_hits'] == 0
        
        # Perform analysis
        options = AnalysisOptions(parallel_processing=False)
        result = self.orchestrator.analyze_codebase(str(self.temp_dir), options)
        
        # Check updated statistics
        stats = self.orchestrator.get_cache_statistics()
        assert stats['file_cache_entries'] == 2
        
        # Perform second analysis to generate cache hits
        result2 = self.orchestrator.analyze_codebase(str(self.temp_dir), options)
        
        stats = self.orchestrator.get_cache_statistics()
        assert stats['cache_hits'] > 0
    
    def test_parallel_processing_with_incremental_analysis(self):
        """Test that incremental analysis works with parallel processing."""
        files = self._create_test_files(4)
        self.orchestrator.unified_parser.parse_file.side_effect = self._mock_parse_file
        
        # Enable parallel processing
        options = AnalysisOptions(parallel_processing=True, max_workers=2)
        
        # First analysis
        result1 = self.orchestrator.analyze_codebase(str(self.temp_dir), options)
        assert len(result1.issues) == 4
        
        # Reset analyzer tracking
        self.mock_analyzer.reset_tracking()
        
        # Modify one file
        time.sleep(0.1)
        files[2].write_text("print('modified file 2')")
        
        # Second analysis with parallel processing
        result2 = self.orchestrator.analyze_codebase(str(self.temp_dir), options)
        
        # Only modified file should be reanalyzed
        assert self.mock_analyzer.call_count == 1
        assert len(self.mock_analyzer.analyzed_files) == 1
        assert str(files[2]) in self.mock_analyzer.analyzed_files


if __name__ == "__main__":
    import pytest
    pytest.main([__file__])