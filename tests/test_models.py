"""Tests for core data models."""

import pytest
from datetime import datetime
from pathlib import Path
import tempfile
import json

from code_quality_agent.core.models import (
    Issue, CodeLocation, IssueCategory, Severity,
    Function, Class, Import, ParsedFile, FileMetadata,
    DependencyGraph, QualityMetrics, ComplexityMetrics,
    CoverageMetrics, AnalysisResult, AnalysisOptions
)


class TestCodeLocation:
    """Tests for CodeLocation model."""
    
    def test_code_location_creation(self):
        """Test creating a CodeLocation."""
        location = CodeLocation(
            file_path="test.py",
            line_start=10,
            line_end=15,
            column_start=5,
            column_end=20
        )
        
        assert location.file_path == "test.py"
        assert location.line_start == 10
        assert location.line_end == 15
        assert location.column_start == 5
        assert location.column_end == 20
    
    def test_code_location_str(self):
        """Test string representation of CodeLocation."""
        location = CodeLocation("test.py", 10, 15, 5, 20)
        assert str(location) == "test.py:10:5-15:20"
        
        location_no_columns = CodeLocation("test.py", 10, 15)
        assert str(location_no_columns) == "test.py:10-15"
    
    def test_code_location_to_dict(self):
        """Test CodeLocation serialization."""
        location = CodeLocation("test.py", 10, 15, 5, 20)
        data = location.to_dict()
        
        expected = {
            "file_path": "test.py",
            "line_start": 10,
            "line_end": 15,
            "column_start": 5,
            "column_end": 20
        }
        assert data == expected


class TestIssue:
    """Tests for Issue model."""
    
    def test_issue_creation(self):
        """Test creating an Issue."""
        location = CodeLocation("test.py", 10, 15)
        issue = Issue(
            id="test-issue-1",
            category=IssueCategory.SECURITY,
            severity=Severity.HIGH,
            title="Test Issue",
            description="This is a test issue",
            location=location,
            affected_files=["test.py"],
            suggestion="Fix this issue",
            confidence=0.9
        )
        
        assert issue.id == "test-issue-1"
        assert issue.category == IssueCategory.SECURITY
        assert issue.severity == Severity.HIGH
        assert issue.confidence == 0.9
    
    def test_issue_auto_id_generation(self):
        """Test automatic ID generation."""
        location = CodeLocation("test.py", 10, 15)
        issue = Issue(
            id="",  # Empty ID should trigger auto-generation
            category=IssueCategory.SECURITY,
            severity=Severity.HIGH,
            title="Test Issue",
            description="This is a test issue",
            location=location,
            affected_files=["test.py"],
            suggestion="Fix this issue",
            confidence=0.9
        )
        
        assert issue.id  # Should have generated an ID
        assert len(issue.id) > 0
    
    def test_issue_confidence_validation(self):
        """Test confidence value validation."""
        location = CodeLocation("test.py", 10, 15)
        
        with pytest.raises(ValueError):
            Issue(
                id="test",
                category=IssueCategory.SECURITY,
                severity=Severity.HIGH,
                title="Test",
                description="Test",
                location=location,
                affected_files=["test.py"],
                suggestion="Fix",
                confidence=1.5  # Invalid confidence > 1.0
            )
    
    def test_issue_serialization(self):
        """Test Issue serialization and deserialization."""
        location = CodeLocation("test.py", 10, 15)
        original_issue = Issue(
            id="test-issue-1",
            category=IssueCategory.SECURITY,
            severity=Severity.HIGH,
            title="Test Issue",
            description="This is a test issue",
            location=location,
            affected_files=["test.py"],
            suggestion="Fix this issue",
            confidence=0.9
        )
        
        # Serialize to dict
        data = original_issue.to_dict()
        
        # Deserialize from dict
        restored_issue = Issue.from_dict(data)
        
        assert restored_issue.id == original_issue.id
        assert restored_issue.category == original_issue.category
        assert restored_issue.severity == original_issue.severity
        assert restored_issue.title == original_issue.title
        assert restored_issue.confidence == original_issue.confidence


