#!/usr/bin/env python3
"""User service layer."""

from typing import List, Optional
from models.user import User
from utils.database import DatabaseManager
from utils.auth import AuthenticationService

class UserService:
    """User business logic service."""
    
    def __init__(self, db_manager: DatabaseManager, auth_service: AuthenticationService):
        """Initialize user service."""
        self.db = db_manager
        self.auth = auth_service
    
    def create_user(self, user: User, password: str = "default123") -> int:
        """Create a new user."""
        # Hash password
        password_hash, salt = self.auth.hash_password(password)
        
        # Insert user into database
        query = """
        INSERT INTO users (username, email, password_hash, salt, created_at, is_active)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        params = (
            user.username,
            user.email,
            password_hash,
            salt,
            user.created_at.isoformat(),
            user.is_active
        )
        
        return self.db.execute_update(query, params)
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        query = "SELECT * FROM users WHERE user_id = ?"
        users = self.db.execute_query(query, (user_id,))
        
        if users:
            user_data = users[0]
            return User(
                username=user_data['username'],
                email=user_data['email'],
                user_id=user_data['user_id']
            )
        
        return None
    
    def get_all_users(self) -> List[User]:
        """Get all users."""
        query = "SELECT * FROM users WHERE is_active = 1"
        users_data = self.db.execute_query(query)
        
        users = []
        for user_data in users_data:
            user = User(
                username=user_data['username'],
                email=user_data['email'],
                user_id=user_data['user_id']
            )
            users.append(user)
        
        return users
    
    def update_user(self, user: User) -> bool:
        """Update user information."""
        query = """
        UPDATE users 
        SET username = ?, email = ?, is_active = ?
        WHERE user_id = ?
        """
        params = (user.username, user.email, user.is_active, user.user_id)
        
        rows_affected = self.db.execute_update(query, params)
        return rows_affected > 0
    
    def delete_user(self, user_id: int) -> bool:
        """Soft delete user (mark as inactive)."""
        query = "UPDATE users SET is_active = 0 WHERE user_id = ?"
        rows_affected = self.db.execute_update(query, (user_id,))
        return rows_affected > 0