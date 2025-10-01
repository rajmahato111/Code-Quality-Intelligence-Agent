#!/usr/bin/env python3
"""User model definition."""

from datetime import datetime
from typing import Optional

class User:
    """User model class."""
    
    def __init__(self, username: str, email: str, user_id: Optional[int] = None):
        """Initialize user."""
        self.user_id = user_id
        self.username = username
        self.email = email
        self.created_at = datetime.now()
        self.is_active = True
    
    def to_dict(self) -> dict:
        """Convert user to dictionary."""
        return {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat(),
            'is_active': self.is_active
        }
    
    def __str__(self) -> str:
        """String representation of user."""
        return f"User(id={self.user_id}, username={self.username})"