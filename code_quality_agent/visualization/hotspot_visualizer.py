"""Hotspot visualization module for generating charts and graphs."""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
from datetime import datetime

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib.patches import Rectangle
    import seaborn as sns
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

from ..core.models import HotspotAnalysis, FileChurnMetrics

logger = logging.getLogger(__name__)


class HotspotVisualizer:
    """Visualizer for code hotspot analysis results."""
    
    def __init__(self, use_plotly: bool = True):
        """
        Initialize the hotspot visualizer.
        
        Args:
            use_plotly: Whether to use Plotly for interactive charts (fallback to matplotlib)
        """
        self.use_plotly = use_plotly and PLOTLY_AVAILABLE
        
        if not self.use_plotly and not MATPLOTLIB_AVAILABLE:
            logger.warning("Neither Plotly nor Matplotlib available. Visualization will be limited.")
    
    def create_hotspot_dashboard(
        self, 
        hotspot_analysis: HotspotAnalysis,
        output_path: Optional[Path] = None
    ) -> Optional[str]:
        """
        Create a comprehensive hotspot dashboard.
        
        Args:
            hotspot_analysis: Results of hotspot analysis
            output_path: Optional path to save the dashboard
            
        Returns:
            HTML content of the dashboard or None if visualization unavailable
        """
        if not self.use_plotly:
            logger.warning("Plotly not available, cannot create interactive dashboard")
            return None
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                "Hotspot Score vs Change Frequency",
                "Complexity vs Churn Distribution", 
                "Top Hotspot Files",
                "Change Frequency Over Time"
            ),
            specs=[
                [{"secondary_y": False}, {"secondary_y": False}],
                [{"secondary_y": False}, {"secondary_y": False}]
            ]
        )
        
        # Plot 1: Hotspot Score vs Change Frequency
        self._add_hotspot_scatter_plot(fig, hotspot_analysis, row=1, col=1)
        
        # Plot 2: Complexity vs Churn Distribution
        self._add_complexity_churn_plot(fig, hotspot_analysis, row=1, col=2)
        
        # Plot 3: Top Hotspot Files Bar Chart
        self._add_top_hotspots_bar_chart(fig, hotspot_analysis, row=2, col=1)
        
        # Plot 4: Change Frequency Timeline
        self._add_change_frequency_timeline(fig, hotspot_analysis, row=2, col=2)
        
        # Update layout
        fig.update_layout(
            title="Code Hotspot Analysis Dashboard",
            height=800,
            showlegend=True,
            template="plotly_white"
        )
        
        # Save or return HTML
        if output_path:
            fig.write_html(str(output_path))
            logger.info(f"Hotspot dashboard saved to: {output_path}")
        
        return fig.to_html(include_plotlyjs=True)
    
    def _add_hotspot_scatter_plot(
        self, 
        fig, 
        hotspot_analysis: HotspotAnalysis, 
        row: int, 
        col: int
    ) -> None:
        """Add hotspot score vs change frequency scatter plot."""
        metrics = hotspot_analysis.file_churn_metrics
        
        if not metrics:
            return
        
        x_values = [m.change_frequency for m in metrics]
        y_values = [m.hotspot_score for m in metrics]
        text_values = [Path(m.file_path).name for m in metrics]
        
        # Color by hotspot status
        colors = [
            'red' if m.file_path in hotspot_analysis.hotspot_files else 'blue'
            for m in metrics
        ]
        
        fig.add_trace(
            go.Scatter(
                x=x_values,
                y=y_values,
                mode='markers',
                marker=dict(
                    color=colors,
                    size=8,
                    opacity=0.7
                ),
                text=text_values,
                hovertemplate="<b>%{text}</b><br>" +
                             "Change Frequency: %{x:.3f}<br>" +
                             "Hotspot Score: %{y:.3f}<extra></extra>",
                name="Files"
            ),
            row=row, col=col
        )
        
        fig.update_xaxes(title_text="Change Frequency (commits/day)", row=row, col=col)
        fig.update_yaxes(title_text="Hotspot Score", row=row, col=col)
    
    def _add_complexity_churn_plot(
        self, 
        fig, 
        hotspot_analysis: HotspotAnalysis, 
        row: int, 
        col: int
    ) -> None:
        """Add complexity vs churn distribution plot."""
        metrics = hotspot_analysis.file_churn_metrics
        
        if not metrics:
            return
        
        x_values = [m.complexity_score for m in metrics]
        y_values = [m.total_commits for m in metrics]
        text_values = [Path(m.file_path).name for m in metrics]
        
        # Size by hotspot score
        sizes = [max(m.hotspot_score * 20, 5) for m in metrics]
        
        fig.add_trace(
            go.Scatter(
                x=x_values,
                y=y_values,
                mode='markers',
                marker=dict(
                    size=sizes,
                    color='orange',
                    opacity=0.6,
                    line=dict(width=1, color='black')
                ),
                text=text_values,
                hovertemplate="<b>%{text}</b><br>" +
                             "Complexity Score: %{x:.2f}<br>" +
                             "Total Commits: %{y}<extra></extra>",
                name="Complexity vs Churn"
            ),
            row=row, col=col
        )
        
        fig.update_xaxes(title_text="Complexity Score", row=row, col=col)
        fig.update_yaxes(title_text="Total Commits", row=row, col=col)
    
    def _add_top_hotspots_bar_chart(
        self, 
        fig, 
        hotspot_analysis: HotspotAnalysis, 
        row: int, 
        col: int
    ) -> None:
        """Add top hotspot files bar chart."""
        metrics = hotspot_analysis.file_churn_metrics
        
        if not metrics:
            return
        
        # Sort by hotspot score and take top 10
        sorted_metrics = sorted(metrics, key=lambda m: m.hotspot_score, reverse=True)[:10]
        
        file_names = [Path(m.file_path).name for m in sorted_metrics]
        hotspot_scores = [m.hotspot_score for m in sorted_metrics]
        
        fig.add_trace(
            go.Bar(
                x=hotspot_scores,
                y=file_names,
                orientation='h',
                marker=dict(color='red', opacity=0.7),
                hovertemplate="<b>%{y}</b><br>" +
                             "Hotspot Score: %{x:.3f}<extra></extra>",
                name="Top Hotspots"
            ),
            row=row, col=col
        )
        
        fig.update_xaxes(title_text="Hotspot Score", row=row, col=col)
        fig.update_yaxes(title_text="Files", row=row, col=col)
    
    def _add_change_frequency_timeline(
        self, 
        fig, 
        hotspot_analysis: HotspotAnalysis, 
        row: int, 
        col: int
    ) -> None:
        """Add change frequency timeline."""
        metrics = hotspot_analysis.file_churn_metrics
        
        if not metrics:
            return
        
        # Group by date ranges (simplified - just show last commit dates)
        dates = [m.last_commit_date for m in metrics]
        frequencies = [m.change_frequency for m in metrics]
        
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=frequencies,
                mode='markers+lines',
                marker=dict(color='green', size=6),
                line=dict(color='green', width=2),
                hovertemplate="Date: %{x}<br>" +
                             "Change Frequency: %{y:.3f}<extra></extra>",
                name="Change Frequency"
            ),
            row=row, col=col
        )
        
        fig.update_xaxes(title_text="Date", row=row, col=col)
        fig.update_yaxes(title_text="Change Frequency", row=row, col=col)
    
    def create_hotspot_heatmap(
        self, 
        hotspot_analysis: HotspotAnalysis,
        output_path: Optional[Path] = None
    ) -> Optional[str]:
        """
        Create a heatmap showing hotspot intensity across files.
        
        Args:
            hotspot_analysis: Results of hotspot analysis
            output_path: Optional path to save the heatmap
            
        Returns:
            HTML content of the heatmap or None if visualization unavailable
        """
        if not self.use_plotly:
            logger.warning("Plotly not available, cannot create heatmap")
            return None
        
        metrics = hotspot_analysis.file_churn_metrics
        if not metrics:
            return None
        
        # Prepare data for heatmap
        file_names = [Path(m.file_path).name for m in metrics]
        
        # Create matrix data
        data_matrix = []
        labels = ['Hotspot Score', 'Complexity', 'Change Frequency', 'Total Commits']
        
        for metric in metrics:
            row = [
                metric.hotspot_score,
                metric.complexity_score,
                metric.change_frequency,
                metric.total_commits / max(m.total_commits for m in metrics)  # Normalize
            ]
            data_matrix.append(row)
        
        fig = go.Figure(data=go.Heatmap(
            z=data_matrix,
            x=labels,
            y=file_names,
            colorscale='Reds',
            hoverongaps=False,
            hovertemplate="File: %{y}<br>" +
                         "Metric: %{x}<br>" +
                         "Value: %{z:.3f}<extra></extra>"
        ))
        
        fig.update_layout(
            title="Hotspot Metrics Heatmap",
            xaxis_title="Metrics",
            yaxis_title="Files",
            height=max(400, len(file_names) * 20)
        )
        
        if output_path:
            fig.write_html(str(output_path))
            logger.info(f"Hotspot heatmap saved to: {output_path}")
        
        return fig.to_html(include_plotlyjs=True)
    
    def create_churn_timeline(
        self, 
        hotspot_analysis: HotspotAnalysis,
        output_path: Optional[Path] = None
    ) -> Optional[str]:
        """
        Create a timeline showing code churn over time.
        
        Args:
            hotspot_analysis: Results of hotspot analysis
            output_path: Optional path to save the timeline
            
        Returns:
            HTML content of the timeline or None if visualization unavailable
        """
        if not MATPLOTLIB_AVAILABLE:
            logger.warning("Matplotlib not available, cannot create timeline")
            return None
        
        metrics = hotspot_analysis.file_churn_metrics
        if not metrics:
            return None
        
        # Create timeline plot
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Sort metrics by first commit date
        sorted_metrics = sorted(metrics, key=lambda m: m.first_commit_date)
        
        for i, metric in enumerate(sorted_metrics):
            # Create timeline bar for each file
            start_date = metric.first_commit_date
            end_date = metric.last_commit_date
            
            # Color intensity based on hotspot score
            color_intensity = metric.hotspot_score
            color = plt.cm.Reds(color_intensity)
            
            # Draw timeline bar
            ax.barh(
                i, 
                (end_date - start_date).days,
                left=start_date,
                height=0.8,
                color=color,
                alpha=0.7,
                label=Path(metric.file_path).name if i < 10 else ""  # Limit labels
            )
        
        # Format plot
        ax.set_xlabel('Date')
        ax.set_ylabel('Files')
        ax.set_title('Code Churn Timeline (Color intensity = Hotspot Score)')
        
        # Format dates on x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        plt.xticks(rotation=45)
        
        # Set y-axis labels
        file_names = [Path(m.file_path).name for m in sorted_metrics]
        ax.set_yticks(range(len(file_names)))
        ax.set_yticklabels(file_names)
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(str(output_path), dpi=300, bbox_inches='tight')
            logger.info(f"Churn timeline saved to: {output_path}")
        
        # Convert to base64 for HTML embedding (simplified)
        return "Timeline chart created (matplotlib)"
    
    def generate_hotspot_report(
        self, 
        hotspot_analysis: HotspotAnalysis,
        output_dir: Path
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive hotspot report with multiple visualizations.
        
        Args:
            hotspot_analysis: Results of hotspot analysis
            output_dir: Directory to save report files
            
        Returns:
            Dictionary with report metadata and file paths
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        report_data = {
            "timestamp": str(datetime.now()),
            "total_files_analyzed": len(hotspot_analysis.file_churn_metrics),
            "hotspot_files_count": len(hotspot_analysis.hotspot_files),
            "complexity_hotspots_count": len(hotspot_analysis.complexity_hotspots),
            "churn_hotspots_count": len(hotspot_analysis.churn_hotspots),
            "visualizations": {}
        }
        
        try:
            # Create dashboard
            dashboard_path = output_dir / "hotspot_dashboard.html"
            dashboard_html = self.create_hotspot_dashboard(hotspot_analysis, dashboard_path)
            if dashboard_html:
                report_data["visualizations"]["dashboard"] = str(dashboard_path)
            
            # Create heatmap
            heatmap_path = output_dir / "hotspot_heatmap.html"
            heatmap_html = self.create_hotspot_heatmap(hotspot_analysis, heatmap_path)
            if heatmap_html:
                report_data["visualizations"]["heatmap"] = str(heatmap_path)
            
            # Create timeline
            timeline_path = output_dir / "churn_timeline.png"
            timeline_result = self.create_churn_timeline(hotspot_analysis, timeline_path)
            if timeline_result:
                report_data["visualizations"]["timeline"] = str(timeline_path)
            
            # Save report metadata
            metadata_path = output_dir / "hotspot_report.json"
            with open(metadata_path, 'w') as f:
                json.dump(report_data, f, indent=2, default=str)
            
            logger.info(f"Hotspot report generated in: {output_dir}")
            
        except Exception as e:
            logger.error(f"Error generating hotspot report: {e}")
        
        return report_data