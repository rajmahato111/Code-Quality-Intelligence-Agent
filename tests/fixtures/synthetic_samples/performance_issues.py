"""
Synthetic Python code samples with known performance issues.
These samples are designed to test performance analyzers.
"""

import time
import re

# PERFORMANCE ISSUE: Inefficient string concatenation
def build_large_string(items):
    """Inefficient string concatenation in loop."""
    result = ""
    for item in items:
        result += str(item) + ","  # O(n²) complexity
    return result

# PERFORMANCE ISSUE: Nested loops with high complexity
def find_duplicates_inefficient(list1, list2):
    """O(n²) algorithm when O(n) is possible."""
    duplicates = []
    for item1 in list1:
        for item2 in list2:  # Nested loop creates O(n²)
            if item1 == item2:
                duplicates.append(item1)
    return duplicates

# PERFORMANCE ISSUE: Inefficient data structure usage
def count_occurrences_slow(items):
    """Using list when dict would be more efficient."""
    counts = []  # Should use dict for O(1) lookup
    for item in items:
        found = False
        for count_item in counts:
            if count_item[0] == item:
                count_item[1] += 1
                found = True
                break
        if not found:
            counts.append([item, 1])
    return counts

# PERFORMANCE ISSUE: Unnecessary repeated computations
def calculate_expensive_operation(data):
    """Repeated expensive computations."""
    results = []
    for item in data:
        # Expensive computation repeated unnecessarily
        expensive_result = sum(range(1000)) * len(str(item))
        processed = expensive_result + item
        results.append(processed)
    return results

# PERFORMANCE ISSUE: Memory inefficient generator usage
def process_large_dataset(filename):
    """Loading entire file into memory unnecessarily."""
    with open(filename, 'r') as f:
        lines = f.readlines()  # Loads entire file into memory
    
    processed = []
    for line in lines:
        processed.append(line.strip().upper())
    return processed

# PERFORMANCE ISSUE: Inefficient regular expression usage
def validate_emails_slow(emails):
    """Compiling regex in loop."""
    valid_emails = []
    for email in emails:
        # Regex compiled on every iteration
        if re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            valid_emails.append(email)
    return valid_emails

# PERFORMANCE ISSUE: Unnecessary database queries in loop
class UserManager:
    """Inefficient database access patterns."""
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    def get_user_details(self, user_ids):
        """N+1 query problem."""
        users = []
        for user_id in user_ids:
            # Separate query for each user (N+1 problem)
            user = self.db.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            users.append(user)
        return users

# PERFORMANCE ISSUE: Inefficient sorting algorithm
def bubble_sort(arr):
    """Using inefficient O(n²) sorting algorithm."""
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr

# PERFORMANCE ISSUE: Memory leak through circular references
class Node:
    """Potential memory leak through circular references."""
    
    def __init__(self, value):
        self.value = value
        self.children = []
        self.parent = None
    
    def add_child(self, child):
        child.parent = self  # Circular reference
        self.children.append(child)

# PERFORMANCE ISSUE: Inefficient file I/O
def process_file_inefficiently(filename):
    """Reading file character by character."""
    result = ""
    with open(filename, 'r') as f:
        while True:
            char = f.read(1)  # Reading one character at a time
            if not char:
                break
            result += char.upper()
    return result

# PERFORMANCE ISSUE: Unnecessary object creation in loop
def format_numbers(numbers):
    """Creating unnecessary objects in loop."""
    formatted = []
    for num in numbers:
        # Creating new formatter object each time
        formatter = "{:.2f}".format
        formatted.append(formatter(num))
    return formatted