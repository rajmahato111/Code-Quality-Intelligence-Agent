#!/usr/bin/env python3
"""
Database Models - Sample Python Application
Contains various code quality issues for demonstration
"""

import datetime
from typing import Optional, List

class User:
    """User model with documentation issues."""
    
    def __init__(self, username, email, password):
        # DOCUMENTATION ISSUE: Missing docstring
        self.username = username
        self.email = email
        self.password = password
        self.created_at = datetime.datetime.now()
        self.is_active = True
    
    def validate_email(self, email):
        # DOCUMENTATION ISSUE: Missing docstring and type hints
        return '@' in email and '.' in email
    
    # DOCUMENTATION ISSUE: Missing docstring
    def get_display_name(self):
        return f"{self.username} ({self.email})"

class Product:
    """Product model with complexity issues."""
    
    def __init__(self, name: str, price: float, category: str):
        """Initialize product."""
        self.name = name
        self.price = price
        self.category = category
        self.inventory = 0
        self.reviews = []
    
    # COMPLEXITY ISSUE: Long parameter list
    def update_product(self, name, price, category, description, weight, 
                      dimensions, color, material, brand, manufacturer):
        """Update product with many parameters."""
        self.name = name
        self.price = price
        self.category = category
        self.description = description
        self.weight = weight
        self.dimensions = dimensions
        self.color = color
        self.material = material
        self.brand = brand
        self.manufacturer = manufacturer
    
    # PERFORMANCE ISSUE: Inefficient calculation
    def calculate_average_rating(self):
        """Calculate average rating inefficiently."""
        if not self.reviews:
            return 0
        
        total = 0
        count = 0
        
        # Inefficient: multiple iterations
        for review in self.reviews:
            if review.get('rating'):
                total += review['rating']
                count += 1
        
        # Another iteration to validate
        for review in self.reviews:
            if review.get('rating') < 1 or review.get('rating') > 5:
                return 0  # Invalid rating found
        
        return total / count if count > 0 else 0

class Order:
    """Order model with duplication issues."""
    
    def __init__(self, user_id: int, products: List[dict]):
        """Initialize order."""
        self.user_id = user_id
        self.products = products
        self.total = 0
        self.status = 'pending'
        self.created_at = datetime.datetime.now()
    
    # DUPLICATION: Similar calculation logic
    def calculate_subtotal(self):
        """Calculate order subtotal."""
        subtotal = 0
        for product in self.products:
            subtotal += product['price'] * product['quantity']
        return subtotal
    
    # DUPLICATION: Similar calculation logic
    def calculate_tax(self):
        """Calculate order tax."""
        subtotal = 0
        for product in self.products:
            subtotal += product['price'] * product['quantity']
        return subtotal * 0.08  # 8% tax
    
    # DUPLICATION: Similar calculation logic
    def calculate_total(self):
        """Calculate order total."""
        subtotal = 0
        for product in self.products:
            subtotal += product['price'] * product['quantity']
        tax = subtotal * 0.08
        return subtotal + tax

# TESTING ISSUE: No test coverage for any of these classes