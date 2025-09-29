"""Comprehensive error handling and user feedback system."""

import sys
import traceback
from typing import Optional, Dict, Any, List
from pathlib import Path
from enum import Enum
import logging

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table


logger = logging.getLogger(__name__)
console = Console()


class ErrorCategory(Enum):
    """Categories of errors that can occur."""
    INPUT_VALIDATION = "input_validation"
    FILE_ACCESS = "file_access"
    PARSING_ERROR = "parsing_error"
    ANALYSIS_ERROR = "analysis_error"
    CONFIGURATION_ERROR = "configuration_error"
    DEPENDENCY_ERROR = "dependency_error"
    RESOURCE_ERROR = "resource_error"
    NETWORK_ERROR = "network_error"
    UNKNOWN_ERROR = "unknown_error"


class CodeQualityError(Exception):
    """Base exception for Code Quality Intelligence Agent errors."""
    
    def __init__(
        self,
        message: str,
        category: ErrorCategory = ErrorCategory.UNKNOWN_ERROR,
        suggestions: Optional[List[str]] = None,
        technical_details: Optional[str] = None,
        recoverable: bool = False
    ):
        """
        Initialize error with user-friendly information.
        
        Args:
            message: User-friendly error message
            category: Category of error for better handling
            suggestions: List of suggestions to fix the error
            technical_details: Technical details for debugging
            recoverable: Whether the error is recoverable
        """
        super().__init__(message)
        self.message = message
        self.category = category
        self.suggestions = suggestions or []
        self.technical_details = technical_details
        self.recoverable = recoverable


class InputValidationError(CodeQualityError):
    """Error for invalid user input."""
    
    def __init__(self, message: str, suggestions: Optional[List[str]] = None):
        super().__init__(
            message=message,
            category=ErrorCategory.INPUT_VALIDATION,
            suggestions=suggestions,
            recoverable=True
        )


class FileAccessError(CodeQualityError):
    """Error for file access issues."""
    
    def __init__(self, message: str, file_path: str, suggestions: Optional[List[str]] = None):
        super().__init__(
            message=message,
            category=ErrorCategory.FILE_ACCESS,
            suggestions=suggestions,
            recoverable=True
        )
        self.file_path = file_path


class ParsingError(CodeQualityError):
    """Error during code parsing."""
    
    def __init__(self, message: str, file_path: str, technical_details: Optional[str] = None):
        super().__init__(
            message=message,
            category=ErrorCategory.PARSING_ERROR,
            technical_details=technical_details,
            recoverable=True
        )
        self.file_path = file_path


class AnalysisError(CodeQualityError):
    """Error during analysis."""
    
    def __init__(self, message: str, analyzer_name: str, technical_details: Optional[str] = None):
        super().__init__(
            message=message,
            category=ErrorCategory.ANALYSIS_ERROR,
            technical_details=technical_details,
            recoverable=True
        )
        self.analyzer_name = analyzer_name


class ConfigurationError(CodeQualityError):
    """Error in configuration."""
    
    def __init__(self, message: str, suggestions: Optional[List[str]] = None):
        super().__init__(
            message=message,
            category=ErrorCategory.CONFIGURATION_ERROR,
            suggestions=suggestions,
            recoverable=True
        )


class DependencyError(CodeQualityError):
    """Error with missing or incompatible dependencies."""
    
    def __init__(self, message: str, dependency: str, suggestions: Optional[List[str]] = None):
        super().__init__(
            message=message,
            category=ErrorCategory.DEPENDENCY_ERROR,
            suggestions=suggestions,
            recoverable=False
        )
        self.dependency = dependency


class ResourceError(CodeQualityError):
    """Error due to resource constraints."""
    
    def __init__(self, message: str, resource_type: str, suggestions: Optional[List[str]] = None):
        super().__init__(
            message=message,
            category=ErrorCategory.RESOURCE_ERROR,
            suggestions=suggestions,
            recoverable=True
        )
        self.resource_type = resource_type


