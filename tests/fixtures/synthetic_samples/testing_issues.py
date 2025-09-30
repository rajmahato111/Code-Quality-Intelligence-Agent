"""
Synthetic Python code samples with testing issues.
These samples are designed to test testing analyzers.
"""

import unittest
from unittest.mock import Mock, patch

# TESTING ISSUE: Function without any tests
def calculate_compound_interest(principal, rate, time, compound_frequency):
    """Calculate compound interest."""
    return principal * (1 + rate / compound_frequency) ** (compound_frequency * time)

# TESTING ISSUE: Critical function without adequate test coverage
def process_financial_transaction(account_id, amount, transaction_type, metadata):
    """Process a financial transaction with various validations."""
    if not account_id:
        raise ValueError("Account ID is required")
    
    if amount <= 0:
        raise ValueError("Amount must be positive")
    
    if transaction_type not in ['deposit', 'withdrawal', 'transfer']:
        raise ValueError("Invalid transaction type")
    
    # Complex business logic that needs thorough testing
    if transaction_type == 'withdrawal':
        balance = get_account_balance(account_id)
        if balance < amount:
            raise ValueError("Insufficient funds")
        
        # Apply withdrawal fees
        if amount > 1000:
            fee = amount * 0.01
            amount += fee
    
    elif transaction_type == 'transfer':
        if not metadata or 'target_account' not in metadata:
            raise ValueError("Target account required for transfers")
        
        # Validate target account exists
        if not account_exists(metadata['target_account']):
            raise ValueError("Target account does not exist")
    
    # Process the transaction
    transaction_id = generate_transaction_id()
    record_transaction(account_id, amount, transaction_type, transaction_id)
    
    return {
        'transaction_id': transaction_id,
        'status': 'completed',
        'processed_amount': amount
    }

# TESTING ISSUE: Tests with poor assertions
class TestCalculator(unittest.TestCase):
    """Test calculator functions."""
    
    def test_addition(self):
        """Test addition function."""
        result = add(2, 3)
        # Poor assertion - doesn't verify the actual result
        self.assertTrue(result)
    
    def test_division(self):
        """Test division function."""
        result = divide(10, 2)
        # Vague assertion
        self.assertIsNotNone(result)
    
    def test_complex_calculation(self):
        """Test complex calculation."""
        result = complex_calculation(1, 2, 3, 4, 5)
        # No assertion at all!
        pass

# TESTING ISSUE: Tests that don't test edge cases
class TestUserValidation(unittest.TestCase):
    """Test user validation functions."""
    
    def test_validate_email(self):
        """Test email validation."""
        # Only tests happy path
        self.assertTrue(validate_email("user@example.com"))
    
    def test_validate_password(self):
        """Test password validation."""
        # Only tests one valid case
        self.assertTrue(validate_password("StrongPassword123!"))
    
    def test_validate_age(self):
        """Test age validation."""
        # Doesn't test boundary conditions
        self.assertTrue(validate_age(25))

# TESTING ISSUE: Tests with hardcoded values and no parameterization
class TestDataProcessing(unittest.TestCase):
    """Test data processing functions."""
    
    def test_process_sales_data_january(self):
        """Test processing January sales data."""
        data = [{'month': 'January', 'sales': 1000}]
        result = process_sales_data(data)
        self.assertEqual(result[0]['processed_sales'], 1100)
    
    def test_process_sales_data_february(self):
        """Test processing February sales data."""
        data = [{'month': 'February', 'sales': 1200}]
        result = process_sales_data(data)
        self.assertEqual(result[0]['processed_sales'], 1320)
    
    def test_process_sales_data_march(self):
        """Test processing March sales data."""
        data = [{'month': 'March', 'sales': 1500}]
        result = process_sales_data(data)
        self.assertEqual(result[0]['processed_sales'], 1650)

