#!/usr/bin/env python3
"""
Utility Functions - Sample Python Application
Various utility functions with quality issues
"""

import re
import json
import requests

# SECURITY ISSUE: Hardcoded API credentials
EXTERNAL_API_KEY = "abc123def456"
EXTERNAL_API_SECRET = "secret789xyz"

def validate_input(data):
    # DOCUMENTATION ISSUE: Missing docstring and type hints
    if not data:
        return False
    
    # COMPLEXITY ISSUE: Nested conditions
    if isinstance(data, dict):
        if 'username' in data:
            if len(data['username']) > 3:
                if re.match(r'^[a-zA-Z0-9_]+$', data['username']):
                    if 'email' in data:
                        if '@' in data['email']:
                            if '.' in data['email']:
                                return True
                            else:
                                return False
                        else:
                            return False
                    else:
                        return False
                else:
                    return False
            else:
                return False
        else:
            return False
    else:
        return False

# PERFORMANCE ISSUE: Inefficient string operations
def format_user_list(users):
    """Format user list with inefficient string concatenation."""
    result = ""
    
    # Inefficient string concatenation in loop
    for user in users:
        result += f"User: {user['name']}\n"
        result += f"Email: {user['email']}\n"
        result += f"Status: {user['status']}\n"
        result += "-" * 30 + "\n"
    
    return result

# DUPLICATION: Similar API call pattern
def fetch_user_data(user_id):
    """Fetch user data from external API."""
    url = f"https://api.example.com/users/{user_id}"
    headers = {
        'Authorization': f'Bearer {EXTERNAL_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        print(f"Error fetching user data: {e}")
        return None

# DUPLICATION: Similar API call pattern
def fetch_product_data(product_id):
    """Fetch product data from external API."""
    url = f"https://api.example.com/products/{product_id}"
    headers = {
        'Authorization': f'Bearer {EXTERNAL_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        print(f"Error fetching product data: {e}")
        return None

# DUPLICATION: Similar API call pattern
def fetch_order_data(order_id):
    """Fetch order data from external API."""
    url = f"https://api.example.com/orders/{order_id}"
    headers = {
        'Authorization': f'Bearer {EXTERNAL_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        print(f"Error fetching order data: {e}")
        return None