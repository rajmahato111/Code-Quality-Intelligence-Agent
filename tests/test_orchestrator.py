"""Tests for the AnalysisOrchestrator class."""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from code_quality_agent.core.orchestrator import AnalysisOrchestrator, AnalysisProgress
from code_quality_agent.core.models import (
    AnalysisOptions, AnalysisStatus, ParsedFile, Issue, IssueCategory, 
    Severity, CodeLocation, QualityMetrics
)
from code_quality_agent.analyzers.base import QualityAnalyzer
from code_quality_agent.analyzers.analyzer_registry import AnalyzerPriority


class MockAnalyzer(QualityAnalyzer):
    """Mock analyzer for testing."""
    
    def __init__(self, name: str = "MockAnalyzer", category: IssueCategory = IssueCategory.SECURITY):
        self.name = name
        self.category = category
        self.enabled = True
        self.confidence_threshold = 0.7
        self.supported_languages = ["python", "javascript"]
    
    def get_name(self) -> str:
        return self.name
    
    def get_category(self) -> IssueCategory:
        return self.category
    
    def get_supported_languages(self) -> list:
        return self.supported_languages
    
    def is_enabled(self) -> bool:
        return self.enabled
    
    def get_confidence_threshold(self) -> float:
        return self.confidence_threshold
    
    def analyze(self, parsed_files, context):
        """Return mock issues."""
        issues = []
        for file in parsed_files:
            issue = Issue(
                id=f"test-{file.path}",
                category=self.category,
                severity=Severity.MEDIUM,
                title=f"Test issue in {file.path}",
                description="Mock issue for testing",
                location=CodeLocation(file.path, 1, 1),
                affected_files=[file.path],
                suggestion="Fix this mock issue",
                confidence=0.8
            )
            issues.append(issue)
        return issues


