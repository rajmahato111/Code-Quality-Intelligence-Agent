"""
Backend API server with intentional quality issues for testing.
"""

from flask import Flask, request, jsonify
import sqlite3
import hashlib

app = Flask(__name__)

# Security issue: hardcoded secret
app.secret_key = "hardcoded_secret_123"

# Performance issue: global database connection
db_conn = sqlite3.connect('app.db', check_same_thread=False)

@app.route('/api/users', methods=['GET'])
def get_users():
    """Get all users."""
    # SQL injection vulnerability
    search = request.args.get('search', '')
    query = f"SELECT * FROM users WHERE name LIKE '%{search}%'"
    
    cursor = db_conn.cursor()
    cursor.execute(query)
    users = cursor.fetchall()
    
    return jsonify(users)

@app.route('/api/login', methods=['POST'])
def login():
    """User login endpoint."""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    # Weak password hashing
    hashed_password = hashlib.md5(password.encode()).hexdigest()
    
    # SQL injection vulnerability
    query = f"SELECT id FROM users WHERE username = '{username}' AND password = '{hashed_password}'"
    cursor = db_conn.cursor()
    cursor.execute(query)
    user = cursor.fetchone()
    
    if user:
        return jsonify({'status': 'success', 'user_id': user[0]})
    else:
        return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 401

# Missing documentation
def process_data(data):
    result = []
    for item in data:
        if item > 0:
            result.append(item * 2)
    return result

# High complexity function
def complex_business_logic(user_data, permissions, settings, context):
    """Complex business logic with high cyclomatic complexity."""
    if user_data:
        if user_data.get('active'):
            if permissions:
                if permissions.get('read'):
                    if settings:
                        if settings.get('enabled'):
                            if context:
                                if context.get('valid'):
                                    return True
    return False

if __name__ == '__main__':
    # Debug mode in production
    app.run(debug=True, host='0.0.0.0')