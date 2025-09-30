"""Synthetic code samples with known quality issues for testing."""

from typing import Dict, List, Any
from pathlib import Path
import tempfile
import os


class SyntheticCodeSample:
    """Represents a synthetic code sample with known issues."""
    
    def __init__(
        self,
        name: str,
        language: str,
        content: str,
        expected_issues: List[Dict[str, Any]],
        description: str = ""
    ):
        self.name = name
        self.language = language
        self.content = content
        self.expected_issues = expected_issues
        self.description = description


# Security Issues Samples
SECURITY_SAMPLES = [
    SyntheticCodeSample(
        name="sql_injection_vulnerable.py",
        language="python",
        content='''"""SQL Injection vulnerability example."""
import sqlite3

def get_user_data(user_id):
    """Vulnerable function with SQL injection."""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # VULNERABLE: Direct string concatenation
    query = "SELECT * FROM users WHERE id = '" + user_id + "'"
    cursor.execute(query)
    
    result = cursor.fetchall()
    conn.close()
    return result

def login_user(username, password):
    """Another SQL injection vulnerability."""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # VULNERABLE: String formatting
    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
    cursor.execute(query)
    
    return cursor.fetchone() is not None
''',
        expected_issues=[
            {
                "category": "security",
                "severity": "high",
                "title": "SQL Injection Vulnerability",
                "line_range": (8, 10),
                "description": "Direct string concatenation in SQL query"
            },
            {
                "category": "security", 
                "severity": "high",
                "title": "SQL Injection Vulnerability",
                "line_range": (19, 21),
                "description": "String formatting in SQL query"
            }
        ],
        description="Python code with SQL injection vulnerabilities"
    ), 
   
    SyntheticCodeSample(
        name="hardcoded_secrets.py",
        language="python",
        content='''"""Hardcoded secrets and credentials."""

# VULNERABLE: Hardcoded API key
API_KEY = "sk-1234567890abcdef"
DATABASE_PASSWORD = "admin123"

class DatabaseConfig:
    def __init__(self):
        # VULNERABLE: Hardcoded credentials
        self.host = "localhost"
        self.username = "admin"
        self.password = "supersecret123"
        self.api_token = "ghp_1234567890abcdef"

def connect_to_service():
    """Function with hardcoded secrets."""
    import requests
    
    # VULNERABLE: Hardcoded token in request
    headers = {
        "Authorization": "Bearer abc123def456",
        "X-API-Key": "secret-key-12345"
    }
    
    return requests.get("https://api.example.com/data", headers=headers)
''',
        expected_issues=[
            {
                "category": "security",
                "severity": "critical",
                "title": "Hardcoded API Key",
                "line_range": (4, 4),
                "description": "API key hardcoded in source code"
            },
            {
                "category": "security",
                "severity": "critical", 
                "title": "Hardcoded Password",
                "line_range": (5, 5),
                "description": "Database password hardcoded in source code"
            },
            {
                "category": "security",
                "severity": "critical",
                "title": "Hardcoded Credentials",
                "line_range": (10, 13),
                "description": "Database credentials hardcoded in class"
            }
        ],
        description="Python code with hardcoded secrets and credentials"
    ),
]
#
 Performance Issues Samples
