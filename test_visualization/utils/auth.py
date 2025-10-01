#!/usr/bin/env python3
"""Authentication utilities."""

import hashlib
import secrets
from typing import Optional
from utils.database import DatabaseManager

class AuthenticationService:
    """Authentication and authorization service."""
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize authentication service."""
        self.db = db_manager
        self.salt_length = 32
    
    def hash_password(self, password: str, salt: Optional[str] = None) -> tuple:
        """Hash password with salt."""
        if salt is None:
            salt = secrets.token_hex(self.salt_length)
        
        # Combine password and salt
        password_salt = password + salt
        
        # Hash using SHA-256
        hashed = hashlib.sha256(password_salt.encode()).hexdigest()
        
        return hashed, salt
    
    def verify_password(self, password: str, hashed_password: str, salt: str) -> bool:
        """Verify password against hash."""
        test_hash, _ = self.hash_password(password, salt)
        return test_hash == hashed_password
    
    def authenticate_user(self, username: str, password: str) -> Optional[dict]:
        """Authenticate user credentials."""
        query = "SELECT * FROM users WHERE username = ?"
        users = self.db.execute_query(query, (username,))
        
        if not users:
            return None
        
        user = users[0]
        if self.verify_password(password, user['password_hash'], user['salt']):
            return user
        
        return None
    
    def generate_session_token(self) -> str:
        """Generate secure session token."""
        return secrets.token_urlsafe(64)