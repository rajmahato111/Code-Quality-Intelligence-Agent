"""Tests for analyzer base infrastructure."""

import pytest
from unittest.mock import Mock, patch

from code_quality_agent.analyzers.base import QualityAnalyzer, IssueCategory, Severity
from code_quality_agent.analyzers.analyzer_registry import AnalyzerRegistry, AnalyzerPriority
from code_quality_agent.analyzers.issue_factory import IssueFactory
from code_quality_agent.analyzers.analyzer_utils import AnalyzerUtils
from code_quality_agent.core.models import ParsedFile, AnalysisContext, AnalysisOptions, FileMetadata


class MockAnalyzer(QualityAnalyzer):
    """Mock analyzer for testing."""
    
    def __init__(self, name="MockAnalyzer", category=IssueCategory.SECURITY, languages=None):
        super().__init__()
        self._name = name
        self._category = category
        self._languages = languages or ["python"]
    
    def analyze(self, parsed_files, context):
        # Return mock issues
        return [
            IssueFactory.create_issue(
                category=self._category,
                severity=Severity.MEDIUM,
                title="Mock Issue",
                description="This is a mock issue",
                file_path=parsed_files[0].path if parsed_files else "test.py",
                line_start=1,
                line_end=1,
                suggestion="Fix the mock issue",
                confidence=0.8
            )
        ]
    
    def get_supported_languages(self):
        return self._languages
    
    def get_category(self):
        return self._category
    
    def get_name(self):
        return self._name