PERFORMANCE_SAMPLES = [
    SyntheticCodeSample(
        name="inefficient_loops.py",
        language="python",
        content='''"""Performance issues with inefficient loops."""

def find_duplicates_slow(items):
    """Inefficient O(n²) duplicate detection."""
    duplicates = []
    
    # PERFORMANCE ISSUE: Nested loops for duplicate detection
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            if items[i] == items[j] and items[i] not in duplicates:
                duplicates.append(items[i])
    
    return duplicates

def process_data_inefficient(data_list):
    """Multiple performance issues."""
    result = []
    
    # PERFORMANCE ISSUE: Repeated string concatenation
    output_string = ""
    for item in data_list:
        output_string += str(item) + ", "
    
    # PERFORMANCE ISSUE: Inefficient list operations
    for item in data_list:
        if item not in result:  # O(n) lookup in list
            result.append(item)
    
    # PERFORMANCE ISSUE: Unnecessary list comprehension in loop
    for i in range(len(data_list)):
        processed = [x * 2 for x in data_list if x > i]
        result.extend(processed)
    
    return result, output_string

class InefficientDataStructure:
    """Class with performance issues."""
    
    def __init__(self):
        self.data = []  # Should use set for lookups
    
    def add_item(self, item):
        # PERFORMANCE ISSUE: O(n) lookup before insert
        if item not in self.data:
            self.data.append(item)
    
    def remove_item(self, item):
        # PERFORMANCE ISSUE: O(n) removal from list
        if item in self.data:
            self.data.remove(item)
''',
        expected_issues=[
            {
                "category": "performance",
                "severity": "high",
                "title": "Inefficient Nested Loops",
                "line_range": (7, 10),
                "description": "O(n²) algorithm for duplicate detection"
            },
            {
                "category": "performance",
                "severity": "medium",
                "title": "Inefficient String Concatenation",
                "line_range": (18, 21),
                "description": "Repeated string concatenation in loop"
            },
            {
                "category": "performance",
                "severity": "medium",
                "title": "Inefficient List Operations",
                "line_range": (24, 26),
                "description": "O(n) lookup in list for each item"
            }
        ],
        description="Python code with various performance issues"
    ),
]# C
omplexity Issues Samples  
COMPLEXITY_SAMPLES = [
    SyntheticCodeSample(
        name="high_complexity.py",
        language="python", 
        content='''"""High complexity code examples."""

def complex_business_logic(user_type, account_status, payment_method, amount, currency, region):
    """Overly complex function with high cyclomatic complexity."""
    
    # COMPLEXITY ISSUE: Too many nested conditions
    if user_type == "premium":
        if account_status == "active":
            if payment_method == "credit_card":
                if amount > 1000:
                    if currency == "USD":
                        if region == "US":
                            fee = amount * 0.01
                        elif region == "EU":
                            fee = amount * 0.015
                        else:
                            fee = amount * 0.02
                    elif currency == "EUR":
                        if region == "EU":
                            fee = amount * 0.012
                        else:
                            fee = amount * 0.025
                    else:
                        fee = amount * 0.03
                else:
                    if currency == "USD":
                        fee = 5.0
                    else:
                        fee = 7.0
            elif payment_method == "bank_transfer":
                if amount > 5000:
                    fee = amount * 0.005
                else:
                    fee = 10.0
            else:
                fee = amount * 0.05
        else:
            fee = amount * 0.1
    elif user_type == "standard":
        if account_status == "active":
            if payment_method == "credit_card":
                fee = amount * 0.025
            else:
                fee = amount * 0.03
        else:
            fee = amount * 0.15
    else:
        fee = amount * 0.2
    
    return fee

class OverlyComplexClass:
    """Class with too many methods and responsibilities."""
    
    def __init__(self, config):
        self.config = config
        self.cache = {}
        self.stats = {}
        self.connections = []
        self.handlers = {}
        self.validators = {}
        self.transformers = {}
        self.filters = {}
        self.processors = {}
        self.formatters = {}
    
    # COMPLEXITY ISSUE: Too many methods (showing just a few)
    def method1(self): pass
    def method2(self): pass  
    def method3(self): pass
    def method4(self): pass
    def method5(self): pass
''',
        expected_issues=[
            {
                "category": "complexity",
                "severity": "high", 
                "title": "High Cyclomatic Complexity",
                "line_range": (4, 47),
                "description": "Function has excessive nested conditions"
            },
            {
                "category": "complexity",
                "severity": "medium",
                "title": "Too Many Instance Variables",
                "line_range": (52, 62),
                "description": "Class has too many instance variables"
            }
        ],
        description="Python code with high complexity issues"
    ),
]# C
ode Duplication Samples
DUPLICATION_SAMPLES = [
    SyntheticCodeSample(
        name="code_duplication.py",
        language="python",
        content='''"""Code duplication examples."""

def calculate_user_discount(user_age, user_type, purchase_amount):
    """Calculate discount for user purchases."""
    base_discount = 0.0
    
    # DUPLICATION: Similar logic repeated
    if user_type == "premium":
        if user_age >= 65:
            base_discount = 0.15
        elif user_age >= 18:
            base_discount = 0.10
        else:
            base_discount = 0.05
    elif user_type == "standard":
        if user_age >= 65:
            base_discount = 0.10
        elif user_age >= 18:
            base_discount = 0.05
        else:
            base_discount = 0.02
    
    if purchase_amount > 1000:
        base_discount += 0.05
    elif purchase_amount > 500:
        base_discount += 0.02
        
    return base_discount

def calculate_business_discount(business_type, years_active, purchase_amount):
    """Calculate discount for business purchases - DUPLICATE LOGIC."""
    base_discount = 0.0
    
    # DUPLICATION: Very similar to user discount logic
    if business_type == "enterprise":
        if years_active >= 10:
            base_discount = 0.15
        elif years_active >= 5:
            base_discount = 0.10
        else:
            base_discount = 0.05
    elif business_type == "small":
        if years_active >= 10:
            base_discount = 0.10
        elif years_active >= 5:
            base_discount = 0.05
        else:
            base_discount = 0.02
    
    if purchase_amount > 1000:
        base_discount += 0.05
    elif purchase_amount > 500:
        base_discount += 0.02
        
    return base_discount

class UserValidator:
    """User validation with duplicated methods."""
    
    def validate_email(self, email):
        # DUPLICATION: Same validation logic
        if not email or "@" not in email:
            return False
        parts = email.split("@")
        if len(parts) != 2:
            return False
        return True
    
    def validate_business_email(self, email):
        # DUPLICATION: Identical to validate_email
        if not email or "@" not in email:
            return False
        parts = email.split("@")
        if len(parts) != 2:
            return False
        return True
''',
        expected_issues=[
            {
                "category": "duplication",
                "severity": "high",
                "title": "Duplicated Function Logic",
                "line_range": [(4, 28), (30, 54)],
                "description": "Similar discount calculation logic duplicated"
            },
            {
                "category": "duplication", 
                "severity": "medium",
                "title": "Identical Method Implementation",
                "line_range": [(59, 65), (67, 73)],
                "description": "Email validation methods are identical"
            }
        ],
        description="Python code with various duplication issues"
    ),
]#
 Testing Issues Samples
