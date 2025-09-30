"""Real-world code samples for testing (simplified versions of common patterns)."""

from typing import Dict, List, Any
from pathlib import Path
import tempfile


class RealWorldSample:
    """Represents a real-world code sample."""
    
    def __init__(
        self,
        name: str,
        language: str,
        content: str,
        source_description: str,
        expected_categories: List[str],
        complexity_level: str = "medium"
    ):
        self.name = name
        self.language = language
        self.content = content
        self.source_description = source_description
        self.expected_categories = expected_categories
        self.complexity_level = complexity_level


# Flask-like web application samples
FLASK_LIKE_SAMPLES = [
    RealWorldSample(
        name="web_app_routes.py",
        language="python",
        content='''"""Flask-like web application with common issues."""
from flask import Flask, request, render_template_string, session
import sqlite3
import os

app = Flask(__name__)

# SECURITY ISSUE: Hardcoded secret key
app.secret_key = "hardcoded-secret-key-123"

@app.route('/user/<user_id>')
def get_user(user_id):
    """Get user information - has SQL injection vulnerability."""
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    
    # SECURITY ISSUE: SQL injection vulnerability
    query = f"SELECT * FROM users WHERE id = {user_id}"
    cursor.execute(query)
    
    user = cursor.fetchone()
    conn.close()
    
    if user:
        # SECURITY ISSUE: Template injection vulnerability
        template = f"<h1>Welcome {user[1]}</h1><p>Email: {user[2]}</p>"
        return render_template_string(template)
    else:
        return "User not found", 404

@app.route('/search')
def search_users():
    """Search users with performance issues."""
    query = request.args.get('q', '')
    
    # PERFORMANCE ISSUE: No input validation or limits
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    
    # PERFORMANCE ISSUE: Inefficient LIKE query without indexes
    sql = f"SELECT * FROM users WHERE name LIKE '%{query}%' OR email LIKE '%{query}%'"
    cursor.execute(sql)
    
    # PERFORMANCE ISSUE: Loading all results into memory
    results = cursor.fetchall()
    conn.close()
    
    # PERFORMANCE ISSUE: Inefficient template rendering
    html = "<ul>"
    for user in results:
        html += f"<li>{user[1]} - {user[2]}</li>"
    html += "</ul>"
    
    return html

if __name__ == '__main__':
    # SECURITY ISSUE: Debug mode in production
    app.run(debug=True, host='0.0.0.0')
''',
        source_description="Simplified Flask web application with common security and performance issues",
        expected_categories=["security", "performance"],
        complexity_level="medium"
    ),
]