"""Tests for the HotspotAnalyzer class."""

import pytest
import tempfile
import os
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from code_quality_agent.analyzers.hotspot_analyzer import HotspotAnalyzer
from code_quality_agent.analyzers.base import IssueCategory, Severity
from code_quality_agent.core.models import (
    ParsedFile, AnalysisContext, AnalysisOptions, FileMetadata,
    GitCommit, FileChurnMetrics, HotspotAnalysis
)


class TestHotspotAnalyzer:
    """Test cases for HotspotAnalyzer."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = HotspotAnalyzer({
            "min_commits_threshold": 3,
            "hotspot_percentile": 0.8,
            "analysis_period_days": 365,
            "complexity_weight": 0.6,
            "churn_weight": 0.4
        })
        
        self.sample_parsed_files = [
            ParsedFile(
                path="/test/file1.py",
                language="python",
                content="def test():\n    pass\n",
                functions=[],
                classes=[],
                imports=[]
            ),
            ParsedFile(
                path="/test/file2.py", 
                language="python",
                content="class TestClass:\n    def method(self):\n        pass\n",
                functions=[],
                classes=[],
                imports=[]
            )
        ]
        
        self.sample_context = AnalysisContext(
            options=AnalysisOptions()
        )
    
    def test_initialization(self):
        """Test analyzer initialization."""
        assert self.analyzer.min_commits_threshold == 3
        assert self.analyzer.hotspot_percentile == 0.8
        assert self.analyzer.analysis_period_days == 365
        assert self.analyzer.complexity_weight == 0.6
        assert self.analyzer.churn_weight == 0.4
    
    def test_get_supported_languages(self):
        """Test supported languages."""
        languages = self.analyzer.get_supported_languages()
        expected_languages = ["python", "javascript", "typescript", "java", "cpp", "c", "go", "rust"]
        assert languages == expected_languages
    
    def test_get_category(self):
        """Test analyzer category."""
        assert self.analyzer.get_category() == IssueCategory.HOTSPOT
    
    def test_find_git_root_existing_repo(self):
        """Test finding git root in existing repository."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a mock .git directory
            git_dir = Path(temp_dir) / ".git"
            git_dir.mkdir()
            
            # Test finding git root
            result = self.analyzer._find_git_root(temp_dir)
            # Use Path to resolve both paths for comparison
            assert Path(result).resolve() == Path(temp_dir).resolve()
    
    def test_find_git_root_no_repo(self):
        """Test finding git root when no repository exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = self.analyzer._find_git_root(temp_dir)
            assert result is None
    
    def test_parse_git_log_output(self):
        """Test parsing git log output."""
        git_output = """abc123|John Doe|2023-01-01 10:00:00 +0000|Initial commit