class TestFunction:
    """Tests for Function model."""
    
    def test_function_creation(self):
        """Test creating a Function."""
        func = Function(
            name="test_function",
            line_start=10,
            line_end=20,
            parameters=["arg1", "arg2"],
            return_type="str",
            docstring="Test function",
            complexity=5,
            is_async=True,
            decorators=["@property"]
        )
        
        assert func.name == "test_function"
        assert func.parameters == ["arg1", "arg2"]
        assert func.return_type == "str"
        assert func.is_async is True
        assert func.complexity == 5
    
    def test_function_serialization(self):
        """Test Function serialization."""
        func = Function("test_func", 10, 20, ["arg1"], "str")
        data = func.to_dict()
        
        assert data["name"] == "test_func"
        assert data["line_start"] == 10
        assert data["parameters"] == ["arg1"]


class TestDependencyGraph:
    """Tests for DependencyGraph model."""
    
    def test_dependency_graph_creation(self):
        """Test creating a DependencyGraph."""
        graph = DependencyGraph()
        assert len(graph.nodes) == 0
        assert len(graph.edges) == 0
    
    def test_add_dependency(self):
        """Test adding dependencies."""
        graph = DependencyGraph()
        graph.add_dependency("file1.py", "file2.py")
        
        assert "file1.py" in graph.nodes
        assert "file2.py" in graph.nodes
        assert ("file1.py", "file2.py") in graph.edges
    
    def test_get_dependencies(self):
        """Test getting dependencies for a file."""
        graph = DependencyGraph()
        graph.add_dependency("file1.py", "file2.py")
        graph.add_dependency("file1.py", "file3.py")
        
        deps = graph.get_dependencies("file1.py")
        assert "file2.py" in deps
        assert "file3.py" in deps
        assert len(deps) == 2
    
    def test_get_dependents(self):
        """Test getting dependents of a file."""
        graph = DependencyGraph()
        graph.add_dependency("file1.py", "file2.py")
        graph.add_dependency("file3.py", "file2.py")
        
        dependents = graph.get_dependents("file2.py")
        assert "file1.py" in dependents
        assert "file3.py" in dependents
        assert len(dependents) == 2
    
    def test_circular_dependency_detection(self):
        """Test circular dependency detection."""
        graph = DependencyGraph()
        
        # No circular dependencies
        graph.add_dependency("file1.py", "file2.py")
        graph.add_dependency("file2.py", "file3.py")
        assert not graph.has_circular_dependencies()
        
        # Add circular dependency
        graph.add_dependency("file3.py", "file1.py")
        assert graph.has_circular_dependencies()


