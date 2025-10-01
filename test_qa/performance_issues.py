#!/usr/bin/env python3
"""Performance critical issues for testing."""

import time

class PerformanceCritical:
    """Class with critical performance issues."""
    
    def __init__(self):
        self.data = []
        
    # CRITICAL: O(n²) algorithm in hot path
    def find_duplicates(self, items):
        """Find duplicates using inefficient nested loops."""
        duplicates = []
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                if items[i] == items[j]:
                    duplicates.append(items[i])
        return duplicates
    
    # CRITICAL: Memory leak potential
    def cache_data(self, key, value):
        """Cache data without size limits."""
        if not hasattr(self, '_cache'):
            self._cache = {}
        self._cache[key] = value  # Never cleaned up
        
    # CRITICAL: Blocking I/O in main thread
    def fetch_data(self, urls):
        """Fetch data synchronously - blocks main thread."""
        results = []
        for url in urls:
            time.sleep(1)  # Simulate network delay
            results.append(f"Data from {url}")
        return results
    
    # CRITICAL: Inefficient string concatenation
    def build_report(self, items):
        """Build report using inefficient string concatenation."""
        report = ""
        for item in items:
            report += f"Item: {item}\n"  # Creates new string each time
        return report