"""
Dependency graph generation and analysis using NetworkX.
"""

import ast
import re
import logging
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass
from collections import defaultdict
import networkx as nx

logger = logging.getLogger(__name__)


@dataclass
class DependencyInfo:
    """Information about a dependency relationship."""
    source: str
    target: str
    dependency_type: str  # 'import', 'function_call', 'class_inheritance', etc.
    line_number: Optional[int] = None
    context: Optional[str] = None


@dataclass
class CircularDependency:
    """Information about a circular dependency."""
    cycle: List[str]
    cycle_length: int
    severity: str  # 'low', 'medium', 'high'
    description: str


@dataclass
class DependencyMetrics:
    """Metrics about the dependency graph."""
    total_nodes: int
    total_edges: int
    circular_dependencies: List[CircularDependency]
    strongly_connected_components: List[List[str]]
    max_depth: int
    average_degree: float
    density: float
    modularity: float


class DependencyGraphGenerator:
    """Generates dependency graphs from source code."""
    
    def __init__(self):
        """Initialize the dependency graph generator."""
        self.graph = nx.DiGraph()
        self.dependencies = []
        self.file_imports = defaultdict(set)
        self.function_calls = defaultdict(set)
        self.class_inheritance = defaultdict(set)
    
    def analyze_codebase(self, codebase_path: str, include_patterns: List[str] = None) -> nx.DiGraph:
        """
        Analyze a codebase and generate a dependency graph.
        
        Args:
            codebase_path: Path to the codebase
            include_patterns: File patterns to include (e.g., ['*.py', '*.js'])
            
        Returns:
            NetworkX directed graph representing dependencies
        """
        if include_patterns is None:
            include_patterns = ['*.py']
        
        codebase_dir = Path(codebase_path)
        
        # Discover files to analyze
        files_to_analyze = []
        for pattern in include_patterns:
            files_to_analyze.extend(codebase_dir.rglob(pattern))
        
        logger.info(f"Analyzing {len(files_to_analyze)} files for dependencies")
        
        # Analyze each file
        for file_path in files_to_analyze:
            try:
                self._analyze_file(file_path, codebase_dir)
            except Exception as e:
                logger.warning(f"Failed to analyze {file_path}: {e}")
        
        # Build the graph
        self._build_graph()
        
        logger.info(f"Generated dependency graph with {self.graph.number_of_nodes()} nodes and {self.graph.number_of_edges()} edges")
        
        return self.graph
    
    def _analyze_file(self, file_path: Path, codebase_dir: Path):
        """Analyze a single file for dependencies."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logger.warning(f"Could not read {file_path}: {e}")
            return
        
        # Get relative path for consistent naming
        relative_path = str(file_path.relative_to(codebase_dir))
        
        # Analyze based on file extension
        if file_path.suffix == '.py':
            self._analyze_python_file(relative_path, content)
        elif file_path.suffix in ['.js', '.ts']:
            self._analyze_javascript_file(relative_path, content)
        # Add more language support as needed
    
    def _analyze_python_file(self, file_path: str, content: str):
        """Analyze Python file for dependencies."""
        try:
            tree = ast.parse(content)
            
            # Extract imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self._add_dependency(
                            file_path, 
                            alias.name, 
                            'import', 
                            node.lineno,
                            f"import {alias.name}"
                        )
                        self.file_imports[file_path].add(alias.name)
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        self._add_dependency(
                            file_path, 
                            node.module, 
                            'import', 
                            node.lineno,
                            f"from {node.module} import ..."
                        )
                        self.file_imports[file_path].add(node.module)
                
                elif isinstance(node, ast.ClassDef):
                    # Extract class inheritance
                    for base in node.bases:
                        if isinstance(base, ast.Name):
                            self._add_dependency(
                                file_path,
                                base.id,
                                'class_inheritance',
                                node.lineno,
                                f"class {node.name}({base.id})"
                            )
                            self.class_inheritance[file_path].add(base.id)
                
                elif isinstance(node, ast.Call):
                    # Extract function calls (simplified)
                    if isinstance(node.func, ast.Name):
                        self.function_calls[file_path].add(node.func.id)
                    elif isinstance(node.func, ast.Attribute):
                        if isinstance(node.func.value, ast.Name):
                            call_target = f"{node.func.value.id}.{node.func.attr}"
                            self.function_calls[file_path].add(call_target)
        
        except SyntaxError as e:
            logger.warning(f"Syntax error in {file_path}: {e}")
        except Exception as e:
            logger.warning(f"Error analyzing Python file {file_path}: {e}")
    
    def _analyze_javascript_file(self, file_path: str, content: str):
        """Analyze JavaScript/TypeScript file for dependencies (simplified regex-based)."""
        try:
            # Extract ES6 imports
            import_patterns = [
                r"import\s+.*?\s+from\s+['\"]([^'\"]+)['\"]",
                r"import\s+['\"]([^'\"]+)['\"]",
                r"const\s+.*?\s*=\s*require\s*\(\s*['\"]([^'\"]+)['\"]\s*\)",
                r"require\s*\(\s*['\"]([^'\"]+)['\"]\s*\)"
            ]
            
            for pattern in import_patterns:
                matches = re.finditer(pattern, content, re.MULTILINE)
                for match in matches:
                    module_name = match.group(1)
                    line_number = content[:match.start()].count('\n') + 1
                    
                    self._add_dependency(
                        file_path,
                        module_name,
                        'import',
                        line_number,
                        match.group(0)
                    )
                    self.file_imports[file_path].add(module_name)
        
        except Exception as e:
            logger.warning(f"Error analyzing JavaScript file {file_path}: {e}")
    
    def _add_dependency(self, source: str, target: str, dep_type: str, 
                       line_number: Optional[int] = None, context: Optional[str] = None):
        """Add a dependency to the collection."""
        dependency = DependencyInfo(
            source=source,
            target=target,
            dependency_type=dep_type,
            line_number=line_number,
            context=context
        )
        self.dependencies.append(dependency)
    
    def _build_graph(self):
        """Build the NetworkX graph from collected dependencies."""
        # Add all files as nodes
        all_files = set()
        for dep in self.dependencies:
            all_files.add(dep.source)
        
        # Create a mapping of module names to file paths
        module_to_file = {}
        for file_path in all_files:
            # Extract module name from file path
            module_name = Path(file_path).stem
            module_to_file[module_name] = file_path
            
            # Also handle dotted imports (e.g., models.user -> models/user.py)
            if '/' in file_path:
                parts = file_path.replace('/', '.').replace('.py', '')
                module_to_file[parts] = file_path
        
        for file_path in all_files:
            self.graph.add_node(file_path, type='file')
        
        # Add dependencies as edges
        for dep in self.dependencies:
            target_file = None
            
            # Try to resolve target to a file path
            if dep.target in all_files:
                # Direct file path match
                target_file = dep.target
            elif dep.target in module_to_file:
                # Module name match
                target_file = module_to_file[dep.target]
            elif dep.target.endswith(('.py', '.js', '.ts')):
                # Target looks like a file
                target_file = dep.target
                if target_file not in all_files:
                    self.graph.add_node(target_file, type='file')
            
            # Create edge if we found a target file
            if target_file and target_file != dep.source:
                self.graph.add_edge(
                    dep.source, 
                    target_file,
                    dependency_type=dep.dependency_type,
                    line_number=dep.line_number,
                    context=dep.context
                )
    
    def get_dependencies(self) -> List[DependencyInfo]:
        """Get all collected dependencies."""
        return self.dependencies
    
    def get_file_imports(self) -> Dict[str, Set[str]]:
        """Get imports by file."""
        return dict(self.file_imports)


class DependencyAnalyzer:
    """Analyzes dependency graphs for patterns and issues."""
    
    def __init__(self, graph: nx.DiGraph):
        """Initialize with a dependency graph."""
        self.graph = graph
    
    def find_circular_dependencies(self) -> List[CircularDependency]:
        """Find circular dependencies in the graph."""
        circular_deps = []
        
        try:
            # Find all simple cycles
            cycles = list(nx.simple_cycles(self.graph))
            
            for cycle in cycles:
                severity = self._assess_cycle_severity(cycle)
                description = self._generate_cycle_description(cycle)
                
                circular_deps.append(CircularDependency(
                    cycle=cycle,
                    cycle_length=len(cycle),
                    severity=severity,
                    description=description
                ))
            
            # Sort by severity and cycle length
            circular_deps.sort(key=lambda x: (
                {'high': 3, 'medium': 2, 'low': 1}[x.severity],
                x.cycle_length
            ), reverse=True)
        
        except Exception as e:
            logger.error(f"Error finding circular dependencies: {e}")
        
        return circular_deps
    
    def _assess_cycle_severity(self, cycle: List[str]) -> str:
        """Assess the severity of a circular dependency."""
        cycle_length = len(cycle)
        
        # Longer cycles are generally more problematic
        if cycle_length >= 5:
            return 'high'
        elif cycle_length >= 3:
            return 'medium'
        else:
            return 'low'
    
    def _generate_cycle_description(self, cycle: List[str]) -> str:
        """Generate a description for a circular dependency."""
        if len(cycle) == 2:
            return f"Direct circular dependency between {cycle[0]} and {cycle[1]}"
        else:
            cycle_str = " → ".join(cycle + [cycle[0]])
            return f"Circular dependency chain: {cycle_str}"
    
    def get_strongly_connected_components(self) -> List[List[str]]:
        """Get strongly connected components."""
        try:
            return list(nx.strongly_connected_components(self.graph))
        except Exception as e:
            logger.error(f"Error finding strongly connected components: {e}")
            return []
    
    def calculate_metrics(self) -> DependencyMetrics:
        """Calculate comprehensive metrics about the dependency graph."""
        try:
            # Basic graph metrics
            total_nodes = self.graph.number_of_nodes()
            total_edges = self.graph.number_of_edges()
            
            # Circular dependencies
            circular_deps = self.find_circular_dependencies()
            
            # Strongly connected components
            scc = self.get_strongly_connected_components()
            
            # Graph depth (longest path)
            max_depth = 0
            if nx.is_directed_acyclic_graph(self.graph):
                try:
                    max_depth = nx.dag_longest_path_length(self.graph)
                except:
                    max_depth = 0
            
            # Average degree
            degrees = [d for n, d in self.graph.degree()]
            average_degree = sum(degrees) / len(degrees) if degrees else 0
            
            # Graph density
            density = nx.density(self.graph)
            
            # Modularity (simplified calculation)
            modularity = 0.0
            try:
                # Convert to undirected for modularity calculation
                undirected = self.graph.to_undirected()
                if undirected.number_of_edges() > 0:
                    communities = nx.community.greedy_modularity_communities(undirected)
                    modularity = nx.community.modularity(undirected, communities)
            except Exception as e:
                logger.warning(f"Could not calculate modularity: {e}")
            
            return DependencyMetrics(
                total_nodes=total_nodes,
                total_edges=total_edges,
                circular_dependencies=circular_deps,
                strongly_connected_components=scc,
                max_depth=max_depth,
                average_degree=average_degree,
                density=density,
                modularity=modularity
            )
        
        except Exception as e:
            logger.error(f"Error calculating dependency metrics: {e}")
            return DependencyMetrics(
                total_nodes=0,
                total_edges=0,
                circular_dependencies=[],
                strongly_connected_components=[],
                max_depth=0,
                average_degree=0.0,
                density=0.0,
                modularity=0.0
            )
    
    def get_most_connected_nodes(self, top_n: int = 10) -> List[Tuple[str, int]]:
        """Get the most connected nodes (highest degree)."""
        try:
            degrees = self.graph.degree()
            sorted_degrees = sorted(degrees, key=lambda x: x[1], reverse=True)
            return sorted_degrees[:top_n]
        except Exception as e:
            logger.error(f"Error getting most connected nodes: {e}")
            return []
    
    def get_dependency_depth(self, node: str) -> int:
        """Get the maximum dependency depth from a given node."""
        try:
            if node not in self.graph:
                return 0
            
            # Use BFS to find maximum depth
            max_depth = 0
            visited = set()
            queue = [(node, 0)]
            
            while queue:
                current_node, depth = queue.pop(0)
                if current_node in visited:
                    continue
                
                visited.add(current_node)
                max_depth = max(max_depth, depth)
                
                # Add successors to queue
                for successor in self.graph.successors(current_node):
                    if successor not in visited:
                        queue.append((successor, depth + 1))
            
            return max_depth
        
        except Exception as e:
            logger.error(f"Error calculating dependency depth for {node}: {e}")
            return 0
    
    def find_dependency_hotspots(self) -> List[Dict[str, Any]]:
        """Find dependency hotspots (nodes with high in-degree and out-degree)."""
        hotspots = []
        
        try:
            for node in self.graph.nodes():
                in_degree = self.graph.in_degree(node)
                out_degree = self.graph.out_degree(node)
                total_degree = in_degree + out_degree
                
                if total_degree > 0:
                    hotspots.append({
                        'node': node,
                        'in_degree': in_degree,
                        'out_degree': out_degree,
                        'total_degree': total_degree,
                        'dependency_depth': self.get_dependency_depth(node)
                    })
            
            # Sort by total degree
            hotspots.sort(key=lambda x: x['total_degree'], reverse=True)
        
        except Exception as e:
            logger.error(f"Error finding dependency hotspots: {e}")
        
        return hotspots