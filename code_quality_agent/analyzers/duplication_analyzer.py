"""Duplication analyzer for detecting code duplication and similar patterns."""

import re
import ast
import hashlib
from typing import List, Dict, Any, Tuple, Set, Optional
from collections import defaultdict
import difflib
import logging

from .base import QualityAnalyzer, IssueCategory, Severity
from .issue_factory import IssueFactory
from .analyzer_utils import AnalyzerUtils
from ..core.models import ParsedFile, AnalysisContext, Issue, Function, Class

logger = logging.getLogger(__name__)


class DuplicationAnalyzer(QualityAnalyzer):
    """Analyzer for detecting code duplication and similar patterns."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the duplication analyzer."""
        super().__init__(config)
        self.supported_languages = ["python", "javascript", "typescript"]
        
        # Duplication detection thresholds (configurable)
        self.thresholds = {
            'exact_match_threshold': config.get('exact_match_threshold', 0.95) if config else 0.95,
            'similar_match_threshold': config.get('similar_match_threshold', 0.80) if config else 0.80,
            'minimum_lines': config.get('minimum_lines', 5) if config else 5,
            'minimum_tokens': config.get('minimum_tokens', 20) if config else 20,
            'function_similarity_threshold': config.get('function_similarity_threshold', 0.75) if config else 0.75
        }
    
    def get_supported_languages(self) -> List[str]:
        """Return list of supported languages."""
        return self.supported_languages
    
    def get_category(self) -> IssueCategory:
        """Return the category of issues this analyzer detects."""
        return IssueCategory.DUPLICATION
    
    def analyze(self, parsed_files: List[ParsedFile], context: AnalysisContext) -> List[Issue]:
        """
        Analyze parsed files for code duplication.
        
        Args:
            parsed_files: List of parsed files to analyze
            context: Analysis context
            
        Returns:
            List of duplication issues found
        """
        issues = []
        
        try:
            # Analyze exact duplicates
            issues.extend(self._find_exact_duplicates(parsed_files))
            
            # Analyze similar code blocks
            issues.extend(self._find_similar_blocks(parsed_files))
            
            # Analyze function duplicates
            issues.extend(self._find_duplicate_functions(parsed_files))
            
            # Analyze class duplicates
            issues.extend(self._find_duplicate_classes(parsed_files))
            
            # Analyze structural duplicates
            issues.extend(self._find_structural_duplicates(parsed_files))
            
        except Exception as e:
            logger.error(f"Duplication analysis failed: {e}")
        
        return issues
    
    def _find_exact_duplicates(self, parsed_files: List[ParsedFile]) -> List[Issue]:
        """Find exact code duplicates across files."""
        issues = []
        
        # Group code blocks by hash
        hash_to_blocks = defaultdict(list)
        
        for parsed_file in parsed_files:
            blocks = self._extract_code_blocks(parsed_file)
            
            for block in blocks:
                if len(block['lines']) >= self.thresholds['minimum_lines']:
                    # Create hash of normalized code
                    normalized_code = self._normalize_code(block['code'])
                    code_hash = hashlib.md5(normalized_code.encode()).hexdigest()
                    
                    hash_to_blocks[code_hash].append({
                        'file': parsed_file.path,
                        'block': block,
                        'normalized_code': normalized_code
                    })
        
        # Find duplicates
        for code_hash, blocks in hash_to_blocks.items():
            if len(blocks) > 1:
                # Found exact duplicates
                primary_block = blocks[0]
                duplicate_files = [block['file'] for block in blocks[1:]]
                
                issues.append(IssueFactory.create_duplication_issue(
                    title="Exact Code Duplication",
                    description=f"Exact duplicate code found in {len(blocks)} files. "
                              f"This code block appears in: {', '.join([b['file'] for b in blocks])}",
                    file_path=primary_block['file'],
                    line_start=primary_block['block']['start_line'],
                    line_end=primary_block['block']['end_line'],
                    suggestion="Extract this duplicated code into a shared function or module "
                             "to eliminate duplication and improve maintainability.",
                    confidence=0.95,
                    duplicate_files=duplicate_files,
                    similarity_score=1.0,
                    severity=Severity.MEDIUM,
                    metadata={
                        'duplication_type': 'exact',
                        'block_size': len(primary_block['block']['lines']),
                        'total_occurrences': len(blocks),
                        'code_hash': code_hash
                    }
                ))
        
        return issues
    
    def _find_similar_blocks(self, parsed_files: List[ParsedFile]) -> List[Issue]:
        """Find similar (but not identical) code blocks."""
        issues = []
        
        # Extract all code blocks
        all_blocks = []
        for parsed_file in parsed_files:
            blocks = self._extract_code_blocks(parsed_file)
            for block in blocks:
                if len(block['lines']) >= self.thresholds['minimum_lines']:
                    all_blocks.append({
                        'file': parsed_file.path,
                        'block': block,
                        'normalized_code': self._normalize_code(block['code'])
                    })
        
        # Compare all pairs of blocks
        for i, block1 in enumerate(all_blocks):
            for j, block2 in enumerate(all_blocks[i+1:], i+1):
                if block1['file'] != block2['file']:  # Don't compare blocks from same file
                    similarity = self._calculate_similarity(
                        block1['normalized_code'], 
                        block2['normalized_code']
                    )
                    
                    if similarity >= self.thresholds['similar_match_threshold']:
                        issues.append(IssueFactory.create_duplication_issue(
                            title="Similar Code Detected",
                            description=f"Similar code found between {block1['file']} and {block2['file']} "
                                      f"with {similarity:.1%} similarity. This may indicate code duplication.",
                            file_path=block1['file'],
                            line_start=block1['block']['start_line'],
                            line_end=block1['block']['end_line'],
                            suggestion="Consider extracting common functionality into a shared function "
                                     "or refactoring to reduce code duplication.",
                            confidence=0.8,
                            duplicate_files=[block2['file']],
                            similarity_score=similarity,
                            severity=self._get_duplication_severity(similarity, len(block1['content'])),
                            metadata={
                                'duplication_type': 'similar',
                                'similarity_score': similarity,
                                'block1_size': len(block1['block']['lines']),
                                'block2_size': len(block2['block']['lines']),
                                'other_location': f"{block2['file']}:{block2['block']['start_line']}-{block2['block']['end_line']}"
                            }
                        ))
        
        return issues
    
    def _find_duplicate_functions(self, parsed_files: List[ParsedFile]) -> List[Issue]:
        """Find duplicate or very similar functions."""
        issues = []
        
        # Collect all functions with their bodies
        all_functions = []
        
        for parsed_file in parsed_files:
            for func in parsed_file.functions:
                # Extract function body from content
                func_body = self._extract_function_body(func, parsed_file.content)
                if func_body:
                    normalized_body = self._normalize_code(func_body)
                    all_functions.append({
                        'file': parsed_file.path,
                        'function': func,
                        'body': normalized_body,
                        'original_body': func_body
                    })
        
        # Compare all functions with each other (regardless of name)
        for i, func1 in enumerate(all_functions):
            for func2 in all_functions[i+1:]:
                # Compare functions from same or different files
                # Skip if it's the exact same function (same file and same line)
                if not (func1['file'] == func2['file'] and 
                       func1['function'].line_start == func2['function'].line_start):
                    # Check if functions have similar parameter counts (optional filter)
                    param_count1 = len(func1['function'].parameters)
                    param_count2 = len(func2['function'].parameters)
                    
                    # Allow functions with same or similar parameter counts
                    if abs(param_count1 - param_count2) <= 1:  # Allow difference of 1 parameter
                        similarity = self._calculate_similarity(func1['body'], func2['body'])
                        
                        if similarity >= self.thresholds['function_similarity_threshold']:
                            issues.append(IssueFactory.create_duplication_issue(
                                title=f"Duplicate Function '{func1['function'].name}'",
                                description=f"Function '{func1['function'].name}' appears to be duplicated "
                                          f"as '{func2['function'].name}' in {func2['file']} with {similarity:.1%} similarity.",
                                file_path=func1['file'],
                                line_start=func1['function'].line_start,
                                line_end=func1['function'].line_end,
                                suggestion="Consider extracting common functionality into a shared utility "
                                         "function or module to eliminate duplication.",
                                confidence=0.85,
                                duplicate_files=[func2['file']],
                                similarity_score=similarity,
                                severity=self._get_duplication_severity(similarity, len(func1['body'])),
                                metadata={
                                    'duplication_type': 'function',
                                    'function_name': func1['function'].name,
                                    'duplicate_function_name': func2['function'].name,
                                    'other_location': f"{func2['file']}:{func2['function'].line_start}",
                                    'similarity_score': similarity
                                }
                            ))
        
        return issues
    
    def _find_duplicate_classes(self, parsed_files: List[ParsedFile]) -> List[Issue]:
        """Find duplicate or very similar classes."""
        issues = []
        
        # Group classes by structure similarity
        for i, file1 in enumerate(parsed_files):
            for j, file2 in enumerate(parsed_files[i+1:], i+1):
                if file1.path != file2.path:
                    for class1 in file1.classes:
                        for class2 in file2.classes:
                            similarity = self._calculate_class_similarity(class1, class2)
                            
                            if similarity >= 0.8:  # High similarity threshold for classes
                                issues.append(IssueFactory.create_duplication_issue(
                                    title=f"Similar Class '{class1.name}'",
                                    description=f"Class '{class1.name}' is very similar to class "
                                              f"'{class2.name}' in {file2.path} ({similarity:.1%} similarity).",
                                    file_path=file1.path,
                                    line_start=class1.line_start,
                                    line_end=class1.line_end,
                                    suggestion="Consider using inheritance, composition, or extracting "
                                             "common functionality to reduce class duplication.",
                                    confidence=0.75,
                                    duplicate_files=[file2.path],
                                    similarity_score=similarity,
                                    severity=Severity.MEDIUM,
                                    metadata={
                                        'duplication_type': 'class',
                                        'class1_name': class1.name,
                                        'class2_name': class2.name,
                                        'class1_methods': len(class1.methods),
                                        'class2_methods': len(class2.methods)
                                    }
                                ))
        
        return issues
    
    def _find_structural_duplicates(self, parsed_files: List[ParsedFile]) -> List[Issue]:
        """Find structural patterns that are duplicated."""
        issues = []
        
        # Look for repeated patterns in code structure
        pattern_counts = defaultdict(list)
        
        for parsed_file in parsed_files:
            patterns = self._extract_structural_patterns(parsed_file)
            
            for pattern in patterns:
                pattern_counts[pattern['signature']].append({
                    'file': parsed_file.path,
                    'pattern': pattern
                })
        
        # Find repeated patterns
        for signature, occurrences in pattern_counts.items():
            if len(occurrences) >= 3:  # Pattern appears 3+ times
                primary = occurrences[0]
                duplicate_files = [occ['file'] for occ in occurrences[1:]]
                
                issues.append(IssueFactory.create_duplication_issue(
                    title="Repeated Code Pattern",
                    description=f"Structural pattern repeated {len(occurrences)} times across files. "
                              f"This pattern appears in: {', '.join([occ['file'] for occ in occurrences])}",
                    file_path=primary['file'],
                    line_start=primary['pattern']['start_line'],
                    line_end=primary['pattern']['end_line'],
                    suggestion="Consider creating a template, function, or design pattern "
                             "to eliminate this repeated structural code.",
                    confidence=0.7,
                    duplicate_files=duplicate_files,
                    similarity_score=0.9,
                    severity=Severity.LOW,
                    metadata={
                        'duplication_type': 'structural',
                        'pattern_signature': signature,
                        'occurrences': len(occurrences)
                    }
                ))
        
        return issues
    
    def _extract_code_blocks(self, parsed_file: ParsedFile) -> List[Dict[str, Any]]:
        """Extract meaningful code blocks from a file."""
        blocks = []
        lines = parsed_file.content.splitlines()
        
        # Extract blocks based on indentation and logical groupings
        current_block = []
        current_start = 0
        base_indent = 0
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Skip empty lines and comments
            if not stripped or stripped.startswith('#') or stripped.startswith('//'):
                if current_block:
                    # End current block
                    blocks.append({
                        'start_line': current_start + 1,
                        'end_line': i,
                        'lines': current_block,
                        'code': '\n'.join(current_block)
                    })
                    current_block = []
                continue
            
            # Calculate indentation
            indent = len(line) - len(line.lstrip())
            
            if not current_block:
                # Start new block
                current_start = i
                base_indent = indent
                current_block = [line]
            elif indent >= base_indent:
                # Continue current block
                current_block.append(line)
            else:
                # End current block and start new one
                if len(current_block) >= self.thresholds['minimum_lines']:
                    blocks.append({
                        'start_line': current_start + 1,
                        'end_line': i,
                        'lines': current_block,
                        'code': '\n'.join(current_block)
                    })
                
                current_start = i
                base_indent = indent
                current_block = [line]
        
        # Add final block
        if len(current_block) >= self.thresholds['minimum_lines']:
            blocks.append({
                'start_line': current_start + 1,
                'end_line': len(lines),
                'lines': current_block,
                'code': '\n'.join(current_block)
            })
        
        return blocks
    
    def _normalize_code(self, code: str) -> str:
        """Normalize code for comparison by removing formatting differences."""
        # Remove comments
        lines = []
        for line in code.splitlines():
            # Remove inline comments (simplified)
            if '#' in line:
                line = line[:line.index('#')]
            if '//' in line:
                line = line[:line.index('//')]
            
            stripped = line.strip()
            if stripped:
                lines.append(stripped)
        
        # Join and normalize whitespace
        normalized = ' '.join(lines)
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Normalize common patterns
        normalized = re.sub(r'\s*([{}();,])\s*', r'\1', normalized)
        
        return normalized.lower()
    
    def _calculate_similarity(self, code1: str, code2: str) -> float:
        """Calculate similarity between two code snippets."""
        if not code1 or not code2:
            return 0.0
        
        # Use difflib to calculate similarity
        similarity = difflib.SequenceMatcher(None, code1, code2).ratio()
        return similarity
    
    def _extract_function_body(self, func: Function, content: str) -> Optional[str]:
        """Extract function body from file content."""
        if not func.line_start or not func.line_end:
            return None
        
        lines = content.splitlines()
        if func.line_start <= len(lines) and func.line_end <= len(lines):
            # Extract function body (skip the definition line)
            body_lines = lines[func.line_start:func.line_end]
            return '\n'.join(body_lines)
        
        return None
    
    def _create_function_signature(self, func: Function) -> str:
        """Create a normalized signature for function comparison."""
        # Normalize parameter names to generic names
        param_count = len(func.parameters)
        generic_params = [f"param{i}" for i in range(param_count)]
        
        signature = f"{func.name}({','.join(generic_params)})"
        return signature
    
    def _calculate_class_similarity(self, class1: Class, class2: Class) -> float:
        """Calculate similarity between two classes."""
        # Compare method names and count
        methods1 = set(method.name for method in class1.methods)
        methods2 = set(method.name for method in class2.methods)
        
        if not methods1 and not methods2:
            return 1.0
        
        if not methods1 or not methods2:
            return 0.0
        
        # Calculate Jaccard similarity
        intersection = len(methods1.intersection(methods2))
        union = len(methods1.union(methods2))
        
        return intersection / union if union > 0 else 0.0
    
    def _extract_structural_patterns(self, parsed_file: ParsedFile) -> List[Dict[str, Any]]:
        """Extract structural patterns from code - only for significant duplication."""
        patterns = []
        lines = parsed_file.content.splitlines()
        
        # Only look for substantial patterns that indicate real duplication
        # Skip common patterns like imports, docstrings, and simple structures
        for i in range(len(lines) - 10):  # Require larger minimum pattern size
            pattern_lines = []
            for j in range(i, min(i + 20, len(lines))):  # Larger pattern size for meaningful duplication
                line = lines[j].strip()
                
                # Skip common, non-duplicative patterns
                if (line and 
                    not line.startswith('#') and 
                    not line.startswith('//') and
                    not line.startswith('import ') and
                    not line.startswith('from ') and
                    not line.startswith('"""') and
                    not line.startswith("'''") and
                    not re.match(r'^\s*def\s+\w+\(', line) and  # Skip function definitions
                    not re.match(r'^\s*class\s+\w+', line) and  # Skip class definitions
                    len(line) > 20):  # Skip very short lines
                    
                    # Create structural signature (remove literals)
                    structural_line = re.sub(r'["\'][^"\']*["\']', '""', line)  # Remove string literals
                    structural_line = re.sub(r'\b\d+\b', '0', structural_line)  # Remove numbers
                    structural_line = re.sub(r'\b[a-zA-Z_]\w*\b', 'VAR', structural_line)  # Replace identifiers
                    pattern_lines.append(structural_line)
                
                # Only consider substantial patterns (at least 8 lines of actual code)
                if len(pattern_lines) >= 8:
                    signature = '|'.join(pattern_lines)
                    patterns.append({
                        'signature': signature,
                        'start_line': i + 1,
                        'end_line': j + 1,
                        'lines': pattern_lines
                    })
                    break  # Move to next starting position
        
        return patterns
    
    def _get_duplication_severity(self, similarity: float, code_length: int = 0) -> Severity:
        """Get severity based on similarity score and code length."""
        # HIGH severity for exact matches or very large duplicated code
        if similarity >= 0.99 or (similarity >= 0.95 and code_length > 100):
            return Severity.HIGH
        elif similarity >= 0.95:
            return Severity.MEDIUM
        elif similarity >= 0.85:
            return Severity.LOW
        else:
            return Severity.INFO