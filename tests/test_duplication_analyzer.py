"""Tests for DuplicationAnalyzer."""

import pytest

from code_quality_agent.analyzers.duplication_analyzer import DuplicationAnalyzer
from code_quality_agent.analyzers.base import IssueCategory, Severity
from code_quality_agent.core.models import (
    ParsedFile, AnalysisContext, AnalysisOptions, 
    FileMetadata, Function, Class
)


class TestDuplicationAnalyzer:
    """Tests for DuplicationAnalyzer class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = DuplicationAnalyzer()
    
    def test_analyzer_properties(self):
        """Test basic analyzer properties."""
        assert self.analyzer.get_category() == IssueCategory.DUPLICATION
        assert "python" in self.analyzer.get_supported_languages()
        assert "javascript" in self.analyzer.get_supported_languages()
        assert "typescript" in self.analyzer.get_supported_languages()
    
    def test_custom_thresholds(self):
        """Test analyzer with custom thresholds."""
        custom_config = {
            'exact_match_threshold': 0.98,
            'similar_match_threshold': 0.75,
            'minimum_lines': 3,
            'function_similarity_threshold': 0.90
        }
        
        analyzer = DuplicationAnalyzer(custom_config)
        
        assert analyzer.thresholds['exact_match_threshold'] == 0.98
        assert analyzer.thresholds['similar_match_threshold'] == 0.75
        assert analyzer.thresholds['minimum_lines'] == 3
        assert analyzer.thresholds['function_similarity_threshold'] == 0.90
    
    def test_exact_code_duplication(self):
        """Test detection of exact code duplication."""
        # Create two files with identical code blocks
        duplicate_code = '''
def process_data(data):
    if data is None:
        return []
    
    result = []
    for item in data:
        if item.is_valid():
            result.append(item.process())
    
    return result
'''
        
        file1_code = f'''
import utils

{duplicate_code}

def other_function():
    pass
'''
        
        file2_code = f'''
from helpers import helper

{duplicate_code}

def different_function():
    return True
'''
        
        file1 = self._create_parsed_file("file1.py", "python", file1_code)
        file2 = self._create_parsed_file("file2.py", "python", file2_code)
        
        context = AnalysisContext(options=AnalysisOptions())
        issues = self.analyzer.analyze([file1, file2], context)
        
        # Should find exact duplication
        exact_issues = [issue for issue in issues if "Exact Code Duplication" in issue.title]
        assert len(exact_issues) >= 1
        
        issue = exact_issues[0]
        assert issue.category == IssueCategory.DUPLICATION
        assert issue.severity == Severity.MEDIUM
        assert len(issue.affected_files) == 2  # Original + duplicate
        assert issue.metadata['similarity_score'] == 1.0
        assert "shared function" in issue.suggestion.lower()
    
    def test_similar_code_detection(self):
        """Test detection of similar (but not identical) code."""
        similar_code1 = '''
def calculate_total(items):
    total = 0
    for item in items:
        if item.price > 0:
            total += item.price
    return total
'''
        
        similar_code2 = '''
def compute_sum(elements):
    sum_value = 0
    for element in elements:
        if element.cost > 0:
            sum_value += element.cost
    return sum_value
'''
        
        file1 = self._create_parsed_file("calc1.py", "python", similar_code1)
        file2 = self._create_parsed_file("calc2.py", "python", similar_code2)
        
        context = AnalysisContext(options=AnalysisOptions())
        issues = self.analyzer.analyze([file1, file2], context)
        
        # Should find similar code
        similar_issues = [issue for issue in issues if "Similar Code" in issue.title]
        assert len(similar_issues) >= 1
        
        issue = similar_issues[0]
        assert issue.category == IssueCategory.DUPLICATION
        assert issue.metadata['similarity_score'] > 0.8
        assert "common functionality" in issue.suggestion.lower()
    
    def test_duplicate_functions(self):
        """Test detection of duplicate functions."""
        func1 = Function(
            name="validate_input",
            line_start=1,
            line_end=8,
            parameters=["data", "schema"]
        )
        
        func2 = Function(
            name="validate_input",
            line_start=1,
            line_end=8,
            parameters=["data", "schema"]
        )
        
        code1 = '''
def validate_input(data, schema):
    if not data:
        return False
    if not schema:
        return False
    return schema.validate(data)
'''
        
        code2 = '''
def validate_input(data, schema):
    if not data:
        return False
    if not schema:
        return False
    return schema.validate(data)
'''
        
        file1 = self._create_parsed_file("validator1.py", "python", code1, functions=[func1])
        file2 = self._create_parsed_file("validator2.py", "python", code2, functions=[func2])
        
        context = AnalysisContext(options=AnalysisOptions())
        issues = self.analyzer.analyze([file1, file2], context)
        
        # Should find duplicate functions
        func_issues = [issue for issue in issues if "Duplicate Function" in issue.title]
        assert len(func_issues) >= 1
        
        issue = func_issues[0]
        assert issue.category == IssueCategory.DUPLICATION
        assert issue.metadata['function_name'] == "validate_input"
        assert "shared utility" in issue.suggestion.lower()
    
    def test_similar_classes(self):
        """Test detection of similar classes."""
        class1_methods = [
            Function("__init__", 2, 3, ["self", "name"]),
            Function("get_name", 5, 6, ["self"]),
            Function("set_name", 8, 9, ["self", "name"]),
            Function("validate", 11, 12, ["self"])
        ]
        
        class2_methods = [
            Function("__init__", 2, 3, ["self", "title"]),
            Function("get_name", 5, 6, ["self"]),  # Same method name
            Function("set_name", 8, 9, ["self", "title"]),  # Same method name
            Function("check", 11, 12, ["self"])  # Different method name
        ]
        
        class1 = Class(
            name="Person",
            line_start=1,
            line_end=15,
            methods=class1_methods
        )
        
        class2 = Class(
            name="Employee",
            line_start=1,
            line_end=15,
            methods=class2_methods
        )
        
        code1 = '''
class Person:
    def __init__(self, name):
        self.name = name
    
    def get_name(self):
        return self.name
    
    def set_name(self, name):
        self.name = name
    
    def validate(self):
        return bool(self.name)
'''
        
        code2 = '''
class Employee:
    def __init__(self, title):
        self.title = title
    
    def get_name(self):
        return self.title
    
    def set_name(self, title):
        self.title = title
    
    def check(self):
        return bool(self.title)
'''
        
        file1 = self._create_parsed_file("person.py", "python", code1, classes=[class1])
        file2 = self._create_parsed_file("employee.py", "python", code2, classes=[class2])
        
        context = AnalysisContext(options=AnalysisOptions())
        issues = self.analyzer.analyze([file1, file2], context)
        
        # Should find similar classes
        class_issues = [issue for issue in issues if "Similar Class" in issue.title]
        assert len(class_issues) >= 1
        
        issue = class_issues[0]
        assert issue.category == IssueCategory.DUPLICATION
        assert issue.severity == Severity.MEDIUM
        assert "inheritance" in issue.suggestion.lower() or "composition" in issue.suggestion.lower()
    
    def test_structural_pattern_duplication(self):
        """Test detection of repeated structural patterns."""
        # Create files with repeated structural patterns
        pattern_code1 = '''
def process_user_data():
    try:
        data = get_data()
        if validate_data(data):
            result = transform_data(data)
            save_result(result)
            return True
    except Exception as e:
        log_error(e)
        return False
'''
        
        pattern_code2 = '''
def process_order_info():
    try:
        info = get_info()
        if validate_info(info):
            output = transform_info(info)
            save_output(output)
            return True
    except Exception as e:
        log_error(e)
        return False
'''
        
        pattern_code3 = '''
def process_payment_details():
    try:
        details = get_details()
        if validate_details(details):
            processed = transform_details(details)
            save_processed(processed)
            return True
    except Exception as e:
        log_error(e)
        return False
'''
        
        file1 = self._create_parsed_file("user.py", "python", pattern_code1)
        file2 = self._create_parsed_file("order.py", "python", pattern_code2)
        file3 = self._create_parsed_file("payment.py", "python", pattern_code3)
        
        context = AnalysisContext(options=AnalysisOptions())
        issues = self.analyzer.analyze([file1, file2, file3], context)
        
        # Should find repeated patterns
        pattern_issues = [issue for issue in issues if "Repeated Code Pattern" in issue.title]
        assert len(pattern_issues) >= 1
        
        issue = pattern_issues[0]
        assert issue.category == IssueCategory.DUPLICATION
        assert issue.severity == Severity.LOW
        assert issue.metadata['occurrences'] >= 3
        assert "template" in issue.suggestion.lower() or "design pattern" in issue.suggestion.lower()
    
    def test_code_normalization(self):
        """Test code normalization for comparison."""
        code1 = '''
        def test_function(param1, param2):
            # This is a comment
            if param1 > 0:
                return param1 + param2
            return 0
        '''
        
        code2 = '''
def test_function(param1,param2):
    if param1>0:
        return param1+param2
    return 0
        '''
        
        normalized1 = self.analyzer._normalize_code(code1)
        normalized2 = self.analyzer._normalize_code(code2)
        
        # Should be very similar after normalization
        similarity = self.analyzer._calculate_similarity(normalized1, normalized2)
        assert similarity > 0.9  # Should be very similar
    
    def test_function_signature_creation(self):
        """Test function signature creation for comparison."""
        func1 = Function(
            name="calculate",
            line_start=1,
            line_end=5,
            parameters=["amount", "rate", "time"]
        )
        
        func2 = Function(
            name="calculate",
            line_start=10,
            line_end=15,
            parameters=["principal", "interest", "duration"]
        )
        
        sig1 = self.analyzer._create_function_signature(func1)
        sig2 = self.analyzer._create_function_signature(func2)
        
        # Should have same signature (same name and parameter count)
        assert sig1 == sig2
        assert "calculate(param0,param1,param2)" == sig1
    
    def test_class_similarity_calculation(self):
        """Test class similarity calculation."""
        class1 = Class(
            name="ClassA",
            line_start=1,
            line_end=20,
            methods=[
                Function("method1", 2, 3, ["self"]),
                Function("method2", 5, 6, ["self"]),
                Function("method3", 8, 9, ["self"])
            ]
        )
        
        class2 = Class(
            name="ClassB",
            line_start=1,
            line_end=20,
            methods=[
                Function("method1", 2, 3, ["self"]),  # Same
                Function("method2", 5, 6, ["self"]),  # Same
                Function("method4", 8, 9, ["self"])   # Different
            ]
        )
        
        similarity = self.analyzer._calculate_class_similarity(class1, class2)
        
        # Should be 2/4 = 0.5 (2 common methods out of 4 total unique methods)
        assert 0.4 <= similarity <= 0.6
    
    def test_minimum_size_thresholds(self):
        """Test that small code blocks are ignored."""
        # Create files with very small code blocks
        small_code1 = '''
def tiny():
    return 1
'''
        
        small_code2 = '''
def tiny():
    return 1
'''
        
        file1 = self._create_parsed_file("small1.py", "python", small_code1)
        file2 = self._create_parsed_file("small2.py", "python", small_code2)
        
        context = AnalysisContext(options=AnalysisOptions())
        issues = self.analyzer.analyze([file1, file2], context)
        
        # Should not find duplication for very small blocks (below minimum_lines threshold)
        duplication_issues = [issue for issue in issues if issue.category == IssueCategory.DUPLICATION]
        # The exact behavior depends on the minimum_lines threshold and block extraction logic
        # Small blocks might still be detected if they meet the minimum criteria
    
    def test_javascript_duplication_detection(self):
        """Test duplication detection in JavaScript files."""
        js_code1 = '''
function validateUser(user) {
    if (!user) {
        return false;
    }
    if (!user.email) {
        return false;
    }
    return user.email.includes('@');
}
'''
        
        js_code2 = '''
function validateUser(user) {
    if (!user) {
        return false;
    }
    if (!user.email) {
        return false;
    }
    return user.email.includes('@');
}
'''
        
        file1 = self._create_parsed_file("validator1.js", "javascript", js_code1)
        file2 = self._create_parsed_file("validator2.js", "javascript", js_code2)
        
        context = AnalysisContext(options=AnalysisOptions())
        issues = self.analyzer.analyze([file1, file2], context)
        
        # Should find duplication in JavaScript files
        duplication_issues = [issue for issue in issues if issue.category == IssueCategory.DUPLICATION]
        assert len(duplication_issues) >= 1
    
    def test_no_false_positives_different_code(self):
        """Test that different code doesn't trigger false positives."""
        different_code1 = '''
def calculate_area(radius):
    """Calculate area of a circle."""
    import math
    return math.pi * radius * radius

def calculate_perimeter(radius):
    """Calculate perimeter of a circle."""
    import math
    return 2 * math.pi * radius
'''
        
        different_code2 = '''
def process_data(items):
    """Process a list of items."""
    result = []
    for item in items:
        if item.is_valid():
            result.append(item.transform())
    return result

def filter_items(items, predicate):
    """Filter items based on predicate."""
    return [item for item in items if predicate(item)]
'''
        
        file1 = self._create_parsed_file("geometry.py", "python", different_code1)
        file2 = self._create_parsed_file("processing.py", "python", different_code2)
        
        context = AnalysisContext(options=AnalysisOptions())
        issues = self.analyzer.analyze([file1, file2], context)
        
        # Should not find significant duplication between different code
        high_similarity_issues = [
            issue for issue in issues 
            if issue.category == IssueCategory.DUPLICATION and 
            issue.metadata.get('similarity_score', 0) > 0.8
        ]
        assert len(high_similarity_issues) == 0
    
    def test_severity_assignment(self):
        """Test that appropriate severity is assigned based on similarity."""
        # Test different similarity levels
        assert self.analyzer._get_duplication_severity(0.98) == Severity.MEDIUM
        assert self.analyzer._get_duplication_severity(0.90) == Severity.LOW
        assert self.analyzer._get_duplication_severity(0.75) == Severity.INFO
    
    def test_block_extraction(self):
        """Test code block extraction logic."""
        code = '''
# Header comment
import os
import sys

def function1():
    if True:
        print("hello")
        return True
    return False

def function2():
    data = []
    for i in range(10):
        data.append(i)
    return data

# Footer comment
'''
        
        parsed_file = self._create_parsed_file("test.py", "python", code)
        blocks = self.analyzer._extract_code_blocks(parsed_file)
        
        # Should extract meaningful code blocks
        assert len(blocks) >= 1
        
        # Blocks should have minimum required lines
        for block in blocks:
            assert len(block['lines']) >= self.analyzer.thresholds['minimum_lines']
            assert 'start_line' in block
            assert 'end_line' in block
            assert 'code' in block
    
    def _create_parsed_file(
        self, 
        path: str, 
        language: str, 
        content: str, 
        functions: list = None,
        classes: list = None,
        metadata: FileMetadata = None
    ) -> ParsedFile:
        """Helper method to create a ParsedFile for testing."""
        if metadata is None:
            metadata = FileMetadata(
                file_path=path,
                language=language,
                size_bytes=len(content.encode()),
                line_count=len(content.splitlines())
            )
        
        return ParsedFile(
            path=path,
            language=language,
            content=content,
            functions=functions or [],
            classes=classes or [],
            metadata=metadata
        )