class TestAnalyzerRegistry:
    """Tests for AnalyzerRegistry."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.registry = AnalyzerRegistry()
    
    def test_register_analyzer(self):
        """Test analyzer registration."""
        analyzer = MockAnalyzer("TestAnalyzer", IssueCategory.SECURITY, ["python"])
        
        self.registry.register_analyzer(analyzer, AnalyzerPriority.HIGH)
        
        # Check registration
        assert "TestAnalyzer" in self.registry._analyzers
        assert self.registry._analyzer_priorities["TestAnalyzer"] == AnalyzerPriority.HIGH
        
        # Check indexing
        assert "TestAnalyzer" in self.registry._category_analyzers[IssueCategory.SECURITY]
        assert "TestAnalyzer" in self.registry._language_analyzers["python"]
    
    def test_unregister_analyzer(self):
        """Test analyzer unregistration."""
        analyzer = MockAnalyzer("TestAnalyzer")
        self.registry.register_analyzer(analyzer)
        
        # Unregister
        result = self.registry.unregister_analyzer("TestAnalyzer")
        assert result is True
        
        # Check removal
        assert "TestAnalyzer" not in self.registry._analyzers
        assert "TestAnalyzer" not in self.registry._analyzer_priorities
        
        # Try to unregister non-existent analyzer
        result = self.registry.unregister_analyzer("NonExistent")
        assert result is False
    
    def test_get_analyzers_for_category(self):
        """Test getting analyzers by category."""
        security_analyzer = MockAnalyzer("SecurityAnalyzer", IssueCategory.SECURITY)
        performance_analyzer = MockAnalyzer("PerformanceAnalyzer", IssueCategory.PERFORMANCE)
        
        self.registry.register_analyzer(security_analyzer)
        self.registry.register_analyzer(performance_analyzer)
        
        security_analyzers = self.registry.get_analyzers_for_category(IssueCategory.SECURITY)
        assert len(security_analyzers) == 1
        assert security_analyzers[0].get_name() == "SecurityAnalyzer"
        
        performance_analyzers = self.registry.get_analyzers_for_category(IssueCategory.PERFORMANCE)
        assert len(performance_analyzers) == 1
        assert performance_analyzers[0].get_name() == "PerformanceAnalyzer"
    
    def test_get_analyzers_for_language(self):
        """Test getting analyzers by language."""
        python_analyzer = MockAnalyzer("PythonAnalyzer", languages=["python"])
        js_analyzer = MockAnalyzer("JSAnalyzer", languages=["javascript"])
        multi_analyzer = MockAnalyzer("MultiAnalyzer", languages=["python", "javascript"])
        
        self.registry.register_analyzer(python_analyzer)
        self.registry.register_analyzer(js_analyzer)
        self.registry.register_analyzer(multi_analyzer)
        
        python_analyzers = self.registry.get_analyzers_for_language("python")
        assert len(python_analyzers) == 2  # PythonAnalyzer and MultiAnalyzer
        
        js_analyzers = self.registry.get_analyzers_for_language("javascript")
        assert len(js_analyzers) == 2  # JSAnalyzer and MultiAnalyzer
    
    def test_get_sorted_analyzers(self):
        """Test getting analyzers sorted by priority."""
        high_analyzer = MockAnalyzer("HighAnalyzer")
        medium_analyzer = MockAnalyzer("MediumAnalyzer")
        low_analyzer = MockAnalyzer("LowAnalyzer")
        
        self.registry.register_analyzer(low_analyzer, AnalyzerPriority.LOW)
        self.registry.register_analyzer(high_analyzer, AnalyzerPriority.HIGH)
        self.registry.register_analyzer(medium_analyzer, AnalyzerPriority.MEDIUM)
        
        sorted_analyzers = self.registry.get_sorted_analyzers()
        
        # Should be sorted by priority (highest first)
        assert sorted_analyzers[0].get_name() == "HighAnalyzer"
        assert sorted_analyzers[1].get_name() == "MediumAnalyzer"
        assert sorted_analyzers[2].get_name() == "LowAnalyzer"
    
    def test_run_analyzers(self):
        """Test running analyzers on parsed files."""
        analyzer1 = MockAnalyzer("Analyzer1", IssueCategory.SECURITY, ["python"])
        analyzer2 = MockAnalyzer("Analyzer2", IssueCategory.PERFORMANCE, ["python"])
        
        self.registry.register_analyzer(analyzer1)
        self.registry.register_analyzer(analyzer2)
        
        # Create mock parsed file
        parsed_file = ParsedFile(
            path="test.py",
            language="python",
            content="def test(): pass",
            metadata=FileMetadata(
                file_path="test.py",
                language="python",
                size_bytes=100,
                line_count=1
            )
        )
        
        context = AnalysisContext(options=AnalysisOptions())
        
        issues = self.registry.run_analyzers([parsed_file], context)
        
        # Should have issues from both analyzers
        assert len(issues) == 2
        assert all(issue.confidence >= 0.7 for issue in issues)  # Default threshold
    
    def test_run_analyzers_with_filters(self):
        """Test running analyzers with category and language filters."""
        security_analyzer = MockAnalyzer("SecurityAnalyzer", IssueCategory.SECURITY, ["python"])
        performance_analyzer = MockAnalyzer("PerformanceAnalyzer", IssueCategory.PERFORMANCE, ["python"])
        js_analyzer = MockAnalyzer("JSAnalyzer", IssueCategory.SECURITY, ["javascript"])
        
        self.registry.register_analyzer(security_analyzer)
        self.registry.register_analyzer(performance_analyzer)
        self.registry.register_analyzer(js_analyzer)
        
        parsed_file = ParsedFile(
            path="test.py",
            language="python",
            content="def test(): pass"
        )
        
        context = AnalysisContext(options=AnalysisOptions())
        
        # Filter by category
        issues = self.registry.run_analyzers(
            [parsed_file], 
            context, 
            categories=[IssueCategory.SECURITY]
        )
        assert len(issues) == 1  # Only security analyzer should run
        
        # Filter by language
        issues = self.registry.run_analyzers(
            [parsed_file], 
            context, 
            languages=["javascript"]
        )
        assert len(issues) == 0  # No JavaScript analyzers should run on Python file
    
    def test_get_registry_statistics(self):
        """Test getting registry statistics."""
        analyzer1 = MockAnalyzer("Analyzer1", IssueCategory.SECURITY, ["python"])
        analyzer2 = MockAnalyzer("Analyzer2", IssueCategory.PERFORMANCE, ["javascript"])
        
        self.registry.register_analyzer(analyzer1, AnalyzerPriority.HIGH)
        self.registry.register_analyzer(analyzer2, AnalyzerPriority.MEDIUM)
        
        stats = self.registry.get_registry_statistics()
        
        assert stats['total_analyzers'] == 2
        assert stats['enabled_analyzers'] == 2
        assert stats['categories']['security'] == 1
        assert stats['categories']['performance'] == 1
        assert stats['languages']['python'] == 1
        assert stats['languages']['javascript'] == 1
        assert stats['priorities']['HIGH'] == 1
        assert stats['priorities']['MEDIUM'] == 1
    
    def test_validate_analyzers(self):
        """Test analyzer validation."""
        valid_analyzer = MockAnalyzer("ValidAnalyzer")
        
        # Create invalid analyzer (missing methods)
        class InvalidAnalyzer:
            def get_name(self):
                return "InvalidAnalyzer"
        
        invalid_analyzer = InvalidAnalyzer()
        
        self.registry.register_analyzer(valid_analyzer)
        self.registry._analyzers["InvalidAnalyzer"] = invalid_analyzer
        
        validation = self.registry.validate_analyzers()
        
        assert "ValidAnalyzer" in validation['valid']
        assert any("InvalidAnalyzer" in item for item in validation['invalid'])


class TestIssueFactory:
    """Tests for IssueFactory."""
    
    def test_create_basic_issue(self):
        """Test creating a basic issue."""
        issue = IssueFactory.create_issue(
            category=IssueCategory.SECURITY,
            severity=Severity.HIGH,
            title="Test Issue",
            description="This is a test issue",
            file_path="test.py",
            line_start=10,
            line_end=15,
            suggestion="Fix the issue",
            confidence=0.9
        )
        
        assert issue.category == IssueCategory.SECURITY
        assert issue.severity == Severity.HIGH
        assert issue.title == "Test Issue"
        assert issue.location.file_path == "test.py"
        assert issue.location.line_start == 10
        assert issue.confidence == 0.9
        assert issue.id  # Should have generated ID
        assert 'created_by' in issue.metadata
    
    def test_create_security_issue(self):
        """Test creating a security-specific issue."""
        issue = IssueFactory.create_security_issue(
            title="SQL Injection Risk",
            description="Potential SQL injection vulnerability",
            file_path="app.py",
            line_start=25,
            line_end=25,
            suggestion="Use parameterized queries",
            confidence=0.85,
            vulnerability_type="sql_injection"
        )
        
        assert issue.category == IssueCategory.SECURITY
        assert issue.metadata['vulnerability_type'] == "sql_injection"
        assert issue.metadata['security_impact'] == "high"
        assert 'A03:2021' in issue.metadata['owasp_category']
    
    def test_create_performance_issue(self):
        """Test creating a performance-specific issue."""
        issue = IssueFactory.create_performance_issue(
            title="Inefficient Loop",
            description="Nested loop with high complexity",
            file_path="utils.py",
            line_start=50,
            line_end=60,
            suggestion="Optimize algorithm",
            confidence=0.75,
            performance_impact="cpu"
        )
        
        assert issue.category == IssueCategory.PERFORMANCE
        assert issue.metadata['performance_impact'] == "cpu"
        assert issue.metadata['optimization_category'] == "CPU Optimization"
    
    def test_create_complexity_issue(self):
        """Test creating a complexity-specific issue."""
        issue = IssueFactory.create_complexity_issue(
            title="High Cyclomatic Complexity",
            description="Function has too many decision points",
            file_path="complex.py",
            line_start=100,
            line_end=150,
            suggestion="Break down into smaller functions",
            confidence=0.95,
            complexity_metric="cyclomatic_complexity",
            complexity_value=15.0,
            threshold=10.0
        )
        
        assert issue.category == IssueCategory.COMPLEXITY
        assert issue.metadata['complexity_value'] == 15.0
        assert issue.metadata['threshold'] == 10.0
        assert issue.metadata['complexity_ratio'] == 1.5
    
    def test_create_duplication_issue(self):
        """Test creating a duplication-specific issue."""
        issue = IssueFactory.create_duplication_issue(
            title="Code Duplication Detected",
            description="Similar code found in multiple files",
            file_path="original.py",
            line_start=20,
            line_end=30,
            suggestion="Extract common functionality",
            confidence=0.88,
            duplicate_files=["duplicate1.py", "duplicate2.py"],
            similarity_score=0.92
        )
        
        assert issue.category == IssueCategory.DUPLICATION
        assert len(issue.affected_files) == 3  # Original + 2 duplicates
        assert issue.metadata['similarity_score'] == 0.92
        assert issue.metadata['duplication_type'] == "near_duplicate"


class TestAnalyzerUtils:
    """Tests for AnalyzerUtils."""
    
    def test_extract_string_literals_python(self):
        """Test extracting string literals from Python code."""
        code = '''
def test():
    name = "John Doe"
    message = 'Hello, world!'
    doc = """This is a docstring"""
    return f"Hello, {name}"
'''
        
        literals = AnalyzerUtils.extract_string_literals(code, "python")
        
        # Should find string literals (exact results depend on AST parsing)
        assert len(literals) > 0
        assert any("John Doe" in literal for literal in literals)
    
    def test_find_hardcoded_secrets(self):
        """Test finding hardcoded secrets."""
        code = '''
API_KEY = "sk-1234567890abcdef1234567890abcdef"
password = "supersecret123"
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
# This is just an example_key = "not_real"
test_password = "dummy"  # This should be ignored
'''
        
        secrets = AnalyzerUtils.find_hardcoded_secrets(code)
        
        # Should find API key, password, and token
        secret_types = [secret[0] for secret in secrets]
        assert "api_key" in secret_types
        assert "password" in secret_types
        assert "token" in secret_types
        
        # Should not find commented or test values
        contexts = [secret[2] for secret in secrets]
        assert not any("example_key" in context for context in contexts)
        assert not any("dummy" in context for context in contexts)
    
    def test_find_sql_injection_risks_python(self):
        """Test finding SQL injection risks in Python."""
        code = '''
def get_user(user_id):
    query = "SELECT * FROM users WHERE id = %s" % user_id  # Risky
    cursor.execute(query)
    
    safe_query = "SELECT * FROM users WHERE id = %s"
    cursor.execute(safe_query, (user_id,))  # Safe
    
    risky_query = f"SELECT * FROM users WHERE name = '{name}'"  # Risky
'''
        
        risks = AnalyzerUtils.find_sql_injection_risks(code, "python")
        
        # Should find risky patterns
        assert len(risks) >= 1
        risk_contexts = [risk[1] for risk in risks]
        assert any("%" in context for context in risk_contexts)
    
    def test_calculate_function_complexity(self):
        """Test calculating function complexity metrics."""
        from code_quality_agent.core.models import Function
        
        func = Function(
            name="complex_function",
            line_start=1,
            line_end=20,
            parameters=["param1", "param2", "param3"],
            complexity=8
        )
        
        code = '''
def complex_function(param1, param2, param3):
    """A complex function for testing."""
    if param1 > 0:
        if param2 > 0:
            for i in range(param1):
                if i % 2 == 0:
                    try:
                        result = param1 / i
                    except ZeroDivisionError:
                        result = 0
                else:
                    while param2 > 0:
                        param2 -= 1
        else:
            result = param1 * 2
    else:
        result = 0
    return result
'''
        
        metrics = AnalyzerUtils.calculate_function_complexity(func, code)
        
        assert metrics['cyclomatic_complexity'] == 8
        assert metrics['cognitive_complexity'] > 0
        assert metrics['nesting_depth'] > 0
        assert metrics['lines_of_code'] > 0
        assert metrics['parameters_count'] == 3
        assert metrics['has_docstring'] is True
    
    def test_find_code_smells(self):
        """Test finding code smells."""
        from code_quality_agent.core.models import ParsedFile, Function, Class
        
        # Create parsed file with code smells
        long_func = Function(
            name="very_long_function",
            line_start=1,
            line_end=60,  # 60 lines long
            parameters=["p1", "p2", "p3", "p4", "p5", "p6"]  # 6 parameters
        )
        
        large_class = Class(
            name="GodClass",
            line_start=70,
            line_end=200,
            methods=[Function(f"method_{i}", i, i) for i in range(25)]  # 25 methods
        )
        
        parsed_file = ParsedFile(
            path="smelly.py",
            language="python",
            content="",
            functions=[long_func],
            classes=[large_class]
        )
        
        smells = AnalyzerUtils.find_code_smells(parsed_file)
        
        # Should find multiple smells
        smell_types = [smell['type'] for smell in smells]
        assert 'long_parameter_list' in smell_types
        assert 'large_class' in smell_types
        assert 'long_function' in smell_types
    
    def test_extract_imports_and_dependencies(self):
        """Test extracting and categorizing imports."""
        from code_quality_agent.core.models import ParsedFile, Import
        
        imports = [
            Import(module="os", is_from_import=False),  # Standard library
            Import(module="requests", is_from_import=False),  # Third party
            Import(module="./utils", is_from_import=True),  # Local
            Import(module=".config", is_from_import=True),  # Relative
        ]
        
        parsed_file = ParsedFile(
            path="test.py",
            language="python",
            content="",
            imports=imports
        )
        
        dependencies = AnalyzerUtils.extract_imports_and_dependencies(parsed_file)
        
        assert "os" in dependencies['standard_library']
        assert "requests" in dependencies['third_party']
        assert "./utils" in dependencies['local']
        assert ".config" in dependencies['relative']
    
    def test_calculate_file_metrics(self):
        """Test calculating file metrics."""
        from code_quality_agent.core.models import ParsedFile, Function, Class, FileMetadata
        
        functions = [
            Function("func1", 1, 10, complexity=3),
            Function("func2", 15, 25, complexity=7),
            Function("func3", 30, 40, complexity=2)
        ]
        
        classes = [
            Class("Class1", 50, 80),
            Class("Class2", 90, 120)
        ]
        
        parsed_file = ParsedFile(
            path="metrics.py",
            language="python",
            content="",
            functions=functions,
            classes=classes,
            metadata=FileMetadata(
                file_path="metrics.py",
                language="python",
                size_bytes=1000,
                line_count=150
            )
        )
        
        metrics = AnalyzerUtils.calculate_file_metrics(parsed_file)
        
        assert metrics['total_lines'] == 150
        assert metrics['function_count'] == 3
        assert metrics['class_count'] == 2
        assert metrics['average_function_complexity'] == 4.0  # (3+7+2)/3
        assert metrics['max_function_complexity'] == 7
        assert metrics['total_complexity'] == 12