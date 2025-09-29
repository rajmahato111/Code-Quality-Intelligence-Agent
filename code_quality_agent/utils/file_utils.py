"""File handling utilities for the Code Quality Intelligence Agent."""

import os
from pathlib import Path
from typing import List, Optional, Set
import fnmatch
import mimetypes


def discover_files(
    root_path: Path, 
    include_patterns: List[str] = None, 
    exclude_patterns: List[str] = None
) -> List[Path]:
    """
    Discover all files that should be analyzed based on include/exclude patterns.
    
    Args:
        root_path: Root directory or file to analyze
        include_patterns: Glob patterns for files to include
        exclude_patterns: Glob patterns for files to exclude
        
    Returns:
        List of file paths to analyze
    """
    if include_patterns is None:
        include_patterns = ["*.py", "*.js", "*.ts", "*.jsx", "*.tsx"]
    
    if exclude_patterns is None:
        exclude_patterns = [
            "node_modules/**", 
            ".git/**", 
            "__pycache__/**", 
            "*.pyc",
            ".venv/**",
            "venv/**",
            "build/**",
            "dist/**"
        ]
    
    files_to_analyze = []
    
    if root_path.is_file():
        # Single file analysis
        if _should_include_file(root_path, include_patterns, exclude_patterns):
            files_to_analyze.append(root_path)
    else:
        # Directory analysis
        for file_path in _walk_directory(root_path):
            if _should_include_file(file_path, include_patterns, exclude_patterns):
                files_to_analyze.append(file_path)
    
    return files_to_analyze


def _walk_directory(directory: Path) -> List[Path]:
    """Recursively walk directory and return all files."""
    files = []
    try:
        for item in directory.rglob("*"):
            if item.is_file():
                files.append(item)
    except (PermissionError, OSError):
        # Skip directories we can't access
        pass
    return files


def _should_include_file(
    file_path: Path, 
    include_patterns: List[str], 
    exclude_patterns: List[str]
) -> bool:
    """Check if a file should be included based on patterns."""
    # Convert to relative path for pattern matching
    relative_path = str(file_path)
    
    # Check exclude patterns first
    for pattern in exclude_patterns:
        if fnmatch.fnmatch(relative_path, pattern) or fnmatch.fnmatch(file_path.name, pattern):
            return False
    
    # Check include patterns
    for pattern in include_patterns:
        if fnmatch.fnmatch(relative_path, pattern) or fnmatch.fnmatch(file_path.name, pattern):
            return True
    
    return False


def detect_language(file_path) -> Optional[str]:
    """
    Detect the programming language of a file based on its extension.
    
    Args:
        file_path: Path to the file (string or Path object)
        
    Returns:
        Programming language name or None if not supported
    """
    extension_map = {
        ".py": "python",
        ".js": "javascript",
        ".jsx": "javascript",
        ".ts": "typescript", 
        ".tsx": "typescript",
        ".mjs": "javascript",
        ".cjs": "javascript",
    }
    
    # Convert to Path object if it's a string
    if isinstance(file_path, str):
        file_path = Path(file_path)
    
    extension = file_path.suffix.lower()
    return extension_map.get(extension)


def get_file_size_mb(file_path) -> float:
    """Get file size in megabytes."""
    try:
        # Convert to Path object if it's a string
        if isinstance(file_path, str):
            file_path = Path(file_path)
        
        size_bytes = file_path.stat().st_size
        return size_bytes / (1024 * 1024)
    except (OSError, FileNotFoundError):
        return 0.0


def is_text_file(file_path: Path) -> bool:
    """Check if a file is a text file."""
    try:
        # Check MIME type
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type and mime_type.startswith('text/'):
            return True
        
        # Check for common text file extensions
        text_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.json', '.yaml', '.yml',
            '.md', '.txt', '.csv', '.xml', '.html', '.css', '.scss', '.less',
            '.sql', '.sh', '.bash', '.zsh', '.fish', '.ps1', '.bat', '.cmd'
        }
        
        if file_path.suffix.lower() in text_extensions:
            return True
        
        # Try to read a small portion to check if it's text
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(1024)
                # Check for null bytes (common in binary files)
                if b'\x00' in chunk:
                    return False
                # Try to decode as UTF-8
                chunk.decode('utf-8')
                return True
        except (UnicodeDecodeError, OSError):
            return False
            
    except Exception:
        return False


def read_file_safely(file_path: Path, encoding: str = 'utf-8') -> Optional[str]:
    """
    Safely read a text file with error handling.
    
    Args:
        file_path: Path to the file
        encoding: Text encoding to use
        
    Returns:
        File content or None if reading failed
    """
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            return f.read()
    except (UnicodeDecodeError, OSError, FileNotFoundError):
        # Try with different encodings
        for fallback_encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
            try:
                with open(file_path, 'r', encoding=fallback_encoding) as f:
                    return f.read()
            except (UnicodeDecodeError, OSError):
                continue
        return None


def create_cache_directory(cache_path: Path) -> None:
    """Create cache directory if it doesn't exist."""
    cache_path.mkdir(parents=True, exist_ok=True)


def get_relative_path(file_path: Path, base_path: Path) -> Path:
    """Get relative path from base path."""
    try:
        return file_path.relative_to(base_path)
    except ValueError:
        # If file_path is not relative to base_path, return the file_path as is
        return file_path