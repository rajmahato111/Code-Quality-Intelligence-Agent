"""Validation utilities for data models and inputs."""

import re
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
from urllib.parse import urlparse

from ..core.models import (
    Issue, CodeLocation, AnalysisOptions, ParsedFile,
    IssueCategory, Severity
)


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


def validate_file_path(file_path: Union[str, Path]) -> Path:
    """
    Validate and normalize a file path.
    
    Args:
        file_path: Path to validate
        
    Returns:
        Validated Path object
        
    Raises:
        ValidationError: If path is invalid
    """
    if isinstance(file_path, str):
        file_path = Path(file_path)
    
    if not isinstance(file_path, Path):
        raise ValidationError(f"Invalid path type: {type(file_path)}")
    
    # Check if path exists
    if not file_path.exists():
        raise ValidationError(f"Path does not exist: {file_path}")
    
    # Check if path is accessible
    try:
        file_path.stat()
    except (PermissionError, OSError) as e:
        raise ValidationError(f"Cannot access path: {file_path} - {e}")
    
    return file_path.resolve()


def validate_analysis_options(options: AnalysisOptions) -> None:
    """
    Validate analysis options.
    
    Args:
        options: Analysis options to validate
        
    Raises:
        ValidationError: If options are invalid
    """
    if not isinstance(options, AnalysisOptions):
        raise ValidationError("Options must be an AnalysisOptions instance")
    
    # Validate patterns
    if not options.include_patterns:
        raise ValidationError("Include patterns cannot be empty")
    
    for pattern in options.include_patterns:
        if not isinstance(pattern, str) or not pattern.strip():
            raise ValidationError(f"Invalid include pattern: {pattern}")
    
    for pattern in options.exclude_patterns:
        if not isinstance(pattern, str):
            raise ValidationError(f"Invalid exclude pattern: {pattern}")
    
    # Validate numeric values
    if options.max_workers < 1:
        raise ValidationError("max_workers must be at least 1")
    
    if not (0.0 <= options.confidence_threshold <= 1.0):
        raise ValidationError("confidence_threshold must be between 0.0 and 1.0")
    
    if options.max_file_size_mb <= 0:
        raise ValidationError("max_file_size_mb must be positive")


def validate_issue(issue: Issue) -> None:
    """
    Validate an Issue object.
    
    Args:
        issue: Issue to validate
        
    Raises:
        ValidationError: If issue is invalid
    """
    if not isinstance(issue, Issue):
        raise ValidationError("Must be an Issue instance")
    
    # Validate required fields
    if not issue.id or not issue.id.strip():
        raise ValidationError("Issue ID cannot be empty")
    
    if not issue.title or not issue.title.strip():
        raise ValidationError("Issue title cannot be empty")
    
    if not issue.description or not issue.description.strip():
        raise ValidationError("Issue description cannot be empty")
    
    # Validate enums
    if not isinstance(issue.category, IssueCategory):
        raise ValidationError(f"Invalid issue category: {issue.category}")
    
    if not isinstance(issue.severity, Severity):
        raise ValidationError(f"Invalid issue severity: {issue.severity}")
    
    # Validate confidence
    if not (0.0 <= issue.confidence <= 1.0):
        raise ValidationError(f"Invalid confidence value: {issue.confidence}")
    
    # Validate location
    validate_code_location(issue.location)
    
    # Validate affected files
    if not issue.affected_files:
        raise ValidationError("Issue must affect at least one file")
    
    for file_path in issue.affected_files:
        if not isinstance(file_path, str) or not file_path.strip():
            raise ValidationError(f"Invalid affected file path: {file_path}")


def validate_code_location(location: CodeLocation) -> None:
    """
    Validate a CodeLocation object.
    
    Args:
        location: Code location to validate
        
    Raises:
        ValidationError: If location is invalid
    """
    if not isinstance(location, CodeLocation):
        raise ValidationError("Must be a CodeLocation instance")
    
    if not location.file_path or not location.file_path.strip():
        raise ValidationError("File path cannot be empty")
    
    if location.line_start < 1:
        raise ValidationError("line_start must be at least 1")
    
    if location.line_end < location.line_start:
        raise ValidationError("line_end must be >= line_start")
    
    if location.column_start is not None and location.column_start < 0:
        raise ValidationError("column_start must be non-negative")
    
    if (location.column_end is not None and 
        location.column_start is not None and 
        location.column_end < location.column_start):
        raise ValidationError("column_end must be >= column_start")


def validate_parsed_file(parsed_file: ParsedFile) -> None:
    """
    Validate a ParsedFile object.
    
    Args:
        parsed_file: Parsed file to validate
        
    Raises:
        ValidationError: If parsed file is invalid
    """
    if not isinstance(parsed_file, ParsedFile):
        raise ValidationError("Must be a ParsedFile instance")
    
    if not parsed_file.path or not parsed_file.path.strip():
        raise ValidationError("File path cannot be empty")
    
    if not parsed_file.language or not parsed_file.language.strip():
        raise ValidationError("Language cannot be empty")
    
    # Validate language is supported
    supported_languages = {"python", "javascript", "typescript"}
    if parsed_file.language.lower() not in supported_languages:
        raise ValidationError(f"Unsupported language: {parsed_file.language}")
    
    # Validate functions
    for func in parsed_file.functions:
        if func.line_start < 1 or func.line_end < func.line_start:
            raise ValidationError(f"Invalid function line numbers: {func.name}")
    
    # Validate classes
    for cls in parsed_file.classes:
        if cls.line_start < 1 or cls.line_end < cls.line_start:
            raise ValidationError(f"Invalid class line numbers: {cls.name}")


