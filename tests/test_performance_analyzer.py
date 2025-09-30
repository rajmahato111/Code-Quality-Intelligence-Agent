"""Tests for PerformanceAnalyzer."""

import pytest

from code_quality_agent.analyzers.performance_analyzer import PerformanceAnalyzer
from code_quality_agent.analyzers.base import IssueCategory, Severity
from code_quality_agent.core.models import (
    ParsedFile, AnalysisContext, AnalysisOptions, 
    FileMetadata, Function, Class
)


class TestPerformanceAnalyzer:
    """Tests for PerformanceAnalyzer class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = PerformanceAnalyzer()
    
    def test_analyzer_properties(self):
        """Test basic analyzer properties."""
        assert self.analyzer.get_category() == IssueCategory.PERFORMANCE
        assert "python" in self.analyzer.get_supported_languages()
        assert "javascript" in self.analyzer.get_supported_languages()
        assert "typescript" in self.analyzer.get_supported_languages()
    
    def test_custom_thresholds(self):
        """Test analyzer with custom thresholds."""
        custom_config = {
            'max_nested_loops': 2,
            'max_loop_complexity': 8,
            'max_string_concatenations': 3,
            'max_database_calls_in_loop': 0
        }
        
        analyzer = PerformanceAnalyzer(custom_config)
        
        assert analyzer.thresholds['max_nested_loops'] == 2
        assert analyzer.thresholds['max_loop_complexity'] == 8
        assert analyzer.thresholds['max_string_concatenations'] == 3
        assert analyzer.thresholds['max_database_calls_in_loop'] == 0
    
    def test_deeply_nested_loops(self):
        """Test detection of deeply nested loops."""
        nested_loops_code = '''
def process_matrix(matrix):
    result = []
    for i in range(len(matrix)):
        for j in range(len(matrix[i])):
            for k in range(len(matrix[i][j])):
                for l in range(len(matrix[i][j][k])):  # 4 levels deep
                    result.append(matrix[i][j][k][l] * 2)
    return result
'''
        
        parsed_file = self._create_parsed_file("nested.py", "python", nested_loops_code)
        context = AnalysisContext(options=AnalysisOptions())
        
        issues = self.analyzer.analyze([parsed_file], context)
        
        # Should find deeply nested loops
        nested_issues = [issue for issue in issues if "Deeply Nested Loops" in issue.title]
        assert len(nested_issues) >= 1
        
        issue = nested_issues[0]
        assert issue.category == IssueCategory.PERFORMANCE
        assert issue.severity == Severity.HIGH
        assert issue.metadata['nesting_depth'] > 3
        assert "refactoring nested loops" in issue.suggestion.lower()
    
    def test_inefficient_loop_patterns_python(self):
        """Test detection of inefficient loop patterns in Python."""
        inefficient_code = '''
def process_items(items):
    # Inefficient: for i in range(len(items))
    for i in range(len(items)):
        print(items[i])
    
    # Inefficient: while with len() check
    i = 0
    while i < len(items):
        print(items[i])
        i += 1
'''
        
        parsed_file = self._create_parsed_file("inefficient.py", "python", inefficient_code)
        context = AnalysisContext(options=AnalysisOptions())
        
        issues = self.analyzer.analyze([parsed_file], context)
        
        # Should find inefficient loop patterns
        loop_issues = [issue for issue in issues if "Inefficient Loop Pattern" in issue.title]
        assert len(loop_issues) >= 1
        
        issue = loop_issues[0]
        assert issue.category == IssueCategory.PERFORMANCE
        assert issue.severity == Severity.MEDIUM
        assert "more efficient loop patterns" in issue.suggestion.lower()
    
    def test_inefficient_loop_patterns_javascript(self):
        """Test detection of inefficient loop patterns in JavaScript."""
        js_inefficient_code = '''
function processArray(arr) {
    // Inefficient: length property accessed in each iteration
    for (var i = 0; i < arr.length; i++) {
        console.log(arr[i]);
    }
    
    // Another inefficient pattern
    for (let j = 0; j < items.length; j++) {
        process(items[j]);
    }
}
'''
        
        parsed_file = self._create_parsed_file("inefficient.js", "javascript", js_inefficient_code)
        context = AnalysisContext(options=AnalysisOptions())
        
        issues = self.analyzer.analyze([parsed_file], context)
        
        # Should find inefficient JavaScript loop patterns
        loop_issues = [issue for issue in issues if "Inefficient Loop Pattern" in issue.title]
        assert len(loop_issues) >= 1
        
        issue = loop_issues[0]
        assert issue.category == IssueCategory.PERFORMANCE
        assert issue.severity == Severity.MEDIUM
    
    def test_database_calls_in_loops(self):
        """Test detection of database calls in loops (N+1 problem)."""
        n_plus_one_code = '''
def get_user_posts(user_ids):
    posts = []
    for user_id in user_ids:
        # N+1 problem: database query in loop
        user_posts = db.query("SELECT * FROM posts WHERE user_id = ?", user_id)
        posts.extend(user_posts)
    return posts

def update_users(users):
    for user in users:
        # Another N+1 problem
        db.execute("UPDATE users SET last_seen = NOW() WHERE id = ?", user.id)
'''
        
        parsed_file = self._create_parsed_file("n_plus_one.py", "python", n_plus_one_code)
        context = AnalysisContext(options=AnalysisOptions())
        
        issues = self.analyzer.analyze([parsed_file], context)
        
        # Should find N+1 problems
        db_issues = [issue for issue in issues if "Database Call in Loop" in issue.title]
        assert len(db_issues) >= 2
        
        issue = db_issues[0]
        assert issue.category == IssueCategory.PERFORMANCE
        assert issue.severity == Severity.HIGH
        assert "batch operations" in issue.suggestion.lower()
    
    def test_string_concatenation_in_loops(self):
        """Test detection of inefficient string concatenation in loops."""
        string_concat_code = '''
def build_html(items):
    html = ""
    for item in items:
        html += "<div>" + item.name + "</div>"  # Inefficient concatenation
        html += "<p>" + item.description + "</p>"
        html += "<hr>"
    return html

def create_csv(data):
    csv_content = ""
    for row in data:
        for cell in row:
            csv_content += str(cell) + ","  # Multiple concatenations in nested loop
        csv_content += "\\n"
    return csv_content
'''
        
        parsed_file = self._create_parsed_file("string_concat.py", "python", string_concat_code)
        context = AnalysisContext(options=AnalysisOptions())
        
        issues = self.analyzer.analyze([parsed_file], context)
        
        # Should find string concatenation issues
        string_issues = [issue for issue in issues if "String Concatenation in Loop" in issue.title]
        assert len(string_issues) >= 1
        
        issue = string_issues[0]
        assert issue.category == IssueCategory.PERFORMANCE
        assert issue.severity == Severity.MEDIUM
        assert "string builders" in issue.suggestion.lower() or "join" in issue.suggestion.lower()
    
    def test_inefficient_list_building(self):
        """Test detection of inefficient list building patterns."""
        inefficient_list_code = '''
def process_numbers(numbers):
    # Inefficient: using append in loop when list comprehension would be better
    result = []
    for num in numbers:
        result.append(num * 2)
    
    # Unnecessary list conversion
    squared = list(x * x for x in numbers)
    
    return result, squared
'''
        
        parsed_file = self._create_parsed_file("list_building.py", "python", inefficient_list_code)
        context = AnalysisContext(options=AnalysisOptions())
        
        issues = self.analyzer.analyze([parsed_file], context)
        
        # Should find inefficient list building
        list_issues = [issue for issue in issues if "Inefficient List Building" in issue.title or "Unnecessary List Conversion" in issue.title]
        assert len(list_issues) >= 1
        
        issue = list_issues[0]
        assert issue.category == IssueCategory.PERFORMANCE
        assert issue.severity == Severity.LOW
    
    def test_high_algorithmic_complexity(self):
        """Test detection of high algorithmic complexity."""
        # Create function with high complexity
        complex_func = Function(
            name="complex_algorithm",
            line_start=1,
            line_end=30,
            parameters=["data"],
            complexity=15  # Above threshold of 10
        )
        
        complex_code = '''
def complex_algorithm(data):
    result = []
    for i in range(len(data)):
        for j in range(len(data)):
            if data[i] > data[j]:
                for k in range(len(data)):
                    if data[k] < data[i]:
                        try:
                            if data[k] % 2 == 0:
                                result.append(data[k])
                        except:
                            continue
    return result
'''
        
        parsed_file = self._create_parsed_file(
            "complex.py", 
            "python", 
            complex_code,
            functions=[complex_func]
        )
        context = AnalysisContext(options=AnalysisOptions())
        
        issues = self.analyzer.analyze([parsed_file], context)
        
        # Should find high complexity issue
        complexity_issues = [issue for issue in issues if "High Algorithmic Complexity" in issue.title]
        assert len(complexity_issues) >= 1
        
        issue = complexity_issues[0]
        assert issue.category == IssueCategory.PERFORMANCE
        assert issue.severity == Severity.MEDIUM
        assert issue.metadata['complexity'] > 10
    
    def test_io_operations_in_loops(self):
        """Test detection of I/O operations in loops."""
        io_in_loop_code = '''
def process_files(filenames):
    results = []
    for filename in filenames:
        # I/O operation in loop
        with open(filename, 'r') as f:
            content = f.read()
            results.append(content.upper())
    return results

def fetch_data(urls):
    data = []
    for url in urls:
        # Network I/O in loop
        response = requests.get(url)
        data.append(response.json())
    return data
'''
        
        parsed_file = self._create_parsed_file("io_loop.py", "python", io_in_loop_code)
        context = AnalysisContext(options=AnalysisOptions())
        
        issues = self.analyzer.analyze([parsed_file], context)
        
        # Should find I/O operations in loops
        io_issues = [issue for issue in issues if "I/O Operation in Loop" in issue.title]
        assert len(io_issues) >= 2
        
        issue = io_issues[0]
        assert issue.category == IssueCategory.PERFORMANCE
        assert issue.severity == Severity.HIGH
        assert "batch operations" in issue.suggestion.lower()
    
    def test_memory_usage_patterns(self):
        """Test detection of potential memory issues."""
        memory_issue_code = '''
# Global list that may grow indefinitely
global_cache = []

def process_data():
    global global_cache
    
    # Global dictionary that may grow indefinitely
    global global_stats = {}
    
    # Large memory allocation
    big_array = [0] * 10000
    
    # Potential infinite growth
    while True:
        global_cache.append(get_new_data())
        if should_stop():
            break
'''
        
        parsed_file = self._create_parsed_file("memory.py", "python", memory_issue_code)
        context = AnalysisContext(options=AnalysisOptions())
        
        issues = self.analyzer.analyze([parsed_file], context)
        
        # Should find memory issues
        memory_issues = [issue for issue in issues if "Potential Memory Issue" in issue.title]
        assert len(memory_issues) >= 1
        
        issue = memory_issues[0]
        assert issue.category == IssueCategory.PERFORMANCE
        assert issue.severity == Severity.MEDIUM
        assert "memory usage patterns" in issue.suggestion.lower()
    
    def test_python_performance_antipatterns(self):
        """Test detection of Python-specific performance anti-patterns."""
        python_antipatterns = '''
def inefficient_python(data, my_dict):
    # Anti-pattern: range(len()) instead of enumerate
    for i in range(len(data)):
        print(i, data[i])
    
    # Anti-pattern: checking dict.keys()
    if 'key' in my_dict.keys():
        return my_dict['key']
    
    # Anti-pattern: unnecessary list() conversion
    keys_list = list(my_dict.keys())
    
    # Anti-pattern: bare except
    try:
        risky_operation()
    except:
        pass
'''
        
        parsed_file = self._create_parsed_file("antipatterns.py", "python", python_antipatterns)
        context = AnalysisContext(options=AnalysisOptions())
        
        issues = self.analyzer.analyze([parsed_file], context)
        
        # Should find Python anti-patterns
        python_issues = [issue for issue in issues if "Python Performance Anti-Pattern" in issue.title]
        assert len(python_issues) >= 2
        
        issue = python_issues[0]
        assert issue.category == IssueCategory.PERFORMANCE
        assert issue.severity == Severity.LOW
    
    def test_javascript_performance_antipatterns(self):
        """Test detection of JavaScript-specific performance anti-patterns."""
        js_antipatterns = '''
function inefficientJS() {
    var items = document.querySelectorAll('.item');
    
    // Anti-pattern: DOM query in loop
    for (var i = 0; i < items.length; i++) {
        var element = document.getElementById('container');
        element.appendChild(items[i]);
    }
    
    // Anti-pattern: innerHTML concatenation
    var html = '';
    for (var j = 0; j < data.length; j++) {
        document.body.innerHTML += '<div>' + data[j] + '</div>';
    }
    
    // Anti-pattern: RegExp in loop
    for (var k = 0; k < strings.length; k++) {
        var regex = new RegExp(pattern);
        if (regex.test(strings[k])) {
            console.log('match');
        }
    }
    
    // Anti-pattern: JSON deep clone
    var cloned = JSON.parse(JSON.stringify(originalObject));
}
'''
        
        parsed_file = self._create_parsed_file("antipatterns.js", "javascript", js_antipatterns)
        context = AnalysisContext(options=AnalysisOptions())
        
        issues = self.analyzer.analyze([parsed_file], context)
        
        # Should find JavaScript anti-patterns
        js_issues = [issue for issue in issues if "JavaScript Performance Anti-Pattern" in issue.title]
        assert len(js_issues) >= 2
        
        issue = js_issues[0]
        assert issue.category == IssueCategory.PERFORMANCE
        assert issue.severity == Severity.MEDIUM
    
    def test_no_issues_for_efficient_code(self):
        """Test that efficient code doesn't trigger false positives."""
        efficient_code = '''
def efficient_processing(data):
    """Efficient data processing example."""
    # Good: using list comprehension
    processed = [item * 2 for item in data if item > 0]
    
    # Good: using enumerate instead of range(len())
    for index, item in enumerate(data):
        if index % 2 == 0:
            print(f"Even index {index}: {item}")
    
    # Good: using join for string building
    result = ''.join(str(item) for item in processed)
    
    # Good: batch database operation (simulated)
    if processed:
        batch_insert(processed)
    
    return result

def batch_insert(items):
    """Simulated batch database operation."""
    # This would be a single database call
    pass
'''
        
        parsed_file = self._create_parsed_file("efficient.py", "python", efficient_code)
        context = AnalysisContext(options=AnalysisOptions())
        
        issues = self.analyzer.analyze([parsed_file], context)
        
        # Should have minimal or no high-severity performance issues
        high_severity_issues = [
            issue for issue in issues 
            if issue.category == IssueCategory.PERFORMANCE and issue.severity == Severity.HIGH
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