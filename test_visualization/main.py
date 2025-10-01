#!/usr/bin/env python3
"""Main application entry point."""

from utils.database import DatabaseManager
from utils.auth import AuthenticationService
from models.user import User
from models.product import Product
from services.user_service import UserService
from services.product_service import ProductService
import logging
import sys

def main():
    """Main application function."""
    # Initialize logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize database
    db = DatabaseManager("app.db")
    
    # Initialize services
    auth_service = AuthenticationService(db)
    user_service = UserService(db, auth_service)
    product_service = ProductService(db)
    
    # Create sample user
    user = User("john_doe", "john@example.com")
    user_service.create_user(user)
    
    # Create sample product
    product = Product("laptop", 999.99)
    product_service.add_product(product)
    
    print("Application started successfully!")

if __name__ == "__main__":
    main()