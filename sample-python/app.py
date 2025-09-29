#!/usr/bin/env python3
"""
Sample Python Application - Web UI Test
This file contains various security and quality issues for web UI demonstration
"""

import os
import sqlite3
import hashlib
import pickle
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# SECURITY ISSUE: Hardcoded secret key
app.secret_key = "super-secret-key-123"

# SECURITY ISSUE: Hardcoded database credentials
DATABASE_URL = "postgresql://admin:password123@localhost/mydb"
API_KEY = "sk-1234567890abcdef"

class UserManager:
    """User management with security vulnerabilities."""
    
    def __init__(self):
        self.db_path = "users.db"
    
    # SECURITY ISSUE: SQL Injection vulnerability
    def get_user(self, user_id):
        """Get user by ID - vulnerable to SQL injection."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Vulnerable query - allows SQL injection
        query = f"SELECT * FROM users WHERE id = '{user_id}'"
        cursor.execute(query)
        
        result = cursor.fetchone()
        conn.close()
        return result
    
    # SECURITY ISSUE: Weak password hashing
    def hash_password(self, password):
        """Hash password using weak MD5."""
        return hashlib.md5(password.encode()).hexdigest()
    
    # SECURITY ISSUE: Unsafe deserialization
    def load_user_data(self, serialized_data):
        """Load user data from pickle - unsafe."""
        return pickle.loads(serialized_data)

@app.route('/api/users/<user_id>')
def api_get_user(user_id):
    """API endpoint to get user - has security issues."""
    user_manager = UserManager()
    
    # SECURITY ISSUE: No input validation
    user = user_manager.get_user(user_id)
    
    if user:
        return jsonify({
            'id': user[0],
            'username': user[1],
            'email': user[2]
        })
    else:
        return jsonify({'error': 'User not found'}), 404

# SECURITY ISSUE: Command injection vulnerability
@app.route('/api/backup')
def backup_database():
    """Backup database - vulnerable to command injection."""
    filename = request.args.get('filename', 'backup.sql')
    
    # Vulnerable to command injection
    os.system(f"mysqldump mydb > {filename}")
    
    return jsonify({'message': f'Backup created: {filename}'})

# PERFORMANCE ISSUE: Inefficient algorithm
def find_duplicates(data):
    """Find duplicates with O(n²) complexity."""
    duplicates = []
    
    # Inefficient nested loops
    for i in range(len(data)):
        for j in range(i + 1, len(data)):
            if data[i] == data[j]:
                duplicates.append(data[i])
    
    return duplicates

# COMPLEXITY ISSUE: High cyclomatic complexity
def process_user_request(user, request_type, permissions, settings):
    """Process user request with high complexity."""
    
    if user:
        if user.get('active'):
            if user.get('verified'):
                if request_type == 'data_access':
                    if permissions:
                        if permissions.get('read_data'):
                            if settings:
                                if settings.get('data_access_enabled'):
                                    if user.get('role') == 'admin':
                                        return {'status': 'success', 'data': 'admin_data'}
                                    elif user.get('role') == 'user':
                                        if permissions.get('read_own_data'):
                                            return {'status': 'success', 'data': 'user_data'}
                                        else:
                                            return {'status': 'error', 'message': 'Insufficient permissions'}
                                    else:
                                        return {'status': 'error', 'message': 'Unknown role'}
                                else:
                                    return {'status': 'error', 'message': 'Data access disabled'}
                            else:
                                return {'status': 'error', 'message': 'No settings'}
                        else:
                            return {'status': 'error', 'message': 'No read permission'}
                    else:
                        return {'status': 'error', 'message': 'No permissions'}
                else:
                    return {'status': 'error', 'message': 'Unknown request type'}
            else:
                return {'status': 'error', 'message': 'User not verified'}
        else:
            return {'status': 'error', 'message': 'User not active'}
    else:
        return {'status': 'error', 'message': 'No user provided'}

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')  # SECURITY ISSUE: Debug mode in production