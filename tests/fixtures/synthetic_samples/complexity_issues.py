"""
Synthetic Python code samples with high complexity issues.
These samples are designed to test complexity analyzers.
"""

# COMPLEXITY ISSUE: Deeply nested conditions (high cyclomatic complexity)
def process_user_request(user, request_type, data, permissions, settings):
    """Function with excessive cyclomatic complexity."""
    if user:
        if user.is_authenticated:
            if request_type == 'create':
                if permissions.can_create:
                    if data:
                        if data.get('title'):
                            if len(data['title']) > 0:
                                if len(data['title']) < 100:
                                    if settings.allow_creation:
                                        if user.has_quota():
                                            if data.get('category'):
                                                if data['category'] in ['A', 'B', 'C']:
                                                    return create_item(data)
                                                else:
                                                    return error('Invalid category')
                                            else:
                                                return error('Missing category')
                                        else:
                                            return error('Quota exceeded')
                                    else:
                                        return error('Creation disabled')
                                else:
                                    return error('Title too long')
                            else:
                                return error('Empty title')
                        else:
                            return error('Missing title')
                    else:
                        return error('No data provided')
                else:
                    return error('No create permission')
            elif request_type == 'update':
                if permissions.can_update:
                    if data:
                        if data.get('id'):
                            return update_item(data)
                        else:
                            return error('Missing ID')
                    else:
                        return error('No data provided')
                else:
                    return error('No update permission')
            elif request_type == 'delete':
                if permissions.can_delete:
                    if data:
                        if data.get('id'):
                            return delete_item(data['id'])
                        else:
                            return error('Missing ID')
                    else:
                        return error('No data provided')
                else:
                    return error('No delete permission')
            else:
                return error('Unknown request type')
        else:
            return error('User not authenticated')
    else:
        return error('No user provided')

# COMPLEXITY ISSUE: Function with too many parameters
def create_user_account(username, password, email, first_name, last_name, 
                       phone, address, city, state, zip_code, country,
                       birth_date, gender, occupation, company, department,
                       manager, salary, start_date, benefits, preferences,
                       notifications, privacy_settings, security_questions):
    """Function with excessive number of parameters."""
    # Implementation would go here
    pass

# COMPLEXITY ISSUE: Large class with too many methods and responsibilities
class UserManagementSystem:
    """Class with too many responsibilities (violates SRP)."""
    
    def __init__(self):
        self.users = {}
        self.sessions = {}
        self.permissions = {}
        self.audit_log = []
        self.email_service = None
        self.database = None
    
    # User management methods
    def create_user(self, user_data): pass
    def update_user(self, user_id, data): pass
    def delete_user(self, user_id): pass
    def get_user(self, user_id): pass
    def list_users(self, filters): pass
    def search_users(self, query): pass
    def validate_user_data(self, data): pass
    def hash_password(self, password): pass
    def verify_password(self, password, hash): pass
    
    # Session management methods
    def create_session(self, user_id): pass
    def validate_session(self, session_id): pass
    def destroy_session(self, session_id): pass
    def cleanup_expired_sessions(self): pass
    def get_session_info(self, session_id): pass
    
    # Permission management methods
    def assign_permission(self, user_id, permission): pass
    def revoke_permission(self, user_id, permission): pass
    def check_permission(self, user_id, permission): pass
    def list_user_permissions(self, user_id): pass
    def create_role(self, role_name, permissions): pass
    def assign_role(self, user_id, role): pass
    
    # Email methods
    def send_welcome_email(self, user_id): pass
    def send_password_reset_email(self, user_id): pass
    def send_notification_email(self, user_id, message): pass
    def validate_email_address(self, email): pass
    
    # Database methods
    def save_user_to_database(self, user): pass
    def load_user_from_database(self, user_id): pass
    def update_user_in_database(self, user_id, data): pass
    def delete_user_from_database(self, user_id): pass
    
    # Audit methods
    def log_user_action(self, user_id, action): pass
    def get_audit_log(self, user_id): pass
    def export_audit_log(self, format): pass
    
    # Utility methods
    def generate_user_id(self): pass
    def validate_phone_number(self, phone): pass
    def format_user_display_name(self, user): pass
    def calculate_user_age(self, birth_date): pass

