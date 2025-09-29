"""Documentation analyzer for detecting documentation gaps and quality issues."""

import re
import ast
from typing import List, Dict, Any, Set, Optional, Tuple
from datetime import datetime
import logging

from .base import QualityAnalyzer, IssueCategory, Severity
from .issue_factory import IssueFactory
from .analyzer_utils import AnalyzerUtils
from ..core.models import ParsedFile, AnalysisContext, Issue, Function, Class

logger = logging.getLogger(__name__)


class DocumentationAnalyzer(QualityAnalyzer):
    """Analyzer for detecting documentation gaps and quality issues."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the documentation analyzer."""
        super().__init__(config)
        self.supported_languages = ["python", "javascript", "typescript"]
        
        # Documentation analysis thresholds (configurable)
        self.thresholds = {
            'min_public_function_doc_coverage': config.get('min_public_function_doc_coverage', 0.8) if config else 0.8,
            'min_class_doc_coverage': config.get('min_class_doc_coverage', 0.9) if config else 0.9,
            'min_docstring_length': config.get('min_docstring_length', 10) if config else 10,
            'max_function_params_without_doc': config.get('max_function_params_without_doc', 3) if config else 3,
            'complex_function_doc_threshold': config.get('complex_function_doc_threshold', 5) if config else 5
        }
        
        # Documentation patterns for different languages
        self.doc_patterns = {
            'python': {
                'docstring': r'"""([^"]*)"""',
                'single_docstring': r"'''([^']*)'''",
                'inline_comment': r'#\s*(.+)',
                'todo': r'#\s*TODO:?\s*(.+)',
                'fixme': r'#\s*FIXME:?\s*(.+)',
                'param_doc': r':param\s+(\w+):\s*(.+)',
                'return_doc': r':return[s]?:\s*(.+)',
                'type_hint': r':\s*([^=]+)\s*='
            },
            'javascript': {
                'jsdoc': r'/\*\*([^*]|\*(?!/))*\*/',
                'inline_comment': r'//\s*(.+)',
                'block_comment': r'/\*([^*]|\*(?!/))*\*/',
                'todo': r'//\s*TODO:?\s*(.+)',
                'fixme': r'//\s*FIXME:?\s*(.+)',
                'param_doc': r'@param\s+\{([^}]+)\}\s+(\w+)\s*-?\s*(.+)',
                'return_doc': r'@returns?\s+\{([^}]+)\}\s*(.+)',
                'type_annotation': r':\s*([^=\s]+)'
            },
            'typescript': {
                'jsdoc': r'/\*\*([^*]|\*(?!/))*\*/',
                'inline_comment': r'//\s*(.+)',
                'block_comment': r'/\*([^*]|\*(?!/))*\*/',
                'todo': r'//\s*TODO:?\s*(.+)',
                'fixme': r'//\s*FIXME:?\s*(.+)',
                'param_doc': r'@param\s+(\w+)\s*-?\s*(.+)',
                'return_doc': r'@returns?\s+(.+)',
                'type_annotation': r':\s*([^=\s]+)'
            }
        }
    
    def get_supported_languages(self) -> List[str]:
        """Return list of supported languages."""
        return self.supported_languages
    
    def get_category(self) -> IssueCategory:
        """Return the category of issues this analyzer detects."""
        return IssueCategory.DOCUMENTATION
    
    def analyze(self, parsed_files: List[ParsedFile], context: AnalysisContext) -> List[Issue]:
        """
        Analyze parsed files for documentation issues.
        
        Args:
            parsed_files: List of parsed files to analyze
            context: Analysis context
            
        Returns:
            List of documentation issues found
        """
        issues = []
        
        try:
            for parsed_file in parsed_files:
                # Analyze function documentation
                issues.extend(self._analyze_function_documentation(parsed_file))
                
                # Analyze class documentation
                issues.extend(self._analyze_class_documentation(parsed_file))
                
                # Analyze module documentation
                issues.extend(self._analyze_module_documentation(parsed_file))
                
                # Analyze comment quality
                issues.extend(self._analyze_comment_quality(parsed_file))
                
                # Analyze API documentation
                issues.extend(self._analyze_api_documentation(parsed_file))
                
                # Analyze documentation consistency
                issues.extend(self._analyze_documentation_consistency(parsed_file))
                
        except Exception as e:
            logger.error(f"Documentation analysis failed: {e}")
        
        return issues
    
    def _analyze_function_documentation(self, parsed_file: ParsedFile) -> List[Issue]:
        """Analyze function documentation quality and coverage."""
        issues = []
        
        for func in parsed_file.functions:
            # Skip private functions for some checks
            is_public = not func.name.startswith('_')
            is_complex = func.complexity > self.thresholds['complex_function_doc_threshold']
            has_many_params = len(func.parameters) > self.thresholds['max_function_params_without_doc']
            
            # Check for missing docstring
            if not func.docstring:
                if is_public or is_complex or has_many_params:
                    severity = Severity.HIGH if is_public else Severity.MEDIUM
                    issues.append(IssueFactory.create_documentation_issue(
                        title=f"Missing Docstring for Function '{func.name}'",
                        description=f"Function '{func.name}' lacks documentation. "
                                  f"{'Public functions' if is_public else 'Complex functions'} "
                                  f"should have clear documentation explaining their purpose.",
                        file_path=parsed_file.path,
                        line_start=func.line_start,
                        line_end=func.line_start,
                        suggestion="Add a docstring explaining what this function does, "
                                 "its parameters, return value, and any side effects.",
                        confidence=0.9,
                        documentation_type="missing_function_docstring",
                        severity=severity,
                        metadata={
                            'function_name': func.name,
                            'is_public': is_public,
                            'complexity': func.complexity,
                            'parameter_count': len(func.parameters)
                        }
                    ))
            else:
                # Check docstring quality
                docstring_issues = self._analyze_docstring_quality(
                    func.docstring, func, parsed_file, "function"
                )
                issues.extend(docstring_issues)
            
            # Check parameter documentation for functions with many parameters
            if has_many_params and func.docstring:
                param_doc_issues = self._check_parameter_documentation(
                    func, parsed_file
                )
                issues.extend(param_doc_issues)
        
        return issues
    
    def _analyze_class_documentation(self, parsed_file: ParsedFile) -> List[Issue]:
        """Analyze class documentation quality and coverage."""
        issues = []
        
        for cls in parsed_file.classes:
            # Check for missing class docstring
            if not cls.docstring:
                issues.append(IssueFactory.create_documentation_issue(
                    title=f"Missing Docstring for Class '{cls.name}'",
                    description=f"Class '{cls.name}' lacks documentation. "
                              f"Classes should have clear documentation explaining their purpose "
                              f"and usage.",
                    file_path=parsed_file.path,
                    line_start=cls.line_start,
                    line_end=cls.line_start,
                    suggestion="Add a class docstring explaining what this class represents, "
                             "its main responsibilities, and how to use it.",
                    confidence=0.9,
                    documentation_type="missing_class_docstring",
                    severity=Severity.HIGH,
                    metadata={
                        'class_name': cls.name,
                        'method_count': len(cls.methods),
                        'has_inheritance': bool(cls.base_classes)
                    }
                ))
            else:
                # Check class docstring quality
                docstring_issues = self._analyze_docstring_quality(
                    cls.docstring, cls, parsed_file, "class"
                )
                issues.extend(docstring_issues)
            
            # Check method documentation coverage
            public_methods = [m for m in cls.methods if not m.name.startswith('_')]
            undocumented_methods = [m for m in public_methods if not m.docstring]
            
            if len(undocumented_methods) > 0:
                coverage = 1 - (len(undocumented_methods) / len(public_methods))
                if coverage < self.thresholds['min_class_doc_coverage']:
                    issues.append(IssueFactory.create_documentation_issue(
                        title=f"Low Method Documentation Coverage in '{cls.name}'",
                        description=f"Class '{cls.name}' has low method documentation coverage "
                                  f"({coverage:.1%}). {len(undocumented_methods)} out of "
                                  f"{len(public_methods)} public methods lack documentation.",
                        file_path=parsed_file.path,
                        line_start=cls.line_start,
                        line_end=cls.line_end,
                        suggestion="Add docstrings to public methods explaining their purpose, "
                                 "parameters, and return values.",
                        confidence=0.8,
                        documentation_type="low_method_coverage",
                        severity=Severity.MEDIUM,
                        metadata={
                            'class_name': cls.name,
                            'coverage': coverage,
                            'undocumented_methods': [m.name for m in undocumented_methods]
                        }
                    ))
        
        return issues
    
    def _analyze_module_documentation(self, parsed_file: ParsedFile) -> List[Issue]:
        """Analyze module-level documentation."""
        issues = []
        
        # Check for module docstring
        has_module_docstring = self._has_module_docstring(parsed_file)
        
        if not has_module_docstring:
            # Only require module docstring for non-trivial modules
            if (len(parsed_file.functions) > 3 or 
                len(parsed_file.classes) > 1 or 
                len(parsed_file.imports) > 5):
                
                issues.append(IssueFactory.create_documentation_issue(
                    title="Missing Module Documentation",
                    description=f"Module {parsed_file.path} lacks module-level documentation. "
                              f"Modules should have a docstring explaining their purpose and contents.",
                    file_path=parsed_file.path,
                    line_start=1,
                    line_end=3,
                    suggestion="Add a module docstring at the top of the file explaining "
                             "what this module does and its main components.",
                    confidence=0.7,
                    documentation_type="missing_module_docstring",
                    severity=Severity.LOW,
                    metadata={
                        'function_count': len(parsed_file.functions),
                        'class_count': len(parsed_file.classes),
                        'import_count': len(parsed_file.imports)
                    }
                ))
        
        return issues
    
    def _analyze_comment_quality(self, parsed_file: ParsedFile) -> List[Issue]:
        """Analyze the quality of comments in the code."""
        issues = []
        lines = parsed_file.content.splitlines()
        
        # Find TODO and FIXME comments
        todo_fixme_issues = self._find_todo_fixme_comments(parsed_file, lines)
        issues.extend(todo_fixme_issues)
        
        # Find outdated comments
        outdated_comment_issues = self._find_outdated_comments(parsed_file, lines)
        issues.extend(outdated_comment_issues)
        
        # Find commented-out code
        commented_code_issues = self._find_commented_out_code(parsed_file, lines)
        issues.extend(commented_code_issues)
        
        return issues
    
    def _analyze_api_documentation(self, parsed_file: ParsedFile) -> List[Issue]:
        """Analyze API documentation for public interfaces."""
        issues = []
        
        # Find public API functions and classes
        public_functions = [f for f in parsed_file.functions if not f.name.startswith('_')]
        public_classes = [c for c in parsed_file.classes if not c.name.startswith('_')]
        
        # Check if this appears to be an API module
        is_api_module = (
            'api' in parsed_file.path.lower() or
            'interface' in parsed_file.path.lower() or
            len(public_functions) > 5 or
            len(public_classes) > 2
        )
        
        if is_api_module:
            # Check for comprehensive API documentation
            undocumented_apis = []
            
            for func in public_functions:
                if not func.docstring or len(func.docstring) < self.thresholds['min_docstring_length']:
                    undocumented_apis.append(f"function '{func.name}'")
            
            for cls in public_classes:
                if not cls.docstring or len(cls.docstring) < self.thresholds['min_docstring_length']:
                    undocumented_apis.append(f"class '{cls.name}'")
            
            if undocumented_apis:
                issues.append(IssueFactory.create_documentation_issue(
                    title="Insufficient API Documentation",
                    description=f"API module {parsed_file.path} has insufficient documentation "
                              f"for public interfaces: {', '.join(undocumented_apis)}.",
                    file_path=parsed_file.path,
                    line_start=1,
                    line_end=10,
                    suggestion="Add comprehensive documentation for all public APIs including "
                             "usage examples, parameter descriptions, and return values.",
                    confidence=0.8,
                    documentation_type="insufficient_api_documentation",
                    severity=Severity.HIGH,
                    metadata={
                        'undocumented_apis': undocumented_apis,
                        'public_function_count': len(public_functions),
                        'public_class_count': len(public_classes)
                    }
                ))
        
        return issues
    
    def _analyze_documentation_consistency(self, parsed_file: ParsedFile) -> List[Issue]:
        """Analyze consistency of documentation style and format."""
        issues = []
        
        # Check docstring style consistency
        docstring_styles = self._analyze_docstring_styles(parsed_file)
        if len(docstring_styles) > 1:
            issues.append(IssueFactory.create_documentation_issue(
                title="Inconsistent Documentation Style",
                description=f"File {parsed_file.path} uses multiple documentation styles: "
                          f"{', '.join(docstring_styles)}. Consistent style improves readability.",
                file_path=parsed_file.path,
                line_start=1,
                line_end=10,
                suggestion="Choose one documentation style and apply it consistently "
                         "throughout the file (e.g., Google style, NumPy style, or JSDoc).",
                confidence=0.6,
                documentation_type="inconsistent_style",
                severity=Severity.LOW,
                metadata={
                    'detected_styles': docstring_styles
                }
            ))
        
        return issues
    
    def _analyze_docstring_quality(
        self, 
        docstring: str, 
        element: any, 
        parsed_file: ParsedFile, 
        element_type: str
    ) -> List[Issue]:
        """Analyze the quality of a specific docstring."""
        issues = []
        
        # Check docstring length
        if len(docstring.strip()) < self.thresholds['min_docstring_length']:
            issues.append(IssueFactory.create_documentation_issue(
                title=f"Short {element_type.title()} Docstring",
                description=f"{element_type.title()} '{element.name}' has a very short docstring "
                          f"({len(docstring.strip())} characters). Documentation should be "
                          f"descriptive and helpful.",
                file_path=parsed_file.path,
                line_start=element.line_start,
                line_end=element.line_start,
                suggestion=f"Expand the docstring to better explain the {element_type}'s "
                         f"purpose, behavior, and usage.",
                confidence=0.7,
                documentation_type="short_docstring",
                severity=Severity.LOW,
                metadata={
                    'element_name': element.name,
                    'element_type': element_type,
                    'docstring_length': len(docstring.strip())
                }
            ))
        
        # Check for placeholder docstrings
        placeholder_patterns = [
            r'^\s*todo\s*$',
            r'^\s*fixme\s*$',
            r'^\s*placeholder\s*$',
            r'^\s*description\s*$',
            r'^\s*\.\.\.\s*$'
        ]
        
        for pattern in placeholder_patterns:
            if re.match(pattern, docstring.strip(), re.IGNORECASE):
                issues.append(IssueFactory.create_documentation_issue(
                    title=f"Placeholder {element_type.title()} Docstring",
                    description=f"{element_type.title()} '{element.name}' has a placeholder "
                              f"docstring that should be replaced with actual documentation.",
                    file_path=parsed_file.path,
                    line_start=element.line_start,
                    line_end=element.line_start,
                    suggestion=f"Replace the placeholder with meaningful documentation "
                             f"explaining the {element_type}'s purpose and usage.",
                    confidence=0.9,
                    documentation_type="placeholder_docstring",
                    severity=Severity.MEDIUM,
                    metadata={
                        'element_name': element.name,
                        'element_type': element_type,
                        'placeholder_text': docstring.strip()
                    }
                ))
                break
        
        return issues
    
    def _check_parameter_documentation(self, func: Function, parsed_file: ParsedFile) -> List[Issue]:
        """Check if function parameters are properly documented."""
        issues = []
        
        if not func.docstring:
            return issues
        
        # Extract parameter documentation from docstring
        language = parsed_file.language
        param_pattern = self.doc_patterns[language].get('param_doc', '')
        
        if param_pattern:
            documented_params = set()
            for match in re.finditer(param_pattern, func.docstring, re.MULTILINE):
                if language == 'python':
                    documented_params.add(match.group(1))
                else:  # JavaScript/TypeScript
                    documented_params.add(match.group(2))
            
            # Check which parameters are missing documentation
            undocumented_params = []
            for param in func.parameters:
                # Skip 'self' and 'cls' parameters
                if param not in ['self', 'cls'] and param not in documented_params:
                    undocumented_params.append(param)
            
            if undocumented_params:
                issues.append(IssueFactory.create_documentation_issue(
                    title=f"Undocumented Parameters in '{func.name}'",
                    description=f"Function '{func.name}' has undocumented parameters: "
                              f"{', '.join(undocumented_params)}. Functions with many parameters "
                              f"should document each parameter's purpose.",
                    file_path=parsed_file.path,
                    line_start=func.line_start,
                    line_end=func.line_start,
                    suggestion="Add parameter documentation to the docstring explaining "
                             "what each parameter is for and its expected type.",
                    confidence=0.8,
                    documentation_type="undocumented_parameters",
                    severity=Severity.MEDIUM,
                    metadata={
                        'function_name': func.name,
                        'undocumented_parameters': undocumented_params,
                        'total_parameters': len(func.parameters)
                    }
                ))
        
        return issues
    
    def _has_module_docstring(self, parsed_file: ParsedFile) -> bool:
        """Check if the module has a docstring."""
        lines = parsed_file.content.splitlines()
        
        # Look for module docstring in the first few lines (after imports)
        in_docstring = False
        docstring_started = False
        
        for line in lines[:20]:  # Check first 20 lines
            stripped = line.strip()
            
            # Skip empty lines and imports
            if not stripped or stripped.startswith('import ') or stripped.startswith('from '):
                continue
            
            # Check for docstring start
            if stripped.startswith('"""') or stripped.startswith("'''"):
                if not docstring_started:
                    docstring_started = True
                    in_docstring = True
                    # Check if it's a single-line docstring
                    if stripped.count('"""') == 2 or stripped.count("'''") == 2:
                        return True
                else:
                    # End of multi-line docstring
                    return True
            elif in_docstring:
                # Inside multi-line docstring
                continue
            else:
                # Hit code before finding docstring
                break
        
        return docstring_started
    
    def _find_todo_fixme_comments(self, parsed_file: ParsedFile, lines: List[str]) -> List[Issue]:
        """Find TODO and FIXME comments."""
        issues = []
        language = parsed_file.language
        
        todo_pattern = self.doc_patterns[language].get('todo', '')
        fixme_pattern = self.doc_patterns[language].get('fixme', '')
        
        for line_num, line in enumerate(lines, 1):
            # Check for TODO comments
            if todo_pattern:
                todo_match = re.search(todo_pattern, line, re.IGNORECASE)
                if todo_match:
                    issues.append(IssueFactory.create_documentation_issue(
                        title="TODO Comment Found",
                        description=f"TODO comment found at line {line_num}: {todo_match.group(1).strip()}",
                        file_path=parsed_file.path,
                        line_start=line_num,
                        line_end=line_num,
                        suggestion="Consider creating a task or issue to track this TODO item, "
                                 "or implement the missing functionality.",
                        confidence=0.9,
                        documentation_type="todo_comment",
                        severity=Severity.INFO,
                        metadata={
                            'todo_text': todo_match.group(1).strip(),
                            'line_content': line.strip()
                        }
                    ))
            
            # Check for FIXME comments
            if fixme_pattern:
                fixme_match = re.search(fixme_pattern, line, re.IGNORECASE)
                if fixme_match:
                    issues.append(IssueFactory.create_documentation_issue(
                        title="FIXME Comment Found",
                        description=f"FIXME comment found at line {line_num}: {fixme_match.group(1).strip()}",
                        file_path=parsed_file.path,
                        line_start=line_num,
                        line_end=line_num,
                        suggestion="Address the issue mentioned in this FIXME comment "
                                 "or create a task to track it.",
                        confidence=0.9,
                        documentation_type="fixme_comment",
                        severity=Severity.LOW,
                        metadata={
                            'fixme_text': fixme_match.group(1).strip(),
                            'line_content': line.strip()
                        }
                    ))
        
        return issues
    
    def _find_outdated_comments(self, parsed_file: ParsedFile, lines: List[str]) -> List[Issue]:
        """Find potentially outdated comments."""
        issues = []
        
        # Look for comments with old dates or version references
        outdated_patterns = [
            r'(19|20)\d{2}',  # Years
            r'version\s+[0-9.]+',  # Version numbers
            r'deprecated',
            r'obsolete',
            r'old\s+way',
            r'legacy'
        ]
        
        for line_num, line in enumerate(lines, 1):
            if line.strip().startswith('#') or line.strip().startswith('//'):
                comment_text = line.strip().lower()
                
                for pattern in outdated_patterns:
                    if re.search(pattern, comment_text):
                        issues.append(IssueFactory.create_documentation_issue(
                            title="Potentially Outdated Comment",
                            description=f"Comment at line {line_num} may be outdated: {line.strip()}",
                            file_path=parsed_file.path,
                            line_start=line_num,
                            line_end=line_num,
                            suggestion="Review this comment and update or remove it if it's no longer relevant.",
                            confidence=0.6,
                            documentation_type="outdated_comment",
                            severity=Severity.INFO,
                            metadata={
                                'comment_text': line.strip(),
                                'matched_pattern': pattern
                            }
                        ))
                        break
        
        return issues
    
    def _find_commented_out_code(self, parsed_file: ParsedFile, lines: List[str]) -> List[Issue]:
        """Find commented-out code that should be removed."""
        issues = []
        
        # Patterns that suggest commented-out code
        code_patterns = [
            r'#\s*(def|class|if|for|while|try|import|from)',  # Python
            r'//\s*(function|class|if|for|while|try|import|const|let|var)',  # JavaScript
            r'#\s*[a-zA-Z_]\w*\s*[=\(]',  # Assignment or function call
            r'//\s*[a-zA-Z_]\w*\s*[=\(]'
        ]
        
        consecutive_commented_lines = 0
        start_line = 0
        
        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()
            
            if (stripped.startswith('#') or stripped.startswith('//')):
                # Check if this looks like commented-out code
                is_code = any(re.search(pattern, stripped) for pattern in code_patterns)
                
                if is_code:
                    if consecutive_commented_lines == 0:
                        start_line = line_num
                    consecutive_commented_lines += 1
                else:
                    # Reset counter for non-code comments
                    if consecutive_commented_lines >= 3:  # Multiple lines of commented code
                        issues.append(IssueFactory.create_documentation_issue(
                            title="Commented-Out Code Found",
                            description=f"Commented-out code found from line {start_line} to {line_num - 1}. "
                                      f"Consider removing dead code instead of commenting it out.",
                            file_path=parsed_file.path,
                            line_start=start_line,
                            line_end=line_num - 1,
                            suggestion="Remove commented-out code. Use version control to track "
                                     "code history instead of leaving dead code in comments.",
                            confidence=0.7,
                            documentation_type="commented_out_code",
                            severity=Severity.LOW,
                            metadata={
                                'line_count': consecutive_commented_lines
                            }
                        ))
                    consecutive_commented_lines = 0
            else:
                # Non-comment line
                if consecutive_commented_lines >= 3:
                    issues.append(IssueFactory.create_documentation_issue(
                        title="Commented-Out Code Found",
                        description=f"Commented-out code found from line {start_line} to {line_num - 1}.",
                        file_path=parsed_file.path,
                        line_start=start_line,
                        line_end=line_num - 1,
                        suggestion="Remove commented-out code. Use version control to track "
                                 "code history instead of leaving dead code in comments.",
                        confidence=0.7,
                        documentation_type="commented_out_code",
                        severity=Severity.LOW,
                        metadata={
                            'line_count': consecutive_commented_lines
                        }
                    ))
                consecutive_commented_lines = 0
        
        return issues
    
    def _analyze_docstring_styles(self, parsed_file: ParsedFile) -> List[str]:
        """Analyze what documentation styles are used in the file."""
        styles = set()
        
        # Check all docstrings in the file
        all_docstrings = []
        
        for func in parsed_file.functions:
            if func.docstring:
                all_docstrings.append(func.docstring)
        
        for cls in parsed_file.classes:
            if cls.docstring:
                all_docstrings.append(cls.docstring)
        
        # Analyze styles
        for docstring in all_docstrings:
            # Google style
            if re.search(r'Args:|Arguments:|Returns?:|Yields?:|Raises?:', docstring):
                styles.add('Google')
            
            # NumPy style
            if re.search(r'Parameters\s*\n\s*-+|Returns?\s*\n\s*-+', docstring):
                styles.add('NumPy')
            
            # Sphinx style
            if re.search(r':param\s+\w+:|:returns?:|:raises?:', docstring):
                styles.add('Sphinx')
            
            # JSDoc style
            if re.search(r'@param|@returns?|@throws?', docstring):
                styles.add('JSDoc')
        
        return list(styles)