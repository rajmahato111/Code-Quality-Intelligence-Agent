"""Complexity analyzer for detecting overly complex code structures."""

import re
import ast
import math
from typing import List, Dict, Any, Tuple, Optional
import logging

from .base import QualityAnalyzer, IssueCategory, Severity
from .issue_factory import IssueFactory
from .analyzer_utils import AnalyzerUtils
from ..core.models import ParsedFile, AnalysisContext, Issue, Function, Class

logger = logging.getLogger(__name__)


class ComplexityAnalyzer(QualityAnalyzer):
    """Analyzer for detecting overly complex code structures and maintainability issues."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the complexity analyzer."""
        super().__init__(config)
        self.supported_languages = ["python", "javascript", "typescript"]
        
        # Complexity thresholds (configurable)
        self.thresholds = {
            'cyclomatic_complexity': config.get('cyclomatic_threshold', 10) if config else 10,
            'cognitive_complexity': config.get('cognitive_threshold', 15) if config else 15,
            'nesting_depth': config.get('nesting_threshold', 4) if config else 4,
            'function_length': config.get('function_length_threshold', 50) if config else 50,
            'parameter_count': config.get('parameter_threshold', 5) if config else 5,
            'class_size': config.get('class_size_threshold', 20) if config else 20,
            'file_length': config.get('file_length_threshold', 500) if config else 500,
            'maintainability_index': config.get('maintainability_threshold', 20) if config else 20
        }
    
    def get_supported_languages(self) -> List[str]:
        """Return list of supported languages."""
        return self.supported_languages
    
    def get_category(self) -> IssueCategory:
        """Return the category of issues this analyzer detects."""
        return IssueCategory.COMPLEXITY
    
    def analyze(self, parsed_files: List[ParsedFile], context: AnalysisContext) -> List[Issue]:
        """
        Analyze parsed files for complexity issues.
        
        Args:
            parsed_files: List of parsed files to analyze
            context: Analysis context
            
        Returns:
            List of complexity issues found
        """
        issues = []
        
        for parsed_file in parsed_files:
            try:
                # Analyze function complexity
                issues.extend(self._analyze_function_complexity(parsed_file))
                
                # Analyze class complexity
                issues.extend(self._analyze_class_complexity(parsed_file))
                
                # Analyze file-level complexity
                issues.extend(self._analyze_file_complexity(parsed_file))
                
                # Analyze maintainability
                issues.extend(self._analyze_maintainability(parsed_file))
                
                # Analyze code structure issues
                issues.extend(self._analyze_structure_issues(parsed_file))
                
            except Exception as e:
                logger.error(f"Complexity analysis failed for {parsed_file.path}: {e}")
        
        return issues
    
    def _analyze_function_complexity(self, parsed_file: ParsedFile) -> List[Issue]:
        """Analyze complexity issues in functions."""
        issues = []
        
        for func in parsed_file.functions:
            # Get detailed complexity metrics
            metrics = AnalyzerUtils.calculate_function_complexity(func, parsed_file.content)
            
            # Check cyclomatic complexity
            if metrics['cyclomatic_complexity'] > self.thresholds['cyclomatic_complexity']:
                issues.append(IssueFactory.create_complexity_issue(
                    title=f"High Cyclomatic Complexity in '{func.name}'",
                    description=f"Function '{func.name}' has cyclomatic complexity of "
                              f"{metrics['cyclomatic_complexity']}, which exceeds the threshold of "
                              f"{self.thresholds['cyclomatic_complexity']}. High cyclomatic complexity "
                              f"makes code harder to understand, test, and maintain.",
                    file_path=parsed_file.path,
                    line_start=func.line_start,
                    line_end=func.line_end,
                    suggestion="Consider breaking this function into smaller, more focused functions. "
                             "Reduce the number of decision points (if/else, loops, try/catch).",
                    confidence=0.9,
                    complexity_metric="cyclomatic_complexity",
                    complexity_value=metrics['cyclomatic_complexity'],
                    threshold=self.thresholds['cyclomatic_complexity'],
                    severity=self._get_complexity_severity(
                        metrics['cyclomatic_complexity'], 
                        self.thresholds['cyclomatic_complexity']
                    ),
                    metadata={
                        'function_name': func.name,
                        'all_metrics': metrics
                    }
                ))
            
            # Check cognitive complexity
            if metrics['cognitive_complexity'] > self.thresholds['cognitive_complexity']:
                issues.append(IssueFactory.create_complexity_issue(
                    title=f"High Cognitive Complexity in '{func.name}'",
                    description=f"Function '{func.name}' has cognitive complexity of "
                              f"{metrics['cognitive_complexity']}, which exceeds the threshold of "
                              f"{self.thresholds['cognitive_complexity']}. High cognitive complexity "
                              f"makes code difficult to understand and reason about.",
                    file_path=parsed_file.path,
                    line_start=func.line_start,
                    line_end=func.line_end,
                    suggestion="Simplify the logic flow. Consider extracting nested conditions "
                             "into separate functions or using early returns to reduce nesting.",
                    confidence=0.85,
                    complexity_metric="cognitive_complexity",
                    complexity_value=metrics['cognitive_complexity'],
                    threshold=self.thresholds['cognitive_complexity'],
                    severity=self._get_complexity_severity(
                        metrics['cognitive_complexity'], 
                        self.thresholds['cognitive_complexity']
                    ),
                    metadata={
                        'function_name': func.name,
                        'all_metrics': metrics
                    }
                ))
            
            # Check nesting depth
            if metrics['nesting_depth'] > self.thresholds['nesting_depth']:
                issues.append(IssueFactory.create_complexity_issue(
                    title=f"Excessive Nesting Depth in '{func.name}'",
                    description=f"Function '{func.name}' has nesting depth of "
                              f"{metrics['nesting_depth']}, which exceeds the threshold of "
                              f"{self.thresholds['nesting_depth']}. Deep nesting makes code "
                              f"harder to read and understand.",
                    file_path=parsed_file.path,
                    line_start=func.line_start,
                    line_end=func.line_end,
                    suggestion="Reduce nesting by using early returns, guard clauses, or "
                             "extracting nested logic into separate functions.",
                    confidence=0.9,
                    complexity_metric="nesting_depth",
                    complexity_value=metrics['nesting_depth'],
                    threshold=self.thresholds['nesting_depth'],
                    severity=Severity.MEDIUM,
                    metadata={
                        'function_name': func.name,
                        'all_metrics': metrics
                    }
                ))
            
            # Check function length
            func_length = func.line_end - func.line_start if func.line_end else 0
            if func_length > self.thresholds['function_length']:
                issues.append(IssueFactory.create_complexity_issue(
                    title=f"Long Function '{func.name}'",
                    description=f"Function '{func.name}' is {func_length} lines long, "
                              f"which exceeds the threshold of {self.thresholds['function_length']} lines. "
                              f"Long functions are harder to understand, test, and maintain.",
                    file_path=parsed_file.path,
                    line_start=func.line_start,
                    line_end=func.line_end,
                    suggestion="Break this function into smaller, more focused functions. "
                             "Each function should have a single responsibility.",
                    confidence=0.8,
                    complexity_metric="function_length",
                    complexity_value=func_length,
                    threshold=self.thresholds['function_length'],
                    severity=Severity.MEDIUM,
                    metadata={
                        'function_name': func.name,
                        'all_metrics': metrics
                    }
                ))
            
            # Check parameter count
            if len(func.parameters) > self.thresholds['parameter_count']:
                issues.append(IssueFactory.create_complexity_issue(
                    title=f"Too Many Parameters in '{func.name}'",
                    description=f"Function '{func.name}' has {len(func.parameters)} parameters, "
                              f"which exceeds the threshold of {self.thresholds['parameter_count']}. "
                              f"Functions with many parameters are harder to use and understand.",
                    file_path=parsed_file.path,
                    line_start=func.line_start,
                    line_end=func.line_end,
                    suggestion="Consider grouping related parameters into objects/dictionaries, "
                             "or breaking the function into smaller functions with fewer parameters.",
                    confidence=0.85,
                    complexity_metric="parameter_count",
                    complexity_value=len(func.parameters),
                    threshold=self.thresholds['parameter_count'],
                    severity=Severity.LOW,
                    metadata={
                        'function_name': func.name,
                        'parameters': func.parameters,
                        'all_metrics': metrics
                    }
                ))
        
        return issues
    
    def _analyze_class_complexity(self, parsed_file: ParsedFile) -> List[Issue]:
        """Analyze complexity issues in classes."""
        issues = []
        
        for cls in parsed_file.classes:
            # Check class size (number of methods)
            method_count = len(cls.methods)
            if method_count > self.thresholds['class_size']:
                issues.append(IssueFactory.create_complexity_issue(
                    title=f"Large Class '{cls.name}'",
                    description=f"Class '{cls.name}' has {method_count} methods, "
                              f"which exceeds the threshold of {self.thresholds['class_size']}. "
                              f"Large classes violate the Single Responsibility Principle "
                              f"and are harder to maintain.",
                    file_path=parsed_file.path,
                    line_start=cls.line_start,
                    line_end=cls.line_end,
                    suggestion="Consider breaking this class into smaller, more focused classes. "
                             "Each class should have a single responsibility.",
                    confidence=0.8,
                    complexity_metric="class_size",
                    complexity_value=method_count,
                    threshold=self.thresholds['class_size'],
                    severity=Severity.MEDIUM,
                    metadata={
                        'class_name': cls.name,
                        'method_count': method_count,
                        'method_names': [m.name for m in cls.methods]
                    }
                ))
            
            # Analyze class cohesion
            cohesion_issues = self._analyze_class_cohesion(cls, parsed_file)
            issues.extend(cohesion_issues)
            
            # Check for god class pattern
            if method_count > 30:  # Very large class
                issues.append(IssueFactory.create_complexity_issue(
                    title=f"God Class Pattern in '{cls.name}'",
                    description=f"Class '{cls.name}' appears to be a 'God Class' with "
                              f"{method_count} methods. This anti-pattern indicates a class "
                              f"that knows too much or does too much.",
                    file_path=parsed_file.path,
                    line_start=cls.line_start,
                    line_end=cls.line_end,
                    suggestion="Refactor this class by extracting related functionality "
                             "into separate classes. Apply the Single Responsibility Principle.",
                    confidence=0.9,
                    complexity_metric="god_class",
                    complexity_value=method_count,
                    threshold=30,
                    severity=Severity.HIGH,
                    metadata={
                        'class_name': cls.name,
                        'method_count': method_count,
                        'anti_pattern': 'god_class'
                    }
                ))
        
        return issues
    
    def _analyze_file_complexity(self, parsed_file: ParsedFile) -> List[Issue]:
        """Analyze file-level complexity issues."""
        issues = []
        
        # Check file length
        line_count = parsed_file.metadata.line_count if parsed_file.metadata else 0
        if line_count > self.thresholds['file_length']:
            issues.append(IssueFactory.create_complexity_issue(
                title="Large File",
                description=f"File has {line_count} lines, which exceeds the threshold of "
                          f"{self.thresholds['file_length']} lines. Large files are harder "
                          f"to navigate and maintain.",
                file_path=parsed_file.path,
                line_start=1,
                line_end=line_count,
                suggestion="Consider splitting this file into smaller, more focused modules. "
                         "Group related functionality together.",
                confidence=0.7,
                complexity_metric="file_length",
                complexity_value=line_count,
                threshold=self.thresholds['file_length'],
                severity=Severity.LOW,
                metadata={
                    'total_functions': len(parsed_file.functions),
                    'total_classes': len(parsed_file.classes)
                }
            ))
        
        # Calculate overall file complexity
        total_complexity = sum(func.complexity for func in parsed_file.functions)
        if total_complexity > 50 and len(parsed_file.functions) > 0:
            avg_complexity = total_complexity / len(parsed_file.functions)
            if avg_complexity > 8:
                issues.append(IssueFactory.create_complexity_issue(
                    title="High Overall File Complexity",
                    description=f"File has high overall complexity with average function "
                              f"complexity of {avg_complexity:.1f}. This indicates the file "
                              f"may be doing too much.",
                    file_path=parsed_file.path,
                    line_start=1,
                    line_end=line_count,
                    suggestion="Consider refactoring complex functions and splitting "
                             "the file into smaller, more focused modules.",
                    confidence=0.75,
                    complexity_metric="average_complexity",
                    complexity_value=avg_complexity,
                    threshold=8,
                    severity=Severity.MEDIUM,
                    metadata={
                        'total_complexity': total_complexity,
                        'function_count': len(parsed_file.functions),
                        'average_complexity': avg_complexity
                    }
                ))
        
        return issues
    
    def _analyze_maintainability(self, parsed_file: ParsedFile) -> List[Issue]:
        """Analyze maintainability issues."""
        issues = []
        
        # Calculate maintainability index for the file
        maintainability_index = self._calculate_maintainability_index(parsed_file)
        
        if maintainability_index < self.thresholds['maintainability_index']:
            severity = Severity.HIGH if maintainability_index < 10 else Severity.MEDIUM
            
            issues.append(IssueFactory.create_complexity_issue(
                title="Low Maintainability Index",
                description=f"File has a maintainability index of {maintainability_index:.1f}, "
                          f"which is below the threshold of {self.thresholds['maintainability_index']}. "
                          f"Low maintainability indicates code that is difficult to maintain.",
                file_path=parsed_file.path,
                line_start=1,
                line_end=parsed_file.metadata.line_count if parsed_file.metadata else 100,
                suggestion="Improve maintainability by reducing complexity, adding documentation, "
                         "and improving code structure. Consider refactoring complex functions.",
                confidence=0.8,
                complexity_metric="maintainability_index",
                complexity_value=maintainability_index,
                threshold=self.thresholds['maintainability_index'],
                severity=severity,
                metadata={
                    'maintainability_grade': self._get_maintainability_grade(maintainability_index)
                }
            ))
        
        return issues
    
    def _analyze_structure_issues(self, parsed_file: ParsedFile) -> List[Issue]:
        """Analyze structural complexity issues."""
        issues = []
        
        # Check for deeply nested structures in the code
        issues.extend(self._check_deep_nesting(parsed_file))
        
        # Check for complex conditional expressions
        issues.extend(self._check_complex_conditions(parsed_file))
        
        # Check for long parameter lists in function calls
        issues.extend(self._check_long_parameter_lists(parsed_file))
        
        return issues
    
    def _analyze_class_cohesion(self, cls: Class, parsed_file: ParsedFile) -> List[Issue]:
        """Analyze class cohesion issues."""
        issues = []
        
        # Simple heuristic: if a class has many methods but few shared attributes,
        # it might have low cohesion
        if len(cls.methods) > 10:
            # This is a simplified cohesion check
            # In a full implementation, you'd analyze method interactions
            issues.append(IssueFactory.create_complexity_issue(
                title=f"Potential Low Cohesion in '{cls.name}'",
                description=f"Class '{cls.name}' has many methods ({len(cls.methods)}), "
                          f"which may indicate low cohesion. Methods in a class should "
                          f"work together toward a common purpose.",
                file_path=parsed_file.path,
                line_start=cls.line_start,
                line_end=cls.line_end,
                suggestion="Review the class design. Consider if all methods belong together "
                         "or if some should be moved to separate classes.",
                confidence=0.6,
                complexity_metric="class_cohesion",
                complexity_value=len(cls.methods),
                threshold=10,
                severity=Severity.LOW,
                metadata={
                    'class_name': cls.name,
                    'method_count': len(cls.methods)
                }
            ))
        
        return issues
    
    def _check_deep_nesting(self, parsed_file: ParsedFile) -> List[Issue]:
        """Check for deeply nested code structures."""
        issues = []
        lines = parsed_file.content.splitlines()
        
        for line_num, line in enumerate(lines, 1):
            # Count indentation level (simplified)
            indent_level = (len(line) - len(line.lstrip())) // 4  # Assuming 4-space indents
            
            if indent_level > 6:  # Very deep nesting
                issues.append(IssueFactory.create_complexity_issue(
                    title="Excessive Nesting Depth",
                    description=f"Code at line {line_num} has excessive nesting depth "
                              f"({indent_level} levels). Deep nesting makes code hard to read.",
                    file_path=parsed_file.path,
                    line_start=line_num,
                    line_end=line_num,
                    suggestion="Reduce nesting by using early returns, extracting methods, "
                             "or simplifying conditional logic.",
                    confidence=0.7,
                    complexity_metric="nesting_depth",
                    complexity_value=indent_level,
                    threshold=6,
                    severity=Severity.MEDIUM,
                    metadata={
                        'code_snippet': line.strip()
                    }
                ))
        
        return issues
    
    def _check_complex_conditions(self, parsed_file: ParsedFile) -> List[Issue]:
        """Check for overly complex conditional expressions."""
        issues = []
        lines = parsed_file.content.splitlines()
        
        for line_num, line in enumerate(lines, 1):
            # Count logical operators in conditions
            if 'if ' in line or 'elif ' in line or 'while ' in line:
                logical_ops = line.count(' and ') + line.count(' or ') + line.count('&&') + line.count('||')
                
                if logical_ops > 3:  # Complex condition
                    issues.append(IssueFactory.create_complexity_issue(
                        title="Complex Conditional Expression",
                        description=f"Conditional expression at line {line_num} has "
                                  f"{logical_ops} logical operators, making it complex "
                                  f"and hard to understand.",
                        file_path=parsed_file.path,
                        line_start=line_num,
                        line_end=line_num,
                        suggestion="Break complex conditions into smaller, named boolean "
                                 "variables or separate functions for better readability.",
                        confidence=0.8,
                        complexity_metric="conditional_complexity",
                        complexity_value=logical_ops,
                        threshold=3,
                        severity=Severity.LOW,
                        metadata={
                            'code_snippet': line.strip(),
                            'logical_operators': logical_ops
                        }
                    ))
        
        return issues
    
    def _check_long_parameter_lists(self, parsed_file: ParsedFile) -> List[Issue]:
        """Check for function calls with many parameters."""
        issues = []
        lines = parsed_file.content.splitlines()
        
        # This is a simplified check - in practice, you'd use AST parsing
        for line_num, line in enumerate(lines, 1):
            # Look for function calls with many commas (indicating many parameters)
            if '(' in line and ')' in line:
                # Count commas between parentheses
                paren_content = re.search(r'\(([^)]*)\)', line)
                if paren_content:
                    param_content = paren_content.group(1)
                    comma_count = param_content.count(',')
                    
                    if comma_count > 6:  # Many parameters
                        issues.append(IssueFactory.create_complexity_issue(
                            title="Function Call with Many Arguments",
                            description=f"Function call at line {line_num} has many arguments "
                                      f"({comma_count + 1}), which may indicate a design issue.",
                            file_path=parsed_file.path,
                            line_start=line_num,
                            line_end=line_num,
                            suggestion="Consider using parameter objects, named parameters, "
                                     "or builder patterns to reduce parameter count.",
                            confidence=0.6,
                            complexity_metric="parameter_count",
                            complexity_value=comma_count + 1,
                            threshold=6,
                            severity=Severity.LOW,
                            metadata={
                                'code_snippet': line.strip()
                            }
                        ))
        
        return issues
    
    def _calculate_maintainability_index(self, parsed_file: ParsedFile) -> float:
        """Calculate maintainability index for a file."""
        if not parsed_file.functions:
            return 100.0  # Empty file is perfectly maintainable
        
        # Simplified maintainability index calculation
        total_complexity = sum(func.complexity for func in parsed_file.functions)
        avg_complexity = total_complexity / len(parsed_file.functions)
        
        line_count = parsed_file.metadata.line_count if parsed_file.metadata else 100
        
        # Simplified formula (real MI is more complex)
        # MI = 171 - 5.2 * ln(Halstead Volume) - 0.23 * (Cyclomatic Complexity) - 16.2 * ln(Lines of Code)
        # Using simplified approximation
        
        if line_count <= 0:
            return 100.0
        
        mi = 171 - 0.23 * avg_complexity - 16.2 * math.log(line_count)
        
        # Normalize to 0-100 scale
        return max(0, min(100, mi))
    
    def _get_maintainability_grade(self, mi: float) -> str:
        """Get maintainability grade from index."""
        if mi >= 85:
            return "A"
        elif mi >= 70:
            return "B"
        elif mi >= 50:
            return "C"
        elif mi >= 25:
            return "D"
        else:
            return "F"
    
    def _get_complexity_severity(self, value: float, threshold: float) -> Severity:
        """Get severity based on how much the value exceeds the threshold."""
        ratio = value / threshold
        
        if ratio >= 2.0:
            return Severity.HIGH
        elif ratio >= 1.5:
            return Severity.MEDIUM
        else:
            return Severity.LOW