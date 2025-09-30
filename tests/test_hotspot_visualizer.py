"""Tests for the HotspotVisualizer class."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime

from code_quality_agent.visualization.hotspot_visualizer import HotspotVisualizer
from code_quality_agent.core.models import HotspotAnalysis, FileChurnMetrics


class TestHotspotVisualizer:
    """Test cases for HotspotVisualizer."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.visualizer = HotspotVisualizer(use_plotly=False)  # Disable plotly for testing
        
        # Create sample hotspot analysis data
        self.sample_churn_metrics = [
            FileChurnMetrics(
                file_path="/test/hotspot1.py",
                total_commits=15,
                unique_authors=4,
                lines_added=200,
                lines_deleted=100,
                first_commit_date=datetime(2023, 1, 1),
                last_commit_date=datetime(2023, 12, 31),
                change_frequency=0.3,
                complexity_score=7.5,
                hotspot_score=0.85
            ),
            FileChurnMetrics(
                file_path="/test/normal.py",
                total_commits=5,
                unique_authors=2,
                lines_added=50,
                lines_deleted=25,
                first_commit_date=datetime(2023, 6, 1),
                last_commit_date=datetime(2023, 8, 15),
                change_frequency=0.1,
                complexity_score=3.0,
                hotspot_score=0.4
            ),
            FileChurnMetrics(
                file_path="/test/hotspot2.py",
                total_commits=20,
                unique_authors=6,
                lines_added=300,
                lines_deleted=150,
                first_commit_date=datetime(2023, 2, 1),
                last_commit_date=datetime(2023, 11, 30),
                change_frequency=0.25,
                complexity_score=9.0,
                hotspot_score=0.9
            )
        ]
        
        self.sample_hotspot_analysis = HotspotAnalysis(
            file_churn_metrics=self.sample_churn_metrics,
            hotspot_files=["/test/hotspot1.py", "/test/hotspot2.py"],
            complexity_hotspots=["/test/hotspot2.py"],
            churn_hotspots=["/test/hotspot1.py"],
            recommendations=[
                "Prioritize refactoring for hotspot files",
                "Increase test coverage for high-churn files",
                "Consider breaking down complex functions"
            ]
        )
    
    def test_initialization(self):
        """Test visualizer initialization."""
        # Test with plotly disabled
        viz = HotspotVisualizer(use_plotly=False)
        assert viz.use_plotly is False
        
        # Test default initialization
        viz_default = HotspotVisualizer()
        # use_plotly depends on whether plotly is available
        assert isinstance(viz_default.use_plotly, bool)
    
    @patch('code_quality_agent.visualization.hotspot_visualizer.PLOTLY_AVAILABLE', True)
    def test_create_hotspot_dashboard_plotly_available(self):
        """Test dashboard creation when Plotly is available."""
        with patch('plotly.graph_objects.Figure') as mock_fig_class:
            mock_fig = Mock()
            mock_fig.to_html.return_value = "<html>Dashboard</html>"
            mock_fig_class.return_value = mock_fig
            
            with patch('plotly.subplots.make_subplots', return_value=mock_fig):
                visualizer = HotspotVisualizer(use_plotly=True)
                visualizer.use_plotly = True  # Force enable for test
                
                result = visualizer.create_hotspot_dashboard(self.sample_hotspot_analysis)
                
                # Check that result is HTML content (may be real plotly HTML)
                assert result is not None
                assert isinstance(result, str)
                assert "<html>" in result.lower()
    
    def test_create_hotspot_dashboard_plotly_unavailable(self):
        """Test dashboard creation when Plotly is unavailable."""
        result = self.visualizer.create_hotspot_dashboard(self.sample_hotspot_analysis)
        assert result is None
    
    @patch('code_quality_agent.visualization.hotspot_visualizer.PLOTLY_AVAILABLE', True)
    def test_create_hotspot_heatmap_plotly_available(self):
        """Test heatmap creation when Plotly is available."""
        with patch('plotly.graph_objects.Figure') as mock_fig_class:
            mock_fig = Mock()
            mock_fig.to_html.return_value = "<html>Heatmap</html>"
            mock_fig_class.return_value = mock_fig
            
            visualizer = HotspotVisualizer(use_plotly=True)
            visualizer.use_plotly = True  # Force enable for test
            
            result = visualizer.create_hotspot_heatmap(self.sample_hotspot_analysis)
            
            assert result == "<html>Heatmap</html>"
    
    def test_create_hotspot_heatmap_plotly_unavailable(self):
        """Test heatmap creation when Plotly is unavailable."""
        result = self.visualizer.create_hotspot_heatmap(self.sample_hotspot_analysis)
        assert result is None
    
    @patch('code_quality_agent.visualization.hotspot_visualizer.MATPLOTLIB_AVAILABLE', True)
    def test_create_churn_timeline_matplotlib_available(self):
        """Test timeline creation when Matplotlib is available."""
        with patch('matplotlib.pyplot.subplots') as mock_subplots:
            mock_fig = Mock()
            mock_ax = Mock()
            mock_subplots.return_value = (mock_fig, mock_ax)
            
            with patch('matplotlib.pyplot.savefig'), \
                 patch('matplotlib.pyplot.tight_layout'):
                
                result = self.visualizer.create_churn_timeline(self.sample_hotspot_analysis)
                
                assert result == "Timeline chart created (matplotlib)"
    
    def test_create_churn_timeline_matplotlib_unavailable(self):
        """Test timeline creation when Matplotlib is unavailable."""
        with patch('code_quality_agent.visualization.hotspot_visualizer.MATPLOTLIB_AVAILABLE', False):
            visualizer = HotspotVisualizer()
            result = visualizer.create_churn_timeline(self.sample_hotspot_analysis)
            assert result is None
    
    def test_generate_hotspot_report(self):
        """Test comprehensive hotspot report generation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            
            # Mock the visualization methods to avoid dependencies
            with patch.object(self.visualizer, 'create_hotspot_dashboard', return_value="<html>Dashboard</html>"), \
                 patch.object(self.visualizer, 'create_hotspot_heatmap', return_value="<html>Heatmap</html>"), \
                 patch.object(self.visualizer, 'create_churn_timeline', return_value="Timeline created"):
                
                report_data = self.visualizer.generate_hotspot_report(
                    self.sample_hotspot_analysis, 
                    output_dir
                )
            
            # Check report data structure
            assert "timestamp" in report_data
            assert "total_files_analyzed" in report_data
            assert "hotspot_files_count" in report_data
            assert "complexity_hotspots_count" in report_data
            assert "churn_hotspots_count" in report_data
            assert "visualizations" in report_data
            
            # Check counts
            assert report_data["total_files_analyzed"] == 3
            assert report_data["hotspot_files_count"] == 2
            assert report_data["complexity_hotspots_count"] == 1
            assert report_data["churn_hotspots_count"] == 1
            
            # Check that metadata file was created
            metadata_file = output_dir / "hotspot_report.json"
            assert metadata_file.exists()
    
    def test_generate_hotspot_report_empty_analysis(self):
        """Test report generation with empty hotspot analysis."""
        empty_analysis = HotspotAnalysis()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            
            report_data = self.visualizer.generate_hotspot_report(empty_analysis, output_dir)
            
            # Should handle empty data gracefully
            assert report_data["total_files_analyzed"] == 0
            assert report_data["hotspot_files_count"] == 0
            assert report_data["complexity_hotspots_count"] == 0
            assert report_data["churn_hotspots_count"] == 0
    
    def test_dashboard_with_output_path(self):
        """Test dashboard creation with output path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "dashboard.html"
            
            # Test with real plotly if available
            try:
                import plotly
                visualizer = HotspotVisualizer(use_plotly=True)
                
                result = visualizer.create_hotspot_dashboard(
                    self.sample_hotspot_analysis, 
                    output_path
                )
                
                # Should create output file and return HTML
                assert output_path.exists()
                assert result is not None
                assert isinstance(result, str)
                assert "<html>" in result.lower()
                
            except ImportError:
                # Mock plotly if not available
                with patch('code_quality_agent.visualization.hotspot_visualizer.PLOTLY_AVAILABLE', True):
                    with patch('plotly.subplots.make_subplots') as mock_subplots:
                        mock_fig = Mock()
                        mock_fig.to_html.return_value = "<html>Dashboard</html>"
                        mock_fig.write_html = Mock()
                        mock_subplots.return_value = mock_fig
                        
                        visualizer = HotspotVisualizer(use_plotly=True)
                        visualizer.use_plotly = True
                        
                        result = visualizer.create_hotspot_dashboard(
                            self.sample_hotspot_analysis, 
                            output_path
                        )
                        
                        # Should call write_html with the output path
                        mock_fig.write_html.assert_called_once_with(str(output_path))
                        assert result == "<html>Dashboard</html>"
    
    def test_heatmap_with_output_path(self):
        """Test heatmap creation with output path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "heatmap.html"
            
            # Mock plotly to avoid dependency
            with patch('code_quality_agent.visualization.hotspot_visualizer.PLOTLY_AVAILABLE', True):
                with patch('plotly.graph_objects.Figure') as mock_fig_class:
                    mock_fig = Mock()
                    mock_fig.to_html.return_value = "<html>Heatmap</html>"
                    mock_fig.write_html = Mock()
                    mock_fig_class.return_value = mock_fig
                    
                    visualizer = HotspotVisualizer(use_plotly=True)
                    visualizer.use_plotly = True
                    
                    result = visualizer.create_hotspot_heatmap(
                        self.sample_hotspot_analysis,
                        output_path
                    )
                    
                    # Should call write_html with the output path
                    mock_fig.write_html.assert_called_once_with(str(output_path))
                    assert result == "<html>Heatmap</html>"
    
    def test_timeline_with_output_path(self):
        """Test timeline creation with output path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "timeline.png"
            
            # Mock matplotlib to avoid dependency
            with patch('code_quality_agent.visualization.hotspot_visualizer.MATPLOTLIB_AVAILABLE', True):
                with patch('matplotlib.pyplot.subplots') as mock_subplots, \
                     patch('matplotlib.pyplot.savefig') as mock_savefig, \
                     patch('matplotlib.pyplot.tight_layout'):
                    
                    mock_fig = Mock()
                    mock_ax = Mock()
                    mock_subplots.return_value = (mock_fig, mock_ax)
                    
                    result = self.visualizer.create_churn_timeline(
                        self.sample_hotspot_analysis,
                        output_path
                    )
                    
                    # Should call savefig with the output path
                    mock_savefig.assert_called_once_with(
                        str(output_path), 
                        dpi=300, 
                        bbox_inches='tight'
                    )
                    assert result == "Timeline chart created (matplotlib)"
    
    def test_error_handling_in_report_generation(self):
        """Test error handling during report generation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            
            # Mock methods to raise exceptions
            with patch.object(self.visualizer, 'create_hotspot_dashboard', side_effect=Exception("Test error")), \
                 patch.object(self.visualizer, 'create_hotspot_heatmap', side_effect=Exception("Test error")), \
                 patch.object(self.visualizer, 'create_churn_timeline', side_effect=Exception("Test error")):
                
                # Should not raise exception, but handle gracefully
                report_data = self.visualizer.generate_hotspot_report(
                    self.sample_hotspot_analysis,
                    output_dir
                )
                
                # Should still return basic report data
                assert "timestamp" in report_data
                assert "total_files_analyzed" in report_data
    
    def test_empty_metrics_handling(self):
        """Test handling of empty metrics in visualizations."""
        empty_analysis = HotspotAnalysis(
            file_churn_metrics=[],
            hotspot_files=[],
            complexity_hotspots=[],
            churn_hotspots=[],
            recommendations=[]
        )
        
        # Should handle empty data without errors
        result1 = self.visualizer.create_hotspot_dashboard(empty_analysis)
        result2 = self.visualizer.create_hotspot_heatmap(empty_analysis)
        result3 = self.visualizer.create_churn_timeline(empty_analysis)
        
        # All should return None or handle gracefully
        assert result1 is None  # Plotly not available
        assert result2 is None  # Plotly not available
        assert result3 is None  # Matplotlib not available or empty data


@pytest.mark.integration
class TestHotspotVisualizerIntegration:
    """Integration tests for HotspotVisualizer with real dependencies."""
    
    def setup_method(self):
        """Set up integration test fixtures."""
        # Create sample data
        self.sample_churn_metrics = [
            FileChurnMetrics(
                file_path="/test/file1.py",
                total_commits=10,
                unique_authors=3,
                lines_added=150,
                lines_deleted=75,
                first_commit_date=datetime(2023, 1, 1),
                last_commit_date=datetime(2023, 6, 1),
                change_frequency=0.2,
                complexity_score=5.0,
                hotspot_score=0.7
            ),
            FileChurnMetrics(
                file_path="/test/file2.py",
                total_commits=25,
                unique_authors=5,
                lines_added=400,
                lines_deleted=200,
                first_commit_date=datetime(2023, 2, 1),
                last_commit_date=datetime(2023, 8, 1),
                change_frequency=0.4,
                complexity_score=8.5,
                hotspot_score=0.9
            )
        ]
        
        self.sample_analysis = HotspotAnalysis(
            file_churn_metrics=self.sample_churn_metrics,
            hotspot_files=["/test/file2.py"],
            complexity_hotspots=["/test/file2.py"],
            churn_hotspots=["/test/file2.py"],
            recommendations=["Test recommendation"]
        )
    
    @pytest.mark.skipif(
        not hasattr(pytest, 'importorskip') or 
        pytest.importorskip("plotly", reason="Plotly not available") is None,
        reason="Plotly not available"
    )
    def test_real_plotly_dashboard(self):
        """Test dashboard creation with real Plotly (if available)."""
        try:
            import plotly
            visualizer = HotspotVisualizer(use_plotly=True)
            
            with tempfile.TemporaryDirectory() as temp_dir:
                output_path = Path(temp_dir) / "test_dashboard.html"
                
                result = visualizer.create_hotspot_dashboard(
                    self.sample_analysis,
                    output_path
                )
                
                # Should create HTML content
                assert result is not None
                assert isinstance(result, str)
                assert "<html>" in result or "plotly" in result.lower()
                
                # Should create output file
                assert output_path.exists()
                
        except ImportError:
            pytest.skip("Plotly not available for integration test")
    
    @pytest.mark.skipif(
        not hasattr(pytest, 'importorskip') or 
        pytest.importorskip("matplotlib", reason="Matplotlib not available") is None,
        reason="Matplotlib not available"
    )
    def test_real_matplotlib_timeline(self):
        """Test timeline creation with real Matplotlib (if available)."""
        try:
            import matplotlib
            visualizer = HotspotVisualizer(use_plotly=False)
            
            with tempfile.TemporaryDirectory() as temp_dir:
                output_path = Path(temp_dir) / "test_timeline.png"
                
                result = visualizer.create_churn_timeline(
                    self.sample_analysis,
                    output_path
                )
                
                # Should create result
                assert result is not None
                assert isinstance(result, str)
                
                # Should create output file
                assert output_path.exists()
                
        except ImportError:
            pytest.skip("Matplotlib not available for integration test")