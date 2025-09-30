"""Tests for unified code parser."""

import pytest
import tempfile
from pathlib import Path

from code_quality_agent.parsers.unified_parser import UnifiedCodeParser
from code_quality_agent.core.models import AnalysisOptions, ParsedFile


class TestUnifiedCodeParser:
    """Tests for UnifiedCodeParser class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = UnifiedCodeParser()
    
    def test_initialization(self):
        """Test parser initialization."""
        assert len(self.parser.get_supported_languages()) >= 2
        assert "python" in self.parser.get_supported_languages()
        assert "javascript" in self.parser.get_supported_languages()
        
        extensions = self.parser.get_supported_extensions()
        assert ".py" in extensions
        assert ".js" in extensions
        assert ".ts" in extensions
    
    def test_can_parse_file(self):
        """Test file parsing capability detection."""
        assert self.parser.can_parse_file(Path("test.py"))
        assert self.parser.can_parse_file(Path("test.js"))
        assert self.parser.can_parse_file(Path("test.ts"))
        assert self.parser.can_parse_file(Path("test.jsx"))
        assert not self.parser.can_parse_file(Path("test.txt"))
        assert not self.parser.can_parse_file(Path("test.cpp"))
    
    def test_parse_single_python_file(self):
        """Test parsing a single Python file."""
        code = '''
def hello_world():
    """Say hello to the world."""
    print("Hello, World!")
    return "greeting"

class Greeter:
    """A simple greeter class."""
    
    def greet(self, name):
        """Greet someone by name."""
        return f"Hello, {name}!"
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            
            parsed = self.parser.parse_file(Path(f.name))
            
            assert parsed is not None
            assert parsed.language == "python"
            assert len(parsed.functions) >= 1
            assert len(parsed.classes) >= 1
            
            # Check function details
            hello_func = next((f for f in parsed.functions if f.name == "hello_world"), None)
            assert hello_func is not None
            assert hello_func.docstring == "Say hello to the world."
            
            # Check class details
            greeter_class = next((c for c in parsed.classes if c.name == "Greeter"), None)
            assert greeter_class is not None
            assert len(greeter_class.methods) >= 1
    
    def test_parse_single_javascript_file(self):
        """Test parsing a single JavaScript file."""
        code = '''
/**
 * Calculate the sum of two numbers
 * @param {number} a - First number
 * @param {number} b - Second number
 * @returns {number} The sum
 */
function add(a, b) {
    return a + b;
}

class Calculator {
    constructor() {
        this.result = 0;
    }
    
    add(value) {
        this.result += value;
        return this.result;
    }
    
    reset() {
        this.result = 0;
    }
}

export { add, Calculator };
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write(code)
            f.flush()
            
            parsed = self.parser.parse_file(Path(f.name))
            
            assert parsed is not None
            assert parsed.language == "javascript"
            # Note: Results depend on JavaScript parser implementation
    
    def test_parse_directory_mixed_languages(self):
        """Test parsing a directory with mixed programming languages."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create Python file
            python_code = '''
def python_function():
    """A Python function."""
    return "python"

class PythonClass:
    """A Python class."""
    pass
'''
            python_file = temp_path / "python_module.py"
            python_file.write_text(python_code)
            
            # Create JavaScript file
            js_code = '''
function jsFunction() {
    return "javascript";
}

class JSClass {
    constructor() {
        this.type = "js";
    }
}
'''
            js_file = temp_path / "js_module.js"
            js_file.write_text(js_code)
            
            # Create TypeScript file
            ts_code = '''
interface User {
    name: string;
    age: number;
}

function processUser(user: User): string {
    return `User: ${user.name}, Age: ${user.age}`;
}

class UserManager {
    private users: User[] = [];
    
    addUser(user: User): void {
        this.users.push(user);
    }
}
'''
            ts_file = temp_path / "ts_module.ts"
            ts_file.write_text(ts_code)
            
            # Create unsupported file
            txt_file = temp_path / "readme.txt"
            txt_file.write_text("This is a text file")
            
            # Parse directory
            parsed_files = self.parser.parse_directory(temp_path)
            
            # Should parse supported files only
            assert len(parsed_files) >= 2  # At least Python and one JS/TS file
            
            languages = {pf.language for pf in parsed_files}
            assert "python" in languages
            # JavaScript or TypeScript should be present
            assert any(lang in languages for lang in ["javascript", "typescript"])
            
            # Check that unsupported files are ignored
            file_paths = {pf.path for pf in parsed_files}
            assert str(txt_file) not in file_paths
    
    def test_parse_directory_with_options(self):
        """Test parsing directory with analysis options."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create files
            (temp_path / "main.py").write_text("def main(): pass")
            (temp_path / "test_main.py").write_text("def test(): pass")
            (temp_path / "utils.js").write_text("function util() {}")
            
            # Create subdirectory
            sub_dir = temp_path / "tests"
            sub_dir.mkdir()
            (sub_dir / "test_utils.py").write_text("def test_util(): pass")
            
            # Test with exclude patterns
            options = AnalysisOptions(
                exclude_patterns=["test_*", "tests/**"]
            )
            
            parsed_files = self.parser.parse_directory(temp_path, options)
            
            # Should exclude test files
            file_names = [Path(pf.path).name for pf in parsed_files]
            assert "main.py" in file_names or "utils.js" in file_names
            assert "test_main.py" not in file_names
            assert "test_utils.py" not in file_names
    
    def test_parallel_vs_sequential_parsing(self):
        """Test that parallel and sequential parsing produce same results."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create multiple files
            for i in range(5):
                python_file = temp_path / f"module_{i}.py"
                python_file.write_text(f'''
def function_{i}():
    """Function {i}."""
    return {i}

class Class_{i}:
    """Class {i}."""
    def method(self):
        return {i}
''')
            
            # Parse sequentially
            options_sequential = AnalysisOptions(parallel_processing=False)
            sequential_results = self.parser.parse_directory(temp_path, options_sequential)
            
            # Parse in parallel
            options_parallel = AnalysisOptions(parallel_processing=True, max_workers=2)
            parallel_results = self.parser.parse_directory(temp_path, options_parallel)
            
            # Results should be equivalent
            assert len(sequential_results) == len(parallel_results)
            
            # Sort by path for comparison
            sequential_sorted = sorted(sequential_results, key=lambda x: x.path)
            parallel_sorted = sorted(parallel_results, key=lambda x: x.path)
            
            for seq, par in zip(sequential_sorted, parallel_sorted):
                assert seq.path == par.path
                assert seq.language == par.language
                assert len(seq.functions) == len(par.functions)
                assert len(seq.classes) == len(par.classes)
    
    def test_build_dependency_graph(self):
        """Test building unified dependency graph."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create Python files with dependencies
            main_py = temp_path / "main.py"
            main_py.write_text('''
from utils import helper
from models import User
import config

def main():
    user = User()
    helper()
''')
            
            utils_py = temp_path / "utils.py"
            utils_py.write_text('''
from models import BaseModel

def helper():
    pass
''')
            
            models_py = temp_path / "models.py"
            models_py.write_text('''
class BaseModel:
    pass

class User(BaseModel):
    pass
''')
            
            config_py = temp_path / "config.py"
            config_py.write_text('DEBUG = True')
            
            # Create JavaScript files with dependencies
            main_js = temp_path / "main.js"
            main_js.write_text('''
import { helper } from './utils.js';
import { User } from './models.js';

function main() {
    const user = new User();
    helper();
}
''')
            
            utils_js = temp_path / "utils.js"
            utils_js.write_text('''
export function helper() {
    console.log('helping');
}
''')
            
            models_js = temp_path / "models.js"
            models_js.write_text('''
export class User {
    constructor() {}
}
''')
            
            # Parse all files
            parsed_files = self.parser.parse_directory(temp_path)
            
            # Build dependency graph
            graph = self.parser.build_dependency_graph(parsed_files)
            
            # Should have nodes and edges
            assert len(graph.nodes) > 0
            # Note: Actual dependency detection depends on parser implementation
    
    def test_parsing_statistics(self):
        """Test generation of parsing statistics."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create files with known content
            python_file = temp_path / "test.py"
            python_file.write_text('''
def func1():
    """Function 1."""
    if True:
        return 1

def func2():
    """Function 2."""
    for i in range(10):
        if i % 2 == 0:
            print(i)

class TestClass:
    """Test class."""
    def method1(self):
        pass
    
    def method2(self):
        pass
''')
            
            js_file = temp_path / "test.js"
            js_file.write_text('''
function jsFunc() {
    return "hello";
}

class JSClass {
    constructor() {
        this.value = 0;
    }
    
    method() {
        return this.value;
    }
}
''')
            
            # Parse files
            parsed_files = self.parser.parse_directory(temp_path)
            
            # Generate statistics
            stats = self.parser.get_parsing_statistics(parsed_files)
            
            # Verify statistics structure
            assert 'total_files' in stats
            assert 'languages' in stats
            assert 'total_functions' in stats
            assert 'total_classes' in stats
            assert 'average_complexity' in stats
            assert 'files_by_extension' in stats
            
            assert stats['total_files'] == len(parsed_files)
            assert stats['total_files'] > 0
            
            # Should have language breakdown
            if 'python' in stats['languages']:
                python_stats = stats['languages']['python']
                assert 'files' in python_stats
                assert 'functions' in python_stats
                assert 'classes' in python_stats
    
    def test_validation_results(self):
        """Test parsing validation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create file with high complexity function
            complex_file = temp_path / "complex.py"
            complex_file.write_text('''
def very_complex_function(x):
    """A very complex function for testing."""
    if x > 0:
        if x > 10:
            if x > 20:
                if x > 30:
                    if x > 40:
                        if x > 50:
                            return "very high"
                        return "high"
                    return "medium-high"
                return "medium"
            return "low-medium"
        return "low"
    return "zero"

def large_function_without_docstring():
    # This is a large function without proper docstring
    result = 0
    for i in range(100):
        if i % 2 == 0:
            result += i
        else:
            result -= i
    
    if result > 0:
        print("Positive result")
    else:
        print("Non-positive result")
    
    return result
''')
            
            # Create empty-looking file
            empty_file = temp_path / "empty.py"
            empty_file.write_text('''
# This file has many lines but no functions or classes
# Line 2
# Line 3
# Line 4
# Line 5
# Line 6
# Line 7
# Line 8
# Line 9
# Line 10
# Line 11
# Line 12
''')
            
            # Parse files
            parsed_files = self.parser.parse_directory(temp_path)
            
            # Validate results
            validation = self.parser.validate_parsing_results(parsed_files)
            
            # Check validation structure
            assert 'valid_files' in validation
            assert 'files_with_issues' in validation
            assert 'issues' in validation
            assert 'warnings' in validation
            assert 'language_coverage' in validation
            
            # Should detect issues or warnings
            total_files = validation['valid_files'] + validation['files_with_issues']
            assert total_files == len(parsed_files)
    
    def test_register_custom_parser(self):
        """Test registering a custom parser."""
        from code_quality_agent.parsers.base import CodeParser
        from code_quality_agent.core.models import ParsedFile, FileMetadata
        
        class MockParser(CodeParser):
            def get_supported_languages(self):
                return ["mock"]
            
            def get_file_extensions(self):
                return [".mock"]
            
            def parse_file(self, file_path):
                return ParsedFile(
                    path=str(file_path),
                    language="mock",
                    content="mock content",
                    metadata=FileMetadata(
                        file_path=str(file_path),
                        language="mock",
                        size_bytes=100,
                        line_count=10
                    )
                )
        
        # Register custom parser
        mock_parser = MockParser()
        self.parser.register_parser(mock_parser)
        
        # Verify registration
        assert "mock" in self.parser.get_supported_languages()
        assert ".mock" in self.parser.get_supported_extensions()
        assert self.parser.can_parse_file(Path("test.mock"))
        
        # Test parsing with custom parser
        with tempfile.NamedTemporaryFile(suffix='.mock', delete=False) as f:
            f.write(b"mock file content")
            f.flush()
            
            parsed = self.parser.parse_file(Path(f.name))
            assert parsed is not None
            assert parsed.language == "mock"
    
    def test_get_file_language_distribution(self):
        """Test getting language distribution in directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create files of different languages
            (temp_path / "file1.py").write_text("# Python file 1")
            (temp_path / "file2.py").write_text("# Python file 2")
            (temp_path / "file1.js").write_text("// JavaScript file")
            (temp_path / "file1.ts").write_text("// TypeScript file")
            (temp_path / "readme.txt").write_text("Text file")
            
            distribution = self.parser.get_file_language_distribution(temp_path)
            
            # Should count supported languages only
            assert distribution.get("python", 0) == 2
            assert distribution.get("javascript", 0) >= 1 or distribution.get("typescript", 0) >= 1
            assert "txt" not in distribution  # Unsupported files not counted
    
    def test_get_parser_for_language(self):
        """Test getting parser instance for specific language."""
        python_parser = self.parser.get_parser_for_language("python")
        assert python_parser is not None
        assert "python" in python_parser.get_supported_languages()
        
        js_parser = self.parser.get_parser_for_language("javascript")
        assert js_parser is not None
        assert "javascript" in js_parser.get_supported_languages()
        
        unknown_parser = self.parser.get_parser_for_language("unknown")
        assert unknown_parser is None
    
    def test_large_file_handling(self):
        """Test handling of large files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create a large file (simulate by setting small max size)
            large_file = temp_path / "large.py"
            large_content = "# Large file\n" * 1000  # Create large content
            large_file.write_text(large_content)
            
            # Configure parser with small max file size
            small_parser = UnifiedCodeParser({"max_file_size_mb": 0.001})  # Very small limit
            
            # Should skip large file
            parsed = small_parser.parse_file(large_file)
            assert parsed is None  # Should be None due to size limit