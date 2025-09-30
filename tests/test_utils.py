"""Tests for utility functions."""

import pytest
import tempfile
from pathlib import Path
import json

from code_quality_agent.utils.file_utils import (
    discover_files, detect_language, get_file_size_mb,
    is_text_file, read_file_safely, _should_include_file
)
from code_quality_agent.utils.validation import (
    validate_file_path, validate_analysis_options, validate_issue,
    validate_code_location, validate_github_url, ValidationError,
    sanitize_filename, validate_language_support
)
from code_quality_agent.utils.serialization import (
    serialize_to_json, deserialize_from_json, create_analysis_summary,
    export_issues_to_csv, create_metrics_report
)
from code_quality_agent.core.models import (
    AnalysisOptions, Issue, CodeLocation, IssueCategory, Severity,
    AnalysisResult, QualityMetrics, ComplexityMetrics
)


class TestFileUtils:
    """Tests for file utility functions."""
    
    def test_detect_language(self):
        """Test language detection from file extensions."""
        assert detect_language(Path("test.py")) == "python"
        assert detect_language(Path("test.js")) == "javascript"
        assert detect_language(Path("test.jsx")) == "javascript"
        assert detect_language(Path("test.ts")) == "typescript"
        assert detect_language(Path("test.tsx")) == "typescript"
        assert detect_language(Path("test.txt")) is None
    
    def test_should_include_file(self):
        """Test file inclusion logic."""
        include_patterns = ["*.py", "*.js"]
        exclude_patterns = ["test_*", "node_modules/**"]
        
        # Should include
        assert _should_include_file(
            Path("main.py"), include_patterns, exclude_patterns
        )
        assert _should_include_file(
            Path("app.js"), include_patterns, exclude_patterns
        )
        
        # Should exclude
        assert not _should_include_file(
            Path("test_main.py"), include_patterns, exclude_patterns
        )
        assert not _should_include_file(
            Path("node_modules/lib.js"), include_patterns, exclude_patterns
        )
        assert not _should_include_file(
            Path("README.md"), include_patterns, exclude_patterns
        )
    
    def test_discover_files(self):
        """Test file discovery functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test files
            (temp_path / "main.py").write_text("print('hello')")
            (temp_path / "app.js").write_text("console.log('hello')")
            (temp_path / "test_main.py").write_text("# test")
            (temp_path / "README.md").write_text("# README")
            
            # Create subdirectory
            sub_dir = temp_path / "src"
            sub_dir.mkdir()
            (sub_dir / "utils.py").write_text("def helper(): pass")
            
            # Test discovery
            files = discover_files(temp_path)
            file_names = [f.name for f in files]
            
            assert "main.py" in file_names
            assert "app.js" in file_names
            assert "utils.py" in file_names
            assert "test_main.py" not in file_names  # Should be excluded
            assert "README.md" not in file_names  # Not in include patterns
    
    def test_discover_single_file(self):
        """Test discovering a single file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            test_file = temp_path / "test.py"
            test_file.write_text("print('test')")
            
            files = discover_files(test_file)
            assert len(files) == 1
            assert files[0] == test_file
    
    def test_is_text_file(self):
        """Test text file detection."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create text file
            text_file = temp_path / "test.py"
            text_file.write_text("print('hello')")
            assert is_text_file(text_file)
            
            # Create binary file
            binary_file = temp_path / "test.bin"
            binary_file.write_bytes(b'\x00\x01\x02\x03')
            assert not is_text_file(binary_file)
    
    def test_read_file_safely(self):
        """Test safe file reading."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create UTF-8 file
            utf8_file = temp_path / "utf8.py"
            utf8_file.write_text("print('hello')", encoding='utf-8')
            
            content = read_file_safely(utf8_file)
            assert content == "print('hello')"
            
            # Test non-existent file
            non_existent = temp_path / "missing.py"
            assert read_file_safely(non_existent) is None