TESTING_SAMPLES = [
    SyntheticCodeSample(
        name="untested_code.py",
        language="python",
        content='''"""Code with testing issues."""

def critical_payment_processor(amount, card_number, cvv):
    """Critical function with no tests."""
    # TESTING ISSUE: No unit tests for critical payment logic
    if not card_number or len(card_number) != 16:
        raise ValueError("Invalid card number")
    
    if not cvv or len(cvv) != 3:
        raise ValueError("Invalid CVV")
    
    # Simulate payment processing
    if amount <= 0:
        return {"status": "failed", "error": "Invalid amount"}
    
    # Complex business logic without tests
    fee = calculate_processing_fee(amount)
    total = amount + fee
    
    return {
        "status": "success",
        "amount": amount,
        "fee": fee,
        "total": total,
        "transaction_id": generate_transaction_id()
    }

def calculate_processing_fee(amount):
    """Fee calculation without tests."""
    # TESTING ISSUE: Complex logic without test coverage
    if amount < 10:
        return 0.50
    elif amount < 100:
        return amount * 0.03
    elif amount < 1000:
        return amount * 0.025
    else:
        return amount * 0.02

def generate_transaction_id():
    """Transaction ID generation without tests."""
    import random
    import string
    
    # TESTING ISSUE: Random generation needs deterministic tests
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))

class UserManager:
    """Class with untested methods."""
    
    def __init__(self):
        self.users = {}
    
    def create_user(self, username, email, password):
        """User creation without tests."""
        # TESTING ISSUE: No tests for user validation
        if username in self.users:
            raise ValueError("User already exists")
        
        if not self._validate_email(email):
            raise ValueError("Invalid email")
        
        if len(password) < 8:
            raise ValueError("Password too short")
        
        self.users[username] = {
            "email": email,
            "password": self._hash_password(password),
            "created_at": self._get_timestamp()
        }
        
        return True
    
    def _validate_email(self, email):
        # TESTING ISSUE: Private method needs testing
        return "@" in email and "." in email
    
    def _hash_password(self, password):
        # TESTING ISSUE: Security-critical function untested
        import hashlib
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _get_timestamp(self):
        # TESTING ISSUE: Time-dependent function needs mocking
        import datetime
        return datetime.datetime.now().isoformat()
''',
        expected_issues=[
            {
                "category": "testing",
                "severity": "critical",
                "title": "Critical Function Untested",
                "line_range": (4, 24),
                "description": "Payment processing function lacks unit tests"
            },
            {
                "category": "testing",
                "severity": "high", 
                "title": "Complex Logic Untested",
                "line_range": (26, 35),
                "description": "Fee calculation logic has no test coverage"
            },
            {
                "category": "testing",
                "severity": "high",
                "title": "Security Function Untested", 
                "line_range": (69, 72),
                "description": "Password hashing function lacks tests"
            }
        ],
        description="Python code with testing coverage issues"
    ),
]# 
Documentation Issues Samples
DOCUMENTATION_SAMPLES = [
    SyntheticCodeSample(
        name="poor_documentation.py", 
        language="python",
        content='''"""Documentation issues example."""

def process_payment(amount, method, user_id):
    # DOCUMENTATION ISSUE: No docstring for public function
    if method == "card":
        return charge_card(amount, user_id)
    elif method == "bank":
        return process_bank_transfer(amount, user_id)
    else:
        return {"error": "Invalid payment method"}

class PaymentProcessor:
    # DOCUMENTATION ISSUE: No class docstring
    
    def __init__(self, config):
        # DOCUMENTATION ISSUE: No docstring for constructor
        self.config = config
        self.api_key = config.get("api_key")
    
    def charge_card(self, amount, user_id):
        # DOCUMENTATION ISSUE: No docstring, complex parameters undocumented
        card_info = self._get_user_card(user_id)
        
        # Complex logic without explanation
        if self._validate_card(card_info):
            result = self._process_charge(amount, card_info)
            self._log_transaction(result)
            return result
        else:
            return {"error": "Invalid card"}
    
    def _get_user_card(self, user_id):
        # DOCUMENTATION ISSUE: Private method without docstring
        pass
    
    def _validate_card(self, card_info):
        # DOCUMENTATION ISSUE: No documentation for validation logic
        pass
    
    def _process_charge(self, amount, card_info):
        # DOCUMENTATION ISSUE: Critical method without documentation
        pass
    
    def _log_transaction(self, result):
        pass

# DOCUMENTATION ISSUE: Complex algorithm without explanation
def calculate_risk_score(user_data, transaction_history, current_transaction):
    score = 0
    
    # Undocumented risk calculation
    if len(transaction_history) < 5:
        score += 20
    
    avg_amount = sum(t["amount"] for t in transaction_history) / len(transaction_history)
    if current_transaction["amount"] > avg_amount * 3:
        score += 30
    
    if user_data.get("country") in ["XX", "YY", "ZZ"]:
        score += 15
    
    # More undocumented logic
    time_since_last = current_transaction["timestamp"] - transaction_history[-1]["timestamp"]
    if time_since_last < 300:  # 5 minutes
        score += 25
    
    return min(score, 100)
''',
        expected_issues=[
            {
                "category": "documentation",
                "severity": "medium",
                "title": "Missing Function Docstring",
                "line_range": (4, 4),
                "description": "Public function lacks documentation"
            },
            {
                "category": "documentation",
                "severity": "medium", 
                "title": "Missing Class Docstring",
                "line_range": (11, 11),
                "description": "Public class lacks documentation"
            },
            {
                "category": "documentation",
                "severity": "high",
                "title": "Complex Algorithm Undocumented",
                "line_range": (47, 66),
                "description": "Risk calculation algorithm needs explanation"
            }
        ],
        description="Python code with documentation issues"
    ),
]# JavaS
cript/TypeScript Samples
JAVASCRIPT_SAMPLES = [
    SyntheticCodeSample(
        name="security_issues.js",
        language="javascript",
        content='''/**
 * JavaScript security vulnerabilities.
 */

// SECURITY ISSUE: eval() usage
function executeUserCode(userInput) {
    // VULNERABLE: Direct eval of user input
    return eval(userInput);
}

// SECURITY ISSUE: innerHTML with user data
function displayUserMessage(message) {
    // VULNERABLE: XSS vulnerability
    document.getElementById('message').innerHTML = message;
}

// SECURITY ISSUE: Weak random number generation
function generateSessionToken() {
    // VULNERABLE: Math.random() is not cryptographically secure
    return Math.random().toString(36).substring(2, 15);
}

class ApiClient {
    constructor() {
        // SECURITY ISSUE: Hardcoded API endpoint and key
        this.apiUrl = 'https://api.internal.com/v1';
        this.apiKey = 'sk-1234567890abcdef';
    }
    
    async fetchUserData(userId) {
        // SECURITY ISSUE: No input validation
        const url = `${this.apiUrl}/users/${userId}`;
        
        const response = await fetch(url, {
            headers: {
                'Authorization': `Bearer ${this.apiKey}`,
                'Content-Type': 'application/json'
            }
        });
        
        return response.json();
    }
}

// PERFORMANCE ISSUE: Inefficient DOM manipulation
function updateUserList(users) {
    const container = document.getElementById('users');
    container.innerHTML = ''; // Clears all content
    
    // PERFORMANCE ISSUE: Creating DOM elements in loop
    users.forEach(user => {
        const div = document.createElement('div');
        div.innerHTML = `<span>${user.name}</span><span>${user.email}</span>`;
        container.appendChild(div);
    });
}
''',
        expected_issues=[
            {
                "category": "security",
                "severity": "critical",
                "title": "Code Injection via eval()",
                "line_range": (8, 8),
                "description": "Direct eval of user input allows code injection"
            },
            {
                "category": "security",
                "severity": "high",
                "title": "XSS Vulnerability",
                "line_range": (14, 14),
                "description": "innerHTML with user data enables XSS attacks"
            },
            {
                "category": "security",
                "severity": "medium",
                "title": "Weak Random Generation",
                "line_range": (20, 20),
                "description": "Math.random() not suitable for security tokens"
            },
            {
                "category": "performance",
                "severity": "medium",
                "title": "Inefficient DOM Manipulation",
                "line_range": (47, 53),
                "description": "Creating DOM elements in loop is inefficient"
            }
        ],
        description="JavaScript code with security and performance issues"
    ),
]# Uti
lity functions for creating test data
def get_synthetic_samples() -> Dict[str, List[SyntheticCodeSample]]:
    """Get all synthetic code samples organized by category."""
    return {
        "security": SECURITY_SAMPLES,
        "performance": PERFORMANCE_SAMPLES, 
        "complexity": COMPLEXITY_SAMPLES,
        "duplication": DUPLICATION_SAMPLES,
        "testing": TESTING_SAMPLES,
        "documentation": DOCUMENTATION_SAMPLES,
        "javascript": JAVASCRIPT_SAMPLES
    }