# TESTING ISSUE: Tests that don't clean up properly
class TestDatabaseOperations(unittest.TestCase):
    """Test database operations."""
    
    def test_create_user(self):
        """Test user creation."""
        # Creates test data but doesn't clean up
        user_id = create_user({'name': 'Test User', 'email': 'test@example.com'})
        self.assertIsNotNone(user_id)
        # Missing cleanup - user remains in database
    
    def test_update_user(self):
        """Test user update."""
        # Creates test data but doesn't clean up
        user_id = create_user({'name': 'Test User', 'email': 'test@example.com'})
        updated = update_user(user_id, {'name': 'Updated User'})
        self.assertTrue(updated)
        # Missing cleanup

# TESTING ISSUE: Tests with external dependencies not mocked
class TestEmailService(unittest.TestCase):
    """Test email service."""
    
    def test_send_welcome_email(self):
        """Test sending welcome email."""
        # Calls actual email service instead of mocking
        result = send_welcome_email('user@example.com', 'John Doe')
        self.assertTrue(result['sent'])
    
    def test_send_notification(self):
        """Test sending notification."""
        # Makes actual HTTP request instead of mocking
        result = send_push_notification('user123', 'Hello World')
        self.assertEqual(result['status'], 'delivered')

# TESTING ISSUE: Tests that are too slow
class TestPerformanceOperations(unittest.TestCase):
    """Test performance-critical operations."""
    
    def test_large_data_processing(self):
        """Test processing large dataset."""
        # Generates huge dataset in test, making it slow
        large_dataset = generate_test_data(1000000)  # 1 million records
        result = process_large_dataset(large_dataset)
        self.assertIsNotNone(result)
    
    def test_complex_algorithm(self):
        """Test complex algorithm."""
        # Runs actual complex algorithm instead of using smaller test case
        input_data = generate_complex_input(50000)
        result = run_complex_algorithm(input_data)
        self.assertTrue(len(result) > 0)

# TESTING ISSUE: Flaky tests that depend on timing
class TestAsyncOperations(unittest.TestCase):
    """Test asynchronous operations."""
    
    def test_async_task_completion(self):
        """Test async task completion."""
        import time
        
        # Starts async task
        task_id = start_async_task({'data': 'test'})
        
        # Waits fixed time instead of proper synchronization
        time.sleep(2)  # Flaky - might not be enough time
        
        status = get_task_status(task_id)
        self.assertEqual(status, 'completed')

# TESTING ISSUE: Tests with unclear purpose
class TestMiscellaneous(unittest.TestCase):
    """Miscellaneous tests."""
    
    def test_something(self):
        """Test something."""
        # Unclear what this test is supposed to verify
        result = do_something()
        self.assertTrue(result)
    
    def test_another_thing(self):
        """Test another thing."""
        # No clear test objective
        x = calculate_x()
        y = calculate_y()
        z = combine(x, y)
        # Multiple assertions without clear relationship
        self.assertGreater(x, 0)
        self.assertLess(y, 100)
        self.assertIsInstance(z, dict)

# Helper functions (stubs)
def add(a, b): return a + b
def divide(a, b): return a / b if b != 0 else None
def complex_calculation(a, b, c, d, e): return a + b + c + d + e
def validate_email(email): return '@' in email
def validate_password(password): return len(password) >= 8
def validate_age(age): return 0 <= age <= 150
def process_sales_data(data): return [{'processed_sales': item['sales'] * 1.1} for item in data]
def create_user(data): return 1
def update_user(user_id, data): return True
def send_welcome_email(email, name): return {'sent': True}
def send_push_notification(user_id, message): return {'status': 'delivered'}
def generate_test_data(size): return list(range(size))
def process_large_dataset(data): return len(data)
def generate_complex_input(size): return list(range(size))
def run_complex_algorithm(data): return data[:10]
def start_async_task(data): return 'task_123'
def get_task_status(task_id): return 'completed'
def do_something(): return True
def calculate_x(): return 42
def calculate_y(): return 24
def combine(x, y): return {'x': x, 'y': y}
def get_account_balance(account_id): return 1000
def account_exists(account_id): return True
def generate_transaction_id(): return 'txn_123'
def record_transaction(account_id, amount, transaction_type, transaction_id): pass