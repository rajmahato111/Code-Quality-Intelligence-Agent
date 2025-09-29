"""Advanced caching and incremental analysis manager."""

import json
import pickle
import hashlib
import logging
from typing import Dict, List, Set, Optional, Any, Tuple
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

from .models import AnalysisResult, ParsedFile, Issue, AnalysisOptions


logger = logging.getLogger(__name__)


@dataclass
class FileCache:
    """Cache entry for a single file's analysis results."""
    file_path: str
    last_modified: float
    content_hash: str
    parsed_file: Optional[ParsedFile] = None
    issues: List[Issue] = None
    analysis_timestamp: datetime = None
    
    def __post_init__(self):
        if self.analysis_timestamp is None:
            self.analysis_timestamp = datetime.now()
        if self.issues is None:
            self.issues = []


@dataclass
class CacheMetadata:
    """Metadata for the entire cache."""
    version: str = "1.0"
    created_at: datetime = None
    last_cleanup: datetime = None
    total_entries: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.last_cleanup is None:
            self.last_cleanup = datetime.now()


class CacheManager:
    """Advanced cache manager for analysis results and incremental analysis."""
    
    def __init__(
        self, 
        cache_dir: Optional[Path] = None,
        ttl_hours: int = 24,
        max_cache_size_mb: int = 100,
        enable_persistent_cache: bool = True
    ):
        """
        Initialize the cache manager.
        
        Args:
            cache_dir: Directory to store persistent cache files
            ttl_hours: Time-to-live for cache entries in hours
            max_cache_size_mb: Maximum cache size in megabytes
            enable_persistent_cache: Whether to enable persistent disk cache
        """
        self.cache_dir = cache_dir or Path.home() / ".code_quality_agent" / "cache"
        self.ttl_hours = ttl_hours
        self.max_cache_size_mb = max_cache_size_mb
        self.enable_persistent_cache = enable_persistent_cache
        
        # In-memory caches
        self._file_cache: Dict[str, FileCache] = {}
        self._analysis_cache: Dict[str, AnalysisResult] = {}
        self._metadata = CacheMetadata()
        
        # Initialize cache directory
        if self.enable_persistent_cache:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self._load_persistent_cache()
    
    def _get_file_hash(self, file_path: Path) -> str:
        """Generate a hash for file content."""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            return hashlib.sha256(content).hexdigest()
        except Exception as e:
            logger.warning(f"Could not hash file {file_path}: {e}")
            return ""
    
    def _get_cache_key(self, path: str, options: AnalysisOptions) -> str:
        """Generate a cache key for analysis results."""
        cache_data = {
            'path': str(Path(path).resolve()),
            'options': options.to_dict(),
            'version': self._metadata.version
        }
        cache_str = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_str.encode()).hexdigest()
    
    def _is_file_changed(self, file_path: Path, cached_entry: FileCache) -> bool:
        """Check if a file has changed since it was cached."""
        try:
            current_mtime = file_path.stat().st_mtime
            current_hash = self._get_file_hash(file_path)
            
            return (
                current_mtime != cached_entry.last_modified or
                current_hash != cached_entry.content_hash
            )
        except Exception as e:
            logger.warning(f"Could not check file changes for {file_path}: {e}")
            return True  # Assume changed if we can't check
    
    def _is_cache_entry_expired(self, entry_time: datetime) -> bool:
        """Check if a cache entry has expired."""
        age = datetime.now() - entry_time
        return age.total_seconds() > (self.ttl_hours * 3600)
    
    def get_changed_files(
        self, 
        files_to_analyze: List[Path], 
        force_refresh: bool = False
    ) -> Tuple[List[Path], List[Path]]:
        """
        Identify which files have changed and need re-analysis.
        
        Args:
            files_to_analyze: List of files to check
            force_refresh: If True, treat all files as changed
            
        Returns:
            Tuple of (changed_files, unchanged_files)
        """
        if force_refresh:
            return files_to_analyze, []
        
        changed_files = []
        unchanged_files = []
        
        for file_path in files_to_analyze:
            file_key = str(file_path.resolve())
            
            if file_key in self._file_cache:
                cached_entry = self._file_cache[file_key]
                
                # Check if cache entry is expired
                if self._is_cache_entry_expired(cached_entry.analysis_timestamp):
                    changed_files.append(file_path)
                    continue
                
                # Check if file has changed
                if self._is_file_changed(file_path, cached_entry):
                    changed_files.append(file_path)
                else:
                    unchanged_files.append(file_path)
            else:
                # File not in cache, needs analysis
                changed_files.append(file_path)
        
        logger.info(f"Incremental analysis: {len(changed_files)} changed, {len(unchanged_files)} unchanged")
        return changed_files, unchanged_files
    
    def cache_file_analysis(
        self, 
        file_path: Path, 
        parsed_file: ParsedFile, 
        issues: List[Issue]
    ) -> None:
        """
        Cache the analysis results for a single file.
        
        Args:
            file_path: Path to the analyzed file
            parsed_file: Parsed file data
            issues: Issues found in the file
        """
        try:
            file_key = str(file_path.resolve())
            
            cache_entry = FileCache(
                file_path=file_key,
                last_modified=file_path.stat().st_mtime,
                content_hash=self._get_file_hash(file_path),
                parsed_file=parsed_file,
                issues=issues,
                analysis_timestamp=datetime.now()
            )
            
            self._file_cache[file_key] = cache_entry
            logger.debug(f"Cached analysis for {file_path}")
            
        except Exception as e:
            logger.warning(f"Could not cache file analysis for {file_path}: {e}")
    
    def get_cached_file_analysis(self, file_path: Path) -> Optional[Tuple[ParsedFile, List[Issue]]]:
        """
        Get cached analysis results for a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Tuple of (parsed_file, issues) or None if not cached/expired
        """
        file_key = str(file_path.resolve())
        
        if file_key not in self._file_cache:
            self._metadata.cache_misses += 1
            return None
        
        cached_entry = self._file_cache[file_key]
        
        # Check if expired
        if self._is_cache_entry_expired(cached_entry.analysis_timestamp):
            self._metadata.cache_misses += 1
            del self._file_cache[file_key]
            return None
        
        # Check if file changed
        if self._is_file_changed(file_path, cached_entry):
            self._metadata.cache_misses += 1
            del self._file_cache[file_key]
            return None
        
        self._metadata.cache_hits += 1
        return cached_entry.parsed_file, cached_entry.issues
    
    def cache_analysis_result(self, cache_key: str, result: AnalysisResult) -> None:
        """
        Cache a complete analysis result.
        
        Args:
            cache_key: Unique key for the analysis
            result: Analysis result to cache
        """
        self._analysis_cache[cache_key] = result
        self._metadata.total_entries = len(self._file_cache) + len(self._analysis_cache)
        
        if self.enable_persistent_cache:
            self._save_analysis_result_to_disk(cache_key, result)
        
        logger.debug(f"Cached analysis result with key: {cache_key}")
    
    def get_cached_analysis_result(self, cache_key: str) -> Optional[AnalysisResult]:
        """
        Get a cached analysis result.
        
        Args:
            cache_key: Unique key for the analysis
            
        Returns:
            Cached analysis result or None if not found/expired
        """
        # Check in-memory cache first
        if cache_key in self._analysis_cache:
            result = self._analysis_cache[cache_key]
            if not self._is_cache_entry_expired(result.timestamp):
                self._metadata.cache_hits += 1
                return result
            else:
                del self._analysis_cache[cache_key]
        
        # Check persistent cache
        if self.enable_persistent_cache:
            result = self._load_analysis_result_from_disk(cache_key)
            if result and not self._is_cache_entry_expired(result.timestamp):
                self._analysis_cache[cache_key] = result  # Load back to memory
                self._metadata.cache_hits += 1
                return result
        
        self._metadata.cache_misses += 1
        return None
    
    def cleanup_expired_entries(self) -> int:
        """
        Remove expired cache entries.
        
        Returns:
            Number of entries removed
        """
        removed_count = 0
        current_time = datetime.now()
        
        # Clean file cache
        expired_files = []
        for file_key, entry in self._file_cache.items():
            if self._is_cache_entry_expired(entry.analysis_timestamp):
                expired_files.append(file_key)
        
        for file_key in expired_files:
            del self._file_cache[file_key]
            removed_count += 1
        
        # Clean analysis cache
        expired_analyses = []
        for cache_key, result in self._analysis_cache.items():
            if self._is_cache_entry_expired(result.timestamp):
                expired_analyses.append(cache_key)
        
        for cache_key in expired_analyses:
            del self._analysis_cache[cache_key]
            removed_count += 1
            
            # Remove from disk cache too
            if self.enable_persistent_cache:
                self._remove_analysis_result_from_disk(cache_key)
        
        self._metadata.last_cleanup = current_time
        self._metadata.total_entries = len(self._file_cache) + len(self._analysis_cache)
        
        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} expired cache entries")
        
        return removed_count
    
    def clear_cache(self) -> None:
        """Clear all cache entries."""
        self._file_cache.clear()
        self._analysis_cache.clear()
        
        if self.enable_persistent_cache:
            # Remove all cache files
            for cache_file in self.cache_dir.glob("*.cache"):
                try:
                    cache_file.unlink()
                except Exception as e:
                    logger.warning(f"Could not remove cache file {cache_file}: {e}")
        
        self._metadata = CacheMetadata()
        logger.info("Cache cleared")
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get detailed cache statistics."""
        # Calculate cache size
        cache_size_mb = 0
        if self.enable_persistent_cache:
            try:
                cache_size_mb = sum(
                    f.stat().st_size for f in self.cache_dir.glob("*.cache")
                ) / (1024 * 1024)
            except Exception:
                cache_size_mb = 0
        
        hit_rate = 0.0
        total_requests = self._metadata.cache_hits + self._metadata.cache_misses
        if total_requests > 0:
            hit_rate = (self._metadata.cache_hits / total_requests) * 100
        
        return {
            'file_cache_entries': len(self._file_cache),
            'analysis_cache_entries': len(self._analysis_cache),
            'total_entries': self._metadata.total_entries,
            'cache_hits': self._metadata.cache_hits,
            'cache_misses': self._metadata.cache_misses,
            'hit_rate_percent': hit_rate,
            'cache_size_mb': cache_size_mb,
            'max_cache_size_mb': self.max_cache_size_mb,
            'ttl_hours': self.ttl_hours,
            'persistent_cache_enabled': self.enable_persistent_cache,
            'last_cleanup': self._metadata.last_cleanup.isoformat() if isinstance(self._metadata.last_cleanup, datetime) else str(self._metadata.last_cleanup),
            'created_at': self._metadata.created_at.isoformat() if isinstance(self._metadata.created_at, datetime) else str(self._metadata.created_at)
        }
    
    def _save_analysis_result_to_disk(self, cache_key: str, result: AnalysisResult) -> None:
        """Save analysis result to persistent cache."""
        try:
            cache_file = self.cache_dir / f"{cache_key}.cache"
            with open(cache_file, 'wb') as f:
                pickle.dump(result, f)
        except Exception as e:
            logger.warning(f"Could not save analysis result to disk: {e}")
    
    def _load_analysis_result_from_disk(self, cache_key: str) -> Optional[AnalysisResult]:
        """Load analysis result from persistent cache."""
        try:
            cache_file = self.cache_dir / f"{cache_key}.cache"
            if cache_file.exists():
                with open(cache_file, 'rb') as f:
                    return pickle.load(f)
        except Exception as e:
            logger.warning(f"Could not load analysis result from disk: {e}")
        return None
    
    def _remove_analysis_result_from_disk(self, cache_key: str) -> None:
        """Remove analysis result from persistent cache."""
        try:
            cache_file = self.cache_dir / f"{cache_key}.cache"
            if cache_file.exists():
                cache_file.unlink()
        except Exception as e:
            logger.warning(f"Could not remove analysis result from disk: {e}")
    
    def _load_persistent_cache(self) -> None:
        """Load cache metadata and entries from disk."""
        try:
            metadata_file = self.cache_dir / "metadata.json"
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    data = json.load(f)
                    self._metadata = CacheMetadata(**data)
        except Exception as e:
            logger.warning(f"Could not load cache metadata: {e}")
    
    def _save_persistent_cache(self) -> None:
        """Save cache metadata to disk."""
        if not self.enable_persistent_cache:
            return
            
        try:
            metadata_file = self.cache_dir / "metadata.json"
            with open(metadata_file, 'w') as f:
                # Convert datetime objects to ISO format for JSON serialization
                metadata_dict = asdict(self._metadata)
                
                # Safely convert datetime objects to ISO format
                if isinstance(self._metadata.created_at, datetime):
                    metadata_dict['created_at'] = self._metadata.created_at.isoformat()
                elif isinstance(self._metadata.created_at, str):
                    metadata_dict['created_at'] = self._metadata.created_at
                else:
                    metadata_dict['created_at'] = datetime.now().isoformat()
                
                if isinstance(self._metadata.last_cleanup, datetime):
                    metadata_dict['last_cleanup'] = self._metadata.last_cleanup.isoformat()
                elif isinstance(self._metadata.last_cleanup, str):
                    metadata_dict['last_cleanup'] = self._metadata.last_cleanup
                else:
                    metadata_dict['last_cleanup'] = datetime.now().isoformat()
                
                json.dump(metadata_dict, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save cache metadata: {e}")
    
    def __del__(self):
        """Save persistent cache on destruction."""
        if self.enable_persistent_cache:
            self._save_persistent_cache()