"""Tests for TestingAnalyzer."""

import pytest

from code_quality_agent.analyzers.testing_analyzer import TestingAnalyzer
from code_quality_agent.analyzers.base import IssueCategory, Severity
from code_quality_agent.core.models import (
    ParsedFile, AnalysisContext, AnalysisOptions, 
    FileMetadata, Function, Class
)


class TestTestingAnalyzer:
    """Tests for TestingAnalyzer class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = TestingAnalyzer()
    
    def test_analyzer_properties(self):
        """Test basic analyzer properties."""
        assert self.analyzer.get_category() == IssueCategory.TESTING
        assert "python" in self.analyzer.get_supported_languages()
        assert "javascript" in self.analyzer.get_supported_languages()
        assert "typescript" in self.analyzer.get_supported_languages()
    
    def test_custom_thresholds(self):
        """Test analyzer with custom thresholds."""
        custom_config = {
            'min_test_coverage': 0.9,
            'max_test_complexity': 3,
            'min_assertions_per_test': 2,
            'max_test_length': 30
        }
        
        analyzer = TestingAnalyzer(custom_config)
        
        assert analyzer.thresholds['min_test_coverage'] == 0.9
        assert analyzer.thresholds['max_test_complexity'] == 3
        assert analyzer.thresholds['min_assertions_per_test'] == 2
        assert analyzer.thresholds['max_test_length'] == 30
    
    def test_test_file_identification_python(self):
        """Test identification of Python test files."""
        # Test file by naming convention
        test_file1 = self._create_parsed_file("test_module.py", "python", "def test_something(): pass")
        assert self.analyzer._is_test_file(test_file1)
        
        test_file2 = self._create_parsed_file("module_test.py", "python", "def test_something(): pass")
        assert self.analyzer._is_test_file(test_file2)
        
        test_file3 = self._create_parsed_file("tests/test_utils.py", "python", "def test_something(): pass")
        assert self.analyzer._is_test_file(test_file3)
        
        # Test file by content
        test_file4 = self._create_parsed_file("check.py", "python", "import unittest\nclass TestCase(unittest.TestCase): pass")
        assert self.analyzer._is_test_file(test_file4)
        
        # Non-test file
        source_file = self._create_parsed_file("module.py", "python", "def function(): pass")
        assert not self.analyzer._is_test_file(source_file)
    
    def test_test_file_identification_javascript(self):
        """Test identification of JavaScript test files."""
        # Test file by naming convention
        test_file1 = self._create_parsed_file("module.test.js", "javascript", "test('should work', () => {});")
        assert self.analyzer._is_test_file(test_file1)
        
        test_file2 = self._create_parsed_file("module.spec.js", "javascript", "describe('module', () => {});")
        assert self.analyzer._is_test_file(test_file2)
        
        test_file3 = self._create_parsed_file("__tests__/module.js", "javascript", "it('should work', () => {});")
        assert self.analyzer._is_test_file(test_file3)
        
        # Non-test file
        source_file = self._create_parsed_file("module.js", "javascript", "function doSomething() {}")
        assert not self.analyzer._is_test_file(source_file)
    
    def test_no_test_files_found(self):
        """Test detection when no test files are found."""
        # Create source files without corresponding tests
        source_func = Function("calculate", 1, 10, ["x", "y"])
        source_file = self._create_parsed_file(
            "calculator.py", 
            "python", 
            "def calculate(x, y): return x + y",
            functions=[source_func]
        )
        
        context = AnalysisContext(options=AnalysisOptions())
        issues = self.analyzer.analyze([source_file], context)
        
        # Should find "no test files" issue
        no_test_issues = [issue for issue in issues if "No Test Files Found" in issue.title]
        assert len(no_test_issues) >= 1
        
        issue = no_test_issues[0]
        assert issue.category == IssueCategory.TESTING
        assert issue.severity == Severity.HIGH
        assert "testing framework" in issue.suggestion.lower()
    
    def test_low_test_coverage(self):
        """Test detection of low test coverage."""
        # Create source file with multiple functions
        source_functions = [
            Function("add", 1, 3, ["a", "b"]),
            Function("subtract", 5, 7, ["a", "b"]),
            Function("multiply", 9, 11, ["a", "b"]),
            Function("divide", 13, 15, ["a", "b"])
        ]
        
        source_file = self._create_parsed_file(
            "math_utils.py",
            "python",
            '''
def add(a, b): return a + b
def subtract(a, b): return a - b
def multiply(a, b): return a * b
def divide(a, b): return a / b
''',
            functions=source_functions
        )
        
        # Create test file that only tests one function
        test_file = self._create_parsed_file(
            "test_math_utils.py",
            "python",
            '''
def test_add():
    assert add(2, 3) == 5
'''
        )
        
        context = AnalysisContext(options=AnalysisOptions())
        issues = self.analyzer.analyze([source_file, test_file], context)
        
        # Should find low coverage issue
        coverage_issues = [issue for issue in issues if "Low Test Coverage" in issue.title]
        assert len(coverage_issues) >= 1
        
        issue = coverage_issues[0]
        assert issue.category == IssueCategory.TESTING
        assert issue.severity == Severity.MEDIUM
        assert issue.metadata['coverage_ratio'] < 0.8
        assert "improve coverage" in issue.suggestion.lower()
    
    def test_untested_critical_function(self):
        """Test detection of untested critical functions."""
        # Create critical function (public, complex)
        critical_func = Function(
            "process_payment", 
            1, 20, 
            ["amount", "card_number", "cvv", "expiry"],  # Many parameters
            complexity=8  # High complexity
        )
        
        source_file = self._create_parsed_file(
            "payment.py",
            "python",
            '''
def process_payment(amount, card_number, cvv, expiry):
    # Complex payment processing logic
    if amount <= 0:
        raise ValueError("Invalid amount")
    # ... more complex logic
    return {"status": "success"}
''',
            functions=[critical_func]
        )
        
        # Create test file that doesn't test the critical function
        test_file = self._create_parsed_file(
            "test_payment.py",
            "python",
            '''
def test_other_function():
    assert True
'''
        )
        
        context = AnalysisContext(options=AnalysisOptions())
        issues = self.analyzer.analyze([source_file, test_file], context)
        
        # Should find untested critical function
        critical_issues = [issue for issue in issues if "Untested Critical Function" in issue.title]
        assert len(critical_issues) >= 1
        
        issue = critical_issues[0]
        assert issue.category == IssueCategory.TESTING
        assert issue.severity == Severity.HIGH
        assert "comprehensive tests" in issue.suggestion.lower()
    
    def test_complex_test_function(self):
        """Test detection of overly complex test functions."""
        # Create complex test function
        complex_test_func = Function(
            "test_complex_scenario",
            1, 30,
            ["self"],
            complexity=8  # Above threshold of 5
        )
        
        test_file = self._create_parsed_file(
            "test_complex.py",
            "python",
            '''
def test_complex_scenario():
    # Very complex test with many branches
    if condition1:
        if condition2:
            for item in items:
                if item.valid:
                    try:
                        result = process(item)
                        assert result.success
                    except Exception:
                        assert False
    else:
        assert True
''',
            functions=[complex_test_func]
        )
        
        context = AnalysisContext(options=AnalysisOptions())
        issues = self.analyzer.analyze([test_file], context)
        
        # Should find complex test issue
        complex_issues = [issue for issue in issues if "Complex Test Function" in issue.title]
        assert len(complex_issues) >= 1
        
        issue = complex_issues[0]
        assert issue.category == IssueCategory.TESTING
        assert issue.severity == Severity.LOW
        assert "breaking it into smaller" in issue.suggestion.lower()
    
    def test_long_test_function(self):
        """Test detection of overly long test functions."""
        # Create long test function
        long_test_func = Function(
            "test_very_long_scenario",
            1, 60,  # 60 lines, above threshold of 50
            ["self"]
        )
        
        long_test_code = "def test_very_long_scenario():\n" + "    # test line\n" * 58 + "    assert True"
        
        test_file = self._create_parsed_file(
            "test_long.py",
            "python",
            long_test_code,
            functions=[long_test_func]
        )
        
        context = AnalysisContext(options=AnalysisOptions())
        issues = self.analyzer.analyze([test_file], context)
        
        # Should find long test issue
        long_issues = [issue for issue in issues if "Long Test Function" in issue.title]
        assert len(long_issues) >= 1
        
        issue = long_issues[0]
        assert issue.category == IssueCategory.TESTING
        assert issue.severity == Severity.LOW
        assert "single responsibility" in issue.suggestion.lower()
    
    def test_test_without_assertions(self):
        """Test detection of tests without assertions."""
        # Create test function without assertions
        no_assert_func = Function("test_no_assertions", 1, 5, [])
        
        test_file = self._create_parsed_file(
            "test_no_assert.py",
            "python",
            '''
def test_no_assertions():
    # This test doesn't assert anything
    result = some_function()
    print(result)
''',
            functions=[no_assert_func]
        )
        
        context = AnalysisContext(options=AnalysisOptions())
        issues = self.analyzer.analyze([test_file], context)
        
        # Should find no assertions issue
        assertion_issues = [issue for issue in issues if "Test Without Assertions" in issue.title]
        assert len(assertion_issues) >= 1
        
        issue = assertion_issues[0]
        assert issue.category == IssueCategory.TESTING
        assert issue.severity == Severity.MEDIUM
        assert "Add assertions" in issue.suggestion
    
    def test_missing_test_documentation(self):
        """Test detection of missing test documentation."""
        test_file = self._create_parsed_file(
            "test_undocumented.py",
            "python",
            '''
def test_something():
    assert True

def test_another_thing():
    assert False
'''
        )
        
        context = AnalysisContext(options=AnalysisOptions())
        issues = self.analyzer.analyze([test_file], context)
        
        # Should find missing documentation issue
        doc_issues = [issue for issue in issues if "Test File Lacks Documentation" in issue.title]
        assert len(doc_issues) >= 1
        
        issue = doc_issues[0]
        assert issue.category == IssueCategory.TESTING
        assert issue.severity == Severity.LOW
        assert "module docstring" in issue.suggestion.lower()
    
    def test_duplicate_test_code(self):
        """Test detection of duplicate code in tests."""
        test_file = self._create_parsed_file(
            "test_duplicate.py",
            "python",
            '''
def test_first():
    setup_data = create_test_data()
    result = process(setup_data)
    assert result.is_valid()

def test_second():
    setup_data = create_test_data()
    result = process(setup_data)
    assert result.is_complete()

def test_third():
    setup_data = create_test_data()
    result = process(setup_data)
    assert result.is_ready()
'''
        )
        
        context = AnalysisContext(options=AnalysisOptions())
        issues = self.analyzer.analyze([test_file], context)
        
        # Should find duplicate test code
        duplicate_issues = [issue for issue in issues if "Duplicate Test Code" in issue.title]
        assert len(duplicate_issues) >= 1
        
        issue = duplicate_issues[0]
        assert issue.category == IssueCategory.TESTING
        assert issue.severity == Severity.LOW
        assert "helper methods" in issue.suggestion.lower()
    
    def test_magic_numbers_in_tests(self):
        """Test detection of magic numbers in test code."""
        test_file = self._create_parsed_file(
            "test_magic.py",
            "python",
            '''
def test_calculation():
    result = calculate(12345, 67890)  # Magic numbers
    assert result == 80235
    
    data = [1, 2, 3]  # Small numbers, should be ignored
    assert len(data) == 3
'''
        )
        
        context = AnalysisContext(options=AnalysisOptions())
        issues = self.analyzer.analyze([test_file], context)
        
        # Should find magic numbers issue
        magic_issues = [issue for issue in issues if "Magic Numbers in Test" in issue.title]
        assert len(magic_issues) >= 1
        
        issue = magic_issues[0]
        assert issue.category == IssueCategory.TESTING
        assert issue.severity == Severity.LOW
        assert "named constants" in issue.suggestion.lower()
    
    def test_broad_exception_catching(self):
        """Test detection of broad exception catching in tests."""
        test_file = self._create_parsed_file(
            "test_exceptions.py",
            "python",
            '''
def test_with_broad_catch():
    try:
        risky_operation()
    except:  # Too broad
        pass

def test_with_specific_catch():
    try:
        risky_operation()
    except ValueError:  # Specific, good
        pass
'''
        )
        
        context = AnalysisContext(options=AnalysisOptions())
        issues = self.analyzer.analyze([test_file], context)
        
        # Should find broad exception catching
        exception_issues = [issue for issue in issues if "Broad Exception Catching" in issue.title]
        assert len(exception_issues) >= 1
        
        issue = exception_issues[0]
        assert issue.category == IssueCategory.TESTING
        assert issue.severity == Severity.LOW
        assert "specific exception types" in issue.suggestion.lower()
    
    def test_test_dependencies(self):
        """Test detection of test dependencies."""
        test_file = self._create_parsed_file(
            "test_dependencies.py",
            "python",
            '''
shared_state = {}

class TestWithDependencies:
    def test_first(self):
        global shared_state
        shared_state['key'] = 'value'
        assert True
    
    def test_second(self):
        # This test depends on test_first
        assert shared_state['key'] == 'value'
'''
        )
        
        context = AnalysisContext(options=AnalysisOptions())
        issues = self.analyzer.analyze([test_file], context)
        
        # Should find test dependencies
        dependency_issues = [issue for issue in issues if "Test Dependencies" in issue.title]
        assert len(dependency_issues) >= 1
        
        issue = dependency_issues[0]
        assert issue.category == IssueCategory.TESTING
        assert issue.severity == Severity.MEDIUM
        assert "independent" in issue.suggestion.lower()
    
    def test_javascript_test_detection(self):
        """Test detection of JavaScript test issues."""
        # JavaScript test file
        js_test_file = self._create_parsed_file(
            "module.test.js",
            "javascript",
            '''
describe('Module', () => {
    it('should work', () => {
        // No assertions
        const result = doSomething();
        console.log(result);
    });
    
    it('should handle complex case', () => {
        // Complex test logic
        if (condition) {
            for (let i = 0; i < 100; i++) {
                if (items[i].valid) {
                    expect(process(items[i])).toBeTruthy();
                }
            }
        }
    });
});
'''
        )
        
        context = AnalysisContext(options=AnalysisOptions())
        issues = self.analyzer.analyze([js_test_file], context)
        
        # Should find testing issues in JavaScript
        testing_issues = [issue for issue in issues if issue.category == IssueCategory.TESTING]
        assert len(testing_issues) >= 1
    
    def test_function_tested_detection(self):
        """Test detection of whether functions are tested."""
        source_func = Function("calculate_tax", 1, 10, ["amount", "rate"])
        source_file = self._create_parsed_file(
            "tax.py",
            "python",
            "def calculate_tax(amount, rate): return amount * rate",
            functions=[source_func]
        )
        
        # Test file that tests the function
        test_file = self._create_parsed_file(
            "test_tax.py",
            "python",
            '''
def test_calculate_tax():
    result = calculate_tax(100, 0.1)
    assert result == 10
'''
        )
        
        # Function should be detected as tested
        is_tested = self.analyzer._is_function_tested(source_func, source_file, [test_file])
        assert is_tested
        
        # Test with function not mentioned in tests
        untested_func = Function("calculate_discount", 1, 5, ["amount"])
        is_tested = self.analyzer._is_function_tested(untested_func, source_file, [test_file])
        assert not is_tested
    
    def test_assertion_counting(self):
        """Test counting of assertions in test functions."""
        test_func = Function("test_with_assertions", 1, 10, [])
        
        test_content = '''
def test_with_assertions():
    result = calculate(5, 3)
    assert result == 8
    self.assertEqual(result, 8)
    expect(result).to.equal(8)
'''
        
        count = self.analyzer._count_assertions(test_func, test_content)
        assert count >= 3  # Should find multiple assertion patterns
    
    def test_no_issues_for_well_tested_code(self):
        """Test that well-tested code doesn't trigger issues."""
        # Well-structured source file
        source_func = Function("add_numbers", 1, 3, ["a", "b"])
        source_file = self._create_parsed_file(
            "calculator.py",
            "python",
            '''
def add_numbers(a, b):
    """Add two numbers together."""
    return a + b
''',
            functions=[source_func]
        )
        
        # Comprehensive test file
        test_file = self._create_parsed_file(
            "test_calculator.py",
            "python",
            '''
"""Tests for calculator module."""
import unittest

class TestCalculator(unittest.TestCase):
    def test_add_numbers_positive(self):
        """Test adding positive numbers."""
        result = add_numbers(2, 3)
        self.assertEqual(result, 5)
    
    def test_add_numbers_negative(self):
        """Test adding negative numbers."""
        result = add_numbers(-2, -3)
        self.assertEqual(result, -5)
    
    def test_add_numbers_zero(self):
        """Test adding with zero."""
        result = add_numbers(5, 0)
        self.assertEqual(result, 5)
'''
        )
        
        context = AnalysisContext(options=AnalysisOptions())
        issues = self.analyzer.analyze([source_file, test_file], context)
        
        # Should have minimal or no high-severity testing issues
        high_severity_issues = [
            issue for issue in issues 
            if issue.category == IssueCategory.TESTING and issue.severity == Severity.HIGH
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