class TestValidation:
    """Tests for validation utilities."""
    
    def test_validate_file_path(self):
        """Test file path validation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            test_file = temp_path / "test.py"
            test_file.write_text("test")
            
            # Valid path
            validated = validate_file_path(test_file)
            assert validated.exists()
            
            # Invalid path
            with pytest.raises(ValidationError):
                validate_file_path(temp_path / "missing.py")
    
    def test_validate_analysis_options(self):
        """Test analysis options validation."""
        # Valid options
        options = AnalysisOptions()
        validate_analysis_options(options)  # Should not raise
        
        # Invalid options
        invalid_options = AnalysisOptions(max_workers=0)
        with pytest.raises(ValidationError):
            validate_analysis_options(invalid_options)
        
        invalid_options = AnalysisOptions(confidence_threshold=1.5)
        with pytest.raises(ValidationError):
            validate_analysis_options(invalid_options)
    
    def test_validate_code_location(self):
        """Test code location validation."""
        # Valid location
        location = CodeLocation("test.py", 10, 15)
        validate_code_location(location)  # Should not raise
        
        # Invalid locations
        with pytest.raises(ValidationError):
            validate_code_location(CodeLocation("", 10, 15))  # Empty path
        
        with pytest.raises(ValidationError):
            validate_code_location(CodeLocation("test.py", 0, 15))  # Invalid line start
        
        with pytest.raises(ValidationError):
            validate_code_location(CodeLocation("test.py", 15, 10))  # line_end < line_start
    
    def test_validate_issue(self):
        """Test issue validation."""
        location = CodeLocation("test.py", 10, 15)
        
        # Valid issue
        issue = Issue(
            id="test-1",
            category=IssueCategory.SECURITY,
            severity=Severity.HIGH,
            title="Test Issue",
            description="Test description",
            location=location,
            affected_files=["test.py"],
            suggestion="Fix it",
            confidence=0.9
        )
        validate_issue(issue)  # Should not raise
        
        # Invalid issue - empty title
        invalid_issue = Issue(
            id="test-2",
            category=IssueCategory.SECURITY,
            severity=Severity.HIGH,
            title="",  # Empty title
            description="Test description",
            location=location,
            affected_files=["test.py"],
            suggestion="Fix it",
            confidence=0.9
        )
        with pytest.raises(ValidationError):
            validate_issue(invalid_issue)
    
    def test_validate_github_url(self):
        """Test GitHub URL validation."""
        # Valid URLs
        result = validate_github_url("https://github.com/owner/repo")
        assert result["owner"] == "owner"
        assert result["repo"] == "repo"
        
        result = validate_github_url("https://github.com/owner/repo.git")
        assert result["repo"] == "repo"  # .git suffix removed
        
        # Invalid URLs
        with pytest.raises(ValidationError):
            validate_github_url("https://gitlab.com/owner/repo")
        
        with pytest.raises(ValidationError):
            validate_github_url("https://github.com/owner")  # Missing repo
        
        with pytest.raises(ValidationError):
            validate_github_url("not-a-url")
    
    def test_sanitize_filename(self):
        """Test filename sanitization."""
        assert sanitize_filename("normal_file.py") == "normal_file.py"
        assert sanitize_filename("file<with>invalid:chars") == "file_with_invalid_chars"
        assert sanitize_filename("  .hidden_file.  ") == "hidden_file"
        assert sanitize_filename("") == "unnamed_file"
    
    def test_validate_language_support(self):
        """Test language support validation."""
        assert validate_language_support("python")
        assert validate_language_support("javascript")
        assert validate_language_support("typescript")
        assert not validate_language_support("cobol")
        assert not validate_language_support("unknown")


class TestSerialization:
    """Tests for serialization utilities."""
    
    def test_serialize_to_json(self):
        """Test JSON serialization."""
        data = {"test": "value", "number": 42}
        json_str = serialize_to_json(data)
        
        # Should be valid JSON
        parsed = json.loads(json_str)
        assert parsed["test"] == "value"
        assert parsed["number"] == 42
    
    def test_serialize_to_file(self):
        """Test JSON serialization to file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.json"
            data = {"test": "value"}
            
            serialize_to_json(data, file_path)
            
            assert file_path.exists()
            with open(file_path) as f:
                loaded = json.load(f)
            assert loaded["test"] == "value"
    
    def test_deserialize_from_json(self):
        """Test JSON deserialization."""
        json_str = '{"test": "value", "number": 42}'
        data = deserialize_from_json(json_str)
        
        assert data["test"] == "value"
        assert data["number"] == 42
    
    def test_create_analysis_summary(self):
        """Test analysis summary creation."""
        location = CodeLocation("test.py", 10, 15)
        issue = Issue(
            id="test-1",
            category=IssueCategory.SECURITY,
            severity=Severity.HIGH,
            title="Test Issue",
            description="Test",
            location=location,
            affected_files=["test.py"],
            suggestion="Fix",
            confidence=0.9
        )
        
        result = AnalysisResult(
            codebase_path="/test",
            issues=[issue],
            parsed_files=[]
        )
        
        summary = create_analysis_summary(result)
        
        assert summary["total_issues"] == 1
        assert summary["issues_by_category"]["security"] == 1
        assert summary["issues_by_severity"]["high"] == 1
        assert summary["codebase_path"] == "/test"
    
    def test_export_issues_to_csv(self):
        """Test CSV export functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "issues.csv"
            
            location = CodeLocation("test.py", 10, 15)
            issue = Issue(
                id="test-1",
                category=IssueCategory.SECURITY,
                severity=Severity.HIGH,
                title="Test Issue",
                description="Test description",
                location=location,
                affected_files=["test.py"],
                suggestion="Fix it",
                confidence=0.9
            )
            
            export_issues_to_csv([issue], csv_path)
            
            assert csv_path.exists()
            content = csv_path.read_text()
            assert "test-1" in content
            assert "security" in content
            assert "high" in content
    
    def test_create_metrics_report(self):
        """Test metrics report creation."""
        complexity = ComplexityMetrics(
            cyclomatic_complexity=5.5,
            cognitive_complexity=3.2,
            nesting_depth=2,
            lines_of_code=100
        )
        
        metrics = QualityMetrics(
            overall_score=85.5,
            complexity_metrics=complexity,
            maintainability_index=75.0
        )
        
        report = create_metrics_report(metrics)
        
        assert report["overall_quality"]["score"] == 85.5
        assert report["overall_quality"]["grade"] == "B"
        assert report["complexity"]["cyclomatic_complexity"] == 5.5
        assert report["complexity"]["lines_of_code"] == 100