# COMPLEXITY ISSUE: Deeply nested loops
def process_matrix_data(matrices):
    """Function with deeply nested loops."""
    results = []
    for matrix in matrices:
        matrix_result = []
        for row_idx, row in enumerate(matrix):
            row_result = []
            for col_idx, cell in enumerate(row):
                cell_result = []
                for char_idx, char in enumerate(str(cell)):
                    for bit_idx in range(8):
                        if ord(char) & (1 << bit_idx):
                            for operation in ['add', 'subtract', 'multiply']:
                                for factor in range(1, 10):
                                    cell_result.append(
                                        perform_operation(operation, bit_idx, factor)
                                    )
                row_result.append(cell_result)
            matrix_result.append(row_result)
        results.append(matrix_result)
    return results

# COMPLEXITY ISSUE: Long method with multiple responsibilities
def process_order(order_data):
    """Method that does too many things."""
    # Validate order data
    if not order_data:
        raise ValueError("Order data is required")
    
    if 'customer_id' not in order_data:
        raise ValueError("Customer ID is required")
    
    if 'items' not in order_data or not order_data['items']:
        raise ValueError("Order items are required")
    
    # Calculate totals
    subtotal = 0
    tax_amount = 0
    shipping_cost = 0
    
    for item in order_data['items']:
        item_price = item['price'] * item['quantity']
        subtotal += item_price
        
        if item.get('taxable', True):
            tax_amount += item_price * 0.08
    
    # Apply discounts
    discount_amount = 0
    if order_data.get('discount_code'):
        discount_code = order_data['discount_code']
        if discount_code == 'SAVE10':
            discount_amount = subtotal * 0.10
        elif discount_code == 'SAVE20':
            discount_amount = subtotal * 0.20
        elif discount_code == 'FREESHIP':
            shipping_cost = 0
    
    # Calculate shipping
    if shipping_cost == 0:  # Not already set to free
        total_weight = sum(item.get('weight', 0) * item['quantity'] 
                          for item in order_data['items'])
        if total_weight < 5:
            shipping_cost = 5.99
        elif total_weight < 20:
            shipping_cost = 12.99
        else:
            shipping_cost = 19.99
    
    # Process payment
    total_amount = subtotal + tax_amount + shipping_cost - discount_amount
    
    payment_result = process_payment(
        order_data['payment_method'],
        total_amount,
        order_data['customer_id']
    )
    
    if not payment_result['success']:
        raise Exception(f"Payment failed: {payment_result['error']}")
    
    # Update inventory
    for item in order_data['items']:
        update_inventory(item['product_id'], -item['quantity'])
    
    # Create order record
    order_id = generate_order_id()
    order_record = {
        'id': order_id,
        'customer_id': order_data['customer_id'],
        'items': order_data['items'],
        'subtotal': subtotal,
        'tax_amount': tax_amount,
        'shipping_cost': shipping_cost,
        'discount_amount': discount_amount,
        'total_amount': total_amount,
        'payment_id': payment_result['payment_id'],
        'status': 'confirmed'
    }
    
    save_order(order_record)
    
    # Send confirmation email
    send_order_confirmation_email(order_data['customer_id'], order_record)
    
    # Log the order
    log_order_event(order_id, 'order_created')
    
    return order_record

# Helper functions (stubs)
def create_item(data): return {'id': 1, 'status': 'created'}
def update_item(data): return {'id': data['id'], 'status': 'updated'}
def delete_item(item_id): return {'id': item_id, 'status': 'deleted'}
def error(message): return {'error': message}
def perform_operation(op, a, b): return a + b
def process_payment(method, amount, customer_id): return {'success': True, 'payment_id': '123'}
def update_inventory(product_id, quantity): pass
def generate_order_id(): return 'ORD-123'
def save_order(order): pass
def send_order_confirmation_email(customer_id, order): pass
def log_order_event(order_id, event): pass