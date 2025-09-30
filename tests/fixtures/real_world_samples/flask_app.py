"""
Real-world Flask application sample with various quality issues.
Based on common patterns found in production applications.
"""

from flask import Flask, request, jsonify, session
import sqlite3
import hashlib
import os
import subprocess
import pickle

app = Flask(__name__)
app.secret_key = "hardcoded_secret_key_123"  # Security issue

# Global database connection (not thread-safe)
db_connection = None

def get_db_connection():
    """Get database connection."""
    global db_connection
    if db_connection is None:
        db_connection = sqlite3.connect('app.db', check_same_thread=False)
    return db_connection

@app.route('/login', methods=['POST'])
def login():
    """User login endpoint."""
    username = request.form.get('username')
    password = request.form.get('password')
    
    # SQL injection vulnerability
    conn = get_db_connection()
    cursor = conn.cursor()
    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
    cursor.execute(query)
    user = cursor.fetchone()
    
    if user:
        session['user_id'] = user[0]
        return jsonify({'status': 'success', 'message': 'Login successful'})
    else:
        return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 401

@app.route('/search')
def search():
    """Search endpoint with XSS vulnerability."""
    query = request.args.get('q', '')
    
    # XSS vulnerability - direct output without escaping
    return f"<h1>Search results for: {query}</h1>"

@app.route('/upload', methods=['POST'])
def upload_file():
    """File upload with path traversal vulnerability."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    filename = request.form.get('filename', file.filename)
    
    # Path traversal vulnerability
    filepath = os.path.join('/uploads', filename)
    file.save(filepath)
    
    return jsonify({'message': 'File uploaded successfully', 'path': filepath})

@app.route('/execute', methods=['POST'])
def execute_command():
    """Command execution endpoint."""
    command = request.json.get('command')
    
    # Command injection vulnerability
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    return jsonify({
        'stdout': result.stdout,
        'stderr': result.stderr,
        'returncode': result.returncode
    })

@app.route('/deserialize', methods=['POST'])
def deserialize_data():
    """Data deserialization endpoint."""
    data = request.get_data()
    
    # Unsafe deserialization
    try:
        obj = pickle.loads(data)
        return jsonify({'result': str(obj)})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/users/<int:user_id>')
def get_user(user_id):
    """Get user information."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # SQL injection through string formatting
    cursor.execute(f"SELECT id, username, email FROM users WHERE id = {user_id}")
    user = cursor.fetchone()
    
    if user:
        return jsonify({
            'id': user[0],
            'username': user[1],
            'email': user[2]
        })
    else:
        return jsonify({'error': 'User not found'}), 404

@app.route('/hash_password', methods=['POST'])
def hash_password():
    """Hash password using weak algorithm."""
    password = request.json.get('password')
    
    # Weak hashing algorithm
    hashed = hashlib.md5(password.encode()).hexdigest()
    
    return jsonify({'hashed_password': hashed})

@app.route('/admin/backup')
def create_backup():
    """Create database backup (admin only)."""
    # Missing authentication check
    
    # Hardcoded backup path
    backup_path = '/tmp/backup.sql'
    
    # Command injection vulnerability
    command = f"mysqldump -u root -ppassword123 mydb > {backup_path}"
    os.system(command)
    
    return jsonify({'message': 'Backup created', 'path': backup_path})

def process_user_data(users):
    """Process user data with performance issues."""
    processed_users = []
    
    # Inefficient nested loops
    for user in users:
        user_permissions = []
        for permission in get_all_permissions():  # Called for each user
            if user_has_permission(user['id'], permission['id']):  # N+1 query problem
                user_permissions.append(permission)
        
        user['permissions'] = user_permissions
        processed_users.append(user)
    
    return processed_users

def validate_email(email):
    """Validate email with duplicated logic."""
    if not email:
        return False, "Email is required"
    
    if '@' not in email:
        return False, "Email must contain @ symbol"
    
    if len(email) < 5:
        return False, "Email is too short"
    
    if len(email) > 100:
        return False, "Email is too long"
    
    return True, "Valid email"

def validate_admin_email(email):
    """Validate admin email with duplicated logic."""
    if not email:
        return False, "Email is required"
    
    if '@' not in email:
        return False, "Email must contain @ symbol"
    
    if len(email) < 5:
        return False, "Email is too short"
    
    if len(email) > 100:
        return False, "Email is too long"
    
    # Additional admin validation
    if not email.endswith('@company.com'):
        return False, "Admin email must be from company domain"
    
    return True, "Valid admin email"

# Complex function with high cyclomatic complexity
def process_order(order_data):
    """Process order with complex business logic."""
    if not order_data:
        return {'error': 'No order data provided'}
    
    if 'customer_id' not in order_data:
        return {'error': 'Customer ID required'}
    
    if 'items' not in order_data:
        return {'error': 'Order items required'}
    
    total = 0
    for item in order_data['items']:
        if 'price' not in item:
            return {'error': 'Item price required'}
        
        if 'quantity' not in item:
            return {'error': 'Item quantity required'}
        
        if item['quantity'] <= 0:
            return {'error': 'Invalid quantity'}
        
        item_total = item['price'] * item['quantity']
        
        if 'discount' in item:
            if item['discount'] > 0:
                if item['discount'] < 1:
                    item_total *= (1 - item['discount'])
                else:
                    item_total -= item['discount']
        
        if 'tax_rate' in item:
            if item['tax_rate'] > 0:
                item_total *= (1 + item['tax_rate'])
        
        total += item_total
    
    if 'shipping' in order_data:
        if order_data['shipping'] > 0:
            total += order_data['shipping']
    
    if 'discount_code' in order_data:
        if order_data['discount_code'] == 'SAVE10':
            total *= 0.9
        elif order_data['discount_code'] == 'SAVE20':
            total *= 0.8
        elif order_data['discount_code'] == 'SAVE50':
            total *= 0.5
    
    return {'total': total, 'status': 'processed'}

# Helper functions (stubs)
def get_all_permissions():
    return [{'id': 1, 'name': 'read'}, {'id': 2, 'name': 'write'}]

def user_has_permission(user_id, permission_id):
    return True

if __name__ == '__main__':
    # Debug mode enabled in production
    app.run(debug=True, host='0.0.0.0', port=5000)