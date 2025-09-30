"""
Synthetic Python code samples with documentation issues.
These samples are designed to test documentation analyzers.
"""

# DOCUMENTATION ISSUE: Missing docstring
def calculate_tax(amount, rate):
    return amount * rate

# DOCUMENTATION ISSUE: Inadequate docstring
def process_payment(amount, method):
    """Process payment."""
    if method == 'credit':
        return charge_credit_card(amount)
    elif method == 'debit':
        return charge_debit_card(amount)
    else:
        raise ValueError("Invalid payment method")

# DOCUMENTATION ISSUE: Missing parameter documentation
def create_user_account(username, password, email, profile_data):
    """Create a new user account in the system."""
    # Implementation here
    pass

# DOCUMENTATION ISSUE: Missing return value documentation
def get_user_permissions(user_id):
    """
    Get permissions for a user.
    
    Args:
        user_id (int): The ID of the user
    """
    # Implementation here
    return ['read', 'write', 'delete']

# DOCUMENTATION ISSUE: Outdated documentation
def calculate_discount(price, discount_percent, membership_level):
    """
    Calculate discount for a product.
    
    Args:
        price (float): Original price
        discount_percent (float): Discount percentage
    
    Returns:
        float: Discounted price
    """
    # Note: membership_level parameter added but not documented
    if membership_level == 'premium':
        discount_percent *= 1.5
    
    return price * (1 - discount_percent / 100)

# DOCUMENTATION ISSUE: Complex function without examples
def parse_configuration_file(file_path, schema_validation=True, 
                           custom_parsers=None, error_handling='strict'):
    """
    Parse a configuration file with various options.
    
    Args:
        file_path (str): Path to configuration file
        schema_validation (bool): Whether to validate against schema
        custom_parsers (dict): Custom parsing functions
        error_handling (str): How to handle parsing errors
    
    Returns:
        dict: Parsed configuration data
    
    Raises:
        ConfigurationError: When parsing fails
        ValidationError: When schema validation fails
    """
    # Complex implementation without usage examples
    pass

class DataProcessor:
    """Process various types of data."""
    
    # DOCUMENTATION ISSUE: Missing method documentation
    def __init__(self, config):
        self.config = config
        self.processed_count = 0
    
    # DOCUMENTATION ISSUE: Vague documentation
    def process(self, data):
        """Process data."""
        pass
    
    # DOCUMENTATION ISSUE: Missing exception documentation
    def validate_data(self, data):
        """
        Validate input data.
        
        Args:
            data (dict): Data to validate
        
        Returns:
            bool: True if valid
        """
        if not isinstance(data, dict):
            raise TypeError("Data must be a dictionary")
        
        if 'required_field' not in data:
            raise ValueError("Missing required field")
        
        return True
    
    # DOCUMENTATION ISSUE: Inconsistent documentation style
    def transform_data(self, data):
        """
        Transform data according to configuration
        
        Parameters:
        data -- input data to transform
        
        Return:
        transformed data
        """
        pass

# DOCUMENTATION ISSUE: Missing class documentation
class UserManager:
    
    def __init__(self, database_url):
        """Initialize user manager."""
        self.db_url = database_url
    
    def create_user(self, user_data):
        """Create a new user."""
        pass
    
    def get_user(self, user_id):
        """Get user by ID."""
        pass

# DOCUMENTATION ISSUE: Confusing parameter names without documentation
def calculate_metrics(x, y, z, flag1, flag2, mode):
    """Calculate various metrics."""
    if flag1:
        result = x * y
    else:
        result = x + y
    
    if flag2 and mode == 'advanced':
        result *= z
    
    return result

# DOCUMENTATION ISSUE: Missing type hints and documentation
def complex_algorithm(data, options, callbacks):
    """Perform complex algorithm."""
    # Complex implementation without clear documentation
    for item in data:
        if options.get('validate'):
            if not validate_item(item):
                continue
        
        processed = transform_item(item, options)
        
        if callbacks:
            for callback in callbacks:
                callback(processed)
    
    return True

# DOCUMENTATION ISSUE: Magic numbers without explanation
def calculate_score(base_score, multipliers):
    """Calculate final score."""
    # Magic numbers without explanation
    adjusted_score = base_score * 1.2
    
    if adjusted_score > 100:
        adjusted_score = 100 + (adjusted_score - 100) * 0.5
    
    for multiplier in multipliers:
        adjusted_score *= multiplier
    
    # Another magic number
    if adjusted_score < 10:
        adjusted_score = 10
    
    return adjusted_score

# DOCUMENTATION ISSUE: Incomplete documentation for complex return type
def analyze_data(dataset):
    """
    Analyze dataset and return results.
    
    Args:
        dataset (list): Input dataset
    
    Returns:
        dict: Analysis results
    """
    # Returns complex nested structure but documentation doesn't specify format
    return {
        'summary': {
            'total_records': len(dataset),
            'valid_records': 0,
            'invalid_records': 0
        },
        'statistics': {
            'mean': 0,
            'median': 0,
            'std_dev': 0
        },
        'categories': {
            'A': {'count': 0, 'percentage': 0},
            'B': {'count': 0, 'percentage': 0},
            'C': {'count': 0, 'percentage': 0}
        },
        'recommendations': []
    }

# Helper functions (stubs)
def charge_credit_card(amount): return {'status': 'success', 'transaction_id': '123'}
def charge_debit_card(amount): return {'status': 'success', 'transaction_id': '456'}
def validate_item(item): return True
def transform_item(item, options): return item