5\t2\tfile1.py
def456|Jane Smith|2023-01-02 15:30:00 +0000|Update file
3\t1\tfile1.py
2\t0\tfile2.py"""
        
        commits = self.analyzer._parse_git_log_output(git_output)
        
        assert len(commits) == 2
        
        # Check first commit
        assert commits[0].hash == "abc123"
        assert commits[0].author == "John Doe"
        assert commits[0].message == "Initial commit"
        assert "file1.py" in commits[0].files_changed
        
        # Check second commit
        assert commits[1].hash == "def456"
        assert commits[1].author == "Jane Smith"
        assert commits[1].message == "Update file"
        assert "file1.py" in commits[1].files_changed
        assert "file2.py" in commits[1].files_changed
    
    def test_calculate_file_churn_metrics(self):
        """Test calculating file churn metrics."""
        commits = [
            GitCommit(
                hash="abc123",
                author="John Doe",
                date=datetime(2023, 1, 1),
                message="Initial commit",
                files_changed=["file1.py"]
            ),
            GitCommit(
                hash="def456",
                author="Jane Smith", 
                date=datetime(2023, 1, 10),
                message="Update file",
                files_changed=["file1.py"]
            ),
            GitCommit(
                hash="ghi789",
                author="John Doe",
                date=datetime(2023, 1, 20),
                message="Fix bug",
                files_changed=["file1.py"]
            )
        ]
        
        metrics = self.analyzer._calculate_file_churn_metrics("/test/file1.py", commits)
        
        assert metrics.file_path == "/test/file1.py"
        assert metrics.total_commits == 3
        assert metrics.unique_authors == 2
        assert metrics.first_commit_date == datetime(2023, 1, 1)
        assert metrics.last_commit_date == datetime(2023, 1, 20)
        assert metrics.change_frequency > 0  # Should be commits per day
    
    def test_calculate_complexity_scores(self):
        """Test calculating complexity scores for files."""
        # Create parsed files with complexity data
        from code_quality_agent.core.models import Function, Class
        
        parsed_files = [
            ParsedFile(
                path="/test/simple.py",
                language="python",
                content="def simple():\n    return 1\n",
                functions=[
                    Function(name="simple", line_start=1, line_end=2, complexity=1)
                ],
                classes=[],
                imports=[]
            ),
            ParsedFile(
                path="/test/complex.py",
                language="python", 
                content="def complex():\n    for i in range(10):\n        if i > 5:\n            print(i)\n",
                functions=[
                    Function(name="complex", line_start=1, line_end=4, complexity=5)
                ],
                classes=[
                    Class(
                        name="TestClass",
                        line_start=5,
                        line_end=10,
                        methods=[
                            Function(name="method", line_start=6, line_end=8, complexity=3)
                        ]
                    )
                ],
                imports=[]
            )
        ]
        
        complexity_scores = self.analyzer._calculate_complexity_scores(parsed_files)
        
        assert "/test/simple.py" in complexity_scores
        assert "/test/complex.py" in complexity_scores
        assert complexity_scores["/test/simple.py"] == 1.0  # Single function with complexity 1
        assert complexity_scores["/test/complex.py"] == 4.0  # Average of 5 and 3
    
    def test_identify_hotspots(self):
        """Test hotspot identification logic."""
        # Create sample churn metrics
        churn_metrics = {
            "/test/file1.py": FileChurnMetrics(
                file_path="/test/file1.py",
                total_commits=10,
                unique_authors=3,
                lines_added=100,
                lines_deleted=50,
                first_commit_date=datetime(2023, 1, 1),
                last_commit_date=datetime(2023, 12, 31),
                change_frequency=0.5  # High churn
            ),
            "/test/file2.py": FileChurnMetrics(
                file_path="/test/file2.py",
                total_commits=2,
                unique_authors=1,
                lines_added=20,
                lines_deleted=5,
                first_commit_date=datetime(2023, 6, 1),
                last_commit_date=datetime(2023, 6, 15),
                change_frequency=0.1  # Low churn
            )
        }
        
        # Create sample complexity scores
        complexity_scores = {
            "/test/file1.py": 8.0,  # High complexity
            "/test/file2.py": 2.0   # Low complexity
        }
        
        hotspot_analysis = self.analyzer._identify_hotspots(churn_metrics, complexity_scores)
        
        assert isinstance(hotspot_analysis, HotspotAnalysis)
        assert len(hotspot_analysis.file_churn_metrics) == 2
        
        # file1.py should be identified as a hotspot (high churn + high complexity)
        assert "/test/file1.py" in hotspot_analysis.hotspot_files
        
        # Check that hotspot scores were calculated
        file1_metrics = next(m for m in hotspot_analysis.file_churn_metrics if m.file_path == "/test/file1.py")
        assert file1_metrics.hotspot_score > 0
        assert file1_metrics.complexity_score == 8.0
    
    def test_generate_recommendations(self):
        """Test recommendation generation."""
        hotspot_files = ["/test/hotspot1.py", "/test/hotspot2.py"]
        complexity_hotspots = ["/test/complex1.py", "/test/complex2.py"]
        churn_hotspots = ["/test/churn1.py"]
        
        churn_metrics = {
            "/test/high_churn.py": FileChurnMetrics(
                file_path="/test/high_churn.py",
                total_commits=50,
                unique_authors=8,
                lines_added=1000,
                lines_deleted=500,
                first_commit_date=datetime(2023, 1, 1),
                last_commit_date=datetime(2023, 12, 31),
                change_frequency=0.2  # Very high churn
            )
        }
        
        recommendations = self.analyzer._generate_recommendations(
            hotspot_files, complexity_hotspots, churn_hotspots, churn_metrics
        )
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        
        # Check that recommendations mention hotspots
        recommendation_text = " ".join(recommendations)
        assert "hotspot" in recommendation_text.lower()
        assert "complexity" in recommendation_text.lower()
    
    @patch('subprocess.run')
    def test_analyze_with_git_repo(self, mock_subprocess):
        """Test analysis with mocked git repository."""
        # Mock git log output
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = """abc123|John Doe|2023-01-01 10:00:00 +0000|Initial commit
5\t2\tfile1.py
def456|Jane Smith|2023-01-02 15:30:00 +0000|Update file
3\t1\tfile1.py"""
        mock_subprocess.return_value = mock_result
        
        # Mock finding git root
        with patch.object(self.analyzer, '_find_git_root', return_value="/test"):
            issues = self.analyzer.analyze(self.sample_parsed_files, self.sample_context)
        
        # Should return issues (even if empty due to thresholds)
        assert isinstance(issues, list)
    
    def test_analyze_no_git_repo(self):
        """Test analysis when no git repository is found."""
        with patch.object(self.analyzer, '_find_git_root', return_value=None):
            issues = self.analyzer.analyze(self.sample_parsed_files, self.sample_context)
        
        # Should return empty list when no git repo found
        assert issues == []
    
    def test_generate_hotspot_issues(self):
        """Test generating issues for hotspots."""
        # Create hotspot analysis with sample data
        churn_metrics = FileChurnMetrics(
            file_path="/test/hotspot.py",
            total_commits=15,
            unique_authors=4,
            lines_added=200,
            lines_deleted=100,
            first_commit_date=datetime(2023, 1, 1),
            last_commit_date=datetime(2023, 12, 31),
            change_frequency=0.3,
            complexity_score=7.5,
            hotspot_score=0.85
        )
        
        hotspot_analysis = HotspotAnalysis(
            file_churn_metrics=[churn_metrics],
            hotspot_files=["/test/hotspot.py"],
            complexity_hotspots=["/test/hotspot.py"],
            churn_hotspots=["/test/hotspot.py"],
            recommendations=["Test recommendation"]
        )
        
        parsed_files = [
            ParsedFile(
                path="/test/hotspot.py",
                language="python",
                content="def test():\n    pass\n",
                functions=[],
                classes=[],
                imports=[]
            )
        ]
        
        issues = self.analyzer._generate_hotspot_issues(hotspot_analysis, parsed_files)
        
        assert len(issues) == 1
        issue = issues[0]
        
        assert issue.category == IssueCategory.HOTSPOT
        assert issue.severity.value == Severity.HIGH.value
        assert "hotspot" in issue.title.lower()
        assert issue.location.file_path == "/test/hotspot.py"
        assert issue.confidence == 0.8
        
        # Check metadata
        assert "hotspot_score" in issue.metadata
        assert "complexity_score" in issue.metadata
        assert "change_frequency" in issue.metadata
        assert issue.metadata["hotspot_score"] == 0.85
    
    def test_create_hotspot_description(self):
        """Test creating hotspot issue descriptions."""
        churn_metrics = FileChurnMetrics(
            file_path="/test/file.py",
            total_commits=10,
            unique_authors=3,
            lines_added=150,
            lines_deleted=75,
            first_commit_date=datetime(2023, 1, 1),
            last_commit_date=datetime(2023, 12, 31),
            change_frequency=0.25,
            hotspot_score=0.8
        )
        
        parsed_file = ParsedFile(
            path="/test/file.py",
            language="python",
            content="def test():\n    pass\n",
            functions=[],
            classes=[],
            imports=[]
        )
        
        description = self.analyzer._create_hotspot_description(churn_metrics, parsed_file)
        
        assert "hotspot" in description.lower()
        assert "10" in description  # total commits
        assert "3" in description   # unique authors
        assert "0.25" in description  # change frequency
        assert "150" in description  # lines added
        assert "75" in description   # lines deleted
    
    def test_create_hotspot_suggestion(self):
        """Test creating hotspot issue suggestions."""
        churn_metrics = FileChurnMetrics(
            file_path="/test/file.py",
            total_commits=20,
            unique_authors=5,
            lines_added=300,
            lines_deleted=150,
            first_commit_date=datetime(2023, 1, 1),
            last_commit_date=datetime(2023, 12, 31),
            change_frequency=0.15,  # High frequency
            hotspot_score=0.9
        )
        
        # Create a large file with many functions
        from code_quality_agent.core.models import Function
        functions = [Function(f"func_{i}", i, i+1) for i in range(15)]
        
        parsed_file = ParsedFile(
            path="/test/file.py",
            language="python",
            content="\n".join([f"def func_{i}():\n    pass" for i in range(15)]),
            functions=functions,
            classes=[],
            imports=[]
        )
        
        suggestion = self.analyzer._create_hotspot_suggestion(churn_metrics, parsed_file)
        
        assert isinstance(suggestion, str)
        assert len(suggestion) > 0
        
        # Should contain suggestions for high churn and many functions
        assert "multi-author" in suggestion.lower() or "functions" in suggestion.lower()
    
    def test_get_detailed_churn_stats_error_handling(self):
        """Test error handling in detailed churn stats."""
        # Test with invalid file path
        lines_added, lines_deleted = self.analyzer._get_detailed_churn_stats("/nonexistent/file.py", [])
        
        assert lines_added == 0
        assert lines_deleted == 0
    
    def test_empty_churn_metrics(self):
        """Test handling of empty churn metrics."""
        empty_metrics = self.analyzer._calculate_file_churn_metrics("/test/file.py", [])
        
        assert empty_metrics.file_path == "/test/file.py"
        assert empty_metrics.total_commits == 0
        assert empty_metrics.unique_authors == 0
        assert empty_metrics.change_frequency == 0.0


@pytest.mark.integration
class TestHotspotAnalyzerIntegration:
    """Integration tests for HotspotAnalyzer with real git repositories."""
    
    def setup_method(self):
        """Set up integration test fixtures."""
        self.analyzer = HotspotAnalyzer()
    
    def test_analyze_real_git_repo(self):
        """Test analysis on a real git repository (if available)."""
        # This test requires a real git repository
        # Skip if not in a git repository
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                pytest.skip("Not in a git repository")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pytest.skip("Git not available or timeout")
        
        # Create sample parsed files for current directory
        current_dir = Path.cwd()
        python_files = list(current_dir.glob("**/*.py"))[:5]  # Limit to 5 files
        
        if not python_files:
            pytest.skip("No Python files found in current directory")
        
        parsed_files = []
        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                parsed_file = ParsedFile(
                    path=str(py_file),
                    language="python",
                    content=content,
                    functions=[],
                    classes=[],
                    imports=[]
                )
                parsed_files.append(parsed_file)
            except Exception:
                continue  # Skip files that can't be read
        
        if not parsed_files:
            pytest.skip("No readable Python files found")
        
        # Create analysis context
        context = AnalysisContext(
            options=AnalysisOptions()
        )
        
        # Run analysis
        issues = self.analyzer.analyze(parsed_files, context)
        
        # Should return a list (may be empty if no hotspots found)
        assert isinstance(issues, list)
        
        # If issues found, validate their structure
        for issue in issues:
            assert issue.category == IssueCategory.HOTSPOT
            assert issue.severity in [Severity.HIGH, Severity.MEDIUM, Severity.LOW]
            assert issue.confidence > 0
            assert len(issue.title) > 0
            assert len(issue.description) > 0
            assert len(issue.suggestion) > 0