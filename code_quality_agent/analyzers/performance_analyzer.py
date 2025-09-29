"""Performance analyzer for detecting performance bottlenecks and inefficiencies."""

import re
import ast
from typing import List, Dict, Any, Set, Optional, Tuple
import logging

from .base import QualityAnalyzer, IssueCategory, Severity
from .issue_factory import IssueFactory
from .analyzer_utils import AnalyzerUtils
from ..core.models import ParsedFile, AnalysisContext, Issue, Function, Class

logger = logging.getLogger(__name__)


class PerformanceAnalyzer(QualityAnalyzer):
    """Analyzer for detecting performance bottlenecks and inefficiencies."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the performance analyzer."""
        super().__init__(config)
        self.supported_languages = ["python", "javascript", "typescript"]
        
        # Performance analysis thresholds (configurable)
        self.thresholds = {
            'max_nested_loops': config.get('max_nested_loops', 1) if config else 1,  # Detect O(n²) and above
            'max_loop_complexity': config.get('max_loop_complexity', 10) if config else 10,
            'max_string_concatenations': config.get('max_string_concatenations', 2) if config else 2,
            'max_database_calls_in_loop': config.get('max_database_calls_in_loop', 1) if config else 1
        }
        
        # Performance anti-patterns for different languages
        self._init_performance_patterns()
    
    def _init_performance_patterns(self):
        """Initialize performance anti-pattern detection patterns."""
        self.python_patterns = {
            'inefficient_loops': [
                r'for\s+\w+\s+in\s+range\s*\(\s*len\s*\(',  # for i in range(len(list))
                r'while\s+.*len\s*\(',  # while with len() check
            ],
            'string_concatenation': [
                r'\w+\s*\+=\s*["\']',  # string += "text"
                r'\w+\s*=\s*\w+\s*\+\s*["\']',  # string = string + "text"
            ],
            'inefficient_data_structures': [
                r'\.append\s*\(\s*.*\s*\)\s*.*for\s+.*in',  # list.append in loop
                r'list\s*\(\s*.*\s*for\s+.*in.*\)',  # list comprehension to list()
            ],
            'database_in_loop': [
                r'for\s+.*:\s*.*\.(query|execute|find|get)\s*\(',
                r'while\s+.*:\s*.*\.(query|execute|find|get)\s*\(',
            ],
            'inefficient_imports': [
                r'from\s+\*\s+import',  # from * import
                r'import\s+.*,.*,.*,',  # multiple imports in one line
            ]
        }
        
        self.javascript_patterns = {
            'inefficient_loops': [
                r'for\s*\(\s*var\s+\w+\s*=\s*0\s*;\s*\w+\s*<\s*\w+\.length',  # for(var i=0; i<arr.length; i++)
                r'for\s*\(\s*let\s+\w+\s*=\s*0\s*;\s*\w+\s*<\s*\w+\.length',  # for(let i=0; i<arr.length; i++)
            ],
            'string_concatenation': [
                r'\w+\s*\+=\s*["\']',  # string += "text"
                r'\w+\s*=\s*\w+\s*\+\s*["\']',  # string = string + "text"
            ],
            'dom_manipulation': [
                r'document\.getElementById.*for\s*\(',  # DOM queries in loops
                r'document\.querySelector.*for\s*\(',
                r'\.innerHTML\s*\+=',  # innerHTML concatenation
            ],
            'inefficient_array_methods': [
                r'\.push\s*\(.*\)\s*.*for\s*\(',  # array.push in loop
                r'\.concat\s*\(.*\)\s*.*for\s*\(',  # array.concat in loop
            ]
        }
    
    def get_supported_languages(self) -> List[str]:
        """Return list of supported languages."""
        return self.supported_languages
    
    def get_category(self) -> IssueCategory:
        """Return the category of issues this analyzer detects."""
        return IssueCategory.PERFORMANCE 
   
    def analyze(self, parsed_files: List[ParsedFile], context: AnalysisContext) -> List[Issue]:
        """
        Analyze parsed files for performance issues.
        
        Args:
            parsed_files: List of parsed files to analyze
            context: Analysis context
            
        Returns:
            List of performance issues found
        """
        issues = []
        
        try:
            for parsed_file in parsed_files:
                # Analyze loop performance
                issues.extend(self._analyze_loop_performance(parsed_file))
                
                # Analyze string operations
                issues.extend(self._analyze_string_operations(parsed_file))
                
                # Analyze data structure usage
                issues.extend(self._analyze_data_structure_usage(parsed_file))
                
                # Analyze algorithm complexity
                issues.extend(self._analyze_algorithm_complexity(parsed_file))
                
                # Analyze I/O operations
                issues.extend(self._analyze_io_operations(parsed_file))
                
                # Analyze memory usage patterns
                issues.extend(self._analyze_memory_patterns(parsed_file))
                
                # Language-specific performance issues
                if parsed_file.language == "python":
                    issues.extend(self._analyze_python_performance(parsed_file))
                elif parsed_file.language in ["javascript", "typescript"]:
                    issues.extend(self._analyze_javascript_performance(parsed_file))
                
        except Exception as e:
            logger.error(f"Performance analysis failed: {e}")
        
        return issues
    
    def _analyze_loop_performance(self, parsed_file: ParsedFile) -> List[Issue]:
        """Analyze loop performance issues."""
        issues = []
        lines = parsed_file.content.splitlines()
        
        # Detect nested loops
        issues.extend(self._detect_nested_loops(parsed_file, lines))
        
        # Detect inefficient loop patterns
        issues.extend(self._detect_inefficient_loops(parsed_file, lines))
        
        # Detect database calls in loops
        issues.extend(self._detect_database_calls_in_loops(parsed_file, lines))
        
        return issues
    
    def _detect_nested_loops(self, parsed_file: ParsedFile, lines: List[str]) -> List[Issue]:
        """Detect deeply nested loops."""
        issues = []
        loop_depth = 0
        loop_stack = []
        
        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Detect loop start
            if (re.search(r'\b(for|while)\b', stripped) and 
                ':' in stripped and not stripped.startswith('#')):
                loop_depth += 1
                loop_stack.append(line_num)
                
                if loop_depth > self.thresholds['max_nested_loops']:
                    # Determine severity based on nesting depth
                    if loop_depth == 2:
                        severity = Severity.MEDIUM
                        title = "O(n²) Nested Loops Detected"
                        description = f"O(n²) nested loops detected at line {line_num}. " \
                                    f"This quadratic complexity can cause significant performance " \
                                    f"issues with large datasets."
                    elif loop_depth == 3:
                        severity = Severity.HIGH
                        title = "O(n³) Triple Nested Loops Detected"
                        description = f"O(n³) triple nested loops detected at line {line_num}. " \
                                    f"This cubic complexity can cause severe performance " \
                                    f"degradation with moderate datasets."
                    else:
                        severity = Severity.HIGH
                        title = "Deeply Nested Loops"
                        description = f"Deeply nested loops detected at line {line_num} " \
                                    f"(depth: {loop_depth}). This can lead to poor performance " \
                                    f"with O(n^{loop_depth}) complexity."
                    
                    issues.append(IssueFactory.create_performance_issue(
                        title=title,
                        description=description,
                        file_path=parsed_file.path,
                        line_start=line_num,
                        line_end=line_num,
                        suggestion="Consider refactoring nested loops by extracting inner logic "
                                 "into separate functions, using more efficient algorithms, "
                                 "or combining operations where possible.",
                        confidence=0.9,
                        performance_impact="cpu",
                        severity=severity,
                        metadata={
                            'nesting_depth': loop_depth,
                            'loop_stack': loop_stack.copy(),
                            'complexity_class': f"O(n^{loop_depth})"
                        }
                    ))
            
            # Detect loop end (improved - based on indentation)
            elif loop_depth > 0 and stripped and not stripped.startswith('#'):
                current_indent = len(line) - len(line.lstrip())
                
                # Check if we've exited any loops based on indentation
                while loop_stack and loop_depth > 0:
                    loop_line = lines[loop_stack[-1] - 1]
                    loop_indent = len(loop_line) - len(loop_line.lstrip())
                    
                    if current_indent <= loop_indent:
                        loop_depth = max(0, loop_depth - 1)
                        loop_stack.pop()
                    else:
                        break
        
        return issues    

    def _detect_inefficient_loops(self, parsed_file: ParsedFile, lines: List[str]) -> List[Issue]:
        """Detect inefficient loop patterns."""
        issues = []
        language = parsed_file.language
        
        if language == "python":
            patterns = self.python_patterns['inefficient_loops']
        elif language in ['javascript', 'typescript']:
            patterns = self.javascript_patterns['inefficient_loops']
        else:
            return issues
        
        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue
                
            for pattern in patterns:
                if re.search(pattern, line):
                    issues.append(IssueFactory.create_performance_issue(
                        title="Inefficient Loop Pattern",
                        description=f"Inefficient loop pattern detected at line {line_num}. "
                                  f"This pattern can be optimized for better performance.",
                        file_path=parsed_file.path,
                        line_start=line_num,
                        line_end=line_num,
                        suggestion="Consider using more efficient loop patterns, caching "
                                 "length calculations, or using built-in optimized methods.",
                        confidence=0.7,
                        performance_impact="cpu",
                        severity=Severity.MEDIUM,
                        metadata={
                            'pattern_matched': pattern,
                            'code_snippet': line.strip()
                        }
                    ))
                    break
        
        return issues
    
    def _detect_database_calls_in_loops(self, parsed_file: ParsedFile, lines: List[str]) -> List[Issue]:
        """Detect database calls inside loops (N+1 problem)."""
        issues = []
        
        # Track loop context using indentation
        loop_stack = []  # Stack of (line_num, indent_level)
        
        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue
                
            current_indent = len(line) - len(line.lstrip())
            
            # Remove loops from stack if we've exited them (based on indentation)
            while loop_stack and current_indent <= loop_stack[-1][1]:
                loop_stack.pop()
            
            # Detect loop start
            if re.search(r'\b(for|while)\b', stripped) and ':' in stripped:
                loop_stack.append((line_num, current_indent))
            
            # Look for database operations in loop
            elif loop_stack:  # We're inside a loop
                db_patterns = [
                    r'\.(query|execute|find|save|update|delete)\s*\(',  # Removed 'get' to avoid dict.get() false positives
                    r'SELECT\s+.*FROM',
                    r'INSERT\s+INTO',
                    r'UPDATE\s+.*SET',
                    r'DELETE\s+FROM',
                    r'\.(objects|filter|all|first|last)\s*\(',  # Django ORM patterns
                    r'cursor\.(execute|fetchone|fetchall)',  # Direct database cursor operations
                    r'session\.(query|add|commit|rollback)',  # SQLAlchemy patterns
                ]
                
                for pattern in db_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        issues.append(IssueFactory.create_performance_issue(
                            title="Database Call in Loop (N+1 Problem)",
                            description=f"Database operation detected inside loop at line {line_num}. "
                                      f"This creates an N+1 query problem that can severely impact performance.",
                            file_path=parsed_file.path,
                            line_start=line_num,
                            line_end=line_num,
                            suggestion="Move database operations outside the loop, use batch operations, "
                                     "or implement eager loading to reduce database round trips.",
                            confidence=0.9,
                            performance_impact="io",
                            severity=Severity.HIGH,
                            metadata={
                                'loop_start_line': loop_stack[-1][0],
                                'db_operation': pattern,
                                'code_snippet': line.strip()
                            }
                        ))
                        break
        
        return issues   
 
    def _analyze_string_operations(self, parsed_file: ParsedFile) -> List[Issue]:
        """Analyze string operation performance."""
        issues = []
        lines = parsed_file.content.splitlines()
        
        # Track loop context using indentation
        loop_stack = []  # Stack of (line_num, indent_level, concat_count)
        
        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue
                
            current_indent = len(line) - len(line.lstrip())
            
            # Remove loops from stack if we've exited them (based on indentation)
            while loop_stack and current_indent <= loop_stack[-1][1]:
                loop_stack.pop()
            
            # Detect loop start
            if re.search(r'\b(for|while)\b', stripped) and ':' in stripped:
                loop_stack.append((line_num, current_indent, 0))  # line_num, indent, concat_count
            
            # Detect string concatenation
            elif loop_stack:  # We're inside a loop
                concat_patterns = [
                    r'\w+\s*\+=\s*["\']',  # string += "text"
                    r'\w+\s*=\s*\w+\s*\+\s*["\']',  # string = string + "text"
                    r'\.join\s*\(\s*\[.*\+.*\]',  # inefficient join usage
                ]
                
                for pattern in concat_patterns:
                    if re.search(pattern, line):
                        # Update concatenation count for current loop
                        loop_start, loop_indent, concat_count = loop_stack[-1]
                        concat_count += 1
                        loop_stack[-1] = (loop_start, loop_indent, concat_count)
                        
                        # Report issue if threshold reached
                        if concat_count > self.thresholds['max_string_concatenations']:
                            issues.append(IssueFactory.create_performance_issue(
                                title="Inefficient String Concatenation in Loop",
                                description=f"String concatenation detected in loop at line {line_num}. "
                                          f"This creates temporary string objects and can be slow for large datasets.",
                                file_path=parsed_file.path,
                                line_start=line_num,
                                line_end=line_num,
                                suggestion="Use string builders, list.join(), or template strings "
                                         "for efficient string concatenation in loops.",
                                confidence=0.8,
                                performance_impact="memory",
                                severity=Severity.MEDIUM,
                                metadata={
                                    'concatenation_count': concat_count,
                                    'pattern_matched': pattern,
                                    'loop_start_line': loop_start
                                }
                            ))
                        break
        
        return issues
    
    def _analyze_data_structure_usage(self, parsed_file: ParsedFile) -> List[Issue]:
        """Analyze data structure usage for performance issues."""
        issues = []
        lines = parsed_file.content.splitlines()
        
        for line_num, line in enumerate(lines, 1):
            # Detect inefficient list operations
            if parsed_file.language == "python":
                # list.append() in loop when list comprehension could be used
                if re.search(r'\.append\s*\(.*\).*for\s+.*in', line):
                    issues.append(IssueFactory.create_performance_issue(
                        title="Inefficient List Building",
                        description=f"List.append() in loop detected at line {line_num}. "
                                  f"List comprehensions are typically faster and more readable.",
                        file_path=parsed_file.path,
                        line_start=line_num,
                        line_end=line_num,
                        suggestion="Consider using list comprehension instead of append() in loop "
                                 "for better performance and readability.",
                        confidence=0.7,
                        performance_impact="cpu",
                        severity=Severity.LOW,
                        metadata={
                            'code_snippet': line.strip()
                        }
                    ))
                
                # Using list() on generator when not needed
                if re.search(r'list\s*\(\s*.*\s*for\s+.*in.*\)', line):
                    issues.append(IssueFactory.create_performance_issue(
                        title="Unnecessary List Conversion",
                        description=f"Unnecessary list() conversion of generator at line {line_num}. "
                                  f"Consider using the generator directly if possible.",
                        file_path=parsed_file.path,
                        line_start=line_num,
                        line_end=line_num,
                        suggestion="Use generators directly when possible to save memory "
                                 "and improve performance.",
                        confidence=0.6,
                        performance_impact="memory",
                        severity=Severity.LOW,
                        metadata={
                            'code_snippet': line.strip()
                        }
                    ))
        
        return issues
    
    def _analyze_algorithm_complexity(self, parsed_file: ParsedFile) -> List[Issue]:
        """Analyze algorithmic complexity issues."""
        issues = []
        
        for func in parsed_file.functions:
            if func.complexity > self.thresholds['max_loop_complexity']:
                # High complexity often indicates nested loops or inefficient algorithms
                issues.append(IssueFactory.create_performance_issue(
                    title=f"High Algorithmic Complexity in '{func.name}'",
                    description=f"Function '{func.name}' has high cyclomatic complexity "
                              f"({func.complexity}), which may indicate nested loops or "
                              f"inefficient algorithms that could impact performance.",
                    file_path=parsed_file.path,
                    line_start=func.line_start,
                    line_end=func.line_end,
                    suggestion="Review the algorithm for optimization opportunities. "
                             "Consider reducing nested loops, using more efficient data structures, "
                             "or breaking the function into smaller, more efficient parts.",
                    confidence=0.6,
                    performance_impact="cpu",
                    severity=Severity.MEDIUM,
                    metadata={
                        'function_name': func.name,
                        'complexity': func.complexity,
                        'parameter_count': len(func.parameters)
                    }
                ))
        
        return issues
    
    def _analyze_io_operations(self, parsed_file: ParsedFile) -> List[Issue]:
        """Analyze I/O operation performance."""
        issues = []
        lines = parsed_file.content.splitlines()
        
        # Track loop context using indentation
        loop_stack = []  # Stack of (line_num, indent_level)
        
        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue
                
            current_indent = len(line) - len(line.lstrip())
            
            # Remove loops from stack if we've exited them (based on indentation)
            while loop_stack and current_indent <= loop_stack[-1][1]:
                loop_stack.pop()
            
            # Detect loop start
            if re.search(r'\b(for|while)\b', stripped) and ':' in stripped:
                loop_stack.append((line_num, current_indent))
            
            # Detect I/O operations
            elif loop_stack:  # We're inside a loop
                io_patterns = [
                    r'open\s*\(',
                    r'\.read\s*\(',
                    r'\.write\s*\(',
                    r'\.close\s*\(',
                    r'requests\.(get|post|put|delete)',
                    r'fetch\s*\(',
                    r'axios\.(get|post|put|delete)'
                ]
                
                for pattern in io_patterns:
                    if re.search(pattern, line):
                        issues.append(IssueFactory.create_performance_issue(
                            title="I/O Operation in Loop",
                            description=f"I/O operation detected in loop at line {line_num}. "
                                      f"Repeated I/O operations can significantly impact performance.",
                            file_path=parsed_file.path,
                            line_start=line_num,
                            line_end=line_num,
                            suggestion="Move I/O operations outside loops when possible, "
                                     "use batch operations, or implement connection pooling.",
                            confidence=0.8,
                            performance_impact="io",
                            severity=Severity.HIGH,
                            metadata={
                                'loop_start_line': loop_stack[-1][0],
                                'io_operation': pattern,
                                'code_snippet': line.strip()
                            }
                        ))
                        break
        
        return issues
    
    def _analyze_memory_patterns(self, parsed_file: ParsedFile) -> List[Issue]:
        """Analyze memory usage patterns."""
        issues = []
        lines = parsed_file.content.splitlines()
        
        for line_num, line in enumerate(lines, 1):
            # Detect potential memory leaks or inefficient memory usage
            memory_patterns = [
                (r'global\s+\w+.*=.*\[\]', "Global list that may grow indefinitely"),
                (r'global\s+\w+.*=.*\{\}', "Global dictionary that may grow indefinitely"),
                (r'\.append\s*\(.*\).*while\s+True', "Infinite loop with list growth"),
                (r'.*=.*\*.*\d{4,}', "Large memory allocation"),
            ]
            
            for pattern, description in memory_patterns:
                if re.search(pattern, line):
                    issues.append(IssueFactory.create_performance_issue(
                        title="Potential Memory Issue",
                        description=f"{description} detected at line {line_num}. "
                                  f"This could lead to excessive memory usage.",
                        file_path=parsed_file.path,
                        line_start=line_num,
                        line_end=line_num,
                        suggestion="Review memory usage patterns and implement proper "
                                 "cleanup, size limits, or more efficient data structures.",
                        confidence=0.5,
                        performance_impact="memory",
                        severity=Severity.MEDIUM,
                        metadata={
                            'pattern_matched': pattern,
                            'code_snippet': line.strip()
                        }
                    ))
                    break
        
        return issues 
   
    def _analyze_python_performance(self, parsed_file: ParsedFile) -> List[Issue]:
        """Analyze Python-specific performance issues."""
        issues = []
        lines = parsed_file.content.splitlines()
        
        for line_num, line in enumerate(lines, 1):
            # Detect inefficient Python patterns
            python_issues = [
                (r'for\s+\w+\s+in\s+range\s*\(\s*len\s*\(', 
                 "Use enumerate() instead of range(len()) for better performance and readability"),
                (r'in\s+\w+\.keys\s*\(\s*\)', 
                 "Checking 'key in dict' is more efficient than 'key in dict.keys()'"),
                (r'list\s*\(\s*\w+\.keys\s*\(\s*\)\s*\)', 
                 "dict.keys() already returns a view, list() conversion may be unnecessary"),
                (r'\.has_key\s*\(', 
                 "dict.has_key() is deprecated, use 'key in dict' instead"),
                (r'except\s*:\s*$', 
                 "Bare except clauses can hide performance issues and errors"),
            ]
            
            for pattern, suggestion in python_issues:
                if re.search(pattern, line):
                    issues.append(IssueFactory.create_performance_issue(
                        title="Python Performance Anti-Pattern",
                        description=f"Python performance anti-pattern detected at line {line_num}.",
                        file_path=parsed_file.path,
                        line_start=line_num,
                        line_end=line_num,
                        suggestion=suggestion,
                        confidence=0.7,
                        performance_impact="cpu",
                        severity=Severity.LOW,
                        metadata={
                            'pattern_matched': pattern,
                            'code_snippet': line.strip()
                        }
                    ))
                    break
        
        return issues
    
    def _analyze_javascript_performance(self, parsed_file: ParsedFile) -> List[Issue]:
        """Analyze JavaScript/TypeScript-specific performance issues."""
        issues = []
        lines = parsed_file.content.splitlines()
        
        for line_num, line in enumerate(lines, 1):
            # Detect inefficient JavaScript patterns
            js_issues = [
                (r'document\.getElementById.*for\s*\(', 
                 "Cache DOM queries outside loops to avoid repeated DOM traversal"),
                (r'document\.querySelector.*for\s*\(', 
                 "Cache DOM queries outside loops to avoid repeated DOM traversal"),
                (r'\.innerHTML\s*\+=', 
                 "Use DocumentFragment or textContent for better performance than innerHTML concatenation"),
                (r'for\s*\(\s*var\s+\w+\s*=\s*0\s*;\s*\w+\s*<\s*\w+\.length', 
                 "Cache array length in variable to avoid repeated property access"),
                (r'new\s+RegExp\s*\(.*\).*for\s*\(', 
                 "Compile regular expressions outside loops for better performance"),
                (r'JSON\.parse\s*\(.*JSON\.stringify', 
                 "Deep cloning with JSON is inefficient, consider using structured cloning or libraries"),
            ]
            
            for pattern, suggestion in js_issues:
                if re.search(pattern, line):
                    issues.append(IssueFactory.create_performance_issue(
                        title="JavaScript Performance Anti-Pattern",
                        description=f"JavaScript performance anti-pattern detected at line {line_num}.",
                        file_path=parsed_file.path,
                        line_start=line_num,
                        line_end=line_num,
                        suggestion=suggestion,
                        confidence=0.7,
                        performance_impact="cpu",
                        severity=Severity.MEDIUM,
                        metadata={
                            'pattern_matched': pattern,
                            'code_snippet': line.strip()
                        }
                    ))
                    break
        
        return issues