"""File discovery utilities for the Code Quality Intelligence Agent."""

import os
import fnmatch
from pathlib import Path
from typing import List, Set, Optional
import logging

logger = logging.getLogger(__name__)


def discover_files(
    root_path: str,
    include_patterns: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None,
    max_file_size_mb: float = 10.0
) -> List[str]:
    """
    Discover files in a directory tree based on include/exclude patterns.
    
    Args:
        root_path: Root directory to search
        include_patterns: Patterns for files to include (e.g., ['*.py', '*.js'])
        exclude_patterns: Patterns for files/directories to exclude
        max_file_size_mb: Maximum file size in MB to include
        
    Returns:
        List of file paths that match the criteria
    """
    if include_patterns is None:
        include_patterns = ['*.py', '*.js', '*.ts', '*.jsx', '*.tsx']
    
    if exclude_patterns is None:
        exclude_patterns = [
            'node_modules/**', '.git/**', '__pycache__/**', '*.pyc',
            '.venv/**', 'venv/**', 'build/**', 'dist/**'
        ]
    
    root = Path(root_path).resolve()
    
    if not root.exists():
        raise FileNotFoundError(f"Path does not exist: {root}")
    
    if root.is_file():
        # Single file
        if _should_include_file(root, include_patterns, exclude_patterns, max_file_size_mb):
            return [str(root)]
        else:
            return []
    
    # Directory - walk recursively
    discovered_files = []
    
    for current_dir, dirs, files in os.walk(root):
        current_path = Path(current_dir)
        
        # Filter directories based on exclude patterns
        dirs[:] = [d for d in dirs if not _should_exclude_directory(current_path / d, exclude_patterns)]
        
        # Process files in current directory
        for file_name in files:
            file_path = current_path / file_name
            
            if _should_include_file(file_path, include_patterns, exclude_patterns, max_file_size_mb):
                discovered_files.append(str(file_path))
    
    logger.info(f"Discovered {len(discovered_files)} files in {root}")
    return discovered_files


def _should_include_file(
    file_path: Path,
    include_patterns: List[str],
    exclude_patterns: List[str],
    max_file_size_mb: float
) -> bool:
    """Check if a file should be included based on patterns and size."""
    
    # Check file size
    try:
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        if file_size_mb > max_file_size_mb:
            logger.debug(f"Skipping large file: {file_path} ({file_size_mb:.1f}MB)")
            return False
    except (OSError, IOError):
        logger.debug(f"Could not check size of file: {file_path}")
        return False
    
    # Check exclude patterns first
    if _matches_patterns(file_path, exclude_patterns):
        return False
    
    # Check include patterns
    return _matches_patterns(file_path, include_patterns)


def _should_exclude_directory(dir_path: Path, exclude_patterns: List[str]) -> bool:
    """Check if a directory should be excluded."""
    return _matches_patterns(dir_path, exclude_patterns)


def _matches_patterns(path: Path, patterns: List[str]) -> bool:
    """Check if a path matches any of the given patterns."""
    path_str = str(path)
    path_name = path.name
    
    for pattern in patterns:
        # Handle glob patterns with **
        if '**' in pattern:
            # Convert glob pattern to work with full path
            if fnmatch.fnmatch(path_str, f"*{pattern}") or fnmatch.fnmatch(path_str, pattern):
                return True
        else:
            # Simple pattern matching on filename
            if fnmatch.fnmatch(path_name, pattern):
                return True
            # Also check full path for patterns like "*.test.js"
            if fnmatch.fnmatch(path_str, f"*{pattern}"):
                return True
    
    return False


def get_file_language(file_path: str) -> Optional[str]:
    """
    Determine the programming language of a file based on its extension.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Language name or None if not recognized
    """
    ext = Path(file_path).suffix.lower()
    
    language_map = {
        '.py': 'python',
        '.js': 'javascript',
        '.jsx': 'javascript',
        '.ts': 'typescript',
        '.tsx': 'typescript',
        '.mjs': 'javascript',
        '.cjs': 'javascript',
    }
    
    return language_map.get(ext)


def filter_files_by_language(file_paths: List[str], languages: List[str]) -> List[str]:
    """
    Filter file paths to only include specified languages.
    
    Args:
        file_paths: List of file paths
        languages: List of language names to include
        
    Returns:
        Filtered list of file paths
    """
    if not languages:
        return file_paths
    
    filtered_files = []
    languages_lower = [lang.lower() for lang in languages]
    
    for file_path in file_paths:
        file_lang = get_file_language(file_path)
        if file_lang and file_lang.lower() in languages_lower:
            filtered_files.append(file_path)
    
    return filtered_files