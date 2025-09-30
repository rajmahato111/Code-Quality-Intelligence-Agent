"""Tests for Python AST parser."""

import pytest
import tempfile
from pathlib import Path
import ast

from code_quality_agent.parsers.python_parser import PythonParser
from code_quality_agent.core.models import ParsedFile, Function, Class, Import


class TestPythonParser:
    """Tests for PythonParser class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = PythonParser()
    
    def test_supported_languages(self):
        """Test supported languages."""
        languages = self.parser.get_supported_languages()
        assert "python" in languages
    
    def test_file_extensions(self):
        """Test supported file extensions."""
        extensions = self.parser.get_file_extensions()
        assert ".py" in extensions
        assert ".pyw" in extensions
    
    def test_can_parse_file(self):
        """Test file parsing capability check."""
        assert self.parser.can_parse_file(Path("test.py"))
        assert self.parser.can_parse_file(Path("test.pyw"))
        assert not self.parser.can_parse_file(Path("test.js"))
        assert not self.parser.can_parse_file(Path("test.txt"))
    
    def test_parse_simple_function(self):
        """Test parsing a simple function."""
        code = '''
def hello_world(name, age=25):
    """Say hello to someone."""
    print(f"Hello, {name}! You are {age} years old.")
    return f"Greeting for {name}"
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            
            parsed = self.parser.parse_file(Path(f.name))
            
            assert parsed is not None
            assert parsed.language == "python"
            assert len(parsed.functions) == 1
            
            func = parsed.functions[0]
            assert func.name == "hello_world"
            assert func.parameters == ["name", "age"]
            assert func.docstring == "Say hello to someone."
            assert not func.is_async
            assert not func.is_method
            assert func.complexity >= 1
    
    def test_parse_async_function(self):
        """Test parsing an async function."""
        code = '''
import asyncio

async def fetch_data(url):
    """Fetch data asynchronously."""
    await asyncio.sleep(1)
    return "data"
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            
            parsed = self.parser.parse_file(Path(f.name))
            
            assert parsed is not None
            assert len(parsed.functions) == 1
            
            func = parsed.functions[0]
            assert func.name == "fetch_data"
            assert func.is_async
            assert func.docstring == "Fetch data asynchronously."
    
    def test_parse_class_with_methods(self):
        """Test parsing a class with methods."""
        code = '''
class Calculator:
    """A simple calculator class."""
    
    def __init__(self, initial_value=0):
        """Initialize calculator."""
        self.value = initial_value
    
    def add(self, x):
        """Add a number."""
        self.value += x
        return self.value
    
    @property
    def current_value(self):
        """Get current value."""
        return self.value
    
    @staticmethod
    def multiply(a, b):
        """Multiply two numbers."""
        return a * b
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            
            parsed = self.parser.parse_file(Path(f.name))
            
            assert parsed is not None
            assert len(parsed.classes) == 1
            
            cls = parsed.classes[0]
            assert cls.name == "Calculator"
            assert cls.docstring == "A simple calculator class."
            assert len(cls.methods) == 4  # __init__, add, current_value, multiply
            
            # Check method details
            init_method = next(m for m in cls.methods if m.name == "__init__")
            assert init_method.is_method
            assert init_method.class_name == "Calculator"
            assert "self" in init_method.parameters
            
            # Check decorator
            property_method = next(m for m in cls.methods if m.name == "current_value")
            assert "@property" in property_method.decorators
    
    def test_parse_inheritance(self):
        """Test parsing class inheritance."""
        code = '''
class Animal:
    """Base animal class."""
    pass

class Dog(Animal):
    """Dog class inheriting from Animal."""
    
    def bark(self):
        """Make a barking sound."""
        return "Woof!"

class GermanShepherd(Dog):
    """German Shepherd inheriting from Dog."""
    pass
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            
            parsed = self.parser.parse_file(Path(f.name))
            
            assert parsed is not None
            assert len(parsed.classes) == 3
            
            # Check inheritance
            dog_class = next(c for c in parsed.classes if c.name == "Dog")
            assert "Animal" in dog_class.base_classes
            
            german_shepherd = next(c for c in parsed.classes if c.name == "GermanShepherd")
            assert "Dog" in german_shepherd.base_classes
    
    def test_parse_imports(self):
        """Test parsing import statements."""
        code = '''
import os
import sys as system
from pathlib import Path
from typing import List, Dict, Optional
from . import local_module
from ..parent import parent_module
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            
            parsed = self.parser.parse_file(Path(f.name))
            
            assert parsed is not None
            imports = parsed.imports
            
            # Check regular import
            os_import = next(imp for imp in imports if imp.module == "os")
            assert not os_import.is_from_import
            assert os_import.alias is None
            
            # Check import with alias
            sys_import = next(imp for imp in imports if imp.module == "sys")
            assert sys_import.alias == "system"
            
            # Check from import
            pathlib_import = next(imp for imp in imports if imp.module == "pathlib")
            assert pathlib_import.is_from_import
            assert "Path" in pathlib_import.names
            
            typing_import = next(imp for imp in imports if imp.module == "typing")
            assert pathlib_import.is_from_import
            assert set(typing_import.names) == {"List", "Dict", "Optional"}
    
    def test_complexity_calculation(self):
        """Test cyclomatic complexity calculation."""
        code = '''
def complex_function(x, y):
    """A function with various control structures."""
    if x > 0:
        if y > 0:
            for i in range(x):
                if i % 2 == 0:
                    try:
                        result = x / i
                    except ZeroDivisionError:
                        result = 0
                    else:
                        result += 1
                else:
                    while y > 0:
                        y -= 1
        else:
            result = [i for i in range(x) if i > 0]
    else:
        result = 0
    
    return result
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            
            parsed = self.parser.parse_file(Path(f.name))
            
            assert parsed is not None
            assert len(parsed.functions) == 1
            
            func = parsed.functions[0]
            # This function has multiple decision points, so complexity should be > 1
            assert func.complexity > 5  # Should be quite complex
    
    def test_parse_decorators(self):
        """Test parsing function and class decorators."""
        code = '''
@dataclass
@frozen
class Point:
    """A point in 2D space."""
    x: int
    y: int

@property
@lru_cache(maxsize=128)
def expensive_calculation(self):
    """An expensive calculation."""
    return sum(range(1000))

@staticmethod
@deprecated("Use new_function instead")
def old_function():
    """An old function."""
    pass
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            
            parsed = self.parser.parse_file(Path(f.name))
            
            assert parsed is not None
            
            # Check class decorators
            point_class = next(c for c in parsed.classes if c.name == "Point")
            assert len(point_class.decorators) >= 1  # Should have decorators
            
            # Check function decorators
            expensive_func = next(f for f in parsed.functions if f.name == "expensive_calculation")
            assert len(expensive_func.decorators) >= 1
    
    def test_parse_syntax_error(self):
        """Test handling of syntax errors."""
        code = '''
def broken_function(
    # Missing closing parenthesis and colon
    print("This is broken")
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            
            parsed = self.parser.parse_file(Path(f.name))
            
            # Should return None for files with syntax errors
            assert parsed is None
    
    def test_parse_empty_file(self):
        """Test parsing an empty file."""
        code = ''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            
            parsed = self.parser.parse_file(Path(f.name))
            
            assert parsed is not None
            assert len(parsed.functions) == 0
            assert len(parsed.classes) == 0
            assert len(parsed.imports) == 0
    
    def test_parse_comments_only(self):
        """Test parsing a file with only comments."""
        code = '''
# This is a comment
# Another comment
"""
This is a docstring at module level
"""
# More comments
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            
            parsed = self.parser.parse_file(Path(f.name))
            
            assert parsed is not None
            assert len(parsed.functions) == 0
            assert len(parsed.classes) == 0
            assert len(parsed.imports) == 0
    
    def test_complexity_metrics(self):
        """Test complexity metrics calculation."""
        code = '''
def simple_function():
    """A simple function."""
    return 42

def complex_function(x):
    """A more complex function."""
    if x > 0:
        for i in range(x):
            if i % 2 == 0:
                print(i)
    return x

class TestClass:
    """A test class."""
    
    def method1(self):
        """Method 1."""
        pass
    
    def method2(self):
        """Method 2."""
        if True:
            return 1
        return 0
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            
            parsed = self.parser.parse_file(Path(f.name))
            metrics = self.parser.get_complexity_metrics(parsed)
            
            assert "cyclomatic_complexity" in metrics
            assert "max_complexity" in metrics
            assert "function_count" in metrics
            assert "class_count" in metrics
            assert "lines_of_code" in metrics
            assert "maintainability_index" in metrics
            
            assert metrics["function_count"] == 4  # 2 functions + 2 methods
            assert metrics["class_count"] == 1
            assert metrics["lines_of_code"] > 0
            assert 0 <= metrics["maintainability_index"] <= 100
    
    def test_dependency_extraction(self):
        """Test dependency graph extraction."""
        # Create multiple test files
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # File 1: main.py
            main_code = '''
from utils import helper_function
from models import User
import config
'''
            main_file = temp_path / "main.py"
            main_file.write_text(main_code)
            
            # File 2: utils.py
            utils_code = '''
from models import BaseModel

def helper_function():
    pass
'''
            utils_file = temp_path / "utils.py"
            utils_file.write_text(utils_code)
            
            # File 3: models.py
            models_code = '''
class BaseModel:
    pass

class User(BaseModel):
    pass
'''
            models_file = temp_path / "models.py"
            models_file.write_text(models_code)
            
            # File 4: config.py
            config_code = '''
DEBUG = True
'''
            config_file = temp_path / "config.py"
            config_file.write_text(config_code)
            
            # Parse all files
            parsed_files = []
            for file_path in [main_file, utils_file, models_file, config_file]:
                parsed = self.parser.parse_file(file_path)
                if parsed:
                    parsed_files.append(parsed)
            
            # Extract dependencies
            graph = self.parser.extract_dependencies(parsed_files)
            
            # Check that dependencies were found
            assert len(graph.nodes) > 0
            assert len(graph.edges) > 0
            
            # Check specific dependencies
            main_deps = graph.get_dependencies(str(main_file))
            assert len(main_deps) > 0  # main.py should have dependencies
    
    def test_file_path_to_module_name(self):
        """Test conversion of file paths to module names."""
        parser = PythonParser()
        
        assert parser._file_path_to_module_name("main.py") == "main"
        assert parser._file_path_to_module_name("src/utils.py") == "utils"
        assert parser._file_path_to_module_name("app/models/user.py") == "models.user"
        assert parser._file_path_to_module_name("lib/package/module.py") == "package.module"
    
    def test_lines_of_code_counting(self):
        """Test lines of code counting."""
        code = '''
# This is a comment
def function():
    """Docstring"""
    # Another comment
    x = 1
    
    y = 2  # Inline comment
    return x + y

# Final comment
'''
        
        parser = PythonParser()
        loc = parser._count_lines_of_code(code)
        
        # Should count only non-comment, non-empty lines
        # Expected: def function():, x = 1, y = 2, return x + y, """Docstring"""
        assert loc >= 4