def validate_github_url(url: str) -> Dict[str, str]:
    """
    Validate and parse a GitHub repository URL.
    
    Args:
        url: GitHub URL to validate
        
    Returns:
        Dictionary with owner and repo name
        
    Raises:
        ValidationError: If URL is invalid
    """
    if not url or not isinstance(url, str):
        raise ValidationError("URL must be a non-empty string")
    
    # Parse URL
    parsed = urlparse(url)
    
    # Check if it's a GitHub URL
    if parsed.netloc.lower() not in ['github.com', 'www.github.com']:
        raise ValidationError("URL must be a GitHub repository URL")
    
    # Extract owner and repo from path
    path_parts = [part for part in parsed.path.split('/') if part]
    
    if len(path_parts) < 2:
        raise ValidationError("Invalid GitHub repository URL format")
    
    owner = path_parts[0]
    repo = path_parts[1]
    
    # Remove .git suffix if present
    if repo.endswith('.git'):
        repo = repo[:-4]
    
    # Validate owner and repo names
    github_name_pattern = re.compile(r'^[a-zA-Z0-9._-]+$')
    
    if not github_name_pattern.match(owner):
        raise ValidationError(f"Invalid GitHub owner name: {owner}")
    
    if not github_name_pattern.match(repo):
        raise ValidationError(f"Invalid GitHub repository name: {repo}")
    
    return {"owner": owner, "repo": repo}


def validate_configuration(config: Dict[str, Any]) -> None:
    """
    Validate configuration dictionary.
    
    Args:
        config: Configuration to validate
        
    Raises:
        ValidationError: If configuration is invalid
    """
    if not isinstance(config, dict):
        raise ValidationError("Configuration must be a dictionary")
    
    # Validate LLM configuration
    if 'llm' in config:
        llm_config = config['llm']
        if not isinstance(llm_config, dict):
            raise ValidationError("LLM configuration must be a dictionary")
        
        if 'provider' in llm_config:
            valid_providers = ['openai', 'anthropic']
            if llm_config['provider'] not in valid_providers:
                raise ValidationError(f"Invalid LLM provider: {llm_config['provider']}")
        
        if 'temperature' in llm_config:
            temp = llm_config['temperature']
            if not isinstance(temp, (int, float)) or not (0.0 <= temp <= 2.0):
                raise ValidationError("Temperature must be between 0.0 and 2.0")
    
    # Validate analysis configuration
    if 'analysis' in config:
        analysis_config = config['analysis']
        if not isinstance(analysis_config, dict):
            raise ValidationError("Analysis configuration must be a dictionary")
        
        if 'max_workers' in analysis_config:
            workers = analysis_config['max_workers']
            if not isinstance(workers, int) or workers < 1:
                raise ValidationError("max_workers must be a positive integer")


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing invalid characters.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove invalid characters for most filesystems
    invalid_chars = r'<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Remove leading/trailing whitespace and dots
    filename = filename.strip(' .')
    
    # Ensure filename is not empty
    if not filename:
        filename = "unnamed_file"
    
    # Limit length
    if len(filename) > 255:
        filename = filename[:255]
    
    return filename


def validate_language_support(language: str) -> bool:
    """
    Check if a programming language is supported.
    
    Args:
        language: Programming language name
        
    Returns:
        True if language is supported
    """
    supported_languages = {
        'python', 'javascript', 'typescript', 'jsx', 'tsx'
    }
    return language.lower() in supported_languages


def validate_file_size(file_path: Path, max_size_mb: float = 10.0) -> None:
    """
    Validate that a file is not too large.
    
    Args:
        file_path: Path to file
        max_size_mb: Maximum allowed size in MB
        
    Raises:
        ValidationError: If file is too large
    """
    try:
        size_bytes = file_path.stat().st_size
        size_mb = size_bytes / (1024 * 1024)
        
        if size_mb > max_size_mb:
            raise ValidationError(
                f"File too large: {size_mb:.1f}MB > {max_size_mb}MB - {file_path}"
            )
    except (OSError, FileNotFoundError) as e:
        raise ValidationError(f"Cannot check file size: {file_path} - {e}")


def is_valid_identifier(name: str) -> bool:
    """
    Check if a string is a valid programming identifier.
    
    Args:
        name: String to check
        
    Returns:
        True if valid identifier
    """
    if not name or not isinstance(name, str):
        return False
    
    # Check if it matches identifier pattern (letters, digits, underscore)
    # Must start with letter or underscore
    identifier_pattern = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')
    return bool(identifier_pattern.match(name))