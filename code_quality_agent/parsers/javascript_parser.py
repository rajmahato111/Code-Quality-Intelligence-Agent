"""JavaScript/TypeScript parser using tree-sitter for AST analysis."""

import json
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional, Dict, Any, Set
import logging
import re

from .base import CodeParser
from ..core.models import (
    ParsedFile, Function, Class, Import, FileMetadata,
    DependencyGraph
)
from ..utils.file_utils import read_file_safely

logger = logging.getLogger(__name__)


class JavaScriptParser(CodeParser):
    """Parser for JavaScript and TypeScript using tree-sitter."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the JavaScript/TypeScript parser."""
        super().__init__(config)
        self.supported_languages = ["javascript", "typescript"]
        self.file_extensions = [".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"]
        self._tree_sitter_available = self._check_tree_sitter_availability()
    
    def get_supported_languages(self) -> List[str]:
        """Return list of supported languages."""
        return self.supported_languages
    
    def get_file_extensions(self) -> List[str]:
        """Return list of supported file extensions."""
        return self.file_extensions
    
    def _check_tree_sitter_availability(self) -> bool:
        """Check if tree-sitter is available."""
        try:
            import tree_sitter
            return True
        except ImportError:
            logger.warning("tree-sitter not available, falling back to regex parsing")
            return False
    
    def parse_file(self, file_path: Path) -> Optional[ParsedFile]:
        """
        Parse a JavaScript/TypeScript file and extract structured information.
        
        Args:
            file_path: Path to the JavaScript/TypeScript file
            
        Returns:
            ParsedFile object or None if parsing failed
        """
        try:
            # Read file content
            content = read_file_safely(file_path)
            if content is None:
                logger.warning(f"Could not read file: {file_path}")
                return None
            
            # Determine language
            language = self._determine_language(file_path)
            
            # Extract metadata
            metadata = FileMetadata(
                file_path=str(file_path),
                language=language,
                size_bytes=len(content.encode('utf-8')),
                line_count=len(content.splitlines()),
                encoding='utf-8'
            )
            
            # Parse using tree-sitter if available, otherwise use regex fallback
            if self._tree_sitter_available:
                ast_data = self._parse_with_tree_sitter(content, language)
            else:
                ast_data = self._parse_with_regex(content, language)
            
            if ast_data is None:
                logger.warning(f"Failed to parse {file_path}")
                return None
            
            # Extract code elements
            functions = self._extract_functions(ast_data, content)
            classes = self._extract_classes(ast_data, content)
            imports = self._extract_imports(ast_data, content)
            
            return ParsedFile(
                path=str(file_path),
                language=language,
                content=content,
                ast=ast_data,
                metadata=metadata,
                functions=functions,
                classes=classes,
                imports=imports
            )
            
        except Exception as e:
            logger.error(f"Failed to parse {file_path}: {e}")
            return None
    
    def _determine_language(self, file_path: Path) -> str:
        """Determine if file is JavaScript or TypeScript."""
        extension = file_path.suffix.lower()
        if extension in ['.ts', '.tsx']:
            return 'typescript'
        return 'javascript'
    
    def _parse_with_tree_sitter(self, content: str, language: str) -> Optional[Dict[str, Any]]:
        """Parse using tree-sitter library."""
        try:
            import tree_sitter
            
            # Try to load the appropriate language with new API
            try:
                if language == 'typescript':
                    import tree_sitter_typescript as ts_typescript
                    language_obj = tree_sitter.Language(ts_typescript.language_typescript())
                else:
                    import tree_sitter_javascript as ts_javascript
                    language_obj = tree_sitter.Language(ts_javascript.language())
                
                # Use new tree-sitter API (v0.21+)
                parser = tree_sitter.Parser(language_obj)
                
            except (ImportError, AttributeError, TypeError):
                # Fallback to older API or disable tree-sitter
                logger.warning(f"Tree-sitter parsing not available for {language}, using regex fallback")
                return None
            
            tree = parser.parse(bytes(content, 'utf8'))
            
            # Convert tree-sitter tree to our format
            return self._tree_sitter_to_dict(tree.root_node, content)
            
        except Exception as e:
            logger.warning(f"Tree-sitter parsing failed: {e}")
            return None
    
    def _tree_sitter_to_dict(self, node, content: str) -> Dict[str, Any]:
        """Convert tree-sitter node to dictionary format."""
        result = {
            'type': node.type,
            'start_point': node.start_point,
            'end_point': node.end_point,
            'text': content[node.start_byte:node.end_byte] if node.start_byte < len(content) else '',
            'children': []
        }
        
        for child in node.children:
            result['children'].append(self._tree_sitter_to_dict(child, content))
        
        return result
    
    def _parse_with_regex(self, content: str, language: str) -> Dict[str, Any]:
        """Fallback parsing using regular expressions."""
        logger.info("Using regex fallback for JavaScript/TypeScript parsing")
        
        # This is a simplified fallback - in production, you'd want more robust parsing
        return {
            'type': 'program',
            'content': content,
            'language': language,
            'fallback': True
        }
    
    def _extract_functions(self, ast_data: Dict[str, Any], content: str) -> List[Function]:
        """Extract function definitions from AST."""
        functions = []
        
        if ast_data.get('fallback'):
            # Use regex fallback
            functions.extend(self._extract_functions_regex(content))
        else:
            # Use tree-sitter data
            functions.extend(self._extract_functions_tree_sitter(ast_data, content))
        
        return functions
    
    def _extract_functions_regex(self, content: str) -> List[Function]:
        """Extract functions using regex patterns."""
        functions = []
        lines = content.splitlines()
        
        # Patterns for different function types
        patterns = [
            # Regular function: function name(params) { }
            r'^\s*function\s+(\w+)\s*\(([^)]*)\)\s*\{',
            # Arrow function: const name = (params) => { }
            r'^\s*(?:const|let|var)\s+(\w+)\s*=\s*\(([^)]*)\)\s*=>\s*\{',
            # Arrow function: const name = params => { }
            r'^\s*(?:const|let|var)\s+(\w+)\s*=\s*(\w+)\s*=>\s*\{',
            # Method: name(params) { }
            r'^\s*(\w+)\s*\(([^)]*)\)\s*\{',
            # Async function: async function name(params) { }
            r'^\s*async\s+function\s+(\w+)\s*\(([^)]*)\)\s*\{',
        ]
        
        for line_num, line in enumerate(lines, 1):
            for pattern in patterns:
                match = re.match(pattern, line)
                if match:
                    name = match.group(1)
                    params_str = match.group(2) if len(match.groups()) > 1 else ''
                    
                    # Parse parameters
                    parameters = []
                    if params_str.strip():
                        params = [p.strip() for p in params_str.split(',')]
                        for param in params:
                            # Handle TypeScript types and default values
                            param_name = param.split(':')[0].split('=')[0].strip()
                            if param_name:
                                parameters.append(param_name)
                    
                    # Find function end (simplified)
                    end_line = self._find_function_end(lines, line_num - 1)
                    
                    # Check if async
                    is_async = 'async' in line
                    
                    # Calculate basic complexity
                    func_content = '\n'.join(lines[line_num-1:end_line])
                    complexity = self._calculate_js_complexity(func_content)
                    
                    function = Function(
                        name=name,
                        line_start=line_num,
                        line_end=end_line + 1,
                        parameters=parameters,
                        return_type=None,  # Would need TypeScript analysis
                        docstring=self._extract_jsdoc(lines, line_num - 1),
                        complexity=complexity,
                        is_async=is_async,
                        is_method=False,  # Would need class context
                        decorators=[]
                    )
                    functions.append(function)
                    break
        
        return functions
    
    def _extract_functions_tree_sitter(self, ast_data: Dict[str, Any], content: str) -> List[Function]:
        """Extract functions using tree-sitter AST."""
        functions = []
        
        def traverse(node):
            if node['type'] in ['function_declaration', 'arrow_function', 'method_definition']:
                func = self._create_function_from_ts_node(node, content)
                if func:
                    functions.append(func)
            
            for child in node.get('children', []):
                traverse(child)
        
        traverse(ast_data)
        return functions
    
    def _create_function_from_ts_node(self, node: Dict[str, Any], content: str) -> Optional[Function]:
        """Create Function object from tree-sitter node."""
        try:
            # Extract function name
            name = self._extract_function_name(node)
            if not name:
                return None
            
            # Extract parameters
            parameters = self._extract_function_parameters(node)
            
            # Extract line numbers
            start_line = node['start_point'][0] + 1
            end_line = node['end_point'][0] + 1
            
            # Check if async
            is_async = 'async' in node.get('text', '')
            
            # Extract JSDoc
            docstring = self._extract_jsdoc_from_node(node, content)
            
            # Calculate complexity
            complexity = self._calculate_js_complexity(node.get('text', ''))
            
            return Function(
                name=name,
                line_start=start_line,
                line_end=end_line,
                parameters=parameters,
                return_type=None,
                docstring=docstring,
                complexity=complexity,
                is_async=is_async,
                is_method=node['type'] == 'method_definition',
                decorators=[]
            )
            
        except Exception as e:
            logger.warning(f"Failed to create function from node: {e}")
            return None
    
    def _extract_classes(self, ast_data: Dict[str, Any], content: str) -> List[Class]:
        """Extract class definitions from AST."""
        classes = []
        
        if ast_data.get('fallback'):
            classes.extend(self._extract_classes_regex(content))
        else:
            classes.extend(self._extract_classes_tree_sitter(ast_data, content))
        
        return classes
    
    def _extract_classes_regex(self, content: str) -> List[Class]:
        """Extract classes using regex patterns."""
        classes = []
        lines = content.splitlines()
        
        # Pattern for class declaration
        class_pattern = r'^\s*class\s+(\w+)(?:\s+extends\s+(\w+))?\s*\{'
        
        for line_num, line in enumerate(lines, 1):
            match = re.match(class_pattern, line)
            if match:
                name = match.group(1)
                base_class = match.group(2) if match.group(2) else None
                
                # Find class end
                end_line = self._find_class_end(lines, line_num - 1)
                
                # Extract methods (simplified)
                class_content = '\n'.join(lines[line_num-1:end_line])
                methods = self._extract_methods_from_class(class_content, line_num)
                
                # Extract JSDoc
                docstring = self._extract_jsdoc(lines, line_num - 1)
                
                cls = Class(
                    name=name,
                    line_start=line_num,
                    line_end=end_line + 1,
                    methods=methods,
                    base_classes=[base_class] if base_class else [],
                    docstring=docstring,
                    decorators=[]
                )
                classes.append(cls)
        
        return classes
    
    def _extract_classes_tree_sitter(self, ast_data: Dict[str, Any], content: str) -> List[Class]:
        """Extract classes using tree-sitter AST."""
        classes = []
        
        def traverse(node):
            if node['type'] == 'class_declaration':
                cls = self._create_class_from_ts_node(node, content)
                if cls:
                    classes.append(cls)
            
            for child in node.get('children', []):
                traverse(child)
        
        traverse(ast_data)
        return classes
    
    def _create_class_from_ts_node(self, node: Dict[str, Any], content: str) -> Optional[Class]:
        """Create Class object from tree-sitter node."""
        try:
            # Extract class name
            name = self._extract_class_name(node)
            if not name:
                return None
            
            # Extract base classes
            base_classes = self._extract_base_classes(node)
            
            # Extract line numbers
            start_line = node['start_point'][0] + 1
            end_line = node['end_point'][0] + 1
            
            # Extract methods
            methods = []
            for child in node.get('children', []):
                if child['type'] == 'method_definition':
                    method = self._create_function_from_ts_node(child, content)
                    if method:
                        method.is_method = True
                        method.class_name = name
                        methods.append(method)
            
            # Extract JSDoc
            docstring = self._extract_jsdoc_from_node(node, content)
            
            return Class(
                name=name,
                line_start=start_line,
                line_end=end_line,
                methods=methods,
                base_classes=base_classes,
                docstring=docstring,
                decorators=[]
            )
            
        except Exception as e:
            logger.warning(f"Failed to create class from node: {e}")
            return None
    
    def _extract_imports(self, ast_data: Dict[str, Any], content: str) -> List[Import]:
        """Extract import statements from AST."""
        imports = []
        
        if ast_data.get('fallback'):
            imports.extend(self._extract_imports_regex(content))
        else:
            imports.extend(self._extract_imports_tree_sitter(ast_data, content))
        
        return imports
    
    def _extract_imports_regex(self, content: str) -> List[Import]:
        """Extract imports using regex patterns."""
        imports = []
        lines = content.splitlines()
        
        # Patterns for different import types
        patterns = [
            # import module from 'path'
            r'^\s*import\s+(\w+)\s+from\s+[\'"]([^\'"]+)[\'"]',
            # import { name1, name2 } from 'path'
            r'^\s*import\s+\{\s*([^}]+)\s*\}\s+from\s+[\'"]([^\'"]+)[\'"]',
            # import * as name from 'path'
            r'^\s*import\s+\*\s+as\s+(\w+)\s+from\s+[\'"]([^\'"]+)[\'"]',
            # import 'path'
            r'^\s*import\s+[\'"]([^\'"]+)[\'"]',
            # const module = require('path')
            r'^\s*(?:const|let|var)\s+(\w+)\s*=\s*require\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)',
        ]
        
        for line_num, line in enumerate(lines, 1):
            for pattern in patterns:
                match = re.match(pattern, line)
                if match:
                    if len(match.groups()) == 1:
                        # import 'path' - no names
                        module = match.group(1)
                        import_obj = Import(
                            module=module,
                            names=[],
                            alias=None,
                            is_from_import=True,
                            line_number=line_num
                        )
                    elif '{' in line:
                        # Named imports
                        names_str = match.group(1)
                        module = match.group(2)
                        names = [n.strip() for n in names_str.split(',')]
                        import_obj = Import(
                            module=module,
                            names=names,
                            alias=None,
                            is_from_import=True,
                            line_number=line_num
                        )
                    else:
                        # Default or namespace import
                        name = match.group(1)
                        module = match.group(2)
                        import_obj = Import(
                            module=module,
                            names=[name],
                            alias=None,
                            is_from_import=True,
                            line_number=line_num
                        )
                    
                    imports.append(import_obj)
                    break
        
        return imports
    
    def _extract_imports_tree_sitter(self, ast_data: Dict[str, Any], content: str) -> List[Import]:
        """Extract imports using tree-sitter AST."""
        imports = []
        
        def traverse(node):
            if node['type'] in ['import_statement', 'import_declaration']:
                import_obj = self._create_import_from_ts_node(node, content)
                if import_obj:
                    imports.append(import_obj)
            
            for child in node.get('children', []):
                traverse(child)
        
        traverse(ast_data)
        return imports
    
    def _calculate_js_complexity(self, code: str) -> int:
        """Calculate cyclomatic complexity for JavaScript/TypeScript code."""
        complexity = 1  # Base complexity
        
        # Count decision points
        decision_keywords = [
            'if', 'else if', 'while', 'for', 'switch', 'case',
            'catch', 'try', '&&', '||', '?', 'do'
        ]
        
        for keyword in decision_keywords:
            if keyword in ['&&', '||', '?']:
                # Count occurrences of logical operators
                complexity += code.count(keyword)
            else:
                # Count keyword occurrences (simple approach)
                complexity += len(re.findall(r'\b' + keyword + r'\b', code))
        
        return complexity
    
    def _find_function_end(self, lines: List[str], start_line: int) -> int:
        """Find the end line of a function (simplified brace matching)."""
        brace_count = 0
        for i, line in enumerate(lines[start_line:], start_line):
            brace_count += line.count('{') - line.count('}')
            if brace_count == 0 and '{' in lines[start_line]:
                return i
        return len(lines) - 1
    
    def _find_class_end(self, lines: List[str], start_line: int) -> int:
        """Find the end line of a class (simplified brace matching)."""
        return self._find_function_end(lines, start_line)
    
    def _extract_jsdoc(self, lines: List[str], line_num: int) -> Optional[str]:
        """Extract JSDoc comment before a function/class."""
        # Look backwards for JSDoc comment
        for i in range(line_num - 1, max(0, line_num - 10), -1):
            line = lines[i].strip()
            if line.startswith('/**'):
                # Found start of JSDoc, collect until */
                jsdoc_lines = []
                for j in range(i, line_num):
                    doc_line = lines[j].strip()
                    if doc_line.startswith('*'):
                        doc_line = doc_line[1:].strip()
                    jsdoc_lines.append(doc_line)
                    if '*/' in doc_line:
                        break
                return '\n'.join(jsdoc_lines).replace('/**', '').replace('*/', '').strip()
            elif line and not line.startswith('//'):
                # Hit non-comment line
                break
        return None
    
    def _extract_methods_from_class(self, class_content: str, class_start_line: int) -> List[Function]:
        """Extract methods from class content."""
        methods = []
        lines = class_content.splitlines()
        
        # Simple method pattern
        method_pattern = r'^\s*(\w+)\s*\(([^)]*)\)\s*\{'
        
        for line_num, line in enumerate(lines, class_start_line):
            match = re.match(method_pattern, line)
            if match and not line.strip().startswith('//'):
                name = match.group(1)
                params_str = match.group(2)
                
                # Skip class declaration line
                if name == 'class':
                    continue
                
                parameters = []
                if params_str.strip():
                    params = [p.strip().split(':')[0].split('=')[0].strip() 
                             for p in params_str.split(',')]
                    parameters = [p for p in params if p]
                
                end_line = self._find_function_end(lines, line_num - class_start_line)
                
                method = Function(
                    name=name,
                    line_start=line_num,
                    line_end=class_start_line + end_line,
                    parameters=parameters,
                    is_method=True,
                    complexity=1
                )
                methods.append(method)
        
        return methods
    
    def _extract_function_name(self, node: Dict[str, Any]) -> Optional[str]:
        """Extract function name from tree-sitter node."""
        # This would need proper tree-sitter node traversal
        text = node.get('text', '')
        match = re.search(r'function\s+(\w+)', text)
        if match:
            return match.group(1)
        
        # Try arrow function pattern
        match = re.search(r'(\w+)\s*=\s*\(.*?\)\s*=>', text)
        if match:
            return match.group(1)
        
        return None
    
    def _extract_function_parameters(self, node: Dict[str, Any]) -> List[str]:
        """Extract function parameters from tree-sitter node."""
        # Simplified parameter extraction
        text = node.get('text', '')
        match = re.search(r'\(([^)]*)\)', text)
        if match:
            params_str = match.group(1)
            if params_str.strip():
                return [p.strip().split(':')[0].split('=')[0].strip() 
                       for p in params_str.split(',')]
        return []
    
    def _extract_class_name(self, node: Dict[str, Any]) -> Optional[str]:
        """Extract class name from tree-sitter node."""
        text = node.get('text', '')
        match = re.search(r'class\s+(\w+)', text)
        return match.group(1) if match else None
    
    def _extract_base_classes(self, node: Dict[str, Any]) -> List[str]:
        """Extract base classes from tree-sitter node."""
        text = node.get('text', '')
        match = re.search(r'extends\s+(\w+)', text)
        return [match.group(1)] if match else []
    
    def _extract_jsdoc_from_node(self, node: Dict[str, Any], content: str) -> Optional[str]:
        """Extract JSDoc from tree-sitter node."""
        # This would need proper implementation with tree-sitter
        return None
    
    def _create_import_from_ts_node(self, node: Dict[str, Any], content: str) -> Optional[Import]:
        """Create Import object from tree-sitter node."""
        # Simplified import extraction
        text = node.get('text', '')
        
        # Extract module path
        module_match = re.search(r'from\s+[\'"]([^\'"]+)[\'"]', text)
        if not module_match:
            module_match = re.search(r'import\s+[\'"]([^\'"]+)[\'"]', text)
        
        if not module_match:
            return None
        
        module = module_match.group(1)
        line_number = node['start_point'][0] + 1
        
        # Extract imported names
        names = []
        if '{' in text:
            names_match = re.search(r'\{([^}]+)\}', text)
            if names_match:
                names = [n.strip() for n in names_match.group(1).split(',')]
        
        return Import(
            module=module,
            names=names,
            alias=None,
            is_from_import=True,
            line_number=line_number
        )
    
    def extract_dependencies(self, parsed_files: List[ParsedFile]) -> DependencyGraph:
        """Extract dependencies between JavaScript/TypeScript files."""
        graph = DependencyGraph()
        
        # Create mapping of module paths to files
        file_to_module = {}
        for parsed_file in parsed_files:
            if parsed_file.language in ['javascript', 'typescript']:
                file_to_module[parsed_file.path] = parsed_file
        
        # Build dependency graph
        for parsed_file in parsed_files:
            if parsed_file.language not in ['javascript', 'typescript']:
                continue
            
            current_file = parsed_file.path
            current_dir = Path(current_file).parent
            
            for import_stmt in parsed_file.imports:
                module_path = import_stmt.module
                
                # Resolve relative imports
                if module_path.startswith('./') or module_path.startswith('../'):
                    resolved_path = (current_dir / module_path).resolve()
                    
                    # Try different extensions
                    for ext in ['.js', '.ts', '.jsx', '.tsx']:
                        candidate = resolved_path.with_suffix(ext)
                        if str(candidate) in file_to_module:
                            graph.add_dependency(current_file, str(candidate))
                            break
                
                # Check for exact matches
                for file_path in file_to_module:
                    file_name = Path(file_path).stem
                    if file_name == module_path or module_path in file_path:
                        graph.add_dependency(current_file, file_path)
        
        return graph