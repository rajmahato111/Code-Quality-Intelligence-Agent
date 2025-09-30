"""
Synthetic Python code samples with known security issues.
These samples are designed to test security analyzers.
"""

import os
import subprocess
import pickle
import sqlite3
from flask import Flask, request

app = Flask(__name__)

# SECURITY ISSUE: Hardcoded credentials
DATABASE_PASSWORD = "admin123"
API_SECRET_KEY = "sk-1234567890abcdef"
AWS_ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"

# SECURITY ISSUE: SQL Injection vulnerability
def get_user_by_id(user_id):
    """Vulnerable to SQL injection."""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    # Vulnerable: Direct string interpolation
    query = f"SELECT * FROM users WHERE id = {user_id}"
    cursor.execute(query)
    return cursor.fetchone()

# SECURITY ISSUE: Command injection vulnerability
def execute_system_command(filename):
    """Vulnerable to command injection."""
    # Vulnerable: shell=True with user input
    result = subprocess.run(f"cat {filename}", shell=True, capture_output=True)
    return result.stdout

# SECURITY ISSUE: Unsafe deserialization
def load_user_data(data):
    """Vulnerable to pickle deserialization attacks."""
    # Vulnerable: pickle.loads with untrusted data
    return pickle.loads(data)

# SECURITY ISSUE: XSS vulnerability in web route
@app.route('/search')
def search():
    """Vulnerable to XSS attacks."""
    query = request.args.get('q', '')
    # Vulnerable: Direct output without escaping
    return f"<h1>Search results for: {query}</h1>"

# SECURITY ISSUE: Path traversal vulnerability
def read_file(filename):
    """Vulnerable to path traversal attacks."""
    # Vulnerable: No path validation
    with open(f"/var/www/uploads/{filename}", 'r') as f:
        return f.read()

# SECURITY ISSUE: Weak random number generation
import random

def generate_session_token():
    """Weak random number generation for security tokens."""
    # Vulnerable: Using predictable random
    return str(random.randint(100000, 999999))

# SECURITY ISSUE: Insecure hash function
import hashlib

def hash_password(password):
    """Using insecure hash function."""
    # Vulnerable: MD5 is cryptographically broken
    return hashlib.md5(password.encode()).hexdigest()

# SECURITY ISSUE: Debug mode enabled in production
if __name__ == '__main__':
    # Vulnerable: Debug mode should not be enabled in production
    app.run(debug=True, host='0.0.0.0')

# SECURITY ISSUE: Eval usage
def calculate_expression(expr):
    """Dangerous use of eval function."""
    # Vulnerable: eval with user input
    return eval(expr)

# SECURITY ISSUE: Insecure file permissions
def create_config_file():
    """Creates file with insecure permissions."""
    with open('/tmp/config.txt', 'w') as f:
        f.write("sensitive_data=secret")
    # Vulnerable: World-readable file with sensitive data
    os.chmod('/tmp/config.txt', 0o777)