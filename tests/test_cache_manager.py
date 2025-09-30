"""Tests for the CacheManager class."""

import tempfile
import time
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from code_quality_agent.core.cache_manager import CacheManager, FileCache, CacheMetadata
from code_quality_agent.core.models import (
    AnalysisResult, AnalysisOptions, ParsedFile, Issue, IssueCategory, 
    Severity, CodeLocation
)


class TestCacheManager:
    """Test cases for CacheManager."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.cache_manager = CacheManager(
            cache_dir=self.temp_dir / "cache",
            ttl_hours=1,  # Short TTL for testing
            enable_persistent_cache=False  # Disable for most tests
        )
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initialization(self):
        """Test cache manager initialization."""
        assert self.cache_manager.cache_dir.exists()
        assert self.cache_manager.ttl_hours == 1
        assert not self.cache_manager.enable_persistent_cache
        assert len(self.cache_manager._file_cache) == 0
        assert len(self.cache_manager._analysis_cache) == 0
    
    def test_file_hash_generation(self):
        """Test file hash generation."""
        # Create a test file
        test_file = self.temp_dir / "test.py"
        test_file.write_text("print('hello world')")
        
        hash1 = self.cache_manager._get_file_hash(test_file)
        assert hash1 != ""
        assert len(hash1) == 64  # SHA256 hash length
        
        # Same content should produce same hash
        hash2 = self.cache_manager._get_file_hash(test_file)
        assert hash1 == hash2
        
        # Different content should produce different hash
        test_file.write_text("print('hello universe')")
        hash3 = self.cache_manager._get_file_hash(test_file)
        assert hash1 != hash3
    
    def test_cache_key_generation(self):
        """Test cache key generation."""
        options = AnalysisOptions()
        
        key1 = self.cache_manager._get_cache_key("/test/path", options)
        key2 = self.cache_manager._get_cache_key("/test/path", options)
        
        assert key1 == key2  # Same inputs should produce same key
        assert len(key1) == 32  # MD5 hash length
        
        # Different paths should produce different keys
        key3 = self.cache_manager._get_cache_key("/different/path", options)
        assert key1 != key3
        
        # Different options should produce different keys
        options2 = AnalysisOptions(parallel_processing=False)
        key4 = self.cache_manager._get_cache_key("/test/path", options2)
        assert key1 != key4
    
    def test_file_change_detection(self):
        """Test file change detection."""
        # Create a test file
        test_file = self.temp_dir / "test.py"
        test_file.write_text("print('hello')")
        
        # Create cache entry
        cache_entry = FileCache(
            file_path=str(test_file),
            last_modified=test_file.stat().st_mtime,
            content_hash=self.cache_manager._get_file_hash(test_file)
        )
        
        # File should not be detected as changed
        assert not self.cache_manager._is_file_changed(test_file, cache_entry)
        
        # Modify file content
        time.sleep(0.1)  # Ensure different timestamp
        test_file.write_text("print('hello world')")
        
        # File should now be detected as changed
        assert self.cache_manager._is_file_changed(test_file, cache_entry)
    
    def test_cache_expiration(self):
        """Test cache entry expiration."""
        # Recent entry should not be expired
        recent_time = datetime.now()
        assert not self.cache_manager._is_cache_entry_expired(recent_time)
        
        # Old entry should be expired
        old_time = datetime.now() - timedelta(hours=2)  # TTL is 1 hour
        assert self.cache_manager._is_cache_entry_expired(old_time)
    
    def test_changed_files_detection(self):
        """Test detection of changed vs unchanged files."""
        # Create test files
        file1 = self.temp_dir / "file1.py"
        file2 = self.temp_dir / "file2.py"
        file3 = self.temp_dir / "file3.py"
        
        file1.write_text("print('file1')")
        file2.write_text("print('file2')")
        file3.write_text("print('file3')")
        
        files_to_analyze = [file1, file2, file3]
        
        # First run - all files should be changed (not in cache)
        changed, unchanged = self.cache_manager.get_changed_files(files_to_analyze)
        assert len(changed) == 3
        assert len(unchanged) == 0
        
        # Cache the files
        for file_path in files_to_analyze:
            parsed_file = ParsedFile(
                path=str(file_path),
                language="python",
                content=file_path.read_text()
            )
            self.cache_manager.cache_file_analysis(file_path, parsed_file, [])
        
        # Second run - all files should be unchanged
        changed, unchanged = self.cache_manager.get_changed_files(files_to_analyze)
        assert len(changed) == 0
        assert len(unchanged) == 3
        
        # Modify one file
        time.sleep(0.1)
        file2.write_text("print('file2 modified')")
        
        # Third run - one file should be changed
        changed, unchanged = self.cache_manager.get_changed_files(files_to_analyze)
        assert len(changed) == 1
        assert len(unchanged) == 2
        assert file2 in changed
    
    def test_force_refresh(self):
        """Test force refresh functionality."""
        # Create and cache a file
        test_file = self.temp_dir / "test.py"
        test_file.write_text("print('hello')")
        
        parsed_file = ParsedFile(
            path=str(test_file),
            language="python",
            content=test_file.read_text()
        )
        self.cache_manager.cache_file_analysis(test_file, parsed_file, [])
        
        # Without force refresh, file should be unchanged
        changed, unchanged = self.cache_manager.get_changed_files([test_file])
        assert len(unchanged) == 1
        
        # With force refresh, file should be changed
        changed, unchanged = self.cache_manager.get_changed_files([test_file], force_refresh=True)
        assert len(changed) == 1
        assert len(unchanged) == 0
    
    def test_file_analysis_caching(self):
        """Test caching and retrieval of file analysis results."""
        test_file = self.temp_dir / "test.py"
        test_file.write_text("print('hello')")
        
        # Create test data
        parsed_file = ParsedFile(
            path=str(test_file),
            language="python",
            content=test_file.read_text()
        )
        
        test_issue = Issue(
            id="test-issue",
            category=IssueCategory.SECURITY,
            severity=Severity.MEDIUM,
            title="Test issue",
            description="Test description",
            location=CodeLocation(str(test_file), 1, 1),
            affected_files=[str(test_file)],
            suggestion="Fix this",
            confidence=0.8
        )
        
        # Cache the analysis
        self.cache_manager.cache_file_analysis(test_file, parsed_file, [test_issue])
        
        # Retrieve from cache
        cached_result = self.cache_manager.get_cached_file_analysis(test_file)
        assert cached_result is not None
        
        cached_parsed_file, cached_issues = cached_result
        assert cached_parsed_file.path == str(test_file)
        assert len(cached_issues) == 1
        assert cached_issues[0].title == "Test issue"
    
    def test_analysis_result_caching(self):
        """Test caching and retrieval of complete analysis results."""
        # Create test analysis result
        result = AnalysisResult(
            analysis_id="test-analysis",
            codebase_path="/test/path",
            issues=[],
            timestamp=datetime.now()
        )
        
        cache_key = "test-cache-key"
        
        # Cache the result
        self.cache_manager.cache_analysis_result(cache_key, result)
        
        # Retrieve from cache
        cached_result = self.cache_manager.get_cached_analysis_result(cache_key)
        assert cached_result is not None
        assert cached_result.analysis_id == "test-analysis"
        assert cached_result.codebase_path == "/test/path"
    
    def test_cache_cleanup(self):
        """Test cleanup of expired cache entries."""
        # Create test files and cache them
        test_file = self.temp_dir / "test.py"
        test_file.write_text("print('hello')")
        
        parsed_file = ParsedFile(
            path=str(test_file),
            language="python",
            content=test_file.read_text()
        )
        
        # Cache with old timestamp (expired)
        old_cache_entry = FileCache(
            file_path=str(test_file),
            last_modified=test_file.stat().st_mtime,
            content_hash=self.cache_manager._get_file_hash(test_file),
            parsed_file=parsed_file,
            issues=[],
            analysis_timestamp=datetime.now() - timedelta(hours=2)  # Expired
        )
        
        self.cache_manager._file_cache[str(test_file)] = old_cache_entry
        
        # Add expired analysis result
        old_result = AnalysisResult(
            analysis_id="old-analysis",
            timestamp=datetime.now() - timedelta(hours=2)  # Expired
        )
        self.cache_manager._analysis_cache["old-key"] = old_result
        
        # Verify entries exist
        assert len(self.cache_manager._file_cache) == 1
        assert len(self.cache_manager._analysis_cache) == 1
        
        # Run cleanup
        removed_count = self.cache_manager.cleanup_expired_entries()
        
        # Verify expired entries were removed
        assert removed_count == 2
        assert len(self.cache_manager._file_cache) == 0
        assert len(self.cache_manager._analysis_cache) == 0
    
    def test_cache_statistics(self):
        """Test cache statistics generation."""
        # Initially empty cache
        stats = self.cache_manager.get_cache_statistics()
        assert stats['file_cache_entries'] == 0
        assert stats['analysis_cache_entries'] == 0
        assert stats['cache_hits'] == 0
        assert stats['cache_misses'] == 0
        
        # Add some cache entries
        test_file = self.temp_dir / "test.py"
        test_file.write_text("print('hello')")
        
        parsed_file = ParsedFile(
            path=str(test_file),
            language="python",
            content=test_file.read_text()
        )
        
        self.cache_manager.cache_file_analysis(test_file, parsed_file, [])
        
        result = AnalysisResult(analysis_id="test")
        self.cache_manager.cache_analysis_result("test-key", result)
        
        # Check updated statistics
        stats = self.cache_manager.get_cache_statistics()
        assert stats['file_cache_entries'] == 1
        assert stats['analysis_cache_entries'] == 1
        
        # Test cache hit
        self.cache_manager.get_cached_file_analysis(test_file)
        stats = self.cache_manager.get_cache_statistics()
        assert stats['cache_hits'] == 1
        
        # Test cache miss
        nonexistent_file = self.temp_dir / "nonexistent.py"
        self.cache_manager.get_cached_file_analysis(nonexistent_file)
        stats = self.cache_manager.get_cache_statistics()
        assert stats['cache_misses'] == 1
    
    def test_cache_clear(self):
        """Test clearing all cache entries."""
        # Add some cache entries
        test_file = self.temp_dir / "test.py"
        test_file.write_text("print('hello')")
        
        parsed_file = ParsedFile(
            path=str(test_file),
            language="python",
            content=test_file.read_text()
        )
        
        self.cache_manager.cache_file_analysis(test_file, parsed_file, [])
        
        result = AnalysisResult(analysis_id="test")
        self.cache_manager.cache_analysis_result("test-key", result)
        
        # Verify entries exist
        assert len(self.cache_manager._file_cache) == 1
        assert len(self.cache_manager._analysis_cache) == 1
        
        # Clear cache
        self.cache_manager.clear_cache()
        
        # Verify cache is empty
        assert len(self.cache_manager._file_cache) == 0
        assert len(self.cache_manager._analysis_cache) == 0
    
    def test_persistent_cache_disabled(self):
        """Test behavior when persistent cache is disabled."""
        # This is already the default for our test setup
        assert not self.cache_manager.enable_persistent_cache
        
        # Cache operations should still work in memory
        result = AnalysisResult(analysis_id="test")
        self.cache_manager.cache_analysis_result("test-key", result)
        
        cached_result = self.cache_manager.get_cached_analysis_result("test-key")
        assert cached_result is not None
        assert cached_result.analysis_id == "test"


class TestPersistentCache:
    """Test cases for persistent cache functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.cache_manager = CacheManager(
            cache_dir=self.temp_dir / "cache",
            ttl_hours=24,
            enable_persistent_cache=True  # Enable for these tests
        )
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_persistent_cache_enabled(self):
        """Test persistent cache functionality."""
        assert self.cache_manager.enable_persistent_cache
        
        # Create and cache an analysis result
        result = AnalysisResult(
            analysis_id="persistent-test",
            codebase_path="/test/path"
        )
        
        cache_key = "persistent-key"
        self.cache_manager.cache_analysis_result(cache_key, result)
        
        # Verify cache file was created
        cache_files = list(self.cache_manager.cache_dir.glob("*.cache"))
        assert len(cache_files) == 1
        
        # Create new cache manager (simulating restart)
        new_cache_manager = CacheManager(
            cache_dir=self.temp_dir / "cache",
            ttl_hours=24,
            enable_persistent_cache=True
        )
        
        # Should be able to load from persistent cache
        cached_result = new_cache_manager.get_cached_analysis_result(cache_key)
        assert cached_result is not None
        assert cached_result.analysis_id == "persistent-test"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__])