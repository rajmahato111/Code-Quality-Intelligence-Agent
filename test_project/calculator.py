def add_numbers(a, b):
    return a + b

def divide_numbers(a, b):
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

class Calculator:
    def __init__(self):
        self.history = []
    
    def calculate(self, operation, x, y):
        if operation == "add":
            result = add_numbers(x, y)
        elif operation == "divide":
            result = divide_numbers(x, y)
        else:
            raise ValueError("Unsupported operation")
        
        self.history.append({
            'operation': operation,
            'operands': [x, y],
            'result': result
        })
        return result