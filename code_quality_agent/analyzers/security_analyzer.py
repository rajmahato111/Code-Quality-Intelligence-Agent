"""Security analyzer for detecting security vulnerabilities and risks."""

import re
import ast
from typing import List, Dict, Any, Tuple, Set
import logging

from .base import QualityAnalyzer, IssueCategory, Severity
from .issue_factory import IssueFactory
from .analyzer_utils import AnalyzerUtils
from ..core.models import ParsedFile, AnalysisContext, Issue

logger = logging.getLogger(__name__)


class SecurityAnalyzer(QualityAnalyzer):
    """Analyzer for detecting security vulnerabilities and risks."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the security analyzer."""
        super().__init__(config)
        self.supported_languages = ["python", "javascript", "typescript"]
        
        # Security patterns for different languages
        self._init_security_patterns()
    
    def _init_security_patterns(self):
        """Initialize security vulnerability patterns."""
        self.python_patterns = {
            'sql_injection': [
                r'execute\s*\(\s*["\'].*%.*["\']',  # String formatting in SQL
                r'execute\s*\(\s*.*\+.*\)',         # String concatenation
                r'cursor\.execute\s*\(\s*f["\']',   # f-string in execute
                r'query\s*=\s*["\'].*%.*["\']',     # Query with % formatting
                r'sql\s*=\s*.*\+.*'                 # SQL with concatenation
            ],
            'command_injection': [
                r'os\.system\s*\(\s*.*\+',          # os.system with concatenation
                r'subprocess\.(call|run|Popen)\s*\(\s*.*\+',  # subprocess with concatenation
                r'eval\s*\(\s*.*input',             # eval with user input
                r'exec\s*\(\s*.*input'              # exec with user input
            ],
            'path_traversal': [
                r'open\s*\(\s*.*\+.*["\']\.\./',    # File open with path traversal
                r'file\s*=\s*.*\+.*["\']\.\./',     # File assignment with traversal
                r'path\s*=\s*.*\+.*["\']\.\./'      # Path with traversal
            ],
            'weak_crypto': [
                r'hashlib\.md5\s*\(',               # MD5 usage
                r'hashlib\.sha1\s*\(',              # SHA1 usage
                r'random\.random\s*\(',             # Weak random for crypto
                r'DES\s*\(',                        # DES encryption
                r'RC4\s*\('                         # RC4 encryption
            ],
            'hardcoded_secrets': [
                r'password\s*=\s*["\'][^"\']{8,}["\']',
                r'api[_-]?key\s*=\s*["\'][^"\']{20,}["\']',
                r'secret\s*=\s*["\'][^"\']{16,}["\']',
                r'token\s*=\s*["\'][^"\']{20,}["\']'
            ]
        }
        
        self.javascript_patterns = {
            'sql_injection': [
                r'query\s*=\s*["`\'].*\$\{.*\}.*["`\']',  # Template literal injection
                r'execute\s*\(\s*["`\'].*\+.*["`\']',      # String concatenation
                r'sql\s*=\s*.*\+.*',                       # SQL concatenation
                r'query\(\s*["`\'].*\$\{.*\}.*["`\']'      # Query with template literal
            ],
            'xss': [
                r'innerHTML\s*=\s*.*\+',            # innerHTML with concatenation
                r'document\.write\s*\(\s*.*\+',     # document.write with concat
                r'\.html\s*\(\s*.*\+',              # jQuery html() with concat
                r'dangerouslySetInnerHTML'          # React dangerous HTML
            ],
            'command_injection': [
                r'exec\s*\(\s*.*\+',                # exec with concatenation
                r'eval\s*\(\s*.*\+',                # eval with concatenation
                r'Function\s*\(\s*.*\+',            # Function constructor
                r'child_process\.exec\s*\(\s*.*\+'  # Node.js exec
            ],
            'weak_crypto': [
                r'Math\.random\s*\(',               # Weak random for crypto
                r'crypto\.createHash\s*\(\s*["\']md5["\']',  # MD5
                r'crypto\.createHash\s*\(\s*["\']sha1["\']'  # SHA1
            ],
            'hardcoded_secrets': [
                r'password\s*[:=]\s*["`\'][^"`\']{8,}["`\']',
                r'apiKey\s*[:=]\s*["`\'][^"`\']{20,}["`\']',
                r'secret\s*[:=]\s*["`\'][^"`\']{16,}["`\']',
                r'token\s*[:=]\s*["`\'][^"`\']{20,}["`\']'
            ]
        }
    
    def get_supported_languages(self) -> List[str]:
        """Return list of supported languages."""
        return self.supported_languages
    
    def get_category(self) -> IssueCategory:
        """Return the category of issues this analyzer detects."""
        return IssueCategory.SECURITY
    
    def analyze(self, parsed_files: List[ParsedFile], context: AnalysisContext) -> List[Issue]:
        """
        Analyze parsed files for security vulnerabilities.
        
        Args:
            parsed_files: List of parsed files to analyze
            context: Analysis context
            
        Returns:
            List of security issues found
        """
        issues = []
        
        for parsed_file in parsed_files:
            try:
                if parsed_file.language == "python":
                    issues.extend(self._analyze_python_security(parsed_file))
                elif parsed_file.language in ["javascript", "typescript"]:
                    issues.extend(self._analyze_javascript_security(parsed_file))
                
                # Common security checks for all languages
                issues.extend(self._analyze_common_security(parsed_file))
                
            except Exception as e:
                logger.error(f"Security analysis failed for {parsed_file.path}: {e}")
        
        return issues
    
    def _analyze_python_security(self, parsed_file: ParsedFile) -> List[Issue]:
        """Analyze Python-specific security issues."""
        issues = []
        content = parsed_file.content
        lines = content.splitlines()
        
        # Check for SQL injection vulnerabilities
        issues.extend(self._check_sql_injection(parsed_file, self.python_patterns['sql_injection']))
        
        # Check for command injection
        issues.extend(self._check_command_injection(parsed_file, self.python_patterns['command_injection']))
        
        # Check for path traversal
        issues.extend(self._check_path_traversal(parsed_file, self.python_patterns['path_traversal']))
        
        # Check for weak cryptography
        issues.extend(self._check_weak_crypto(parsed_file, self.python_patterns['weak_crypto']))
        
        # Check for dangerous imports
        issues.extend(self._check_dangerous_imports(parsed_file))
        
        # Check for pickle usage (Python-specific)
        issues.extend(self._check_pickle_usage(parsed_file))
        
        # Check for eval/exec usage
        issues.extend(self._check_eval_exec_usage(parsed_file))
        
        return issues
    
    def _analyze_javascript_security(self, parsed_file: ParsedFile) -> List[Issue]:
        """Analyze JavaScript/TypeScript-specific security issues."""
        issues = []
        
        # Check for SQL injection vulnerabilities
        issues.extend(self._check_sql_injection(parsed_file, self.javascript_patterns['sql_injection']))
        
        # Check for XSS vulnerabilities
        issues.extend(self._check_xss_vulnerabilities(parsed_file))
        
        # Check for command injection
        issues.extend(self._check_command_injection(parsed_file, self.javascript_patterns['command_injection']))
        
        # Check for weak cryptography
        issues.extend(self._check_weak_crypto(parsed_file, self.javascript_patterns['weak_crypto']))
        
        # Check for dangerous functions
        issues.extend(self._check_dangerous_js_functions(parsed_file))
        
        return issues
    
    def _analyze_common_security(self, parsed_file: ParsedFile) -> List[Issue]:
        """Analyze common security issues across all languages."""
        issues = []
        
        # Check for hardcoded secrets
        issues.extend(self._check_hardcoded_secrets(parsed_file))
        
        # Check for insecure random usage
        issues.extend(self._check_insecure_random(parsed_file))
        
        # Check for debug information leakage
        issues.extend(self._check_debug_leakage(parsed_file))
        
        return issues
    
    def _check_sql_injection(self, parsed_file: ParsedFile, patterns: List[str]) -> List[Issue]:
        """Check for SQL injection vulnerabilities."""
        issues = []
        lines = parsed_file.content.splitlines()
        
        for line_num, line in enumerate(lines, 1):
            for pattern in patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(IssueFactory.create_security_issue(
                        title="Potential SQL Injection Vulnerability",
                        description=f"SQL query construction using string formatting or concatenation "
                                  f"may be vulnerable to SQL injection attacks. Line: {line.strip()}",
                        file_path=parsed_file.path,
                        line_start=line_num,
                        line_end=line_num,
                        suggestion="Use parameterized queries or prepared statements instead of "
                                 "string concatenation for SQL queries.",
                        confidence=0.8,
                        vulnerability_type="sql_injection",
                        severity=Severity.HIGH,
                        metadata={
                            'pattern_matched': pattern,
                            'code_snippet': line.strip()
                        }
                    ))
                    break
        
        return issues
    
    def _check_command_injection(self, parsed_file: ParsedFile, patterns: List[str]) -> List[Issue]:
        """Check for command injection vulnerabilities."""
        issues = []
        lines = parsed_file.content.splitlines()
        
        for line_num, line in enumerate(lines, 1):
            for pattern in patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(IssueFactory.create_security_issue(
                        title="Potential Command Injection Vulnerability",
                        description=f"Command execution with user input may be vulnerable to "
                                  f"command injection attacks. Line: {line.strip()}",
                        file_path=parsed_file.path,
                        line_start=line_num,
                        line_end=line_num,
                        suggestion="Validate and sanitize user input before using in system commands. "
                                 "Consider using safer alternatives or input validation.",
                        confidence=0.85,
                        vulnerability_type="command_injection",
                        severity=Severity.HIGH,
                        metadata={
                            'pattern_matched': pattern,
                            'code_snippet': line.strip()
                        }
                    ))
                    break
        
        return issues
    
    def _check_path_traversal(self, parsed_file: ParsedFile, patterns: List[str]) -> List[Issue]:
        """Check for path traversal vulnerabilities."""
        issues = []
        lines = parsed_file.content.splitlines()
        
        for line_num, line in enumerate(lines, 1):
            for pattern in patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(IssueFactory.create_security_issue(
                        title="Potential Path Traversal Vulnerability",
                        description=f"File path construction may be vulnerable to path traversal "
                                  f"attacks. Line: {line.strip()}",
                        file_path=parsed_file.path,
                        line_start=line_num,
                        line_end=line_num,
                        suggestion="Validate and sanitize file paths. Use os.path.join() or "
                                 "pathlib for safe path construction.",
                        confidence=0.75,
                        vulnerability_type="path_traversal",
                        severity=Severity.MEDIUM,
                        metadata={
                            'pattern_matched': pattern,
                            'code_snippet': line.strip()
                        }
                    ))
                    break
        
        return issues
    
    def _check_weak_crypto(self, parsed_file: ParsedFile, patterns: List[str]) -> List[Issue]:
        """Check for weak cryptographic practices."""
        issues = []
        lines = parsed_file.content.splitlines()
        
        for line_num, line in enumerate(lines, 1):
            for pattern in patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(IssueFactory.create_security_issue(
                        title="Weak Cryptographic Algorithm",
                        description=f"Usage of weak or deprecated cryptographic algorithm. "
                                  f"Line: {line.strip()}",
                        file_path=parsed_file.path,
                        line_start=line_num,
                        line_end=line_num,
                        suggestion="Use strong cryptographic algorithms like SHA-256, SHA-3, "
                                 "or bcrypt for hashing. Avoid MD5, SHA-1, and weak encryption.",
                        confidence=0.9,
                        vulnerability_type="weak_crypto",
                        severity=Severity.MEDIUM,
                        metadata={
                            'pattern_matched': pattern,
                            'code_snippet': line.strip()
                        }
                    ))
                    break
        
        return issues
    
    def _check_hardcoded_secrets(self, parsed_file: ParsedFile) -> List[Issue]:
        """Check for hardcoded secrets and credentials."""
        issues = []
        
        # Use utility function to find secrets
        secrets = AnalyzerUtils.find_hardcoded_secrets(parsed_file.content)
        
        for secret_type, line_num, context in secrets:
            issues.append(IssueFactory.create_security_issue(
                title=f"Hardcoded {secret_type.replace('_', ' ').title()}",
                description=f"Hardcoded {secret_type.replace('_', ' ')} found in source code. "
                          f"This poses a security risk if the code is shared or stored in version control.",
                file_path=parsed_file.path,
                line_start=line_num,
                line_end=line_num,
                suggestion=f"Move {secret_type.replace('_', ' ')} to environment variables, "
                         f"configuration files, or secure credential storage.",
                confidence=0.85,
                vulnerability_type="hardcoded_secret",
                severity=Severity.HIGH,
                metadata={
                    'secret_type': secret_type,
                    'code_snippet': context
                }
            ))
        
        return issues
    
    def _check_xss_vulnerabilities(self, parsed_file: ParsedFile) -> List[Issue]:
        """Check for XSS vulnerabilities in JavaScript/TypeScript."""
        issues = []
        lines = parsed_file.content.splitlines()
        
        xss_patterns = self.javascript_patterns['xss']
        
        for line_num, line in enumerate(lines, 1):
            for pattern in xss_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(IssueFactory.create_security_issue(
                        title="Potential Cross-Site Scripting (XSS) Vulnerability",
                        description=f"Dynamic HTML content generation may be vulnerable to XSS attacks. "
                                  f"Line: {line.strip()}",
                        file_path=parsed_file.path,
                        line_start=line_num,
                        line_end=line_num,
                        suggestion="Sanitize user input and use safe methods for DOM manipulation. "
                                 "Consider using textContent instead of innerHTML for user data.",
                        confidence=0.8,
                        vulnerability_type="xss",
                        severity=Severity.HIGH,
                        metadata={
                            'pattern_matched': pattern,
                            'code_snippet': line.strip()
                        }
                    ))
                    break
        
        return issues
    
    def _check_dangerous_imports(self, parsed_file: ParsedFile) -> List[Issue]:
        """Check for dangerous Python imports."""
        issues = []
        dangerous_imports = ['pickle', 'cPickle', 'marshal', 'shelve']
        
        for import_stmt in parsed_file.imports:
            if import_stmt.module in dangerous_imports:
                issues.append(IssueFactory.create_security_issue(
                    title=f"Dangerous Import: {import_stmt.module}",
                    description=f"Import of {import_stmt.module} module can be dangerous as it "
                              f"can execute arbitrary code during deserialization.",
                    file_path=parsed_file.path,
                    line_start=import_stmt.line_number,
                    line_end=import_stmt.line_number,
                    suggestion=f"Consider safer alternatives to {import_stmt.module}. "
                             f"Use json for data serialization when possible.",
                    confidence=0.7,
                    vulnerability_type="dangerous_import",
                    severity=Severity.MEDIUM,
                    metadata={
                        'dangerous_module': import_stmt.module
                    }
                ))
        
        return issues
    
    def _check_pickle_usage(self, parsed_file: ParsedFile) -> List[Issue]:
        """Check for unsafe pickle usage in Python."""
        issues = []
        lines = parsed_file.content.splitlines()
        
        pickle_patterns = [
            r'pickle\.loads?\s*\(',
            r'cPickle\.loads?\s*\(',
            r'marshal\.loads?\s*\('
        ]
        
        for line_num, line in enumerate(lines, 1):
            for pattern in pickle_patterns:
                if re.search(pattern, line):
                    issues.append(IssueFactory.create_security_issue(
                        title="Unsafe Deserialization",
                        description=f"Pickle/marshal deserialization can execute arbitrary code. "
                                  f"Line: {line.strip()}",
                        file_path=parsed_file.path,
                        line_start=line_num,
                        line_end=line_num,
                        suggestion="Only deserialize data from trusted sources. Consider using "
                                 "safer serialization formats like JSON.",
                        confidence=0.8,
                        vulnerability_type="unsafe_deserialization",
                        severity=Severity.HIGH,
                        metadata={
                            'pattern_matched': pattern,
                            'code_snippet': line.strip()
                        }
                    ))
                    break
        
        return issues
    
    def _check_eval_exec_usage(self, parsed_file: ParsedFile) -> List[Issue]:
        """Check for dangerous eval/exec usage."""
        issues = []
        lines = parsed_file.content.splitlines()
        
        dangerous_patterns = [
            r'\beval\s*\(',
            r'\bexec\s*\(',
            r'__import__\s*\('
        ]
        
        for line_num, line in enumerate(lines, 1):
            for pattern in dangerous_patterns:
                match = re.search(pattern, line)
                if match:
                    # Extract function name from the matched line, not the pattern
                    function_match = re.search(r'(\w+)\s*\(', line)
                    function_name = function_match.group(1) if function_match else "unknown"
                    issues.append(IssueFactory.create_security_issue(
                        title=f"Dangerous Function Usage: {function_name}",
                        description=f"Usage of {function_name}() can execute arbitrary code and "
                                  f"poses security risks. Line: {line.strip()}",
                        file_path=parsed_file.path,
                        line_start=line_num,
                        line_end=line_num,
                        suggestion=f"Avoid using {function_name}() with user input. "
                                 f"Consider safer alternatives for dynamic code execution.",
                        confidence=0.85,
                        vulnerability_type="code_injection",
                        severity=Severity.HIGH,
                        metadata={
                            'dangerous_function': function_name,
                            'code_snippet': line.strip()
                        }
                    ))
                    break
        
        return issues
    
    def _check_dangerous_js_functions(self, parsed_file: ParsedFile) -> List[Issue]:
        """Check for dangerous JavaScript functions."""
        issues = []
        lines = parsed_file.content.splitlines()
        
        dangerous_patterns = [
            (r'\beval\s*\(', 'eval'),
            (r'Function\s*\(', 'Function constructor'),
            (r'setTimeout\s*\(\s*["\']', 'setTimeout with string'),
            (r'setInterval\s*\(\s*["\']', 'setInterval with string')
        ]
        
        for line_num, line in enumerate(lines, 1):
            for pattern, function_name in dangerous_patterns:
                if re.search(pattern, line):
                    issues.append(IssueFactory.create_security_issue(
                        title=f"Dangerous Function Usage: {function_name}",
                        description=f"Usage of {function_name} can execute arbitrary code. "
                                  f"Line: {line.strip()}",
                        file_path=parsed_file.path,
                        line_start=line_num,
                        line_end=line_num,
                        suggestion=f"Avoid using {function_name} with dynamic content. "
                                 f"Use safer alternatives for dynamic behavior.",
                        confidence=0.8,
                        vulnerability_type="code_injection",
                        severity=Severity.HIGH,
                        metadata={
                            'dangerous_function': function_name,
                            'code_snippet': line.strip()
                        }
                    ))
                    break
        
        return issues
    
    def _check_insecure_random(self, parsed_file: ParsedFile) -> List[Issue]:
        """Check for insecure random number generation."""
        issues = []
        lines = parsed_file.content.splitlines()
        
        if parsed_file.language == "python":
            patterns = [r'random\.random\s*\(', r'random\.randint\s*\(']
            suggestion = "Use secrets module for cryptographic purposes: secrets.randbelow(), secrets.token_hex()"
        else:
            patterns = [r'Math\.random\s*\(']
            suggestion = "Use crypto.getRandomValues() for cryptographic purposes"
        
        for line_num, line in enumerate(lines, 1):
            for pattern in patterns:
                if re.search(pattern, line):
                    # Check if it's in a security-sensitive context
                    if any(keyword in line.lower() for keyword in ['password', 'token', 'key', 'salt', 'nonce']):
                        issues.append(IssueFactory.create_security_issue(
                            title="Insecure Random Number Generation",
                            description=f"Weak random number generator used in security-sensitive context. "
                                      f"Line: {line.strip()}",
                            file_path=parsed_file.path,
                            line_start=line_num,
                            line_end=line_num,
                            suggestion=suggestion,
                            confidence=0.9,
                            vulnerability_type="insecure_random",
                            severity=Severity.MEDIUM,
                            metadata={
                                'pattern_matched': pattern,
                                'code_snippet': line.strip()
                            }
                        ))
                        break
        
        return issues
    
    def _check_debug_leakage(self, parsed_file: ParsedFile) -> List[Issue]:
        """Check for debug information leakage."""
        issues = []
        lines = parsed_file.content.splitlines()
        
        debug_patterns = [
            r'print\s*\(\s*.*password',
            r'console\.log\s*\(\s*.*password',
            r'console\.log\s*\(\s*.*token',
            r'print\s*\(\s*.*secret',
            r'console\.error\s*\(\s*.*error\)',
            r'traceback\.print_exc\s*\('
        ]
        
        for line_num, line in enumerate(lines, 1):
            for pattern in debug_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(IssueFactory.create_security_issue(
                        title="Potential Information Leakage",
                        description=f"Debug statement may leak sensitive information. "
                                  f"Line: {line.strip()}",
                        file_path=parsed_file.path,
                        line_start=line_num,
                        line_end=line_num,
                        suggestion="Remove debug statements or ensure they don't leak sensitive "
                                 "information in production.",
                        confidence=0.6,
                        vulnerability_type="information_leakage",
                        severity=Severity.LOW,
                        metadata={
                            'pattern_matched': pattern,
                            'code_snippet': line.strip()
                        }
                    ))
                    break
        
        return issues