"""Utility functions for quality analyzers."""

import re
import ast
from typing import List, Dict, Any, Set, Optional, Tuple
from pathlib import Path

from ..core.models import ParsedFile, Function, Class


class AnalyzerUtils:
    """Utility functions commonly used by quality analyzers."""
    
    @staticmethod
    def extract_string_literals(content: str, language: str) -> List[str]:
        """Extract string literals from source code."""
        literals = []
        
        if language == 'python':
            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Constant) and isinstance(node.value, str):
                        literals.append(node.value)
            except SyntaxError:
                # Fallback to regex for malformed code
                literals.extend(AnalyzerUtils._extract_strings_regex(content, 'python'))
        
        elif language in ['javascript', 'typescript']:
            literals.extend(AnalyzerUtils._extract_strings_regex(content, 'javascript'))
        
        return literals
    
    @staticmethod
    def _extract_strings_regex(content: str, language: str) -> List[str]:
        """Extract strings using regex patterns."""
        literals = []
        
        if language == 'python':
            # Python string patterns
            patterns = [
                r'"""(.*?)"""',  # Triple double quotes
                r"'''(.*?)'''",  # Triple single quotes
                r'"([^"\\]|\\.)*"',  # Double quotes
                r"'([^'\\]|\\.)*'"   # Single quotes
            ]
        else:
            # JavaScript/TypeScript string patterns
            patterns = [
                r'`([^`\\]|\\.)*`',   # Template literals
                r'"([^"\\]|\\.)*"',   # Double quotes
                r"'([^'\\]|\\.)*'"    # Single quotes
            ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.DOTALL)
            literals.extend(matches)
        
        return literals
    
    @staticmethod
    def find_hardcoded_secrets(content: str) -> List[Tuple[str, int, str]]:
        """
        Find potential hardcoded secrets in code.
        
        Returns:
            List of tuples (secret_type, line_number, context)
        """
        secrets = []
        lines = content.splitlines()
        
        # Patterns for different types of secrets
        secret_patterns = {
            'api_key': [
                r'api[_-]?key\s*[=:]\s*["\']([a-zA-Z0-9_-]{20,})["\']',
                r'apikey\s*[=:]\s*["\']([a-zA-Z0-9_-]{20,})["\']'
            ],
            'password': [
                r'password\s*[=:]\s*["\']([^"\']{8,})["\']',
                r'passwd\s*[=:]\s*["\']([^"\']{8,})["\']',
                r'pwd\s*[=:]\s*["\']([^"\']{8,})["\']'
            ],
            'token': [
                r'token\s*[=:]\s*["\']([a-zA-Z0-9_-]{20,})["\']',
                r'access[_-]?token\s*[=:]\s*["\']([a-zA-Z0-9_-]{20,})["\']'
            ],
            'secret': [
                r'secret\s*[=:]\s*["\']([a-zA-Z0-9_-]{16,})["\']',
                r'client[_-]?secret\s*[=:]\s*["\']([a-zA-Z0-9_-]{16,})["\']'
            ],
            'private_key': [
                r'-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----',
                r'private[_-]?key\s*[=:]\s*["\']([a-zA-Z0-9+/=]{100,})["\']'
            ]
        }
        
        for line_num, line in enumerate(lines, 1):
            line_lower = line.lower()
            
            # Skip comments and obvious test/example values
            if (line.strip().startswith('#') or 
                line.strip().startswith('//') or
                'example' in line_lower or
                'test' in line_lower or
                'dummy' in line_lower or
                'placeholder' in line_lower):
                continue
            
            for secret_type, patterns in secret_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        secrets.append((secret_type, line_num, line.strip()))
                        break
        
        return secrets
    
    @staticmethod
    def find_sql_injection_risks(content: str, language: str) -> List[Tuple[int, str]]:
        """
        Find potential SQL injection vulnerabilities.
        
        Returns:
            List of tuples (line_number, context)
        """
        risks = []
        lines = content.splitlines()
        
        if language == 'python':
            # Python SQL injection patterns
            patterns = [
                r'execute\s*\(\s*["\'].*%.*["\']',  # String formatting in SQL
                r'execute\s*\(\s*.*\+.*\)',         # String concatenation
                r'cursor\.execute\s*\(\s*f["\']',   # f-string in execute
                r'query\s*=\s*["\'].*%.*["\']',     # Query with % formatting
                r'sql\s*=\s*.*\+.*'                 # SQL with concatenation
            ]
        else:
            # JavaScript SQL injection patterns
            patterns = [
                r'query\s*=\s*["`\'].*\$\{.*\}.*["`\']',  # Template literal injection
                r'execute\s*\(\s*["`\'].*\+.*["`\']',      # String concatenation
                r'sql\s*=\s*.*\+.*',                       # SQL concatenation
                r'query\(\s*["`\'].*\$\{.*\}.*["`\']'      # Query with template literal
            ]
        
        for line_num, line in enumerate(lines, 1):
            for pattern in patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    risks.append((line_num, line.strip()))
                    break
        
        return risks
    
    @staticmethod
    def calculate_function_complexity(func: Function, content: str) -> Dict[str, Any]:
        """Calculate detailed complexity metrics for a function."""
        if not func.line_start or not func.line_end:
            return {'cyclomatic_complexity': 1, 'cognitive_complexity': 1}
        
        # Extract function content
        lines = content.splitlines()
        func_lines = lines[func.line_start-1:func.line_end]
        func_content = '\n'.join(func_lines)
        
        # Calculate cyclomatic complexity (already available in func.complexity)
        cyclomatic = func.complexity
        
        # Calculate cognitive complexity (simplified)
        cognitive = AnalyzerUtils._calculate_cognitive_complexity(func_content)
        
        # Calculate nesting depth
        nesting_depth = AnalyzerUtils._calculate_nesting_depth(func_content)
        
        # Calculate lines of code
        loc = len([line for line in func_lines if line.strip() and not line.strip().startswith('#')])
        
        return {
            'cyclomatic_complexity': cyclomatic,
            'cognitive_complexity': cognitive,
            'nesting_depth': nesting_depth,
            'lines_of_code': loc,
            'parameters_count': len(func.parameters),
            'has_docstring': bool(func.docstring)
        }
    
    @staticmethod
    def _calculate_cognitive_complexity(content: str) -> int:
        """Calculate cognitive complexity (simplified version)."""
        complexity = 0
        nesting_level = 0
        
        # Keywords that increase cognitive complexity
        complexity_keywords = ['if', 'elif', 'else', 'while', 'for', 'try', 'except', 'finally']
        logical_operators = ['&&', '||', 'and', 'or']
        
        lines = content.splitlines()
        for line in lines:
            stripped = line.strip()
            
            # Count nesting level changes
            if any(keyword in stripped for keyword in ['if', 'while', 'for', 'try', 'def', 'class']):
                if stripped.endswith(':'):
                    nesting_level += 1
            
            # Count complexity-increasing constructs
            for keyword in complexity_keywords:
                if re.search(r'\b' + keyword + r'\b', stripped):
                    complexity += 1 + nesting_level  # Add nesting penalty
            
            # Count logical operators
            for operator in logical_operators:
                complexity += stripped.count(operator)
        
        return max(1, complexity)
    
    @staticmethod
    def _calculate_nesting_depth(content: str) -> int:
        """Calculate maximum nesting depth."""
        max_depth = 0
        current_depth = 0
        
        lines = content.splitlines()
        for line in lines:
            stripped = line.strip()
            
            # Increase depth for block-starting keywords
            if any(keyword in stripped for keyword in ['if', 'while', 'for', 'try', 'with', 'def', 'class']):
                if stripped.endswith(':'):
                    current_depth += 1
                    max_depth = max(max_depth, current_depth)
            
            # Decrease depth for dedenting (simplified)
            if stripped in ['pass', 'break', 'continue', 'return'] or stripped.startswith('except') or stripped.startswith('finally'):
                current_depth = max(0, current_depth - 1)
        
        return max_depth
    
    @staticmethod
    def find_code_smells(parsed_file: ParsedFile) -> List[Dict[str, Any]]:
        """Find common code smells in a parsed file."""
        smells = []
        
        # Long parameter lists
        for func in parsed_file.functions:
            if len(func.parameters) > 5:
                smells.append({
                    'type': 'long_parameter_list',
                    'function': func.name,
                    'line': func.line_start,
                    'parameter_count': len(func.parameters),
                    'severity': 'medium'
                })
        
        # Large classes
        for cls in parsed_file.classes:
            if len(cls.methods) > 20:
                smells.append({
                    'type': 'large_class',
                    'class': cls.name,
                    'line': cls.line_start,
                    'method_count': len(cls.methods),
                    'severity': 'high'
                })
        
        # God functions (very long functions)
        for func in parsed_file.functions:
            if func.line_end and func.line_start:
                func_length = func.line_end - func.line_start
                if func_length > 50:
                    smells.append({
                        'type': 'long_function',
                        'function': func.name,
                        'line': func.line_start,
                        'length': func_length,
                        'severity': 'high'
                    })
        
        return smells
    
    @staticmethod
    def extract_imports_and_dependencies(parsed_file: ParsedFile) -> Dict[str, List[str]]:
        """Extract and categorize imports and dependencies."""
        dependencies = {
            'standard_library': [],
            'third_party': [],
            'local': [],
            'relative': []
        }
        
        # Standard library modules (simplified list)
        stdlib_modules = {
            'os', 'sys', 'json', 'datetime', 'collections', 'itertools',
            'functools', 'pathlib', 're', 'math', 'random', 'urllib',
            'http', 'logging', 'unittest', 'typing', 'asyncio'
        }
        
        for import_stmt in parsed_file.imports:
            module = import_stmt.module
            
            if module.startswith('.'):
                dependencies['relative'].append(module)
            elif module.split('.')[0] in stdlib_modules:
                dependencies['standard_library'].append(module)
            elif '/' in module or module.startswith('./') or module.startswith('../'):
                dependencies['local'].append(module)
            else:
                dependencies['third_party'].append(module)
        
        return dependencies
    
    @staticmethod
    def find_unused_imports(parsed_file: ParsedFile) -> List[str]:
        """Find potentially unused imports (simplified heuristic)."""
        unused = []
        content = parsed_file.content.lower()
        
        for import_stmt in parsed_file.imports:
            if import_stmt.names:
                # Check named imports
                for name in import_stmt.names:
                    if name.lower() not in content:
                        unused.append(f"{import_stmt.module}.{name}")
            else:
                # Check module imports
                module_name = import_stmt.module.split('.')[-1]
                if module_name.lower() not in content:
                    unused.append(import_stmt.module)
        
        return unused
    
    @staticmethod
    def calculate_file_metrics(parsed_file: ParsedFile) -> Dict[str, Any]:
        """Calculate comprehensive metrics for a file."""
        metrics = {
            'total_lines': parsed_file.metadata.line_count if parsed_file.metadata else 0,
            'function_count': len(parsed_file.functions),
            'class_count': len(parsed_file.classes),
            'import_count': len(parsed_file.imports),
            'average_function_complexity': 0,
            'max_function_complexity': 0,
            'total_complexity': 0
        }
        
        if parsed_file.functions:
            complexities = [func.complexity for func in parsed_file.functions]
            metrics['average_function_complexity'] = sum(complexities) / len(complexities)
            metrics['max_function_complexity'] = max(complexities)
            metrics['total_complexity'] = sum(complexities)
        
        return metrics