"""Unit tests for error handling and user feedback system."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from io import StringIO
import sys

from code_quality_agent.core.error_handling import (
    ErrorHandler, InputValidator, CodeQualityError, InputValidationError,
    FileAccessError, ParsingError, AnalysisError, ConfigurationError,
    DependencyError, ResourceError, ErrorCategory, create_error_handler
)


class TestCodeQualityErrors:
    """Test custom error classes."""
    
    def test_code_quality_error_creation(self):
        """Test basic CodeQualityError creation."""
        error = CodeQualityError(
            message="Test error message",
            category=ErrorCategory.INPUT_VALIDATION,
            suggestions=["Fix this", "Try that"],
            technical_details="Technical info",
            recoverable=True
        )
        
        assert str(error) == "Test error message"
        assert error.category == ErrorCategory.INPUT_VALIDATION
        assert error.suggestions == ["Fix this", "Try that"]
        assert error.technical_details == "Technical info"
        assert error.recoverable is True
    
    def test_input_validation_error(self):
        """Test InputValidationError creation."""
        error = InputValidationError(
            "Invalid input provided",
            suggestions=["Check your input", "Use valid format"]
        )
        
        assert str(error) == "Invalid input provided"
        assert error.category == ErrorCategory.INPUT_VALIDATION
        assert error.recoverable is True
        assert "Check your input" in error.suggestions
    
    def test_file_access_error(self):
        """Test FileAccessError creation."""
        error = FileAccessError(
            "Cannot access file",
            file_path="/test/file.py",
            suggestions=["Check permissions"]
        )
        
        assert str(error) == "Cannot access file"
        assert error.category == ErrorCategory.FILE_ACCESS
        assert error.file_path == "/test/file.py"
        assert error.recoverable is True
    
    def test_parsing_error(self):
        """Test ParsingError creation."""
        error = ParsingError(
            "Failed to parse file",
            file_path="/test/file.py",
            technical_details="Syntax error on line 5"
        )
        
        assert str(error) == "Failed to parse file"
        assert error.category == ErrorCategory.PARSING_ERROR
        assert error.file_path == "/test/file.py"
        assert error.technical_details == "Syntax error on line 5"
    
    def test_analysis_error(self):
        """Test AnalysisError creation."""
        error = AnalysisError(
            "Analysis failed",
            analyzer_name="SecurityAnalyzer",
            technical_details="Memory error"
        )
        
        assert str(error) == "Analysis failed"
        assert error.category == ErrorCategory.ANALYSIS_ERROR
        assert error.analyzer_name == "SecurityAnalyzer"
        assert error.technical_details == "Memory error"
    
    def test_dependency_error(self):
        """Test DependencyError creation."""
        error = DependencyError(
            "Missing dependency",
            dependency="tree-sitter",
            suggestions=["Install tree-sitter"]
        )
        
        assert str(error) == "Missing dependency"
        assert error.category == ErrorCategory.DEPENDENCY_ERROR
        assert error.dependency == "tree-sitter"
        assert error.recoverable is False  # Dependencies are not recoverable


class TestErrorHandler:
    """Test ErrorHandler functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.error_handler = ErrorHandler(verbose=False)
        self.verbose_handler = ErrorHandler(verbose=True)
    
    def test_error_handler_initialization(self):
        """Test ErrorHandler initialization."""
        handler = ErrorHandler(verbose=True)
        assert handler.verbose is True
        assert len(handler.error_counts) == 0
        assert len(handler.error_templates) > 0
    
    def test_handle_code_quality_error(self):
        """Test handling of CodeQualityError."""
        error = InputValidationError(
            "Test validation error",
            suggestions=["Fix input", "Try again"]
        )
        
        with patch('code_quality_agent.core.error_handling.console') as mock_console:
            recoverable = self.error_handler.handle_error(error, "Test context")
            
            assert recoverable is True
            assert self.error_handler.error_counts[ErrorCategory.INPUT_VALIDATION] == 1
            mock_console.print.assert_called_once()
    
    def test_handle_generic_error(self):
        """Test handling of generic Python exceptions."""
        error = FileNotFoundError("File not found")
        
        with patch('code_quality_agent.core.error_handling.console') as mock_console:
            recoverable = self.error_handler.handle_error(error, "Test context")
            
            assert recoverable is True  # File access errors are recoverable
            assert self.error_handler.error_counts[ErrorCategory.FILE_ACCESS] == 1
            mock_console.print.assert_called_once()
    
    def test_categorize_generic_error(self):
        """Test categorization of generic errors."""
        # File access errors
        assert self.error_handler._categorize_generic_error(FileNotFoundError()) == ErrorCategory.FILE_ACCESS
        assert self.error_handler._categorize_generic_error(PermissionError()) == ErrorCategory.FILE_ACCESS
        
        # Dependency errors
        assert self.error_handler._categorize_generic_error(ImportError()) == ErrorCategory.DEPENDENCY_ERROR
        
        # Resource errors
        assert self.error_handler._categorize_generic_error(MemoryError()) == ErrorCategory.RESOURCE_ERROR
        
        # Network errors
        assert self.error_handler._categorize_generic_error(ConnectionError()) == ErrorCategory.NETWORK_ERROR
        
        # Unknown errors
        assert self.error_handler._categorize_generic_error(RuntimeError()) == ErrorCategory.UNKNOWN_ERROR
    
    def test_get_generic_suggestions(self):
        """Test suggestion generation for generic errors."""
        # File not found suggestions
        suggestions = self.error_handler._get_generic_suggestions(FileNotFoundError())
        assert any("path is correct" in s for s in suggestions)
        
        # Permission error suggestions
        suggestions = self.error_handler._get_generic_suggestions(PermissionError())
        assert any("permissions" in s for s in suggestions)
        
        # Import error suggestions
        suggestions = self.error_handler._get_generic_suggestions(ImportError())
        assert any("dependencies" in s for s in suggestions)
        
        # Memory error suggestions
        suggestions = self.error_handler._get_generic_suggestions(MemoryError())
        assert any("memory" in s for s in suggestions)
    
    def test_verbose_mode_shows_technical_details(self):
        """Test that verbose mode shows technical details."""
        error = CodeQualityError(
            "Test error",
            technical_details="Detailed technical information"
        )
        
        with patch('code_quality_agent.core.error_handling.console') as mock_console:
            self.verbose_handler.handle_error(error)
            
            # Check that technical details were included in the output
            call_args = mock_console.print.call_args[0][0]
            # For Rich Panel objects, check the renderable content
            if hasattr(call_args, 'renderable'):
                content = str(call_args.renderable)
            else:
                content = str(call_args)
            assert "Detailed technical information" in content
    
    def test_error_summary_display(self):
        """Test error summary display."""
        # Add some errors
        self.error_handler.handle_error(InputValidationError("Error 1"))
        self.error_handler.handle_error(FileAccessError("Error 2", "/test/file"))
        self.error_handler.handle_error(InputValidationError("Error 3"))
        
        with patch('code_quality_agent.core.error_handling.console') as mock_console:
            self.error_handler.display_error_summary()
            
            # Should display table and summary message
            assert mock_console.print.call_count >= 2
    
    def test_error_summary_empty(self):
        """Test error summary when no errors occurred."""
        with patch('code_quality_agent.core.error_handling.console') as mock_console:
            self.error_handler.display_error_summary()
            
            # Should not display anything
            mock_console.print.assert_not_called()


