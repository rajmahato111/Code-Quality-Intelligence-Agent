"""
Synthetic Python code samples with code duplication issues.
These samples are designed to test duplication analyzers.
"""

# DUPLICATION ISSUE: Identical functions with different names
def calculate_rectangle_area(width, height):
    """Calculate area of rectangle."""
    if width <= 0 or height <= 0:
        raise ValueError("Width and height must be positive")
    return width * height

def get_rectangle_area(width, height):
    """Get area of rectangle."""
    if width <= 0 or height <= 0:
        raise ValueError("Width and height must be positive")
    return width * height

def compute_rectangle_area(width, height):
    """Compute area of rectangle."""
    if width <= 0 or height <= 0:
        raise ValueError("Width and height must be positive")
    return width * height

# DUPLICATION ISSUE: Similar validation logic repeated
def validate_user_email(email):
    """Validate user email address."""
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
    """Validate admin email address."""
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

def validate_customer_email(email):
    """Validate customer email address."""
    if not email:
        return False, "Email is required"
    
    if '@' not in email:
        return False, "Email must contain @ symbol"
    
    if len(email) < 5:
        return False, "Email is too short"
    
    if len(email) > 100:
        return False, "Email is too long"
    
    return True, "Valid customer email"

# DUPLICATION ISSUE: Repeated database connection logic
def get_user_by_id(user_id):
    """Get user by ID from database."""
    import sqlite3
    
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result
    except Exception as e:
        if 'conn' in locals():
            conn.close()
        raise e

def get_user_by_email(email):
    """Get user by email from database."""
    import sqlite3
    
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        result = cursor.fetchone()
        conn.close()
        return result
    except Exception as e:
        if 'conn' in locals():
            conn.close()
        raise e

def get_user_by_username(username):
    """Get user by username from database."""
    import sqlite3
    
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        conn.close()
        return result
    except Exception as e:
        if 'conn' in locals():
            conn.close()
        raise e

# DUPLICATION ISSUE: Similar data processing functions
def process_sales_data(data):
    """Process sales data."""
    processed = []
    
    for item in data:
        # Clean the data
        cleaned_item = {}
        for key, value in item.items():
            if isinstance(value, str):
                cleaned_item[key] = value.strip().lower()
            else:
                cleaned_item[key] = value
        
        # Validate required fields
        if 'amount' not in cleaned_item or 'date' not in cleaned_item:
            continue
        
        # Add calculated fields
        cleaned_item['processed_date'] = get_current_timestamp()
        cleaned_item['category'] = 'sales'
        
        processed.append(cleaned_item)
    
    return processed

def process_expense_data(data):
    """Process expense data."""
    processed = []
    
    for item in data:
        # Clean the data
        cleaned_item = {}
        for key, value in item.items():
            if isinstance(value, str):
                cleaned_item[key] = value.strip().lower()
            else:
                cleaned_item[key] = value
        
        # Validate required fields
        if 'amount' not in cleaned_item or 'date' not in cleaned_item:
            continue
        
        # Add calculated fields
        cleaned_item['processed_date'] = get_current_timestamp()
        cleaned_item['category'] = 'expense'
        
        processed.append(cleaned_item)
    
    return processed

def process_inventory_data(data):
    """Process inventory data."""
    processed = []
    
    for item in data:
        # Clean the data
        cleaned_item = {}
        for key, value in item.items():
            if isinstance(value, str):
                cleaned_item[key] = value.strip().lower()
            else:
                cleaned_item[key] = value
        
        # Validate required fields
        if 'quantity' not in cleaned_item or 'product_id' not in cleaned_item:
            continue
        
        # Add calculated fields
        cleaned_item['processed_date'] = get_current_timestamp()
        cleaned_item['category'] = 'inventory'
        
        processed.append(cleaned_item)
    
    return processed

# DUPLICATION ISSUE: Repeated error handling patterns
class UserService:
    """Service with repeated error handling."""
    
    def create_user(self, user_data):
        """Create a new user."""
        try:
            # Validate input
            if not user_data:
                raise ValueError("User data is required")
            
            # Process user creation
            user = self._create_user_record(user_data)
            
            # Log success
            self._log_action("user_created", user['id'])
            
            return {"success": True, "user": user}
            
        except ValueError as e:
            self._log_error("create_user", str(e))
            return {"success": False, "error": str(e)}
        except Exception as e:
            self._log_error("create_user", f"Unexpected error: {str(e)}")
            return {"success": False, "error": "Internal server error"}
    
    def update_user(self, user_id, user_data):
        """Update an existing user."""
        try:
            # Validate input
            if not user_id:
                raise ValueError("User ID is required")
            if not user_data:
                raise ValueError("User data is required")
            
            # Process user update
            user = self._update_user_record(user_id, user_data)
            
            # Log success
            self._log_action("user_updated", user_id)
            
            return {"success": True, "user": user}
            
        except ValueError as e:
            self._log_error("update_user", str(e))
            return {"success": False, "error": str(e)}
        except Exception as e:
            self._log_error("update_user", f"Unexpected error: {str(e)}")
            return {"success": False, "error": "Internal server error"}
    
    def delete_user(self, user_id):
        """Delete a user."""
        try:
            # Validate input
            if not user_id:
                raise ValueError("User ID is required")
            
            # Process user deletion
            self._delete_user_record(user_id)
            
            # Log success
            self._log_action("user_deleted", user_id)
            
            return {"success": True}
            
        except ValueError as e:
            self._log_error("delete_user", str(e))
            return {"success": False, "error": str(e)}
        except Exception as e:
            self._log_error("delete_user", f"Unexpected error: {str(e)}")
            return {"success": False, "error": "Internal server error"}
    
    def _create_user_record(self, user_data):
        # Implementation stub
        return {"id": 1, "name": user_data.get("name")}
    
    def _update_user_record(self, user_id, user_data):
        # Implementation stub
        return {"id": user_id, "name": user_data.get("name")}
    
    def _delete_user_record(self, user_id):
        # Implementation stub
        pass
    
    def _log_action(self, action, user_id):
        # Implementation stub
        pass
    
    def _log_error(self, method, error):
        # Implementation stub
        pass

# DUPLICATION ISSUE: Copy-pasted utility functions
def format_currency_usd(amount):
    """Format amount as USD currency."""
    if amount is None:
        return "$0.00"
    
    if not isinstance(amount, (int, float)):
        try:
            amount = float(amount)
        except (ValueError, TypeError):
            return "$0.00"
    
    return f"${amount:.2f}"

def format_currency_eur(amount):
    """Format amount as EUR currency."""
    if amount is None:
        return "€0.00"
    
    if not isinstance(amount, (int, float)):
        try:
            amount = float(amount)
        except (ValueError, TypeError):
            return "€0.00"
    
    return f"€{amount:.2f}"

def format_currency_gbp(amount):
    """Format amount as GBP currency."""
    if amount is None:
        return "£0.00"
    
    if not isinstance(amount, (int, float)):
        try:
            amount = float(amount)
        except (ValueError, TypeError):
            return "£0.00"
    
    return f"£{amount:.2f}"

# Helper function
def get_current_timestamp():
    """Get current timestamp."""
    import datetime
    return datetime.datetime.now().isoformat()