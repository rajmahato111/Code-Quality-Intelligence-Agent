#!/usr/bin/env python3
"""Test file with critical security and quality issues for Q&A testing."""

import os
import subprocess
import hashlib
import sqlite3

# CRITICAL: Hardcoded credentials
API_SECRET = "sk-1234567890abcdef"
DB_PASSWORD = "admin123"
JWT_SECRET = "my-secret-key"

class VulnerableApp:
    """Application with multiple critical security vulnerabilities."""
    
    def __init__(self):
        self.db_connection = None
        
    # CRITICAL: SQL Injection vulnerability
    def get_user(self, user_id):
        """Get user by ID - VULNERABLE to SQL injection."""
        query = f"SELECT * FROM users WHERE id = '{user_id}'"
        cursor = self.db_connection.execute(query)
        return cursor.fetchone()
    
    # CRITICAL: Command injection vulnerability
    def process_file(self, filename):
        """Process file - VULNERABLE to command injection."""
        os.system(f"cat {filename}")
        
    # CRITICAL: Path traversal vulnerability
    def read_config(self, config_name):
        """Read config file - VULNERABLE to path traversal."""
        with open(f"/app/config/{config_name}", 'r') as f:
            return f.read()
    
    # CRITICAL: Unsafe deserialization
    def load_data(self, data):
        """Load serialized data - VULNERABLE to code execution."""
        import pickle
        return pickle.loads(data)
    
    # CRITICAL: Weak password hashing
    def hash_password(self, password):
        """Hash password using weak algorithm."""
        return hashlib.md5(password.encode()).hexdigest()

# CRITICAL: No input validation
def execute_command(cmd):
    """Execute system command without validation."""
    return subprocess.run(cmd, shell=True, capture_output=True)

# CRITICAL: Information disclosure
def debug_info():
    """Return sensitive debug information."""
    return {
        'database_password': DB_PASSWORD,
        'api_key': API_SECRET,
        'system_info': os.environ
    }

# CRITICAL: Insecure random number generation
def generate_token():
    """Generate security token using weak randomness."""
    import random
    return str(random.randint(1000000, 9999999))

# CRITICAL: Missing authentication
def admin_panel(request):
    """Admin panel without authentication check."""
    if request.path == '/admin':
        return "Welcome to admin panel!"
    
# CRITICAL: Buffer overflow potential (in Python context)
def process_large_data(data):
    """Process data without size limits."""
    result = ""
    for i in range(len(data) * 1000000):  # Potential memory exhaustion
        result += str(i)
    return result