class TestInputValidator:
    """Test InputValidator functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = Path(self.temp_dir) / "test.py"
        self.test_file.write_text("print('Hello, World!')")
    
    def test_validate_path_success(self):
        """Test successful path validation."""
        result = InputValidator.validate_path(str(self.test_file))
        assert result == self.test_file.resolve()
    
    def test_validate_path_empty(self):
        """Test validation of empty path."""
        with pytest.raises(InputValidationError) as exc_info:
            InputValidator.validate_path("")
        
        assert "cannot be empty" in str(exc_info.value)
        assert len(exc_info.value.suggestions) > 0
    
    def test_validate_path_nonexistent(self):
        """Test validation of non-existent path."""
        with pytest.raises(FileAccessError) as exc_info:
            InputValidator.validate_path("/nonexistent/path")
        
        assert "does not exist" in str(exc_info.value)
        assert len(exc_info.value.suggestions) > 0
    
    def test_validate_path_invalid_format(self):
        """Test validation of invalid path format."""
        with pytest.raises(InputValidationError) as exc_info:
            # Use null character which is invalid in paths
            InputValidator.validate_path("invalid\x00path")
        
        assert "Invalid path format" in str(exc_info.value)
    
    def test_validate_file_types_supported_file(self):
        """Test validation of supported file types."""
        # Should not raise an exception
        InputValidator.validate_file_types(self.test_file, ['.py', '.js'])
    
    def test_validate_file_types_unsupported_file(self):
        """Test validation of unsupported file types."""
        unsupported_file = Path(self.temp_dir) / "test.txt"
        unsupported_file.write_text("Hello")
        
        with pytest.raises(InputValidationError) as exc_info:
            InputValidator.validate_file_types(unsupported_file, ['.py', '.js'])
        
        assert "Unsupported file type" in str(exc_info.value)
        assert ".txt" in str(exc_info.value)
    
    def test_validate_file_types_directory_with_supported_files(self):
        """Test validation of directory containing supported files."""
        # Should not raise an exception
        InputValidator.validate_file_types(Path(self.temp_dir), ['.py'])
    
    def test_validate_file_types_directory_without_supported_files(self):
        """Test validation of directory without supported files."""
        empty_dir = Path(self.temp_dir) / "empty"
        empty_dir.mkdir()
        
        with pytest.raises(InputValidationError) as exc_info:
            InputValidator.validate_file_types(empty_dir, ['.py', '.js'])
        
        assert "No supported files found" in str(exc_info.value)
    
    def test_validate_numeric_range_valid(self):
        """Test validation of valid numeric range."""
        # Should not raise an exception
        InputValidator.validate_numeric_range(0.5, 0.0, 1.0, "test value")
    
    def test_validate_numeric_range_too_low(self):
        """Test validation of value below range."""
        with pytest.raises(InputValidationError) as exc_info:
            InputValidator.validate_numeric_range(-0.5, 0.0, 1.0, "test value")
        
        assert "must be between 0.0 and 1.0" in str(exc_info.value)
        assert "got -0.5" in str(exc_info.value)
    
    def test_validate_numeric_range_too_high(self):
        """Test validation of value above range."""
        with pytest.raises(InputValidationError) as exc_info:
            InputValidator.validate_numeric_range(1.5, 0.0, 1.0, "test value")
        
        assert "must be between 0.0 and 1.0" in str(exc_info.value)
        assert "got 1.5" in str(exc_info.value)


class TestErrorHandlingIntegration:
    """Integration tests for error handling system."""
    
    def test_create_error_handler_function(self):
        """Test error handler factory function."""
        handler = create_error_handler(verbose=True)
        assert isinstance(handler, ErrorHandler)
        assert handler.verbose is True
    
    def test_error_recovery_workflow(self):
        """Test complete error recovery workflow."""
        handler = ErrorHandler(verbose=False)
        
        # Simulate a series of errors
        errors = [
            InputValidationError("Invalid input"),
            FileAccessError("Cannot read file", "/test/file.py"),
            ParsingError("Parse failed", "/test/file.py"),
            AnalysisError("Analysis failed", "TestAnalyzer"),
            DependencyError("Missing dep", "test-package")
        ]
        
        recoverable_count = 0
        for error in errors:
            with patch('code_quality_agent.core.error_handling.console'):
                if handler.handle_error(error):
                    recoverable_count += 1
        
        # Most errors should be recoverable except dependency errors
        assert recoverable_count == 4
        assert len(handler.error_counts) == 5
    
    def test_error_categorization_accuracy(self):
        """Test accuracy of error categorization."""
        handler = ErrorHandler()
        
        test_cases = [
            (FileNotFoundError("File not found"), ErrorCategory.FILE_ACCESS),
            (PermissionError("Permission denied"), ErrorCategory.FILE_ACCESS),
            (ImportError("No module named 'test'"), ErrorCategory.DEPENDENCY_ERROR),
            (MemoryError("Out of memory"), ErrorCategory.RESOURCE_ERROR),
            (ConnectionError("Connection failed"), ErrorCategory.NETWORK_ERROR),
            (RuntimeError("Runtime error"), ErrorCategory.UNKNOWN_ERROR),
        ]
        
        for error, expected_category in test_cases:
            actual_category = handler._categorize_generic_error(error)
            assert actual_category == expected_category, f"Failed for {type(error).__name__}"
    
    def test_suggestion_quality(self):
        """Test quality and relevance of error suggestions."""
        handler = ErrorHandler()
        
        # Test that suggestions are relevant and actionable
        file_error = FileNotFoundError("File not found")
        suggestions = handler._get_generic_suggestions(file_error)
        
        assert len(suggestions) > 0
        assert any("path" in s.lower() for s in suggestions)
        assert any("file" in s.lower() for s in suggestions)
        
        # Test import error suggestions
        import_error = ImportError("No module named 'test'")
        suggestions = handler._get_generic_suggestions(import_error)
        
        assert any("install" in s.lower() for s in suggestions)
        assert any("dependencies" in s.lower() for s in suggestions)


class TestErrorHandlingWithCLI:
    """Test error handling integration with CLI components."""
    
    def test_input_validation_in_cli_context(self):
        """Test input validation as it would be used in CLI."""
        # Test path validation
        with pytest.raises(InputValidationError):
            InputValidator.validate_path("")
        
        # Test numeric validation
        with pytest.raises(InputValidationError):
            InputValidator.validate_numeric_range(2.0, 0.0, 1.0, "confidence")
    
    def test_graceful_degradation_simulation(self):
        """Test graceful degradation behavior."""
        handler = ErrorHandler()
        
        # Simulate partial failures in analysis
        parsing_errors = [
            ParsingError("Failed to parse file1.py", "/test/file1.py"),
            ParsingError("Failed to parse file2.py", "/test/file2.py"),
        ]
        
        analysis_errors = [
            AnalysisError("SecurityAnalyzer failed", "SecurityAnalyzer"),
        ]
        
        # Handle all errors
        with patch('code_quality_agent.core.error_handling.console'):
            for error in parsing_errors + analysis_errors:
                handler.handle_error(error)
        
        # Verify error tracking
        assert handler.error_counts[ErrorCategory.PARSING_ERROR] == 2
        assert handler.error_counts[ErrorCategory.ANALYSIS_ERROR] == 1
    
    def test_error_message_formatting(self):
        """Test that error messages are properly formatted."""
        handler = ErrorHandler(verbose=True)
        
        error = CodeQualityError(
            "Test error with formatting",
            category=ErrorCategory.INPUT_VALIDATION,
            suggestions=["Suggestion 1", "Suggestion 2"],
            technical_details="Technical details here"
        )
        
        with patch('code_quality_agent.core.error_handling.console') as mock_console:
            handler.handle_error(error, "Test context")
            
            # Verify that console.print was called with a Panel
            mock_console.print.assert_called_once()
            call_args = mock_console.print.call_args[0][0]
            
            # The call should be a Panel object
            from rich.panel import Panel
            assert isinstance(call_args, Panel)


if __name__ == "__main__":
    pytest.main([__file__])