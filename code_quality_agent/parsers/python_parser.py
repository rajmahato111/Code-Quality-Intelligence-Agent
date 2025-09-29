"""Python AST parser for extracting code structure and metadata."""

import ast
from pathlib import Path
from typing import List, Optional, Dict, Any, Set
import logging

from .base import CodeParser
from ..core.models import (
    ParsedFile, Function, Class, Import, FileMetadata,
    DependencyGraph
)
from ..utils.file_utils import read_file_safely

logger = logging.getLogger(__name__)


class PythonParser(CodeParser):
    """Parser for Python source code using AST."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the Python parser."""
        super().__init__(config)
        self.supported_languages = ["python"]
        self.file_extensions = [".py", ".pyw"]
    
    def get_supported_languages(self) -> List[str]:
        """Return list of supported languages."""
        return self.supported_languages
    
    def get_file_extensions(self) -> List[str]:
        """Return list of supported file extensions."""
        return self.file_extensions
    
    def parse_file(self, file_path: Path) -> Optional[ParsedFile]:
        """
        Parse a Python file and extract structured information.
        
        Args:
            file_path: Path to the Python file
            
        Returns:
            ParsedFile object or None if parsing failed
        """
        try:
            # Read file content
            content = read_file_safely(file_path)
            if content is None:
                logger.warning(f"Could not read file: {file_path}")
                return None
            
            # Parse AST
            try:
                tree = ast.parse(content, filename=str(file_path))
            except SyntaxError as e:
                logger.warning(f"Syntax error in {file_path}: {e}")
                return None
            
            # Extract metadata
            metadata = FileMetadata(
                file_path=str(file_path),
                language="python",
                size_bytes=len(content.encode('utf-8')),
                line_count=len(content.splitlines()),
                encoding='utf-8'
            )
            
            # Extract code elements
            functions = self._extract_functions(tree)
            classes = self._extract_classes(tree)
            imports = self._extract_imports(tree)
            
            return ParsedFile(
                path=str(file_path),
                language="python",
                content=content,
                ast=tree,
                metadata=metadata,
                functions=functions,
                classes=classes,
                imports=imports
            )
            
        except Exception as e:
            logger.error(f"Failed to parse {file_path}: {e}")
            return None
    
    def _extract_functions(self, tree: ast.AST) -> List[Function]:
        """Extract function definitions from AST."""
        functions = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func = self._create_function_from_node(node)
                functions.append(func)
        
        return functions
    
    def _create_function_from_node(self, node: ast.FunctionDef) -> Function:
        """Create Function object from AST node."""
        # Extract parameters
        parameters = []
        for arg in node.args.args:
            parameters.append(arg.arg)
        
        # Handle *args and **kwargs
        if node.args.vararg:
            parameters.append(f"*{node.args.vararg.arg}")
        if node.args.kwarg:
            parameters.append(f"**{node.args.kwarg.arg}")
        
        # Extract return type annotation
        return_type = None
        if node.returns:
            return_type = ast.unparse(node.returns) if hasattr(ast, 'unparse') else None
        
        # Extract docstring
        docstring = None
        if (node.body and 
            isinstance(node.body[0], ast.Expr) and 
            isinstance(node.body[0].value, ast.Constant) and
            isinstance(node.body[0].value.value, str)):
            docstring = node.body[0].value.value
        
        # Extract decorators
        decorators = []
        for decorator in node.decorator_list:
            if hasattr(ast, 'unparse'):
                decorators.append(ast.unparse(decorator))
            elif isinstance(decorator, ast.Name):
                decorators.append(decorator.id)
        
        # Calculate complexity
        complexity = self._calculate_cyclomatic_complexity(node)
        
        # Determine if it's a method
        is_method = self._is_method(node)
        class_name = self._get_containing_class(node) if is_method else None
        
        return Function(
            name=node.name,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            parameters=parameters,
            return_type=return_type,
            docstring=docstring,
            complexity=complexity,
            is_async=isinstance(node, ast.AsyncFunctionDef),
            is_method=is_method,
            class_name=class_name,
            decorators=decorators
        )
    
    def _extract_classes(self, tree: ast.AST) -> List[Class]:
        """Extract class definitions from AST."""
        classes = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                cls = self._create_class_from_node(node)
                classes.append(cls)
        
        return classes
    
    def _create_class_from_node(self, node: ast.ClassDef) -> Class:
        """Create Class object from AST node."""
        # Extract base classes
        base_classes = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                base_classes.append(base.id)
            elif hasattr(ast, 'unparse'):
                base_classes.append(ast.unparse(base))
        
        # Extract docstring
        docstring = None
        if (node.body and 
            isinstance(node.body[0], ast.Expr) and 
            isinstance(node.body[0].value, ast.Constant) and
            isinstance(node.body[0].value.value, str)):
            docstring = node.body[0].value.value
        
        # Extract decorators
        decorators = []
        for decorator in node.decorator_list:
            if hasattr(ast, 'unparse'):
                decorators.append(ast.unparse(decorator))
            elif isinstance(decorator, ast.Name):
                decorators.append(decorator.id)
        
        # Extract methods
        methods = []
        for child in node.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                method = self._create_function_from_node(child)
                method.is_method = True
                method.class_name = node.name
                methods.append(method)
        
        return Class(
            name=node.name,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            methods=methods,
            base_classes=base_classes,
            docstring=docstring,
            decorators=decorators
        )
    
    def _extract_imports(self, tree: ast.AST) -> List[Import]:
        """Extract import statements from AST."""
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    import_obj = Import(
                        module=alias.name,
                        names=[],
                        alias=alias.asname,
                        is_from_import=False,
                        line_number=node.lineno
                    )
                    imports.append(import_obj)
            
            elif isinstance(node, ast.ImportFrom):
                if node.module:  # Skip relative imports without module
                    names = [alias.name for alias in node.names]
                    import_obj = Import(
                        module=node.module,
                        names=names,
                        alias=None,
                        is_from_import=True,
                        line_number=node.lineno
                    )
                    imports.append(import_obj)
        
        return imports
    
    def _calculate_cyclomatic_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity for a function."""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            # Decision points that increase complexity
            if isinstance(child, (ast.If, ast.While, ast.For)):
                complexity += 1
            elif hasattr(ast, 'AsyncFor') and isinstance(child, ast.AsyncFor):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.With):
                complexity += 1
            elif hasattr(ast, 'AsyncWith') and isinstance(child, ast.AsyncWith):
                complexity += 1
            elif isinstance(child, ast.Assert):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                # Each additional condition in and/or
                complexity += len(child.values) - 1
            elif isinstance(child, ast.ListComp):
                # List comprehensions add complexity
                complexity += 1
                for generator in child.generators:
                    complexity += len(generator.ifs)
            elif isinstance(child, ast.SetComp):
                complexity += 1
            elif isinstance(child, ast.DictComp):
                complexity += 1
            elif isinstance(child, ast.GeneratorExp):
                complexity += 1
        
        return complexity
    
    def _is_method(self, node: ast.FunctionDef) -> bool:
        """Check if a function is a method (inside a class)."""
        # Walk up the AST to find if this function is inside a class
        # This is a simplified check - in practice, we'd need parent references
        return len(node.args.args) > 0 and node.args.args[0].arg in ('self', 'cls')
    
    def _get_containing_class(self, node: ast.FunctionDef) -> Optional[str]:
        """Get the name of the containing class for a method."""
        # This is a simplified implementation
        # In practice, we'd need to maintain parent-child relationships in the AST
        return None
    
    def extract_dependencies(self, parsed_files: List[ParsedFile]) -> DependencyGraph:
        """Extract dependencies between Python files."""
        graph = DependencyGraph()
        
        # Create a mapping of module names to file paths
        module_to_file = {}
        for parsed_file in parsed_files:
            if parsed_file.language == "python":
                # Convert file path to module name
                module_name = self._file_path_to_module_name(parsed_file.path)
                module_to_file[module_name] = parsed_file.path
        
        # Build dependency graph
        for parsed_file in parsed_files:
            if parsed_file.language != "python":
                continue
            
            current_file = parsed_file.path
            
            for import_stmt in parsed_file.imports:
                # Handle different import types
                if import_stmt.is_from_import:
                    # from module import name
                    imported_module = import_stmt.module
                else:
                    # import module
                    imported_module = import_stmt.module
                
                # Check if this is a local module
                if imported_module in module_to_file:
                    target_file = module_to_file[imported_module]
                    graph.add_dependency(current_file, target_file)
                
                # Handle relative imports and submodules
                for module_name, file_path in module_to_file.items():
                    if (imported_module.startswith(module_name + '.') or 
                        module_name.startswith(imported_module + '.')):
                        graph.add_dependency(current_file, file_path)
        
        return graph
    
    def _file_path_to_module_name(self, file_path: str) -> str:
        """Convert file path to Python module name."""
        path = Path(file_path)
        
        # Remove .py extension
        if path.suffix == '.py':
            path = path.with_suffix('')
        
        # Convert path separators to dots
        parts = path.parts
        
        # Remove common prefixes like 'src', 'lib', etc.
        if parts and parts[0] in ('src', 'lib', 'app'):
            parts = parts[1:]
        
        return '.'.join(parts)
    
    def get_complexity_metrics(self, parsed_file: ParsedFile) -> Dict[str, Any]:
        """Calculate various complexity metrics for a Python file."""
        if not parsed_file.ast:
            return {}
        
        total_complexity = 0
        max_complexity = 0
        function_count = len(parsed_file.functions)
        class_count = len(parsed_file.classes)
        
        # Calculate total and max complexity
        for func in parsed_file.functions:
            total_complexity += func.complexity
            max_complexity = max(max_complexity, func.complexity)
        
        # Calculate nesting depth
        max_nesting = self._calculate_max_nesting_depth(parsed_file.ast)
        
        # Lines of code (excluding comments and blank lines)
        loc = self._count_lines_of_code(parsed_file.content)
        
        return {
            "cyclomatic_complexity": total_complexity / max(function_count, 1),
            "max_complexity": max_complexity,
            "total_complexity": total_complexity,
            "function_count": function_count,
            "class_count": class_count,
            "max_nesting_depth": max_nesting,
            "lines_of_code": loc,
            "maintainability_index": self._calculate_maintainability_index(
                total_complexity, loc, function_count
            )
        }
    
    def _calculate_max_nesting_depth(self, tree: ast.AST) -> int:
        """Calculate maximum nesting depth in the AST."""
        def get_depth(node: ast.AST, current_depth: int = 0) -> int:
            max_depth = current_depth
            
            # Nodes that increase nesting depth
            nesting_nodes = [ast.If, ast.While, ast.For, ast.With, ast.Try, ast.FunctionDef, ast.ClassDef]
            
            # Add async nodes if they exist in this Python version
            if hasattr(ast, 'AsyncFor'):
                nesting_nodes.append(ast.AsyncFor)
            if hasattr(ast, 'AsyncWith'):
                nesting_nodes.append(ast.AsyncWith)
            if hasattr(ast, 'AsyncFunctionDef'):
                nesting_nodes.append(ast.AsyncFunctionDef)
            
            if isinstance(node, tuple(nesting_nodes)):
                current_depth += 1
            
            # Recursively check children
            for child in ast.iter_child_nodes(node):
                child_depth = get_depth(child, current_depth)
                max_depth = max(max_depth, child_depth)
            
            return max_depth
        
        return get_depth(tree)
    
    def _count_lines_of_code(self, content: str) -> int:
        """Count non-empty, non-comment lines of code."""
        lines = content.splitlines()
        loc = 0
        
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith('#'):
                loc += 1
        
        return loc
    
    def _calculate_maintainability_index(
        self, 
        complexity: int, 
        loc: int, 
        function_count: int
    ) -> float:
        """Calculate maintainability index (simplified version)."""
        import math
        
        if loc == 0:
            return 100.0
        
        # Simplified maintainability index calculation
        # MI = 171 - 5.2 * ln(Halstead Volume) - 0.23 * (Cyclomatic Complexity) - 16.2 * ln(Lines of Code)
        # Using simplified approximation
        
        avg_complexity = complexity / max(function_count, 1)
        
        mi = 171 - 0.23 * avg_complexity - 16.2 * math.log(loc)
        
        # Normalize to 0-100 scale
        return max(0, min(100, mi))