class ErrorHandler:
    """Centralized error handling and user feedback system."""
    
    def __init__(self, verbose: bool = False):
        """
        Initialize error handler.
        
        Args:
            verbose: Whether to show technical details
        """
        self.verbose = verbose
        self.error_counts: Dict[ErrorCategory, int] = {}
        
        # Error message templates
        self.error_templates = {
            ErrorCategory.INPUT_VALIDATION: {
                "icon": "❌",
                "color": "red",
                "title": "Input Validation Error"
            },
            ErrorCategory.FILE_ACCESS: {
                "icon": "📁",
                "color": "yellow",
                "title": "File Access Error"
            },
            ErrorCategory.PARSING_ERROR: {
                "icon": "🔍",
                "color": "orange3",
                "title": "Code Parsing Error"
            },
            ErrorCategory.ANALYSIS_ERROR: {
                "icon": "⚠️",
                "color": "yellow",
                "title": "Analysis Error"
            },
            ErrorCategory.CONFIGURATION_ERROR: {
                "icon": "⚙️",
                "color": "blue",
                "title": "Configuration Error"
            },
            ErrorCategory.DEPENDENCY_ERROR: {
                "icon": "📦",
                "color": "red",
                "title": "Dependency Error"
            },
            ErrorCategory.RESOURCE_ERROR: {
                "icon": "💾",
                "color": "magenta",
                "title": "Resource Error"
            },
            ErrorCategory.NETWORK_ERROR: {
                "icon": "🌐",
                "color": "cyan",
                "title": "Network Error"
            },
            ErrorCategory.UNKNOWN_ERROR: {
                "icon": "❓",
                "color": "red",
                "title": "Unknown Error"
            }
        }
    
    def handle_error(self, error: Exception, context: Optional[str] = None) -> bool:
        """
        Handle an error with user-friendly feedback.
        
        Args:
            error: The error to handle
            context: Additional context about where the error occurred
            
        Returns:
            True if error is recoverable, False otherwise
        """
        if isinstance(error, CodeQualityError):
            return self._handle_code_quality_error(error, context)
        else:
            return self._handle_generic_error(error, context)
    
    def _handle_code_quality_error(self, error: CodeQualityError, context: Optional[str] = None) -> bool:
        """Handle CodeQualityError with rich formatting."""
        template = self.error_templates[error.category]
        
        # Track error counts
        self.error_counts[error.category] = self.error_counts.get(error.category, 0) + 1
        
        # Build error content
        content_parts = []
        
        # Main error message
        content_parts.append(f"[bold]{template['icon']} {error.message}[/bold]")
        
        # Context if provided
        if context:
            content_parts.append(f"\n[dim]Context: {context}[/dim]")
        
        # Technical details in verbose mode
        if self.verbose and error.technical_details:
            content_parts.append(f"\n[dim]Technical Details:[/dim]")
            content_parts.append(f"[dim]{error.technical_details}[/dim]")
        
        # Suggestions
        if error.suggestions:
            content_parts.append(f"\n[bold yellow]💡 Suggestions:[/bold yellow]")
            for i, suggestion in enumerate(error.suggestions, 1):
                content_parts.append(f"  {i}. {suggestion}")
        
        # Display error panel
        console.print(Panel(
            "\n".join(content_parts),
            title=f"[{template['color']}]{template['title']}[/{template['color']}]",
            border_style=template['color']
        ))
        
        return error.recoverable
    
    def _handle_generic_error(self, error: Exception, context: Optional[str] = None) -> bool:
        """Handle generic Python exceptions."""
        error_type = type(error).__name__
        
        # Try to categorize the error
        category = self._categorize_generic_error(error)
        template = self.error_templates[category]
        
        # Track error counts
        self.error_counts[category] = self.error_counts.get(category, 0) + 1
        
        # Build error content
        content_parts = []
        content_parts.append(f"[bold]{template['icon']} {error_type}: {str(error)}[/bold]")
        
        if context:
            content_parts.append(f"\n[dim]Context: {context}[/dim]")
        
        # Add generic suggestions
        suggestions = self._get_generic_suggestions(error)
        if suggestions:
            content_parts.append(f"\n[bold yellow]💡 Suggestions:[/bold yellow]")
            for i, suggestion in enumerate(suggestions, 1):
                content_parts.append(f"  {i}. {suggestion}")
        
        # Technical details in verbose mode
        if self.verbose:
            content_parts.append(f"\n[dim]Stack Trace:[/dim]")
            content_parts.append(f"[dim]{traceback.format_exc()}[/dim]")
        
        # Display error panel
        console.print(Panel(
            "\n".join(content_parts),
            title=f"[{template['color']}]{template['title']}[/{template['color']}]",
            border_style=template['color']
        ))
        
        return category in [ErrorCategory.FILE_ACCESS, ErrorCategory.PARSING_ERROR, ErrorCategory.ANALYSIS_ERROR]
    
    def _categorize_generic_error(self, error: Exception) -> ErrorCategory:
        """Categorize a generic exception."""
        error_type = type(error).__name__
        error_message = str(error).lower()
        
        if isinstance(error, (FileNotFoundError, PermissionError, IsADirectoryError)):
            return ErrorCategory.FILE_ACCESS
        elif isinstance(error, SyntaxError):
            return ErrorCategory.PARSING_ERROR
        elif isinstance(error, ValueError) and any(
            keyword in error_message for keyword in ['parse', 'syntax', 'invalid']
        ):
            return ErrorCategory.PARSING_ERROR
        elif isinstance(error, ImportError):
            return ErrorCategory.DEPENDENCY_ERROR
        elif isinstance(error, MemoryError):
            return ErrorCategory.RESOURCE_ERROR
        elif isinstance(error, OSError) and any(
            keyword in error_message for keyword in ['memory', 'disk', 'space']
        ):
            return ErrorCategory.RESOURCE_ERROR
        elif isinstance(error, (ConnectionError, TimeoutError)):
            return ErrorCategory.NETWORK_ERROR
        else:
            return ErrorCategory.UNKNOWN_ERROR
    
    def _get_generic_suggestions(self, error: Exception) -> List[str]:
        """Get suggestions for generic errors."""
        error_type = type(error).__name__
        error_message = str(error).lower()
        
        if isinstance(error, FileNotFoundError):
            return [
                "Check that the file or directory path is correct",
                "Ensure the file exists and is accessible",
                "Try using an absolute path instead of a relative path"
            ]
        elif isinstance(error, PermissionError):
            return [
                "Check file permissions and ensure you have read access",
                "Try running with appropriate permissions",
                "Ensure the file is not locked by another process"
            ]
        elif isinstance(error, ImportError):
            return [
                "Install missing dependencies using pip or your package manager",
                "Check that all required packages are installed",
                "Verify your Python environment is set up correctly"
            ]
        elif isinstance(error, MemoryError):
            return [
                "Try analyzing smaller portions of the codebase",
                "Increase available memory or use a machine with more RAM",
                "Use the --max-workers option to reduce parallel processing"
            ]
        else:
            return [
                "Try running with --verbose flag for more details",
                "Check the documentation for troubleshooting guidance",
                "Report this issue if the problem persists"
            ]
    
    def display_error_summary(self) -> None:
        """Display a summary of all errors encountered."""
        if not self.error_counts:
            return
        
        table = Table(title="Error Summary", show_header=True, header_style="bold red")
        table.add_column("Error Type", style="cyan")
        table.add_column("Count", style="red", justify="right")
        table.add_column("Recoverable", style="green")
        
        total_errors = 0
        recoverable_errors = 0
        
        for category, count in self.error_counts.items():
            total_errors += count
            template = self.error_templates[category]
            
            # Determine if category is generally recoverable
            is_recoverable = category not in [ErrorCategory.DEPENDENCY_ERROR, ErrorCategory.UNKNOWN_ERROR]
            if is_recoverable:
                recoverable_errors += count
            
            table.add_row(
                f"{template['icon']} {template['title']}",
                str(count),
                "✅" if is_recoverable else "❌"
            )
        
        console.print(table)
        
        # Summary message
        if recoverable_errors == total_errors:
            console.print(f"[green]✅ All {total_errors} errors are recoverable. You can fix these issues and try again.[/green]")
        elif recoverable_errors > 0:
            console.print(f"[yellow]⚠️  {recoverable_errors} of {total_errors} errors are recoverable. Some issues may require attention.[/yellow]")
        else:
            console.print(f"[red]❌ {total_errors} errors occurred and may require significant fixes.[/red]")