def get_samples_by_language(language: str) -> List[SyntheticCodeSample]:
    """Get synthetic samples filtered by programming language."""
    all_samples = get_synthetic_samples()
    filtered_samples = []
    
    for category_samples in all_samples.values():
        for sample in category_samples:
            if sample.language.lower() == language.lower():
                filtered_samples.append(sample)
    
    return filtered_samples

def create_test_codebase(samples: List[SyntheticCodeSample], base_dir: str = None) -> str:
    """
    Create a temporary codebase with the given samples.
    
    Args:
        samples: List of code samples to include
        base_dir: Base directory (creates temp dir if None)
        
    Returns:
        Path to the created test codebase
    """
    if base_dir is None:
        base_dir = tempfile.mkdtemp(prefix="codeql_test_")
    
    base_path = Path(base_dir)
    base_path.mkdir(exist_ok=True)
    
    for sample in samples:
        file_path = base_path / sample.name
        file_path.write_text(sample.content)
    
    return str(base_path)

def get_expected_issue_count() -> Dict[str, int]:
    """Get expected issue counts for validation."""
    all_samples = get_synthetic_samples()
    counts = {}
    
    for category, samples in all_samples.items():
        total_issues = 0
        for sample in samples:
            total_issues += len(sample.expected_issues)
        counts[category] = total_issues
    
    return counts