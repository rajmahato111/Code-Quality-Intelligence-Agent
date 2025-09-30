"""Tests for DocumentationAnalyzer."""

import pytest

from code_quality_agent.analyzers.documentation_analyzer import DocumentationAnalyzer
from code_quality_agent.analyzers.base import IssueCategory, Severity
from code_quality_agent.core.models import (
    ParsedFile, AnalysisContext, AnalysisOptions, 
    FileMetadata, Function, Class
)


class TestDocumentationAnalyzer:
    """Tests for DocumentationAnalyzer class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = DocumentationAnalyzer()
    
    def test_analyzer_properties(self):
        """Test basic analyzer properties."""
        assert self.analyzer.get_category() == IssueCategory.DOCUMENTATION
        assert "python" in self.analyzer.get_supported_languages()
        assert "javascript" in self.analyzer.get_supported_languages()
        assert "typescript" in self.analyzer.get_supported_languages()
    
    def test_custom_thresholds(self):
        """Test analyzer with custom thresholds."""
        custom_config = {
            'min_public_function_doc_coverage': 0.9,
            'min_class_doc_coverage': 0.95,
            'min_docstring_length': 20,
            'max_function_params_without_doc': 2
        }
        
        analyzer = DocumentationAnalyzer(custom_config)
        
        assert analyzer.thresholds['min_public_function_doc_coverage'] == 0.9
        assert analyzer.thresholds['min_class_doc_coverage'] == 0.95
        assert analyzer.thresholds['min_docstring_length'] == 20
        assert analyzer.thresholds['max_function_params_without_doc'] == 2
    
    def test_missing_function_docstring(self):
        """Test detection of missing function docstrings."""
        # Public function without docstring
        public_func = Function(
            name="calculate_total",
            line_start=1,
            line_end=5,
            parameters=["items", "tax_rate"]
        )
        
        code = '''
def calculate_total(items, tax_rate):
    total = sum(item.price for item in items)
    return total * (1 + tax_rate)
'''
        
        parsed_file = self._create_parsed_file(
            "calculator.py", 
            "python", 
            code,
            functions=[public_func]
        )
        
        context = AnalysisContext(options=AnalysisOptions())
        issues = self.analyzer.analyze([parsed_file], context)
        
        # Should find missing docstring issue
        missing_doc_issues = [issue for issue in issues if "Missing Docstring" in issue.title]
        assert len(missing_doc_issues) >= 1
        
        issue = missing_doc_issues[0]
        assert issue.category == IssueCategory.DOCUMENTATION
        assert issue.severity == Severity.HIGH  # Public function
        assert "Add a docstring" in issue.suggestion
    
    def test_missing_class_docstring(self):
        """Test detection of missing class docstrings."""
        # Class without docstring
        undocumented_class = Class(
            name="DataProcessor",
            line_start=1,
            line_end=10,
            methods=[
                Function("process", 3, 5, ["self", "data"]),
                Function("validate", 7, 9, ["self", "data"])
            ]
        )
        
        code = '''
class DataProcessor:
    def process(self, data):
        return data.upper()
    
    def validate(self, data):
        return bool(data)
'''
        
        parsed_file = self._create_parsed_file(
            "processor.py",
            "python",
            code,
            classes=[undocumented_class]
        )
        
        context = AnalysisContext(options=AnalysisOptions())
        issues = self.analyzer.analyze([parsed_file], context)
        
        # Should find missing class docstring
        class_doc_issues = [issue for issue in issues if "Missing Docstring for Class" in issue.title]
        assert len(class_doc_issues) >= 1
        
        issue = class_doc_issues[0]
        assert issue.category == IssueCategory.DOCUMENTATION
        assert issue.severity == Severity.HIGH
        assert "class docstring" in issue.suggestion.lower()
    
    def test_short_docstring(self):
        """Test detection of overly short docstrings."""
        # Function with very short docstring
        short_doc_func = Function(
            name="add",
            line_start=1,
            line_end=3,
            parameters=["a", "b"],
            docstring="Add."  # Very short
        )
        
        code = '''
def add(a, b):
    """Add."""
    return a + b
'''
        
        parsed_file = self._create_parsed_file(
            "math.py",
            "python",
            code,
            functions=[short_doc_func]
        )
        
        context = AnalysisContext(options=AnalysisOptions())
        issues = self.analyzer.analyze([parsed_file], context)
        
        # Should find short docstring issue
        short_doc_issues = [issue for issue in issues if "Short Function Docstring" in issue.title]
        assert len(short_doc_issues) >= 1
        
        issue = short_doc_issues[0]
        assert issue.category == IssueCategory.DOCUMENTATION
        assert issue.severity == Severity.LOW
        assert "Expand the docstring" in issue.suggestion
    
    def test_placeholder_docstring(self):
        """Test detection of placeholder docstrings."""
        # Function with placeholder docstring
        placeholder_func = Function(
            name="process_data",
            line_start=1,
            line_end=3,
            parameters=["data"],
            docstring="TODO"  # Placeholder
        )
        
        code = '''
def process_data(data):
    """TODO"""
    return data.processed()
'''
        
        parsed_file = self._create_parsed_file(
            "processor.py",
            "python",
            code,
            functions=[placeholder_func]
        )
        
        context = AnalysisContext(options=AnalysisOptions())
        issues = self.analyzer.analyze([parsed_file], context)
        
        # Should find placeholder docstring issue
        placeholder_issues = [issue for issue in issues if "Placeholder Function Docstring" in issue.title]
        assert len(placeholder_issues) >= 1
        
        issue = placeholder_issues[0]
        assert issue.category == IssueCategory.DOCUMENTATION
        assert issue.severity == Severity.MEDIUM
        assert "Replace the placeholder" in issue.suggestion
    
    def test_undocumented_parameters(self):
        """Test detection of undocumented parameters."""
        # Function with many parameters but no parameter documentation
        many_params_func = Function(
            name="complex_calculation",
            line_start=1,
            line_end=5,
            parameters=["base_amount", "tax_rate", "discount", "shipping", "currency"],
            docstring="Performs a complex calculation."
        )
        
        code = '''
def complex_calculation(base_amount, tax_rate, discount, shipping, currency):
    """Performs a complex calculation."""
    # Complex calculation logic here
    return result
'''
        
        parsed_file = self._create_parsed_file(
            "calculator.py",
            "python",
            code,
            functions=[many_params_func]
        )
        
        context = AnalysisContext(options=AnalysisOptions())
        issues = self.analyzer.analyze([parsed_file], context)
        
        # Should find undocumented parameters issue
        param_issues = [issue for issue in issues if "Undocumented Parameters" in issue.title]
        assert len(param_issues) >= 1
        
        issue = param_issues[0]
        assert issue.category == IssueCategory.DOCUMENTATION
        assert issue.severity == Severity.MEDIUM
        assert "parameter documentation" in issue.suggestion.lower()
    
    def test_low_method_documentation_coverage(self):
        """Test detection of low method documentation coverage in classes."""
        # Class with many undocumented methods
        poorly_documented_class = Class(
            name="APIClient",
            line_start=1,
            line_end=20,
            methods=[
                Function("get", 3, 5, ["self", "url"]),  # No docstring
                Function("post", 7, 9, ["self", "url", "data"]),  # No docstring
                Function("put", 11, 13, ["self", "url", "data"]),  # No docstring
                Function("delete", 15, 17, ["self", "url"], docstring="Delete resource."),  # Has docstring
            ],
            docstring="API client for REST operations."
        )
        
        code = '''
class APIClient:
    """API client for REST operations."""
    
    def get(self, url):
        return self._request('GET', url)
    
    def post(self, url, data):
        return self._request('POST', url, data)
    
    def put(self, url, data):
        return self._request('PUT', url, data)
    
    def delete(self, url):
        """Delete resource."""
        return self._request('DELETE', url)
'''
        
        parsed_file = self._create_parsed_file(
            "api_client.py",
            "python",
            code,
            classes=[poorly_documented_class]
        )
        
        context = AnalysisContext(options=AnalysisOptions())
        issues = self.analyzer.analyze([parsed_file], context)
        
        # Should find low method coverage issue
        coverage_issues = [issue for issue in issues if "Low Method Documentation Coverage" in issue.title]
        assert len(coverage_issues) >= 1
        
        issue = coverage_issues[0]
        assert issue.category == IssueCategory.DOCUMENTATION
        assert issue.severity == Severity.MEDIUM
        assert issue.metadata['coverage'] < 0.9
    
    def test_missing_module_documentation(self):
        """Test detection of missing module documentation."""
        # Module with many components but no module docstring
        code = '''
import os
import sys
from typing import List, Dict

def function1():
    pass

def function2():
    pass

def function3():
    pass

def function4():
    pass

class Class1:
    pass

class Class2:
    pass
'''
        
        functions = [Function(f"function{i}", i*3, i*3+2, []) for i in range(1, 5)]
        classes = [Class(f"Class{i}", i*10, i*10+5, []) for i in range(1, 3)]
        
        parsed_file = self._create_parsed_file(
            "large_module.py",
            "python",
            code,
            functions=functions,
            classes=classes
        )
        
        context = AnalysisContext(options=AnalysisOptions())
        issues = self.analyzer.analyze([parsed_file], context)
        
        # Should find missing module documentation
        module_doc_issues = [issue for issue in issues if "Missing Module Documentation" in issue.title]
        assert len(module_doc_issues) >= 1
        
        issue = module_doc_issues[0]
        assert issue.category == IssueCategory.DOCUMENTATION
        assert issue.severity == Severity.LOW
        assert "module docstring" in issue.suggestion.lower()
    
    def test_todo_comments(self):
        """Test detection of TODO comments."""
        code = '''
def process_data(data):
    """Process the data."""
    # TODO: Add validation logic here
    result = data.process()
    # TODO: Implement error handling
    return result
'''
        
        parsed_file = self._create_parsed_file("processor.py", "python", code)
        context = AnalysisContext(options=AnalysisOptions())
        issues = self.analyzer.analyze([parsed_file], context)
        
        # Should find TODO comments
        todo_issues = [issue for issue in issues if "TODO Comment Found" in issue.title]
        assert len(todo_issues) >= 2
        
        issue = todo_issues[0]
        assert issue.category == IssueCategory.DOCUMENTATION
        assert issue.severity == Severity.INFO
        assert "task or issue" in issue.suggestion.lower()
    
    def test_fixme_comments(self):
        """Test detection of FIXME comments."""
        code = '''
def calculate(x, y):
    """Calculate something."""
    # FIXME: This calculation is incorrect
    result = x + y  # Should be x * y
    # FIXME: Handle division by zero
    return result / (x - y)
'''
        
        parsed_file = self._create_parsed_file("calculator.py", "python", code)
        context = AnalysisContext(options=AnalysisOptions())
        issues = self.analyzer.analyze([parsed_file], context)
        
        # Should find FIXME comments
        fixme_issues = [issue for issue in issues if "FIXME Comment Found" in issue.title]
        assert len(fixme_issues) >= 2
        
        issue = fixme_issues[0]
        assert issue.category == IssueCategory.DOCUMENTATION
        assert issue.severity == Severity.LOW
        assert "Address the issue" in issue.suggestion
    
    def test_outdated_comments(self):
        """Test detection of potentially outdated comments."""
        code = '''
def legacy_function():
    """Process data the old way."""
    # This is deprecated as of version 1.2
    # TODO: Remove this in 2020
    # Legacy implementation from 2018
    return old_process()
'''
        
        parsed_file = self._create_parsed_file("legacy.py", "python", code)
        context = AnalysisContext(options=AnalysisOptions())
        issues = self.analyzer.analyze([parsed_file], context)
        
        # Should find outdated comments
        outdated_issues = [issue for issue in issues if "Potentially Outdated Comment" in issue.title]
        assert len(outdated_issues) >= 1
        
        issue = outdated_issues[0]
        assert issue.category == IssueCategory.DOCUMENTATION
        assert issue.severity == Severity.INFO
        assert "Review this comment" in issue.suggestion
    
    def test_commented_out_code(self):
        """Test detection of commented-out code."""
        code = '''
def active_function():
    """This function is active."""
    return "active"

# def old_function():
#     """This function is commented out."""
#     old_logic = True
#     if old_logic:
#         return "old"
#     return None

def another_active_function():
    """Another active function."""
    return "also active"
'''
        
        parsed_file = self._create_parsed_file("mixed.py", "python", code)
        context = AnalysisContext(options=AnalysisOptions())
        issues = self.analyzer.analyze([parsed_file], context)
        
        # Should find commented-out code
        commented_code_issues = [issue for issue in issues if "Commented-Out Code Found" in issue.title]
        assert len(commented_code_issues) >= 1
        
        issue = commented_code_issues[0]
        assert issue.category == IssueCategory.DOCUMENTATION
        assert issue.severity == Severity.LOW
        assert "Remove commented-out code" in issue.suggestion
    
    def test_insufficient_api_documentation(self):
        """Test detection of insufficient API documentation."""
        # API module with poorly documented public functions
        api_functions = [
            Function("get_user", 1, 3, ["user_id"]),  # No docstring
            Function("create_user", 5, 7, ["user_data"]),  # No docstring
            Function("update_user", 9, 11, ["user_id", "data"]),  # No docstring
            Function("delete_user", 13, 15, ["user_id"]),  # No docstring
            Function("list_users", 17, 19, ["filters"]),  # No docstring
            Function("_internal_helper", 21, 23, ["data"])  # Private, should be ignored
        ]
        
        code = '''
def get_user(user_id):
    return database.get(user_id)

def create_user(user_data):
    return database.create(user_data)

def update_user(user_id, data):
    return database.update(user_id, data)

def delete_user(user_id):
    return database.delete(user_id)

def list_users(filters):
    return database.list(filters)

def _internal_helper(data):
    return data.processed()
'''
        
        parsed_file = self._create_parsed_file(
            "api/users.py",  # API path
            "python",
            code,
            functions=api_functions
        )
        
        context = AnalysisContext(options=AnalysisOptions())
        issues = self.analyzer.analyze([parsed_file], context)
        
        # Should find insufficient API documentation
        api_doc_issues = [issue for issue in issues if "Insufficient API Documentation" in issue.title]
        assert len(api_doc_issues) >= 1
        
        issue = api_doc_issues[0]
        assert issue.category == IssueCategory.DOCUMENTATION
        assert issue.severity == Severity.HIGH
        assert "comprehensive documentation" in issue.suggestion.lower()
    
    def test_inconsistent_documentation_style(self):
        """Test detection of inconsistent documentation styles."""
        # Functions with different docstring styles
        mixed_style_functions = [
            Function("google_style", 1, 5, ["param1", "param2"], 
                    docstring="Function with Google style.\n\nArgs:\n    param1: First parameter\n    param2: Second parameter\n\nReturns:\n    Result value"),
            Function("sphinx_style", 7, 11, ["param1", "param2"],
                    docstring="Function with Sphinx style.\n\n:param param1: First parameter\n:param param2: Second parameter\n:returns: Result value"),
            Function("numpy_style", 13, 17, ["param1", "param2"],
                    docstring="Function with NumPy style.\n\nParameters\n----------\nparam1 : str\n    First parameter\nReturns\n-------\nstr\n    Result value")
        ]
        
        code = '''
def google_style(param1, param2):
    """Function with Google style.
    
    Args:
        param1: First parameter
        param2: Second parameter
    
    Returns:
        Result value
    """
    return param1 + param2

def sphinx_style(param1, param2):
    """Function with Sphinx style.
    
    :param param1: First parameter
    :param param2: Second parameter
    :returns: Result value
    """
    return param1 + param2

def numpy_style(param1, param2):
    """Function with NumPy style.
    
    Parameters
    ----------
    param1 : str
        First parameter
    
    Returns
    -------
    str
        Result value
    """
    return param1 + param2
'''
        
        parsed_file = self._create_parsed_file(
            "mixed_styles.py",
            "python",
            code,
            functions=mixed_style_functions
        )
        
        context = AnalysisContext(options=AnalysisOptions())
        issues = self.analyzer.analyze([parsed_file], context)
        
        # Should find inconsistent style issue
        style_issues = [issue for issue in issues if "Inconsistent Documentation Style" in issue.title]
        assert len(style_issues) >= 1
        
        issue = style_issues[0]
        assert issue.category == IssueCategory.DOCUMENTATION
        assert issue.severity == Severity.LOW
        assert "consistent style" in issue.suggestion.lower()
    
    def test_javascript_documentation_analysis(self):
        """Test documentation analysis for JavaScript files."""
        js_code = '''
/**
 * Calculate the total price
 * @param {number} price - Base price
 * @param {number} tax - Tax rate
 * @returns {number} Total price including tax
 */
function calculateTotal(price, tax) {
    return price * (1 + tax);
}

// TODO: Add validation for negative prices
function processOrder(order) {
    // Missing JSDoc documentation
    return order.process();
}

class OrderProcessor {
    // Missing class documentation
    
    process(order) {
        // Missing method documentation
        return order.validated();
    }
}
'''
        
        js_functions = [
            Function("calculateTotal", 7, 9, ["price", "tax"], 
                    docstring="Calculate the total price\n@param {number} price - Base price\n@param {number} tax - Tax rate\n@returns {number} Total price including tax"),
            Function("processOrder", 12, 15, ["order"])  # No docstring
        ]
        
        js_classes = [
            Class("OrderProcessor", 17, 25, [
                Function("process", 21, 24, ["self", "order"])  # No docstring
            ])  # No docstring
        ]
        
        parsed_file = self._create_parsed_file(
            "order.js",
            "javascript",
            js_code,
            functions=js_functions,
            classes=js_classes
        )
        
        context = AnalysisContext(options=AnalysisOptions())
        issues = self.analyzer.analyze([parsed_file], context)
        
        # Should find documentation issues in JavaScript
        doc_issues = [issue for issue in issues if issue.category == IssueCategory.DOCUMENTATION]
        assert len(doc_issues) >= 2  # Missing function and class docstrings
        
        # Should find TODO comment
        todo_issues = [issue for issue in issues if "TODO Comment" in issue.title]
        assert len(todo_issues) >= 1
    
    def test_module_with_docstring(self):
        """Test that modules with proper docstrings don't trigger issues."""
        code = '''
"""
This module provides utility functions for data processing.

It includes functions for validation, transformation, and analysis
of various data types commonly used in the application.
"""

import os
from typing import List

def process_data(data: List[str]) -> List[str]:
    """
    Process a list of data items.
    
    Args:
        data: List of strings to process
        
    Returns:
        List of processed strings
    """
    return [item.upper() for item in data]

class DataValidator:
    """
    Validates data according to business rules.
    
    This class provides methods for validating different types
    of data used throughout the application.
    """
    
    def validate(self, data: str) -> bool:
        """
        Validate a data string.
        
        Args:
            data: String to validate
            
        Returns:
            True if valid, False otherwise
        """
        return bool(data and data.strip())
'''
        
        well_documented_func = Function(
            "process_data", 10, 18, ["data"],
            docstring="Process a list of data items.\n\nArgs:\n    data: List of strings to process\n\nReturns:\n    List of processed strings"
        )
        
        well_documented_class = Class(
            "DataValidator", 20, 35, [
                Function("validate", 28, 35, ["self", "data"],
                        docstring="Validate a data string.\n\nArgs:\n    data: String to validate\n\nReturns:\n    True if valid, False otherwise")
            ],
            docstring="Validates data according to business rules.\n\nThis class provides methods for validating different types\nof data used throughout the application."
        )
        
        parsed_file = self._create_parsed_file(
            "well_documented.py",
            "python",
            code,
            functions=[well_documented_func],
            classes=[well_documented_class]
        )
        
        context = AnalysisContext(options=AnalysisOptions())
        issues = self.analyzer.analyze([parsed_file], context)
        
        # Should have minimal or no high-severity documentation issues
        high_severity_issues = [
            issue for issue in issues 
            if issue.category == IssueCategory.DOCUMENTATION and issue.severity == Severity.HIGH
        ]
        assert len(high_severity_issues) == 0
    
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