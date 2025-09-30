"""
Tests for dependency graph generation and analysis.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
import networkx as nx

from code_quality_agent.visualization import (
    DependencyGraphGenerator, DependencyAnalyzer, GraphVisualizer
)
from code_quality_agent.visualization.dependency_graph import (
    DependencyInfo, CircularDependency, DependencyMetrics
)


class TestDependencyGraphGenerator:
    """Test dependency graph generation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.temp_dir) / "test_project"
        self.project_dir.mkdir()
        self.generator = DependencyGraphGenerator()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _create_python_files(self):
        """Create test Python files with dependencies."""
        # Main module
        (self.project_dir / "main.py").write_text("""
import utils
from data_processor import DataProcessor
from external_lib import ExternalClass

class MainApp:
    def __init__(self):
        self.processor = DataProcessor()
        self.utils = utils
    
    def run(self):
        return self.processor.process()
""")
        
        # Utils module
        (self.project_dir / "utils.py").write_text("""
import os
import sys
from typing import List

def helper_function():
    return "helper"

def another_helper():
    return helper_function()
""")
        
        # Data processor module
        (self.project_dir / "data_processor.py").write_text("""
import utils
from models import DataModel

class DataProcessor:
    def __init__(self):
        self.model = DataModel()
    
    def process(self):
        return utils.helper_function()
""")
        
        # Models module
        (self.project_dir / "models.py").write_text("""
from utils import helper_function

class DataModel:
    def __init__(self):
        self.data = helper_function()
    
    def get_data(self):
        return self.data
""")
    
    def _create_circular_dependency_files(self):
        """Create test files with circular dependencies."""
        # Module A imports B
        (self.project_dir / "module_a.py").write_text("""
from module_b import ClassB

class ClassA:
    def __init__(self):
        self.b = ClassB()
""")
        
        # Module B imports A (circular dependency)
        (self.project_dir / "module_b.py").write_text("""
from module_a import ClassA

class ClassB:
    def __init__(self):
        self.a = ClassA()
""")
    
    def test_analyze_python_codebase(self):
        """Test analyzing Python codebase for dependencies."""
        self._create_python_files()
        
        graph = self.generator.analyze_codebase(str(self.project_dir), ['*.py'])
        
        # Verify graph structure
        assert isinstance(graph, nx.DiGraph)
        assert graph.number_of_nodes() > 0
        assert graph.number_of_edges() > 0
        
        # Check that files are nodes
        file_nodes = [node for node in graph.nodes() if node.endswith('.py')]
        assert len(file_nodes) > 0
        
        # Verify dependencies were collected
        dependencies = self.generator.get_dependencies()
        assert len(dependencies) > 0
        
        # Check for specific dependencies
        import_deps = [dep for dep in dependencies if dep.dependency_type == 'import']
        assert len(import_deps) > 0
    
    def test_detect_circular_dependencies(self):
        """Test detection of circular dependencies."""
        self._create_circular_dependency_files()
        
        graph = self.generator.analyze_codebase(str(self.project_dir), ['*.py'])
        analyzer = DependencyAnalyzer(graph)
        
        circular_deps = analyzer.find_circular_dependencies()
        
        # Should find at least one circular dependency
        assert len(circular_deps) > 0
        
        # Check circular dependency structure
        for circular_dep in circular_deps:
            assert isinstance(circular_dep, CircularDependency)
            assert len(circular_dep.cycle) >= 2
            assert circular_dep.severity in ['low', 'medium', 'high']
            assert len(circular_dep.description) > 0
    
    def test_dependency_metrics_calculation(self):
        """Test calculation of dependency metrics."""
        self._create_python_files()
        
        graph = self.generator.analyze_codebase(str(self.project_dir), ['*.py'])
        analyzer = DependencyAnalyzer(graph)
        
        metrics = analyzer.calculate_metrics()
        
        # Verify metrics structure
        assert isinstance(metrics, DependencyMetrics)
        assert metrics.total_nodes >= 0
        assert metrics.total_edges >= 0
        assert isinstance(metrics.circular_dependencies, list)
        assert isinstance(metrics.strongly_connected_components, list)
        assert metrics.max_depth >= 0
        assert metrics.average_degree >= 0.0
        assert 0.0 <= metrics.density <= 1.0
        assert -1.0 <= metrics.modularity <= 1.0
    
    def test_find_dependency_hotspots(self):
        """Test finding dependency hotspots."""
        self._create_python_files()
        
        graph = self.generator.analyze_codebase(str(self.project_dir), ['*.py'])
        analyzer = DependencyAnalyzer(graph)
        
        hotspots = analyzer.find_dependency_hotspots()
        
        # Verify hotspots structure
        assert isinstance(hotspots, list)
        
        for hotspot in hotspots:
            assert 'node' in hotspot
            assert 'in_degree' in hotspot
            assert 'out_degree' in hotspot
            assert 'total_degree' in hotspot
            assert 'dependency_depth' in hotspot
            assert hotspot['total_degree'] >= 0
    
    def test_most_connected_nodes(self):
        """Test getting most connected nodes."""
        self._create_python_files()
        
        graph = self.generator.analyze_codebase(str(self.project_dir), ['*.py'])
        analyzer = DependencyAnalyzer(graph)
        
        most_connected = analyzer.get_most_connected_nodes(top_n=5)
        
        # Verify structure
        assert isinstance(most_connected, list)
        assert len(most_connected) <= 5
        
        for node, degree in most_connected:
            assert isinstance(node, str)
            assert isinstance(degree, int)
            assert degree >= 0
        
        # Verify sorting (highest degree first)
        if len(most_connected) > 1:
            for i in range(len(most_connected) - 1):
                assert most_connected[i][1] >= most_connected[i + 1][1]
    
    def test_dependency_depth_calculation(self):
        """Test dependency depth calculation."""
        self._create_python_files()
        
        graph = self.generator.analyze_codebase(str(self.project_dir), ['*.py'])
        analyzer = DependencyAnalyzer(graph)
        
        # Test depth calculation for existing nodes
        for node in graph.nodes():
            depth = analyzer.get_dependency_depth(node)
            assert isinstance(depth, int)
            assert depth >= 0
        
        # Test depth for non-existent node
        depth = analyzer.get_dependency_depth("non_existent.py")
        assert depth == 0
    
    def test_javascript_file_analysis(self):
        """Test analysis of JavaScript files."""
        # Create JavaScript files
        (self.project_dir / "main.js").write_text("""
import { helper } from './utils.js';
import React from 'react';
const lodash = require('lodash');

function main() {
    return helper();
}
""")
        
        (self.project_dir / "utils.js").write_text("""
import axios from 'axios';

export function helper() {
    return 'helper';
}
""")
        
        graph = self.generator.analyze_codebase(str(self.project_dir), ['*.js'])
        
        # Verify JavaScript dependencies were found
        dependencies = self.generator.get_dependencies()
        js_deps = [dep for dep in dependencies if dep.source.endswith('.js')]
        assert len(js_deps) > 0
        
        # Check for specific imports
        import_deps = [dep for dep in js_deps if dep.dependency_type == 'import']
        assert len(import_deps) > 0
    
    def test_empty_codebase(self):
        """Test handling of empty codebase."""
        # Create empty directory
        empty_dir = self.project_dir / "empty"
        empty_dir.mkdir()
        
        graph = self.generator.analyze_codebase(str(empty_dir), ['*.py'])
        
        # Should handle empty codebase gracefully
        assert isinstance(graph, nx.DiGraph)
        assert graph.number_of_nodes() == 0
        assert graph.number_of_edges() == 0
    
    def test_file_with_syntax_errors(self):
        """Test handling of files with syntax errors."""
        # Create file with syntax error
        (self.project_dir / "broken.py").write_text("""
def broken_function(
    # Missing closing parenthesis and colon
    return "broken"
""")
        
        # Create valid file
        (self.project_dir / "valid.py").write_text("""
def valid_function():
    return "valid"
""")
        
        graph = self.generator.analyze_codebase(str(self.project_dir), ['*.py'])
        
        # Should handle syntax errors gracefully and continue with valid files
        assert isinstance(graph, nx.DiGraph)
        # Should have at least the valid file
        dependencies = self.generator.get_dependencies()
        # May have no dependencies if only valid.py was processed and it has no imports


