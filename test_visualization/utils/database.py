#!/usr/bin/env python3
"""Database management utilities."""

import sqlite3
import logging
from typing import Any, List, Dict

class DatabaseManager:
    """Database connection and query manager."""
    
    def __init__(self, db_path: str):
        """Initialize database manager."""
        self.db_path = db_path
        self.connection = None
        self.logger = logging.getLogger(__name__)
        self._connect()
    
    def _connect(self):
        """Establish database connection."""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row
            self.logger.info(f"Connected to database: {self.db_path}")
        except sqlite3.Error as e:
            self.logger.error(f"Database connection failed: {e}")
            raise
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Execute a SELECT query."""
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            self.logger.error(f"Query execution failed: {e}")
            raise
    
    def execute_update(self, query: str, params: tuple = ()) -> int:
        """Execute an INSERT/UPDATE/DELETE query."""
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            self.connection.commit()
            return cursor.rowcount
        except sqlite3.Error as e:
            self.logger.error(f"Update execution failed: {e}")
            self.connection.rollback()
            raise
    
    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            self.logger.info("Database connection closed")