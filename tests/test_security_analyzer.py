"""Tests for SecurityAnalyzer."""

import pytest
import tempfile
from pathlib import Path

from code_quality_agent.analyzers.security_analyzer import SecurityAnalyzer
from code_quality_agent.analyzers.base import IssueCategory, Severity
from code_quality_agent.core.models import (
    ParsedFile, AnalysisContext, AnalysisOptions, 
    FileMetadata, Import
)


class TestSecurityAnalyzer:
    """Tests for SecurityAnalyzer class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = SecurityAnalyzer()
    
    def test_analyzer_properties(self):
        """Test basic analyzer properties."""
        assert self.analyzer.get_category() == IssueCategory.SECURITY
        assert "python" in self.analyzer.get_supported_languages()
        assert "javascript" in self.analyzer.get_supported_languages()
        assert "typescript" in self.analyzer.get_supported_languages()
    
    def test_sql_injection_python(self):
        """Test SQL injection detection in Python."""
        code = '''
import sqlite3

def get_user(user_id):
    # Vulnerable - string formatting
    query = "SELECT * FROM users WHERE id = %s" % user_id
    cursor.execute(query)
    
    # Vulnerable - string concatenation
    sql = "SELECT * FROM users WHERE name = '" + username + "'"
    cursor.execute(sql)
    
    # Vulnerable - f-string
    cursor.execute(f"SELECT * FROM users WHERE email = '{email}'")
    
    # Safe - parameterized query
    safe_query = "SELECT * FROM users WHERE id = %s"
    cursor.execute(safe_query, (user_id,))
'''
        
        parsed_file = self._create_parsed_file("test.py", "python", code)
        context = AnalysisContext(options=AnalysisOptions())
        
        issues = self.analyzer.analyze([parsed_file], context)
        
        # Should find SQL injection vulnerabilities
        sql_issues = [issue for issue in issues if "SQL Injection" in issue.title]
        assert len(sql_issues) >= 2  # Should find multiple vulnerable patterns
        
        for issue in sql_issues:
            assert issue.category == IssueCategory.SECURITY
            assert issue.severity == Severity.HIGH
            assert "parameterized queries" in issue.suggestion
    
    def test_sql_injection_javascript(self):
        """Test SQL injection detection in JavaScript."""
        code = '''
const mysql = require('mysql');

function getUser(userId) {
    // Vulnerable - template literal
    const query = `SELECT * FROM users WHERE id = ${userId}`;
    connection.query(query);
    
    // Vulnerable - string concatenation
    const sql = "SELECT * FROM users WHERE name = '" + username + "'";
    connection.execute(sql);
    
    // Safe - parameterized query
    const safeQuery = "SELECT * FROM users WHERE id = ?";
    connection.query(safeQuery, [userId]);
}
'''
        
        parsed_file = self._create_parsed_file("test.js", "javascript", code)
        context = AnalysisContext(options=AnalysisOptions())
        
        issues = self.analyzer.analyze([parsed_file], context)
        
        # Should find SQL injection vulnerabilities
        sql_issues = [issue for issue in issues if "SQL Injection" in issue.title]
        assert len(sql_issues) >= 1
        
        for issue in sql_issues:
            assert issue.category == IssueCategory.SECURITY
            assert issue.severity == Severity.HIGH
    
    def test_command_injection_python(self):
        """Test command injection detection in Python."""
        code = '''
import os
import subprocess

def execute_command(user_input):
    # Vulnerable - os.system with concatenation
    os.system("ls " + user_input)
    
    # Vulnerable - subprocess with concatenation
    subprocess.call("grep " + pattern + " file.txt", shell=True)
    
    # Vulnerable - eval with user input
    eval("print(" + user_input + ")")
    
    # Safe - subprocess with list
    subprocess.call(["grep", pattern, "file.txt"])
'''
        
        parsed_file = self._create_parsed_file("test.py", "python", code)
        context = AnalysisContext(options=AnalysisOptions())
        
        issues = self.analyzer.analyze([parsed_file], context)
        
        # Should find command injection vulnerabilities
        cmd_issues = [issue for issue in issues if "Command Injection" in issue.title or "Dangerous Function" in issue.title]
        assert len(cmd_issues) >= 2
        
        for issue in cmd_issues:
            assert issue.category == IssueCategory.SECURITY
            assert issue.severity == Severity.HIGH
    
    def test_xss_vulnerabilities_javascript(self):
        """Test XSS vulnerability detection in JavaScript."""
        code = '''
function displayUserData(userData) {
    // Vulnerable - innerHTML with concatenation
    document.getElementById('content').innerHTML = '<div>' + userData + '</div>';
    
    // Vulnerable - document.write
    document.write('<p>' + userComment + '</p>');
    
    // Vulnerable - jQuery html()
    $('#content').html('<span>' + userInput + '</span>');
    
    // Vulnerable - React dangerouslySetInnerHTML
    return <div dangerouslySetInnerHTML={{__html: userContent}} />;
    
    // Safe - textContent
    document.getElementById('content').textContent = userData;
}
'''
        
        parsed_file = self._create_parsed_file("test.js", "javascript", code)
        context = AnalysisContext(options=AnalysisOptions())
        
        issues = self.analyzer.analyze([parsed_file], context)
        
        # Should find XSS vulnerabilities
        xss_issues = [issue for issue in issues if "XSS" in issue.title or "Cross-Site Scripting" in issue.title]
        assert len(xss_issues) >= 2
        
        for issue in xss_issues:
            assert issue.category == IssueCategory.SECURITY
            assert issue.severity == Severity.HIGH
            assert "sanitize" in issue.suggestion.lower() or "textContent" in issue.suggestion
    
    def test_hardcoded_secrets(self):
        """Test hardcoded secrets detection."""
        code = '''
# Configuration with hardcoded secrets
API_KEY = "sk-1234567890abcdef1234567890abcdef"
DATABASE_PASSWORD = "supersecret123"
JWT_SECRET = "my-super-secret-jwt-key-12345"
ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0"

# These should be ignored
EXAMPLE_KEY = "not_real_key"  # example
TEST_PASSWORD = "dummy"  # test value
'''
        
        parsed_file = self._create_parsed_file("config.py", "python", code)
        context = AnalysisContext(options=AnalysisOptions())
        
        issues = self.analyzer.analyze([parsed_file], context)
        
        # Should find hardcoded secrets
        secret_issues = [issue for issue in issues if "Hardcoded" in issue.title]
        assert len(secret_issues) >= 3  # API key, password, secret, token
        
        for issue in secret_issues:
            assert issue.category == IssueCategory.SECURITY
            assert issue.severity == Severity.HIGH
            assert "environment variables" in issue.suggestion
    
    def test_weak_crypto_python(self):
        """Test weak cryptography detection in Python."""
        code = '''
import hashlib
import random
from Crypto.Cipher import DES

def hash_password(password):
    # Weak - MD5
    md5_hash = hashlib.md5(password.encode()).hexdigest()
    
    # Weak - SHA1
    sha1_hash = hashlib.sha1(password.encode()).hexdigest()
    
    # Weak - random for crypto
    salt = str(random.random())
    
    # Weak - DES encryption
    cipher = DES.new(key, DES.MODE_ECB)
    
    # Strong - SHA256
    sha256_hash = hashlib.sha256(password.encode()).hexdigest()
'''
        
        parsed_file = self._create_parsed_file("crypto.py", "python", code)
        context = AnalysisContext(options=AnalysisOptions())
        
        issues = self.analyzer.analyze([parsed_file], context)
        
        # Should find weak crypto issues
        crypto_issues = [issue for issue in issues if "Weak Cryptographic" in issue.title or "Insecure Random" in issue.title]
        assert len(crypto_issues) >= 2
        
        for issue in crypto_issues:
            assert issue.category == IssueCategory.SECURITY
            assert issue.severity in [Severity.MEDIUM, Severity.HIGH]
    
    def test_dangerous_imports_python(self):
        """Test dangerous imports detection in Python."""
        imports = [
            Import(module="pickle", line_number=1),
            Import(module="cPickle", line_number=2),
            Import(module="marshal", line_number=3),
            Import(module="json", line_number=4),  # Safe import
        ]
        
        parsed_file = ParsedFile(
            path="dangerous.py",
            language="python",
            content="import pickle\nimport cPickle\nimport marshal\nimport json",
            imports=imports,
            metadata=FileMetadata(
                file_path="dangerous.py",
                language="python",
                size_bytes=100,
                line_count=4
            )
        )
        
        context = AnalysisContext(options=AnalysisOptions())
        
        issues = self.analyzer.analyze([parsed_file], context)
        
        # Should find dangerous imports
        import_issues = [issue for issue in issues if "Dangerous Import" in issue.title]
        assert len(import_issues) == 3  # pickle, cPickle, marshal
        
        for issue in import_issues:
            assert issue.category == IssueCategory.SECURITY
            assert issue.severity == Severity.MEDIUM
    
    def test_pickle_usage_python(self):
        """Test unsafe pickle usage detection."""
        code = '''
import pickle
import cPickle

def load_data(data):
    # Unsafe - pickle.loads
    obj = pickle.loads(data)
    
    # Unsafe - cPickle.loads
    obj2 = cPickle.loads(data)
    
    # Safe - pickle.dumps (serialization is generally safe)
    serialized = pickle.dumps(obj)
'''
        
        parsed_file = self._create_parsed_file("pickle_test.py", "python", code)
        context = AnalysisContext(options=AnalysisOptions())
        
        issues = self.analyzer.analyze([parsed_file], context)
        
        # Should find unsafe deserialization
        pickle_issues = [issue for issue in issues if "Unsafe Deserialization" in issue.title]
        assert len(pickle_issues) >= 2
        
        for issue in pickle_issues:
            assert issue.category == IssueCategory.SECURITY
            assert issue.severity == Severity.HIGH
    
    def test_eval_exec_usage_python(self):
        """Test dangerous eval/exec usage detection."""
        code = '''
def process_input(user_input):
    # Dangerous - eval
    result = eval(user_input)
    
    # Dangerous - exec
    exec(user_input)
    
    # Dangerous - __import__
    module = __import__(user_input)
    
    # Safe usage (though still not recommended)
    result = eval("2 + 2")  # Static expression
'''
        
        parsed_file = self._create_parsed_file("eval_test.py", "python", code)
        context = AnalysisContext(options=AnalysisOptions())
        
        issues = self.analyzer.analyze([parsed_file], context)
        
        # Should find dangerous function usage
        eval_issues = [issue for issue in issues if "Dangerous Function" in issue.title]
        assert len(eval_issues) >= 3
        
        for issue in eval_issues:
            assert issue.category == IssueCategory.SECURITY
            assert issue.severity == Severity.HIGH
    
    def test_dangerous_js_functions(self):
        """Test dangerous JavaScript functions detection."""
        code = '''
function processUserInput(input) {
    // Dangerous - eval
    eval(input);
    
    // Dangerous - Function constructor
    const fn = new Function('return ' + input);
    
    // Dangerous - setTimeout with string
    setTimeout('alert("' + input + '")', 1000);
    
    // Dangerous - setInterval with string
    setInterval('console.log("' + input + '")', 1000);
    
    // Safe - setTimeout with function
    setTimeout(() => alert(input), 1000);
}
'''
        
        parsed_file = self._create_parsed_file("dangerous.js", "javascript", code)
        context = AnalysisContext(options=AnalysisOptions())
        
        issues = self.analyzer.analyze([parsed_file], context)
        
        # Should find dangerous function usage
        dangerous_issues = [issue for issue in issues if "Dangerous Function" in issue.title]
        assert len(dangerous_issues) >= 3
        
        for issue in dangerous_issues:
            assert issue.category == IssueCategory.SECURITY
            assert issue.severity == Severity.HIGH
    
    def test_insecure_random_usage(self):
        """Test insecure random number generation detection."""
        python_code = '''
import random

def generate_password():
    # Insecure - random.random for password
    password_part = str(random.random())
    
    # Insecure - random.randint for token
    token = random.randint(1000, 9999)
    
    # Safe - random for non-security purpose
    dice_roll = random.randint(1, 6)
'''
        
        js_code = '''
function generateToken() {
    // Insecure - Math.random for token
    const token = Math.random().toString(36);
    
    // Insecure - Math.random for key
    const key = Math.random() * 1000000;
    
    // Safe - Math.random for animation
    const animationDelay = Math.random() * 1000;
}
'''
        
        python_file = self._create_parsed_file("random_test.py", "python", python_code)
        js_file = self._create_parsed_file("random_test.js", "javascript", js_code)
        context = AnalysisContext(options=AnalysisOptions())
        
        python_issues = self.analyzer.analyze([python_file], context)
        js_issues = self.analyzer.analyze([js_file], context)
        
        # Should find insecure random usage
        python_random_issues = [issue for issue in python_issues if "Insecure Random" in issue.title]
        js_random_issues = [issue for issue in js_issues if "Insecure Random" in issue.title]
        
        assert len(python_random_issues) >= 1
        assert len(js_random_issues) >= 1
        
        for issue in python_random_issues + js_random_issues:
            assert issue.category == IssueCategory.SECURITY
            assert issue.severity == Severity.MEDIUM
    
    def test_debug_information_leakage(self):
        """Test debug information leakage detection."""
        python_code = '''
def login(username, password):
    if authenticate(username, password):
        return True
    else:
        # Dangerous - printing password
        print(f"Failed login for {username} with password {password}")
        
        # Dangerous - printing secret
        print("Secret key:", secret_key)
        
        # Dangerous - full traceback
        import traceback
        traceback.print_exc()
        
        return False
'''
        
        js_code = '''
function authenticate(username, password) {
    try {
        return checkCredentials(username, password);
    } catch (error) {
        // Dangerous - logging password
        console.log("Login failed for", username, "password:", password);
        
        // Dangerous - logging token
        console.log("Token validation failed:", token);
        
        // Dangerous - logging full error
        console.error("Authentication error:", error);
        
        return false;
    }
}
'''
        
        python_file = self._create_parsed_file("debug.py", "python", python_code)
        js_file = self._create_parsed_file("debug.js", "javascript", js_code)
        context = AnalysisContext(options=AnalysisOptions())
        
        python_issues = self.analyzer.analyze([python_file], context)
        js_issues = self.analyzer.analyze([js_file], context)
        
        # Should find information leakage
        python_leak_issues = [issue for issue in python_issues if "Information Leakage" in issue.title]
        js_leak_issues = [issue for issue in js_issues if "Information Leakage" in issue.title]
        
        assert len(python_leak_issues) >= 2
        assert len(js_leak_issues) >= 2
        
        for issue in python_leak_issues + js_leak_issues:
            assert issue.category == IssueCategory.SECURITY
            assert issue.severity == Severity.LOW
    
    def test_path_traversal_python(self):
        """Test path traversal vulnerability detection."""
        code = '''
def read_file(filename):
    # Vulnerable - path concatenation with traversal
    file_path = "/var/www/" + filename + "../../../etc/passwd"
    with open(file_path, 'r') as f:
        return f.read()
    
    # Vulnerable - direct concatenation
    path = base_path + user_input + "/../config.txt"
    
    # Safe - using os.path.join
    import os
    safe_path = os.path.join(base_path, filename)
'''
        
        parsed_file = self._create_parsed_file("path_test.py", "python", code)
        context = AnalysisContext(options=AnalysisOptions())
        
        issues = self.analyzer.analyze([parsed_file], context)
        
        # Should find path traversal vulnerabilities
        path_issues = [issue for issue in issues if "Path Traversal" in issue.title]
        assert len(path_issues) >= 1
        
        for issue in path_issues:
            assert issue.category == IssueCategory.SECURITY
            assert issue.severity == Severity.MEDIUM
    
    def test_no_false_positives_safe_code(self):
        """Test that safe code doesn't trigger false positives."""
        safe_code = '''
import json
import hashlib
import secrets

def safe_function():
    # Safe SQL query
    query = "SELECT * FROM users WHERE id = %s"
    cursor.execute(query, (user_id,))
    
    # Safe hashing
    hash_value = hashlib.sha256(data.encode()).hexdigest()
    
    # Safe random
    secure_token = secrets.token_hex(32)
    
    # Safe serialization
    data = json.dumps({"key": "value"})
    
    # Safe logging
    logger.info("User logged in successfully")
    
    return True
'''
        
        parsed_file = self._create_parsed_file("safe.py", "python", safe_code)
        context = AnalysisContext(options=AnalysisOptions())
        
        issues = self.analyzer.analyze([parsed_file], context)
        
        # Should have minimal or no issues for safe code
        high_severity_issues = [issue for issue in issues if issue.severity == Severity.HIGH]
        assert len(high_severity_issues) == 0
    
    def _create_parsed_file(self, path: str, language: str, content: str) -> ParsedFile:
        """Helper method to create a ParsedFile for testing."""
        return ParsedFile(
            path=path,
            language=language,
            content=content,
            metadata=FileMetadata(
                file_path=path,
                language=language,
                size_bytes=len(content.encode()),
                line_count=len(content.splitlines())
            )
        )