class TestAnalysisOrchestrator:
    """Test cases for AnalysisOrchestrator."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.orchestrator = AnalysisOrchestrator(enable_caching=False)
        self.mock_analyzer = MockAnalyzer()
        
    def test_initialization(self):
        """Test orchestrator initialization."""
        assert self.orchestrator.unified_parser is not None
        assert self.orchestrator.analyzer_registry is not None
        assert self.orchestrator.enable_caching is False
        assert len(self.orchestrator._analysis_cache) == 0
        
    def test_register_analyzer(self):
        """Test analyzer registration."""
        self.orchestrator.register_analyzer(self.mock_analyzer, AnalyzerPriority.HIGH)
        
        # Check if analyzer was registered in the registry
        registered_analyzer = self.orchestrator.analyzer_registry.get_analyzer("MockAnalyzer")
        assert registered_analyzer is not None
        assert registered_analyzer.get_name() == "MockAnalyzer"
        
    def test_progress_tracking(self):
        """Test progress tracking functionality."""
        analysis_id = "test_analysis"
        
        # Create initial progress
        progress = AnalysisProgress(
            analysis_id=analysis_id,
            status=AnalysisStatus.IN_PROGRESS,
            current_phase="Testing",
            files_processed=0,
            total_files=10,
            analyzers_completed=0,
            total_analyzers=3,
            start_time=datetime.now()
        )
        
        self.orchestrator._progress_trackers[analysis_id] = progress
        
        # Test progress updates
        self.orchestrator._update_progress(analysis_id, files_processed=5)
        
        updated_progress = self.orchestrator.get_analysis_status(analysis_id)
        assert updated_progress.files_processed == 5
        assert updated_progress.progress_percentage > 0
        
    def test_progress_callback(self):
        """Test progress callback functionality."""
        analysis_id = "test_analysis"
        callback_calls = []
        
        def progress_callback(progress):
            callback_calls.append(progress.progress_percentage)
        
        self.orchestrator.add_progress_callback(analysis_id, progress_callback)
        
        # Create and update progress
        progress = AnalysisProgress(
            analysis_id=analysis_id,
            status=AnalysisStatus.IN_PROGRESS,
            current_phase="Testing",
            files_processed=0,
            total_files=10,
            analyzers_completed=0,
            total_analyzers=2,
            start_time=datetime.now()
        )
        
        self.orchestrator._progress_trackers[analysis_id] = progress
        self.orchestrator._update_progress(analysis_id, files_processed=5)
        
        assert len(callback_calls) == 1
        assert callback_calls[0] > 0
        
    def test_cache_key_generation(self):
        """Test cache key generation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a test file
            test_file = Path(temp_dir) / "test.py"
            test_file.write_text("print('hello')")
            
            options = AnalysisOptions()
            cache_key = self.orchestrator._generate_cache_key(temp_dir, options)
            
            assert cache_key != ""
            assert len(cache_key) == 32  # MD5 hash length
            
    def test_cache_validation(self):
        """Test cache validation logic."""
        # Test with empty cache
        assert not self.orchestrator._is_cache_valid("nonexistent_key")
        
        # Test with caching disabled
        self.orchestrator.enable_caching = False
        assert not self.orchestrator._is_cache_valid("any_key")
        
    @patch('code_quality_agent.core.orchestrator.discover_files')
    @patch.object(AnalysisOrchestrator, '_parse_files_with_progress')
    @patch.object(AnalysisOrchestrator, '_run_analysis_with_progress')
    def test_analyze_codebase_basic(self, mock_run_analysis, mock_parse_files, mock_discover):
        """Test basic codebase analysis workflow."""
        # Setup mocks
        mock_discover.return_value = [Path("test.py")]
        
        mock_parsed_file = ParsedFile(
            path="test.py",
            language="python",
            content="print('hello')"
        )
        mock_parse_files.return_value = [mock_parsed_file]
        
        mock_issue = Issue(
            id="test-issue",
            category=IssueCategory.SECURITY,
            severity=Severity.MEDIUM,
            title="Test issue",
            description="Test description",
            location=CodeLocation("test.py", 1, 1),
            affected_files=["test.py"],
            suggestion="Fix this",
            confidence=0.8
        )
        mock_run_analysis.return_value = [mock_issue]
        
        # Mock unified parser methods
        self.orchestrator.unified_parser.build_dependency_graph = Mock()
        self.orchestrator.unified_parser.build_dependency_graph.return_value = Mock()
        
        # Run analysis
        result = self.orchestrator.analyze_codebase("/test/path")
        
        # Verify results
        assert result is not None
        assert result.codebase_path == "/test/path"
        assert len(result.issues) == 1
        assert result.issues[0].title == "Test issue"
        assert result.metrics is not None
        
    def test_quality_metrics_calculation(self):
        """Test quality metrics calculation."""
        # Create test data
        issues = [
            Issue(
                id="issue1",
                category=IssueCategory.SECURITY,
                severity=Severity.HIGH,
                title="Security issue",
                description="Test",
                location=CodeLocation("test.py", 1, 1),
                affected_files=["test.py"],
                suggestion="Fix",
                confidence=0.8
            ),
            Issue(
                id="issue2",
                category=IssueCategory.PERFORMANCE,
                severity=Severity.MEDIUM,
                title="Performance issue",
                description="Test",
                location=CodeLocation("test.py", 5, 5),
                affected_files=["test.py"],
                suggestion="Optimize",
                confidence=0.7
            )
        ]
        
        parsed_files = [
            ParsedFile(
                path="test.py",
                language="python",
                content="line1\nline2\nline3\nline4\nline5"
            )
        ]
        
        metrics = self.orchestrator._calculate_quality_metrics(issues, parsed_files)
        
        assert isinstance(metrics, QualityMetrics)
        assert metrics.overall_score >= 0
        assert metrics.overall_score <= 100
        assert IssueCategory.SECURITY in metrics.category_scores
        assert IssueCategory.PERFORMANCE in metrics.category_scores
        assert metrics.technical_debt_ratio >= 0
        
    def test_quality_metrics_no_issues(self):
        """Test quality metrics with no issues."""
        parsed_files = [
            ParsedFile(
                path="test.py",
                language="python",
                content="print('hello')"
            )
        ]
        
        metrics = self.orchestrator._calculate_quality_metrics([], parsed_files)
        
        assert metrics.overall_score == 100.0
        
    def test_parallel_processing_option(self):
        """Test that parallel processing option is respected."""
        options = AnalysisOptions(parallel_processing=False)
        
        with patch.object(self.orchestrator, '_parse_files_with_progress') as mock_parse:
            with patch.object(self.orchestrator, '_run_analysis_with_progress') as mock_analyze:
                with patch('code_quality_agent.core.orchestrator.discover_files') as mock_discover:
                    mock_discover.return_value = []
                    mock_parse.return_value = []
                    mock_analyze.return_value = []
                    
                    self.orchestrator.unified_parser.build_dependency_graph = Mock()
                    self.orchestrator.unified_parser.build_dependency_graph.return_value = Mock()
                    
                    result = self.orchestrator.analyze_codebase("/test", options)
                    
                    # Verify that methods were called with correct options
                    mock_parse.assert_called_once()
                    mock_analyze.assert_called_once()
                    
                    # Check that options were passed through
                    call_args = mock_parse.call_args[0]
                    assert call_args[1] == options  # options parameter
                    
    def test_cache_operations(self):
        """Test cache operations."""
        # Enable caching
        self.orchestrator.enable_caching = True
        
        # Test cache statistics
        stats = self.orchestrator.get_cache_statistics()
        assert 'cached_results' in stats
        assert 'cache_enabled' in stats
        assert stats['cache_enabled'] is True
        
        # Test cache clearing
        self.orchestrator._analysis_cache['test_key'] = Mock()
        assert len(self.orchestrator._analysis_cache) == 1
        
        self.orchestrator.clear_cache()
        assert len(self.orchestrator._analysis_cache) == 0
        
    def test_error_handling_in_analysis(self):
        """Test error handling during analysis."""
        # Register a failing analyzer
        failing_analyzer = MockAnalyzer("FailingAnalyzer")
        failing_analyzer.analyze = Mock(side_effect=Exception("Test error"))
        
        self.orchestrator.register_analyzer(failing_analyzer)
        
        with patch('code_quality_agent.core.orchestrator.discover_files') as mock_discover:
            with patch.object(self.orchestrator, '_parse_files_with_progress') as mock_parse:
                mock_discover.return_value = [Path("test.py")]
                mock_parse.return_value = [
                    ParsedFile(path="test.py", language="python", content="test")
                ]
                
                self.orchestrator.unified_parser.build_dependency_graph = Mock()
                self.orchestrator.unified_parser.build_dependency_graph.return_value = Mock()
                
                # Analysis should complete despite analyzer failure
                result = self.orchestrator.analyze_codebase("/test")
                assert result is not None
                
    def test_file_filtering_by_language(self):
        """Test that files are properly filtered by analyzer language support."""
        # Create analyzers with different language support
        python_analyzer = MockAnalyzer("PythonAnalyzer")
        python_analyzer.supported_languages = ["python"]
        
        js_analyzer = MockAnalyzer("JSAnalyzer")
        js_analyzer.supported_languages = ["javascript"]
        
        self.orchestrator.register_analyzer(python_analyzer)
        self.orchestrator.register_analyzer(js_analyzer)
        
        # Create mixed language files
        parsed_files = [
            ParsedFile(path="test.py", language="python", content="print('hello')"),
            ParsedFile(path="test.js", language="javascript", content="console.log('hello')"),
            ParsedFile(path="test.txt", language="text", content="hello")
        ]
        
        options = AnalysisOptions()
        issues = self.orchestrator._run_analysis_with_progress(parsed_files, options, "test_id")
        
        # Should have issues from both Python and JS files, but not text file
        assert len(issues) == 2
        file_paths = [issue.location.file_path for issue in issues]
        assert "test.py" in file_paths
        assert "test.js" in file_paths
        assert "test.txt" not in file_paths


if __name__ == "__main__":
    pytest.main([__file__])