class TestAnalysisResult:
    """Tests for AnalysisResult model."""
    
    def test_analysis_result_creation(self):
        """Test creating an AnalysisResult."""
        result = AnalysisResult(
            codebase_path="/test/path",
            issues=[],
            parsed_files=[]
        )
        
        assert result.codebase_path == "/test/path"
        assert result.analysis_id  # Should have auto-generated ID
        assert isinstance(result.timestamp, datetime)
    
    def test_get_issues_by_category(self):
        """Test filtering issues by category."""
        location = CodeLocation("test.py", 10, 15)
        security_issue = Issue(
            id="sec-1", category=IssueCategory.SECURITY, severity=Severity.HIGH,
            title="Security Issue", description="Test", location=location,
            affected_files=["test.py"], suggestion="Fix", confidence=0.9
        )
        performance_issue = Issue(
            id="perf-1", category=IssueCategory.PERFORMANCE, severity=Severity.MEDIUM,
            title="Performance Issue", description="Test", location=location,
            affected_files=["test.py"], suggestion="Fix", confidence=0.8
        )
        
        result = AnalysisResult(
            issues=[security_issue, performance_issue]
        )
        
        security_issues = result.get_issues_by_category(IssueCategory.SECURITY)
        assert len(security_issues) == 1
        assert security_issues[0].id == "sec-1"
    
    def test_get_issues_by_severity(self):
        """Test filtering issues by severity."""
        location = CodeLocation("test.py", 10, 15)
        high_issue = Issue(
            id="high-1", category=IssueCategory.SECURITY, severity=Severity.HIGH,
            title="High Issue", description="Test", location=location,
            affected_files=["test.py"], suggestion="Fix", confidence=0.9
        )
        medium_issue = Issue(
            id="med-1", category=IssueCategory.PERFORMANCE, severity=Severity.MEDIUM,
            title="Medium Issue", description="Test", location=location,
            affected_files=["test.py"], suggestion="Fix", confidence=0.8
        )
        
        result = AnalysisResult(
            issues=[high_issue, medium_issue]
        )
        
        high_issues = result.get_issues_by_severity(Severity.HIGH)
        assert len(high_issues) == 1
        assert high_issues[0].id == "high-1"
    
    def test_get_issues_by_file(self):
        """Test filtering issues by file."""
        location1 = CodeLocation("file1.py", 10, 15)
        location2 = CodeLocation("file2.py", 20, 25)
        
        issue1 = Issue(
            id="issue-1", category=IssueCategory.SECURITY, severity=Severity.HIGH,
            title="Issue 1", description="Test", location=location1,
            affected_files=["file1.py"], suggestion="Fix", confidence=0.9
        )
        issue2 = Issue(
            id="issue-2", category=IssueCategory.PERFORMANCE, severity=Severity.MEDIUM,
            title="Issue 2", description="Test", location=location2,
            affected_files=["file2.py"], suggestion="Fix", confidence=0.8
        )
        
        result = AnalysisResult(
            issues=[issue1, issue2]
        )
        
        file1_issues = result.get_issues_by_file("file1.py")
        assert len(file1_issues) == 1
        assert file1_issues[0].id == "issue-1"
    
    def test_analysis_result_serialization(self):
        """Test AnalysisResult serialization."""
        result = AnalysisResult(
            codebase_path="/test/path",
            issues=[],
            parsed_files=[]
        )
        
        data = result.to_dict()
        
        assert data["codebase_path"] == "/test/path"
        assert "analysis_id" in data
        assert "timestamp" in data
        assert "issues" in data
        assert "parsed_files" in data
    
    def test_save_and_load_from_file(self):
        """Test saving and loading AnalysisResult from file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test_result.json"
            
            # Create and save result
            original_result = AnalysisResult(
                codebase_path="/test/path",
                issues=[],
                parsed_files=[]
            )
            original_result.save_to_file(file_path)
            
            # Verify file was created
            assert file_path.exists()
            
            # Load and verify
            loaded_result = AnalysisResult.load_from_file(file_path)
            assert loaded_result.analysis_id == original_result.analysis_id
            assert loaded_result.codebase_path == original_result.codebase_path


class TestAnalysisOptions:
    """Tests for AnalysisOptions model."""
    
    def test_analysis_options_defaults(self):
        """Test default values for AnalysisOptions."""
        options = AnalysisOptions()
        
        assert "*.py" in options.include_patterns
        assert "*.js" in options.include_patterns
        assert "node_modules/**" in options.exclude_patterns
        assert options.parallel_processing is True
        assert options.max_workers == 4
        assert options.confidence_threshold == 0.7
    
    def test_analysis_options_serialization(self):
        """Test AnalysisOptions serialization."""
        options = AnalysisOptions(
            include_patterns=["*.py"],
            exclude_patterns=["test/**"],
            max_workers=2
        )
        
        data = options.to_dict()
        
        assert data["include_patterns"] == ["*.py"]
        assert data["exclude_patterns"] == ["test/**"]
        assert data["max_workers"] == 2