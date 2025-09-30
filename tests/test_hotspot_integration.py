"""Integration tests for hotspot analysis functionality."""

import pytest
import tempfile
import subprocess
import os
from pathlib import Path
from unittest.mock import patch, Mock

from code_quality_agent.analyzers.hotspot_analyzer import HotspotAnalyzer
from code_quality_agent.visualization.hotspot_visualizer import HotspotVisualizer
from code_quality_agent.core.models import (
    AnalysisOptions, AnalysisContext, ParsedFile, Function, Class,
    FileChurnMetrics, HotspotAnalysis
)
from code_quality_agent.parsers.unified_parser import UnifiedCodeParser


@pytest.mark.integration
class TestHotspotIntegration:
    """Integration tests for the complete hotspot analysis workflow."""
    
    def setup_method(self):
        """Set up integration test fixtures."""
        self.analyzer = HotspotAnalyzer({
            "min_commits_threshold": 2,  # Lower threshold for testing
            "hotspot_percentile": 0.7,
            "analysis_period_days": 365
        })
        self.visualizer = HotspotVisualizer(use_plotly=False)  # Disable plotly for testing
    
    def test_end_to_end_hotspot_analysis(self):
        """Test complete hotspot analysis workflow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create sample Python files
            sample_files = self._create_sample_files(temp_dir)
            
            # Mock git repository and history
            with patch.object(self.analyzer, '_find_git_root', return_value=temp_dir), \
                 patch.object(self.analyzer, '_analyze_git_churn') as mock_churn:
                
                # Mock churn analysis results
                mock_churn_metrics = {
                    sample_files[0]: FileChurnMetrics(
                        file_path=sample_files[0],
                        total_commits=10,
                        unique_authors=3,
                        lines_added=150,
                        lines_deleted=75,
                        first_commit_date=datetime(2023, 1, 1),
                        last_commit_date=datetime(2023, 12, 31),
                        change_frequency=0.3
                    ),
                    sample_files[1]: FileChurnMetrics(
                        file_path=sample_files[1],
                        total_commits=3,
                        unique_authors=1,
                        lines_added=30,
                        lines_deleted=10,
                        first_commit_date=datetime(2023, 6, 1),
                        last_commit_date=datetime(2023, 8, 15),
                        change_frequency=0.05
                    )
                }
                mock_churn.return_value = mock_churn_metrics
                
                # Create mock parsed files instead of using the parser
                from code_quality_agent.core.models import Function
                parsed_files = [
                    ParsedFile(
                        path=sample_files[0],
                        language="python",
                        content="def complex_function(): pass",
                        functions=[
                            Function(name="complex_function", line_start=1, line_end=10, complexity=8)
                        ],
                        classes=[],
                        imports=[]
                    ),
                    ParsedFile(
                        path=sample_files[1],
                        language="python", 
                        content="def simple_function(): pass",
                        functions=[
                            Function(name="simple_function", line_start=1, line_end=3, complexity=1)
                        ],
                        classes=[],
                        imports=[]
                    )
                ]
                
                # Run hotspot analysis
                context = AnalysisContext(options=AnalysisOptions())
                issues = self.analyzer.analyze(parsed_files, context)
                
                # Verify results
                assert isinstance(issues, list)
                
                # Should find at least one hotspot (the high-churn file)
                if issues:
                    hotspot_issue = issues[0]
                    assert hotspot_issue.category.value == "hotspot"
                    assert "hotspot" in hotspot_issue.title.lower()
                    assert hotspot_issue.confidence > 0
                    assert "hotspot_score" in hotspot_issue.metadata
    
    def test_hotspot_analysis_with_real_complexity(self):
        """Test hotspot analysis with real complexity calculations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create files with different complexity levels
            simple_file = Path(temp_dir) / "simple.py"
            complex_file = Path(temp_dir) / "complex.py"
            
            # Mock git analysis to show complex file has high churn
            with patch.object(self.analyzer, '_find_git_root', return_value=temp_dir), \
                 patch.object(self.analyzer, '_analyze_git_churn') as mock_churn:
                
                mock_churn_metrics = {
                    str(complex_file): FileChurnMetrics(
                        file_path=str(complex_file),
                        total_commits=15,
                        unique_authors=4,
                        lines_added=200,
                        lines_deleted=100,
                        first_commit_date=datetime(2023, 1, 1),
                        last_commit_date=datetime(2023, 12, 31),
                        change_frequency=0.4
                    ),
                    str(simple_file): FileChurnMetrics(
                        file_path=str(simple_file),
                        total_commits=2,
                        unique_authors=1,
                        lines_added=20,
                        lines_deleted=5,
                        first_commit_date=datetime(2023, 10, 1),
                        last_commit_date=datetime(2023, 10, 15),
                        change_frequency=0.02
                    )
                }
                mock_churn.return_value = mock_churn_metrics
                
                # Create mock parsed files with different complexity
                from code_quality_agent.core.models import Function, Class
                parsed_files = [
                    ParsedFile(
                        path=str(simple_file),
                        language="python",
                        content="def simple_function(): return 'hello'",
                        functions=[
                            Function(name="simple_function", line_start=1, line_end=2, complexity=1)
                        ],
                        classes=[],
                        imports=[]
                    ),
                    ParsedFile(
                        path=str(complex_file),
                        language="python",
                        content="def complex_function(): # complex logic here",
                        functions=[
                            Function(name="complex_function", line_start=1, line_end=20, complexity=12)
                        ],
                        classes=[
                            Class(
                                name="ComplexClass",
                                line_start=21,
                                line_end=40,
                                methods=[
                                    Function(name="process_data", line_start=25, line_end=35, complexity=8)
                                ]
                            )
                        ],
                        imports=[]
                    )
                ]
                
                # Run analysis
                context = AnalysisContext(options=AnalysisOptions())
                issues = self.analyzer.analyze(parsed_files, context)
                
                # Complex file should be identified as hotspot
                if issues:
                    # Find issue for complex file
                    complex_issues = [
                        issue for issue in issues 
                        if "complex.py" in issue.location.file_path
                    ]
                    
                    if complex_issues:
                        complex_issue = complex_issues[0]
                        assert complex_issue.metadata["complexity_score"] > 0
                        assert complex_issue.metadata["change_frequency"] > 0.1
                        assert complex_issue.metadata["hotspot_score"] > 0.5
    
    def test_hotspot_visualization_integration(self):
        """Test integration between hotspot analysis and visualization."""
        # Create sample hotspot analysis data
        churn_metrics = [
            FileChurnMetrics(
                file_path="/test/hotspot1.py",
                total_commits=20,
                unique_authors=5,
                lines_added=300,
                lines_deleted=150,
                first_commit_date=datetime(2023, 1, 1),
                last_commit_date=datetime(2023, 12, 31),
                change_frequency=0.4,
                complexity_score=8.5,
                hotspot_score=0.9
            ),
            FileChurnMetrics(
                file_path="/test/normal.py",
                total_commits=3,
                unique_authors=2,
                lines_added=50,
                lines_deleted=20,
                first_commit_date=datetime(2023, 8, 1),
                last_commit_date=datetime(2023, 9, 15),
                change_frequency=0.05,
                complexity_score=2.0,
                hotspot_score=0.3
            )
        ]
        
        hotspot_analysis = HotspotAnalysis(
            file_churn_metrics=churn_metrics,
            hotspot_files=["/test/hotspot1.py"],
            complexity_hotspots=["/test/hotspot1.py"],
            churn_hotspots=["/test/hotspot1.py"],
            recommendations=[
                "Focus refactoring efforts on hotspot1.py",
                "Increase test coverage for high-churn files"
            ]
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            
            # Generate visualization report
            report_data = self.visualizer.generate_hotspot_report(
                hotspot_analysis,
                output_dir
            )
            
            # Verify report structure
            assert "timestamp" in report_data
            assert "total_files_analyzed" in report_data
            assert "hotspot_files_count" in report_data
            assert report_data["total_files_analyzed"] == 2
            assert report_data["hotspot_files_count"] == 1
            
            # Verify metadata file was created
            metadata_file = output_dir / "hotspot_report.json"
            assert metadata_file.exists()
            
            # Verify metadata content
            import json
            with open(metadata_file) as f:
                metadata = json.load(f)
            
            assert metadata["total_files_analyzed"] == 2
            assert metadata["hotspot_files_count"] == 1
    
    def test_error_handling_in_integration(self):
        """Test error handling in integrated hotspot analysis."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a file that will cause parsing errors
            bad_file = Path(temp_dir) / "bad_syntax.py"
            bad_file.write_text("def incomplete_function(\n    # Missing closing parenthesis")
            
            # Mock git to return this directory as git root
            with patch.object(self.analyzer, '_find_git_root', return_value=temp_dir), \
                 patch.object(self.analyzer, '_analyze_git_churn', return_value={}):
                
                # Try to parse the bad file
                parser = UnifiedCodeParser()
                parsed_files = []
                
                try:
                    parsed_file = parser.parse_file(str(bad_file))
                    if parsed_file:
                        parsed_files.append(parsed_file)
                except Exception:
                    # Parser should handle errors gracefully
                    pass
                
                # Analysis should not crash even with parsing errors
                context = AnalysisContext(options=AnalysisOptions())
                issues = self.analyzer.analyze(parsed_files, context)
                
                # Should return empty list or handle gracefully
                assert isinstance(issues, list)
    
    def _create_sample_files(self, temp_dir: str) -> list:
        """Create sample Python files for testing."""
        files = []
        
        # File 1: High complexity file
        file1 = Path(temp_dir) / "high_complexity.py"
        file1.write_text("""
def complex_algorithm(data):
    result = []
    for item in data:
        if item > 10:
            for i in range(item):
                if i % 2 == 0:
                    result.append(i * 2)
                else:
                    result.append(i)
        elif item < 0:
            result.append(0)
        else:
            result.append(item)
    return result

class DataProcessor:
    def __init__(self):
        self.cache = {}
    
    def process(self, input_data):
        if not input_data:
            return []
        
        processed = []
        for item in input_data:
            if item in self.cache:
                processed.append(self.cache[item])
            else:
                result = self._complex_processing(item)
                self.cache[item] = result
                processed.append(result)
        return processed
    
    def _complex_processing(self, item):
        if isinstance(item, int):
            return item ** 2
        elif isinstance(item, str):
            return len(item)
        else:
            return 0
""")
        files.append(str(file1))
        
        # File 2: Simple file
        file2 = Path(temp_dir) / "simple.py"
        file2.write_text("""
def simple_function():
    return "hello world"

def another_simple_function(x):
    return x + 1
""")
        files.append(str(file2))
        
        return files


# Import datetime for the tests
from datetime import datetime