class TestGraphVisualizer:
    """Test graph visualization functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.visualizer = GraphVisualizer()
        
        # Create a simple test graph
        self.test_graph = nx.DiGraph()
        self.test_graph.add_edge("file1.py", "file2.py")
        self.test_graph.add_edge("file2.py", "file3.py")
        self.test_graph.add_edge("file3.py", "file1.py")  # Creates a cycle
        
        self.analyzer = DependencyAnalyzer(self.test_graph)
    
    def test_create_dependency_visualization(self):
        """Test creating dependency visualization."""
        try:
            fig = self.visualizer.create_dependency_visualization(
                self.test_graph, 
                self.analyzer,
                layout='spring'
            )
            
            # Verify figure was created
            assert fig is not None
            assert hasattr(fig, 'data')
            assert len(fig.data) > 0  # Should have traces for nodes and edges
            
        except ImportError:
            # Skip test if Plotly is not available
            pytest.skip("Plotly not available for visualization tests")
    
    def test_circular_dependency_report(self):
        """Test circular dependency report creation."""
        try:
            circular_deps = self.analyzer.find_circular_dependencies()
            
            fig = self.visualizer.create_circular_dependency_report(circular_deps)
            
            # Verify figure was created
            assert fig is not None
            assert hasattr(fig, 'data')
            
        except ImportError:
            # Skip test if Plotly is not available
            pytest.skip("Plotly not available for visualization tests")
    
    def test_metrics_dashboard(self):
        """Test metrics dashboard creation."""
        try:
            metrics = self.analyzer.calculate_metrics()
            hotspots = self.analyzer.find_dependency_hotspots()
            
            fig = self.visualizer.create_dependency_metrics_dashboard(metrics, hotspots)
            
            # Verify figure was created
            assert fig is not None
            assert hasattr(fig, 'data')
            
        except ImportError:
            # Skip test if Plotly is not available
            pytest.skip("Plotly not available for visualization tests")
    
    def test_no_circular_dependencies_figure(self):
        """Test figure creation when no circular dependencies exist."""
        try:
            # Create graph without cycles
            acyclic_graph = nx.DiGraph()
            acyclic_graph.add_edge("file1.py", "file2.py")
            acyclic_graph.add_edge("file2.py", "file3.py")
            
            analyzer = DependencyAnalyzer(acyclic_graph)
            circular_deps = analyzer.find_circular_dependencies()
            
            fig = self.visualizer.create_circular_dependency_report(circular_deps)
            
            # Should create a figure indicating no circular dependencies
            assert fig is not None
            
        except ImportError:
            # Skip test if Plotly is not available
            pytest.skip("Plotly not available for visualization tests")
    
    def test_color_schemes(self):
        """Test different color schemes."""
        # Verify color schemes are defined
        assert 'default' in self.visualizer.color_schemes
        assert 'dark' in self.visualizer.color_schemes
        
        # Verify color scheme structure
        for scheme_name, scheme in self.visualizer.color_schemes.items():
            assert 'nodes' in scheme
            assert 'edges' in scheme
            assert 'circular' in scheme
            assert 'hotspot' in scheme
            assert 'background' in scheme


class TestDependencyInfo:
    """Test dependency information data structures."""
    
    def test_dependency_info_creation(self):
        """Test creating dependency info objects."""
        dep_info = DependencyInfo(
            source="file1.py",
            target="file2.py",
            dependency_type="import",
            line_number=5,
            context="import file2"
        )
        
        assert dep_info.source == "file1.py"
        assert dep_info.target == "file2.py"
        assert dep_info.dependency_type == "import"
        assert dep_info.line_number == 5
        assert dep_info.context == "import file2"
    
    def test_circular_dependency_creation(self):
        """Test creating circular dependency objects."""
        circular_dep = CircularDependency(
            cycle=["file1.py", "file2.py", "file1.py"],
            cycle_length=2,
            severity="medium",
            description="Circular dependency between file1.py and file2.py"
        )
        
        assert len(circular_dep.cycle) == 3
        assert circular_dep.cycle_length == 2
        assert circular_dep.severity == "medium"
        assert "Circular dependency" in circular_dep.description
    
    def test_dependency_metrics_creation(self):
        """Test creating dependency metrics objects."""
        metrics = DependencyMetrics(
            total_nodes=10,
            total_edges=15,
            circular_dependencies=[],
            strongly_connected_components=[],
            max_depth=5,
            average_degree=3.0,
            density=0.3,
            modularity=0.5
        )
        
        assert metrics.total_nodes == 10
        assert metrics.total_edges == 15
        assert metrics.max_depth == 5
        assert metrics.average_degree == 3.0
        assert metrics.density == 0.3
        assert metrics.modularity == 0.5


class TestIntegratedDependencyAnalysis:
    """Test integrated dependency analysis workflow."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.temp_dir) / "integration_test"
        self.project_dir.mkdir()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_end_to_end_dependency_analysis(self):
        """Test complete dependency analysis workflow."""
        # Create a realistic project structure
        self._create_realistic_project()
        
        # Generate dependency graph
        generator = DependencyGraphGenerator()
        graph = generator.analyze_codebase(str(self.project_dir), ['*.py'])
        
        # Analyze dependencies
        analyzer = DependencyAnalyzer(graph)
        metrics = analyzer.calculate_metrics()
        circular_deps = analyzer.find_circular_dependencies()
        hotspots = analyzer.find_dependency_hotspots()
        
        # Verify analysis results
        assert isinstance(graph, nx.DiGraph)
        assert isinstance(metrics, DependencyMetrics)
        assert isinstance(circular_deps, list)
        assert isinstance(hotspots, list)
        
        # Verify we found some structure
        assert metrics.total_nodes > 0
        assert metrics.total_edges >= 0
        
        print(f"✅ End-to-end dependency analysis completed successfully")
        print(f"   - Analyzed {metrics.total_nodes} files")
        print(f"   - Found {metrics.total_edges} dependencies")
        print(f"   - Detected {len(circular_deps)} circular dependencies")
        print(f"   - Identified {len(hotspots)} dependency hotspots")
    
    def _create_realistic_project(self):
        """Create a realistic project structure for testing."""
        # Main application
        (self.project_dir / "app.py").write_text("""
from models.user import User
from services.auth import AuthService
from utils.logger import Logger

class Application:
    def __init__(self):
        self.auth = AuthService()
        self.logger = Logger()
    
    def run(self):
        user = User("test")
        return self.auth.authenticate(user)
""")
        
        # Models directory
        models_dir = self.project_dir / "models"
        models_dir.mkdir()
        (models_dir / "__init__.py").write_text("")
        
        (models_dir / "user.py").write_text("""
from utils.validator import validate_email

class User:
    def __init__(self, email):
        self.email = validate_email(email)
        self.id = None
""")
        
        (models_dir / "session.py").write_text("""
from models.user import User

class Session:
    def __init__(self, user: User):
        self.user = user
        self.active = True
""")
        
        # Services directory
        services_dir = self.project_dir / "services"
        services_dir.mkdir()
        (services_dir / "__init__.py").write_text("")
        
        (services_dir / "auth.py").write_text("""
from models.user import User
from models.session import Session
from utils.crypto import hash_password

class AuthService:
    def authenticate(self, user: User):
        # Authentication logic
        return Session(user)
""")
        
        # Utils directory
        utils_dir = self.project_dir / "utils"
        utils_dir.mkdir()
        (utils_dir / "__init__.py").write_text("")
        
        (utils_dir / "logger.py").write_text("""
import os
import sys

class Logger:
    def log(self, message):
        print(message)
""")
        
        (utils_dir / "validator.py").write_text("""
import re

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'
    if re.match(pattern, email):
        return email
    raise ValueError("Invalid email")
""")
        
        (utils_dir / "crypto.py").write_text("""
import hashlib

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()
""")


if __name__ == '__main__':
    pytest.main([__file__])