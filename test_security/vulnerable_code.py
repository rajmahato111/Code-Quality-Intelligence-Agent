#!/usr/bin/env python3
"""
Test file with security vulnerabilities for testing the code quality agent.
"""

import os
import subprocess

# Hard-coded secrets (security vulnerability)
API_KEY = "sk-1234567890abcdef1234567890abcdef"
DATABASE_PASSWORD = "admin123"
SECRET_TOKEN = "ghp_1234567890abcdef1234567890abcdef123456"
AWS_ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"
AWS_SECRET_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

def dangerous_eval_function(user_input):
    """Function that uses eval() - major security risk"""
    # Using eval() with user input (security vulnerability)
    result = eval(user_input)
    return result

def execute_command(command):
    """Function that executes shell commands unsafely"""
    # Command injection vulnerability
    os.system(command)
    
def unsafe_subprocess(user_command):
    """Unsafe subprocess execution"""
    # Shell injection vulnerability
    subprocess.call(user_command, shell=True)

def sql_injection_risk(user_id):
    """SQL injection vulnerability"""
    query = f"SELECT * FROM users WHERE id = {user_id}"
    # This would be executed unsafely
    return query

def hardcoded_credentials():
    """Function with hardcoded credentials"""
    username = "admin"
    password = "password123"
    connection_string = f"mysql://admin:password123@localhost/db"
    return connection_string

def weak_crypto():
    """Weak cryptographic practices"""
    import hashlib
    # Using MD5 (weak hash)
    weak_hash = hashlib.md5(b"password").hexdigest()
    return weak_hash

class UnsafeClass:
    """Class with security issues"""
    
    def __init__(self):
        self.secret = "my_secret_key_123"
        self.api_token = "Bearer abc123def456"
    
    def process_data(self, data):
        # Using eval in class method
        return eval(f"len('{data}')")
    
    def debug_info(self):
        # Potential information disclosure
        return {
            'secret': self.secret,
            'token': self.api_token,
            'env_vars': dict(os.environ)
        }

if __name__ == "__main__":
    # Dangerous usage examples
    user_input = input("Enter expression: ")
    result = dangerous_eval_function(user_input)
    print(f"Result: {result}")
    
    # Execute user command
    cmd = input("Enter command: ")
    execute_command(cmd)