class InputValidator:
    """Validates user inputs and provides helpful feedback."""
    
    @staticmethod
    def validate_path(path: str) -> Path:
        """
        Validate and normalize a file or directory path.
        
        Args:
            path: Path string to validate
            
        Returns:
            Validated Path object
            
        Raises:
            InputValidationError: If path is invalid
        """
        if not path or not path.strip():
            raise InputValidationError(
                "Path cannot be empty",
                suggestions=[
                    "Provide a valid file or directory path",
                    "Use '.' for current directory",
                    "Use absolute paths to avoid confusion"
                ]
            )
        
        try:
            path_obj = Path(path).resolve()
        except (OSError, ValueError) as e:
            raise InputValidationError(
                f"Invalid path format: {path}",
                suggestions=[
                    "Check for invalid characters in the path",
                    "Ensure the path follows your operating system's conventions",
                    "Try using forward slashes (/) instead of backslashes"
                ]
            ) from e
        
        if not path_obj.exists():
            raise FileAccessError(
                f"Path does not exist: {path_obj}",
                file_path=str(path_obj),
                suggestions=[
                    "Check that the path is spelled correctly",
                    "Ensure the file or directory exists",
                    "Try using tab completion to avoid typos"
                ]
            )
        
        return path_obj
    
    @staticmethod
    def validate_file_types(path: Path, supported_extensions: Optional[List[str]] = None) -> None:
        """
        Validate that the path contains supported file types.
        
        Args:
            path: Path to validate
            supported_extensions: List of supported file extensions
            
        Raises:
            InputValidationError: If no supported files found
        """
        if supported_extensions is None:
            supported_extensions = ['.py', '.js', '.ts', '.jsx', '.tsx']
        
        if path.is_file():
            if path.suffix.lower() not in supported_extensions:
                raise InputValidationError(
                    f"Unsupported file type: {path.suffix}",
                    suggestions=[
                        f"Supported file types: {', '.join(supported_extensions)}",
                        "Try analyzing a directory containing supported files",
                        "Use --include-patterns to specify custom file patterns"
                    ]
                )
        else:
            # Check if directory contains any supported files
            supported_files = []
            for ext in supported_extensions:
                supported_files.extend(list(path.rglob(f"*{ext}")))
            
            if not supported_files:
                raise InputValidationError(
                    f"No supported files found in directory: {path}",
                    suggestions=[
                        f"Ensure the directory contains files with extensions: {', '.join(supported_extensions)}",
                        "Check subdirectories for supported files",
                        "Use --include-patterns to specify custom file patterns"
                    ]
                )
    
    @staticmethod
    def validate_numeric_range(value: float, min_val: float, max_val: float, name: str) -> None:
        """
        Validate that a numeric value is within the specified range.
        
        Args:
            value: Value to validate
            min_val: Minimum allowed value
            max_val: Maximum allowed value
            name: Name of the parameter for error messages
            
        Raises:
            InputValidationError: If value is out of range
        """
        if not (min_val <= value <= max_val):
            raise InputValidationError(
                f"{name} must be between {min_val} and {max_val}, got {value}",
                suggestions=[
                    f"Use a value between {min_val} and {max_val}",
                    f"Check the documentation for valid {name} ranges"
                ]
            )


def create_error_handler(verbose: bool = False) -> ErrorHandler:
    """
    Create an error handler instance.
    
    Args:
        verbose: Whether to show technical details
        
    Returns:
        Configured ErrorHandler instance
    """
    return ErrorHandler(verbose=verbose)