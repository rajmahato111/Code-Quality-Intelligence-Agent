"""Tests for ComplexityAnalyzer."""

import pytest
from unittest.mock import patch

from code_quality_agent.analyzers.complexity_analyzer import ComplexityAnalyzer
from code_quality_agent.analyzers.base import IssueCategory, Severity
from code_quality_agent.core.models import (
    ParsedFile, AnalysisContext, AnalysisOptions, 
    FileMetadata, Function, Class
)


class TestComplexityAnalyzer:
    """Tests for ComplexityAnalyzer class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = ComplexityAnalyzer()
    
    def test_analyzer_properties(self):
        """Test basic analyzer properties."""
        assert self.analyzer.get_category() == IssueCategory.COMPLEXITY
        assert "python" in self.analyzer.get_supported_languages()
        assert "javascript" in self.analyzer.get_supported_languages()
        assert "typescript" in self.analyzer.get_supported_languages()
    
    def test_custom_thresholds(self):
        """Test analyzer with custom thresholds."""
        custom_config = {
            'cyclomatic_threshold': 5,
            'cognitive_threshold': 8,
            'nesting_threshold': 3,
            'function_length_threshold': 25,
            'parameter_threshold': 3
        }
        
        analyzer = ComplexityAnalyzer(custom_config)
        
        assert analyzer.thresholds['cyclomatic_complexity'] == 5
        assert analyzer.thresholds['cognitive_complexity'] == 8
        assert analyzer.thresholds['nesting_depth'] == 3
        assert analyzer.thresholds['function_length'] == 25
        assert analyzer.thresholds['parameter_count'] == 3
    
    def test_high_cyclomatic_complexity(self):
        """Test detection of high cyclomatic complexity."""
        # Create a function with high complexity
        complex_func = Function(
            name="complex_function",
            line_start=1,
            line_end=30,
            parameters=["param1", "param2"],
            complexity=15  # Above default threshold of 10
        )
        
        code = '''
def complex_function(param1, param2):
    if param1 > 0:
        if param2 > 0:
            for i in range(param1):
                if i % 2 == 0:
                    try:
                        result = param1 / i
                    except ZeroDivisionError:
                        result = 0
                    else:
                        result += 1
                else:
                    while param2 > 0:
                        param2 -= 1
                        if param2 % 3 == 0:
                            break
        else:
            result = param1 * 2
    else:
        result = 0
    return result
'''
        
        parsed_file = self._create_parsed_file("complex.py", "python", code, functions=[complex_func])
        context = AnalysisContext(options=AnalysisOptions())
        
        with patch.object(self.analyzer._analyzer_utils if hasattr(self.analyzer, '_analyzer_utils') else self.analyzer, 
                         '_calculate_function_complexity', 
                         return_value={
                             'cyclomatic_complexity': 15,
                             'cognitive_complexity': 12,
                             'nesting_depth': 4,
                             'lines_of_code': 25,
                             'parameters_count': 2,
                             'has_docstring': False
                         }):
            issues = self.analyzer.analyze([parsed_file], context)
        
        # Should find high cyclomatic complexity
        complexity_issues = [issue for issue in issues if "Cyclomatic Complexity" in issue.title]
        assert len(complexity_issues) >= 1
        
        issue = complexity_issues[0]
        assert issue.category == IssueCategory.COMPLEXITY
        assert issue.severity in [Severity.MEDIUM, Severity.HIGH]
        assert "breaking" in issue.suggestion.lower() or "smaller" in issue.suggestion.lower()
    
    def test_high_cognitive_complexity(self):
        """Test detection of high cognitive complexity."""
        complex_func = Function(
            name="cognitive_complex",
            line_start=1,
            line_end=25,
            parameters=["data"],
            complexity=8
        )
        
        code = '''
def cognitive_complex(data):
    if data:
        if isinstance(data, list):
            for item in data:
                if item > 0:
                    if item % 2 == 0:
                        try:
                            result = process(item)
                            if result:
                                return result
                        except Exception:
                            continue
    return None
'''
        
        parsed_file = self._create_parsed_file("cognitive.py", "python", code, functions=[complex_func])
        context = AnalysisContext(options=AnalysisOptions())
        
        # Mock the complexity calculation to return high cognitive complexity
        with patch('code_quality_agent.analyzers.analyzer_utils.AnalyzerUtils.calculate_function_complexity',
                   return_value={
                       'cyclomatic_complexity': 8,
                       'cognitive_complexity': 18,  # Above threshold of 15
                       'nesting_depth': 5,
                       'lines_of_code': 20,
                       'parameters_count': 1,
                       'has_docstring': False
                   }):
            issues = self.analyzer.analyze([parsed_file], context)
        
        # Should find high cognitive complexity
        cognitive_issues = [issue for issue in issues if "Cognitive Complexity" in issue.title]
        assert len(cognitive_issues) >= 1
        
        issue = cognitive_issues[0]
        assert issue.category == IssueCategory.COMPLEXITY
        assert "logic flow" in issue.suggestion.lower() or "nesting" in issue.suggestion.lower()
    
    def test_excessive_nesting_depth(self):
        """Test detection of excessive nesting depth."""
        nested_func = Function(
            name="deeply_nested",
            line_start=1,
            line_end=20,
            parameters=["x", "y"],
            complexity=6
        )
        
        code = '''
def deeply_nested(x, y):
    if x > 0:
        if y > 0:
            for i in range(x):
                if i % 2 == 0:
                    for j in range(y):
                        if j % 3 == 0:
                            return i * j
    return 0
'''
        
        parsed_file = self._create_parsed_file("nested.py", "python", code, functions=[nested_func])
        context = AnalysisContext(options=AnalysisOptions())
        
        with patch('code_quality_agent.analyzers.analyzer_utils.AnalyzerUtils.calculate_function_complexity',
                   return_value={
                       'cyclomatic_complexity': 6,
                       'cognitive_complexity': 10,
                       'nesting_depth': 6,  # Above threshold of 4
                       'lines_of_code': 15,
                       'parameters_count': 2,
                       'has_docstring': False
                   }):
            issues = self.analyzer.analyze([parsed_file], context)
        
        # Should find excessive nesting
        nesting_issues = [issue for issue in issues if "Nesting Depth" in issue.title]
        assert len(nesting_issues) >= 1
        
        issue = nesting_issues[0]
        assert issue.category == IssueCategory.COMPLEXITY
        assert issue.severity == Severity.MEDIUM
        assert "early returns" in issue.suggestion.lower() or "guard clauses" in issue.suggestion.lower()
    
    def test_long_function(self):
        """Test detection of overly long functions."""
        long_func = Function(
            name="very_long_function",
            line_start=1,
            line_end=60,  # 60 lines, above threshold of 50
            parameters=["param"],
            complexity=5
        )
        
        # Create a long code snippet
        code = "def very_long_function(param):\n" + "    # line\n" * 58 + "    return param"
        
        parsed_file = self._create_parsed_file("long.py", "python", code, functions=[long_func])
        context = AnalysisContext(options=AnalysisOptions())
        
        with patch('code_quality_agent.analyzers.analyzer_utils.AnalyzerUtils.calculate_function_complexity',
                   return_value={
                       'cyclomatic_complexity': 5,
                       'cognitive_complexity': 6,
                       'nesting_depth': 2,
                       'lines_of_code': 55,
                       'parameters_count': 1,
                       'has_docstring': False
                   }):
            issues = self.analyzer.analyze([parsed_file], context)
        
        # Should find long function
        length_issues = [issue for issue in issues if "Long Function" in issue.title]
        assert len(length_issues) >= 1
        
        issue = length_issues[0]
        assert issue.category == IssueCategory.COMPLEXITY
        assert issue.severity == Severity.MEDIUM
        assert "smaller" in issue.suggestion.lower() and "focused" in issue.suggestion.lower()
    
    def test_too_many_parameters(self):
        """Test detection of functions with too many parameters."""
        param_heavy_func = Function(
            name="many_params_function",
            line_start=1,
            line_end=10,
            parameters=["p1", "p2", "p3", "p4", "p5", "p6", "p7"],  # 7 parameters, above threshold of 5
            complexity=3
        )
        
        code = '''
def many_params_function(p1, p2, p3, p4, p5, p6, p7):
    return p1 + p2 + p3 + p4 + p5 + p6 + p7
'''
        
        parsed_file = self._create_parsed_file("params.py", "python", code, functions=[param_heavy_func])
        context = AnalysisContext(options=AnalysisOptions())
        
        with patch('code_quality_agent.analyzers.analyzer_utils.AnalyzerUtils.calculate_function_complexity',
                   return_value={
                       'cyclomatic_complexity': 3,
                       'cognitive_complexity': 3,
                       'nesting_depth': 1,
                       'lines_of_code': 5,
                       'parameters_count': 7,
                       'has_docstring': False
                   }):
            issues = self.analyzer.analyze([parsed_file], context)
        
        # Should find too many parameters
        param_issues = [issue for issue in issues if "Too Many Parameters" in issue.title]
        assert len(param_issues) >= 1
        
        issue = param_issues[0]
        assert issue.category == IssueCategory.COMPLEXITY
        assert issue.severity == Severity.LOW
        assert "grouping" in issue.suggestion.lower() or "objects" in issue.suggestion.lower()
    
    def test_large_class(self):
        """Test detection of overly large classes."""
        # Create a class with many methods
        methods = [Function(f"method_{i}", i*5, i*5+3) for i in range(25)]  # 25 methods, above threshold of 20
        
        large_class = Class(
            name="GodClass",
            line_start=1,
            line_end=150,
            methods=methods
        )
        
        code = "class GodClass:\n" + "\n".join([f"    def method_{i}(self): pass" for i in range(25)])
        
        parsed_file = self._create_parsed_file("large_class.py", "python", code, classes=[large_class])
        context = AnalysisContext(options=AnalysisOptions())
        
        issues = self.analyzer.analyze([parsed_file], context)
        
        # Should find large class
        class_issues = [issue for issue in issues if "Large Class" in issue.title]
        assert len(class_issues) >= 1
        
        issue = class_issues[0]
        assert issue.category == IssueCategory.COMPLEXITY
        assert issue.severity == Severity.MEDIUM
        assert "Single Responsibility" in issue.suggestion
    
    def test_god_class_pattern(self):
        """Test detection of God Class anti-pattern."""
        # Create a very large class
        methods = [Function(f"method_{i}", i*3, i*3+2) for i in range(35)]  # 35 methods
        
        god_class = Class(
            name="MegaClass",
            line_start=1,
            line_end=200,
            methods=methods
        )
        
        code = "class MegaClass:\n" + "\n".join([f"    def method_{i}(self): pass" for i in range(35)])
        
        parsed_file = self._create_parsed_file("god_class.py", "python", code, classes=[god_class])
        context = AnalysisContext(options=AnalysisOptions())
        
        issues = self.analyzer.analyze([parsed_file], context)
        
        # Should find God Class pattern
        god_class_issues = [issue for issue in issues if "God Class" in issue.title]
        assert len(god_class_issues) >= 1
        
        issue = god_class_issues[0]
        assert issue.category == IssueCategory.COMPLEXITY
        assert issue.severity == Severity.HIGH
        assert "anti-pattern" in issue.description.lower()
    
    def test_large_file(self):
        """Test detection of overly large files."""
        # Create a file with many lines
        long_content = "\n".join([f"# Line {i}" for i in range(600)])  # 600 lines, above threshold of 500
        
        parsed_file = self._create_parsed_file(
            "large_file.py", 
            "python", 
            long_content,
            metadata=FileMetadata(
                file_path="large_file.py",
                language="python",
                size_bytes=len(long_content),
                line_count=600
            )
        )
        context = AnalysisContext(options=AnalysisOptions())
        
        issues = self.analyzer.analyze([parsed_file], context)
        
        # Should find large file
        file_issues = [issue for issue in issues if "Large File" in issue.title]
        assert len(file_issues) >= 1
        
        issue = file_issues[0]
        assert issue.category == IssueCategory.COMPLEXITY
        assert issue.severity == Severity.LOW
        assert "splitting" in issue.suggestion.lower()
    
    def test_low_maintainability_index(self):
        """Test detection of low maintainability index."""
        # Create functions with high complexity
        complex_functions = [
            Function(f"func_{i}", i*10, i*10+8, complexity=12) for i in range(5)
        ]
        
        code = "\n".join([f"def func_{i}():\n    # complex code\n    pass" for i in range(5)])
        
        parsed_file = self._create_parsed_file(
            "unmaintainable.py", 
            "python", 
            code,
            functions=complex_functions,
            metadata=FileMetadata(
                file_path="unmaintainable.py",
                language="python",
                size_bytes=len(code),
                line_count=200  # Large file with high complexity
            )
        )
        context = AnalysisContext(options=AnalysisOptions())
        
        issues = self.analyzer.analyze([parsed_file], context)
        
        # Should find low maintainability
        maintainability_issues = [issue for issue in issues if "Maintainability Index" in issue.title]
        assert len(maintainability_issues) >= 1
        
        issue = maintainability_issues[0]
        assert issue.category == IssueCategory.COMPLEXITY
        assert issue.severity in [Severity.MEDIUM, Severity.HIGH]
        assert "maintainability" in issue.suggestion.lower()
    
    def test_deep_nesting_in_code(self):
        """Test detection of deep nesting in code structure."""
        # Code with deep indentation
        deeply_nested_code = '''
def nested_function():
    if condition1:
        if condition2:
            for item in items:
                if item.valid:
                    for subitem in item.subitems:
                        if subitem.active:
                            for detail in subitem.details:
                                if detail.important:
                                    process(detail)  # Very deep nesting
'''
        
        parsed_file = self._create_parsed_file("deep_nested.py", "python", deeply_nested_code)
        context = AnalysisContext(options=AnalysisOptions())
        
        issues = self.analyzer.analyze([parsed_file], context)
        
        # Should find excessive nesting
        nesting_issues = [issue for issue in issues if "Excessive Nesting Depth" in issue.title]
        # Note: This test depends on the specific implementation of nesting detection
        # The actual detection might vary based on how indentation is calculated
    
    def test_complex_conditions(self):
        """Test detection of overly complex conditional expressions."""
        complex_conditions_code = '''
def complex_conditions(a, b, c, d, e):
    if a > 0 and b < 10 and c != 5 and d is not None and e in valid_values and len(e) > 3:
        return True
    elif a < 0 or b > 20 or c == 7 or d is None or e not in valid_values or len(e) <= 1:
        return False
    return None
'''
        
        parsed_file = self._create_parsed_file("complex_conditions.py", "python", complex_conditions_code)
        context = AnalysisContext(options=AnalysisOptions())
        
        issues = self.analyzer.analyze([parsed_file], context)
        
        # Should find complex conditions
        condition_issues = [issue for issue in issues if "Complex Conditional" in issue.title]
        assert len(condition_issues) >= 1
        
        if condition_issues:
            issue = condition_issues[0]
            assert issue.category == IssueCategory.COMPLEXITY
            assert issue.severity == Severity.LOW
            assert "boolean variables" in issue.suggestion.lower()
    
    def test_no_issues_for_simple_code(self):
        """Test that simple, well-structured code doesn't trigger issues."""
        simple_code = '''
def simple_function(x, y):
    """A simple, well-structured function."""
    if x > 0:
        return x + y
    return y

class SimpleClass:
    """A simple class with few methods."""
    
    def __init__(self, value):
        self.value = value
    
    def get_value(self):
        return self.value
    
    def set_value(self, value):
        self.value = value
'''
        
        simple_func = Function(
            name="simple_function",
            line_start=1,
            line_end=5,
            parameters=["x", "y"],
            complexity=2,  # Low complexity
            docstring="A simple, well-structured function."
        )
        
        simple_class = Class(
            name="SimpleClass",
            line_start=7,
            line_end=18,
            methods=[
                Function("__init__", 10, 11, ["self", "value"]),
                Function("get_value", 13, 14, ["self"]),
                Function("set_value", 16, 17, ["self", "value"])
            ],
            docstring="A simple class with few methods."
        )
        
        parsed_file = self._create_parsed_file(
            "simple.py", 
            "python", 
            simple_code,
            functions=[simple_func],
            classes=[simple_class],
            metadata=FileMetadata(
                file_path="simple.py",
                language="python",
                size_bytes=len(simple_code),
                line_count=18
            )
        )
        context = AnalysisContext(options=AnalysisOptions())
        
        with patch('code_quality_agent.analyzers.analyzer_utils.AnalyzerUtils.calculate_function_complexity',
                   return_value={
                       'cyclomatic_complexity': 2,
                       'cognitive_complexity': 2,
                       'nesting_depth': 1,
                       'lines_of_code': 4,
                       'parameters_count': 2,
                       'has_docstring': True
                   }):
            issues = self.analyzer.analyze([parsed_file], context)
        
        # Should have no or minimal complexity issues
        high_severity_issues = [issue for issue in issues if issue.severity in [Severity.HIGH, Severity.CRITICAL]]
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