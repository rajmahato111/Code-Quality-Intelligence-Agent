"""
Interactive graph visualization using Plotly.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import networkx as nx
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np

from .dependency_graph import DependencyAnalyzer, DependencyMetrics, CircularDependency

logger = logging.getLogger(__name__)


class GraphVisualizer:
    """Creates interactive visualizations of dependency graphs."""
    
    def __init__(self):
        """Initialize the graph visualizer."""
        self.color_schemes = {
            'default': {
                'nodes': '#1f77b4',
                'edges': '#7f7f7f',
                'circular': '#d62728',
                'hotspot': '#ff7f0e',
                'background': '#ffffff'
            },
            'dark': {
                'nodes': '#17becf',
                'edges': '#bcbd22',
                'circular': '#e377c2',
                'hotspot': '#ff7f0e',
                'background': '#2f2f2f'
            }
        }
    
    def create_dependency_visualization(
        self, 
        graph: nx.DiGraph, 
        analyzer: DependencyAnalyzer,
        layout: str = 'spring',
        color_scheme: str = 'default',
        highlight_circular: bool = True,
        highlight_hotspots: bool = True,
        max_nodes: int = 100
    ) -> go.Figure:
        """
        Create an interactive dependency graph visualization.
        
        Args:
            graph: NetworkX dependency graph
            analyzer: Dependency analyzer instance
            layout: Layout algorithm ('spring', 'circular', 'hierarchical')
            color_scheme: Color scheme to use
            highlight_circular: Whether to highlight circular dependencies
            highlight_hotspots: Whether to highlight dependency hotspots
            max_nodes: Maximum number of nodes to display
            
        Returns:
            Plotly figure with interactive graph
        """
        try:
            # Limit graph size for performance
            if graph.number_of_nodes() > max_nodes:
                logger.warning(f"Graph has {graph.number_of_nodes()} nodes, limiting to {max_nodes} for visualization")
                graph = self._limit_graph_size(graph, max_nodes)
            
            # Calculate layout positions
            pos = self._calculate_layout(graph, layout)
            
            # Get analysis data
            metrics = analyzer.calculate_metrics()
            circular_deps = metrics.circular_dependencies
            hotspots = analyzer.find_dependency_hotspots()
            
            # Create the figure
            fig = go.Figure()
            
            # Add edges
            self._add_edges(fig, graph, pos, color_scheme, circular_deps if highlight_circular else [])
            
            # Add nodes
            self._add_nodes(fig, graph, pos, color_scheme, hotspots if highlight_hotspots else [], circular_deps if highlight_circular else [])
            
            # Update layout
            self._update_layout(fig, color_scheme, graph.number_of_nodes(), graph.number_of_edges())
            
            # Add annotations for metrics
            self._add_metrics_annotation(fig, metrics)
            
            return fig
        
        except Exception as e:
            logger.error(f"Error creating dependency visualization: {e}")
            return self._create_error_figure(str(e))
    
    def _limit_graph_size(self, graph: nx.DiGraph, max_nodes: int) -> nx.DiGraph:
        """Limit graph size by selecting most connected nodes."""
        try:
            # Get nodes by degree (most connected first)
            degrees = graph.degree()
            sorted_nodes = sorted(degrees, key=lambda x: x[1], reverse=True)
            
            # Select top nodes
            selected_nodes = [node for node, degree in sorted_nodes[:max_nodes]]
            
            # Create subgraph
            return graph.subgraph(selected_nodes).copy()
        
        except Exception as e:
            logger.error(f"Error limiting graph size: {e}")
            return graph
    
    def _calculate_layout(self, graph: nx.DiGraph, layout: str) -> Dict[str, Tuple[float, float]]:
        """Calculate node positions using specified layout algorithm."""
        try:
            if layout == 'spring':
                return nx.spring_layout(graph, k=1, iterations=50)
            elif layout == 'circular':
                return nx.circular_layout(graph)
            elif layout == 'hierarchical':
                # Try to use hierarchical layout if graph is DAG
                if nx.is_directed_acyclic_graph(graph):
                    return nx.nx_agraph.graphviz_layout(graph, prog='dot')
                else:
                    # Fall back to spring layout
                    return nx.spring_layout(graph, k=1, iterations=50)
            else:
                return nx.spring_layout(graph, k=1, iterations=50)
        
        except Exception as e:
            logger.warning(f"Error calculating {layout} layout, falling back to spring: {e}")
            try:
                return nx.spring_layout(graph, k=1, iterations=50)
            except Exception as e2:
                logger.error(f"Error with fallback layout: {e2}")
                # Create simple grid layout as last resort
                nodes = list(graph.nodes())
                n = len(nodes)
                cols = int(np.ceil(np.sqrt(n)))
                pos = {}
                for i, node in enumerate(nodes):
                    row = i // cols
                    col = i % cols
                    pos[node] = (col, row)
                return pos
    
    def _add_edges(self, fig: go.Figure, graph: nx.DiGraph, pos: Dict, color_scheme: str, circular_deps: List[CircularDependency]):
        """Add edges to the figure."""
        colors = self.color_schemes[color_scheme]
        
        # Get circular dependency edges
        circular_edges = set()
        for circular_dep in circular_deps:
            cycle = circular_dep.cycle
            for i in range(len(cycle)):
                source = cycle[i]
                target = cycle[(i + 1) % len(cycle)]
                circular_edges.add((source, target))
        
        # Separate normal and circular edges
        edge_x_normal = []
        edge_y_normal = []
        edge_x_circular = []
        edge_y_circular = []
        
        for edge in graph.edges():
            source, target = edge
            if source in pos and target in pos:
                x0, y0 = pos[source]
                x1, y1 = pos[target]
                
                if edge in circular_edges:
                    edge_x_circular.extend([x0, x1, None])
                    edge_y_circular.extend([y0, y1, None])
                else:
                    edge_x_normal.extend([x0, x1, None])
                    edge_y_normal.extend([y0, y1, None])
        
        # Add normal edges
        if edge_x_normal:
            fig.add_trace(go.Scatter(
                x=edge_x_normal, y=edge_y_normal,
                line=dict(width=1, color=colors['edges']),
                hoverinfo='none',
                mode='lines',
                name='Dependencies',
                showlegend=True
            ))
        
        # Add circular edges
        if edge_x_circular:
            fig.add_trace(go.Scatter(
                x=edge_x_circular, y=edge_y_circular,
                line=dict(width=2, color=colors['circular']),
                hoverinfo='none',
                mode='lines',
                name='Circular Dependencies',
                showlegend=True
            ))
    
    def _add_nodes(self, fig: go.Figure, graph: nx.DiGraph, pos: Dict, color_scheme: str, 
                   hotspots: List[Dict], circular_deps: List[CircularDependency]):
        """Add nodes to the figure."""
        colors = self.color_schemes[color_scheme]
        
        # Get hotspot nodes
        hotspot_nodes = set()
        if hotspots:
            # Take top 10% as hotspots
            hotspot_count = max(1, len(hotspots) // 10)
            hotspot_nodes = {h['node'] for h in hotspots[:hotspot_count]}
        
        # Get circular dependency nodes
        circular_nodes = set()
        for circular_dep in circular_deps:
            circular_nodes.update(circular_dep.cycle)
        
        # Prepare node data
        node_x = []
        node_y = []
        node_text = []
        node_colors = []
        node_sizes = []
        hover_text = []
        
        for node in graph.nodes():
            if node in pos:
                x, y = pos[node]
                node_x.append(x)
                node_y.append(y)
                
                # Node name (shortened for display)
                display_name = Path(node).name if '/' in node else node
                node_text.append(display_name)
                
                # Node color based on type
                if node in circular_nodes:
                    node_colors.append(colors['circular'])
                elif node in hotspot_nodes:
                    node_colors.append(colors['hotspot'])
                else:
                    node_colors.append(colors['nodes'])
                
                # Node size based on degree
                degree = graph.degree(node)
                node_sizes.append(max(10, min(30, degree * 2 + 10)))
                
                # Hover information
                in_degree = graph.in_degree(node)
                out_degree = graph.out_degree(node)
                hover_info = f"<b>{node}</b><br>"
                hover_info += f"In-degree: {in_degree}<br>"
                hover_info += f"Out-degree: {out_degree}<br>"
                hover_info += f"Total degree: {degree}"
                
                if node in hotspot_nodes:
                    hover_info += "<br><b>Dependency Hotspot</b>"
                if node in circular_nodes:
                    hover_info += "<br><b>Part of Circular Dependency</b>"
                
                hover_text.append(hover_info)
        
        # Add nodes
        fig.add_trace(go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            marker=dict(
                size=node_sizes,
                color=node_colors,
                line=dict(width=1, color='white')
            ),
            text=node_text,
            textposition="middle center",
            textfont=dict(size=8),
            hovertext=hover_text,
            hoverinfo='text',
            name='Files',
            showlegend=False
        ))
    
    def _update_layout(self, fig: go.Figure, color_scheme: str, num_nodes: int, num_edges: int):
        """Update figure layout."""
        colors = self.color_schemes[color_scheme]
        
        fig.update_layout(
            title=dict(
                text=f"Dependency Graph ({num_nodes} files, {num_edges} dependencies)",
                x=0.5,
                font=dict(size=16)
            ),
            showlegend=True,
            hovermode='closest',
            margin=dict(b=20, l=5, r=5, t=40),
            annotations=[
                dict(
                    text="Drag to pan, scroll to zoom, hover for details",
                    showarrow=False,
                    xref="paper", yref="paper",
                    x=0.005, y=-0.002,
                    xanchor='left', yanchor='bottom',
                    font=dict(size=10, color='gray')
                )
            ],
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor=colors['background'],
            paper_bgcolor=colors['background']
        )
    
    def _add_metrics_annotation(self, fig: go.Figure, metrics: DependencyMetrics):
        """Add metrics annotation to the figure."""
        metrics_text = f"<b>Graph Metrics:</b><br>"
        metrics_text += f"Nodes: {metrics.total_nodes}<br>"
        metrics_text += f"Edges: {metrics.total_edges}<br>"
        metrics_text += f"Circular Dependencies: {len(metrics.circular_dependencies)}<br>"
        metrics_text += f"Density: {metrics.density:.3f}<br>"
        metrics_text += f"Avg Degree: {metrics.average_degree:.1f}"
        
        fig.add_annotation(
            text=metrics_text,
            xref="paper", yref="paper",
            x=0.02, y=0.98,
            xanchor='left', yanchor='top',
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="gray",
            borderwidth=1,
            font=dict(size=10)
        )
    
    def create_circular_dependency_report(self, circular_deps: List[CircularDependency]) -> go.Figure:
        """Create a detailed report of circular dependencies."""
        try:
            if not circular_deps:
                return self._create_no_circular_deps_figure()
            
            # Create subplots
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=(
                    'Circular Dependencies by Severity',
                    'Cycle Length Distribution',
                    'Severity Distribution',
                    'Top Circular Dependencies'
                ),
                specs=[[{"type": "bar"}, {"type": "histogram"}],
                       [{"type": "pie"}, {"type": "table"}]]
            )
            
            # Severity counts
            severity_counts = {'high': 0, 'medium': 0, 'low': 0}
            cycle_lengths = []
            
            for dep in circular_deps:
                severity_counts[dep.severity] += 1
                cycle_lengths.append(dep.cycle_length)
            
            # Bar chart of severity
            fig.add_trace(
                go.Bar(
                    x=list(severity_counts.keys()),
                    y=list(severity_counts.values()),
                    marker_color=['red', 'orange', 'yellow'],
                    name='Severity Count'
                ),
                row=1, col=1
            )
            
            # Histogram of cycle lengths
            fig.add_trace(
                go.Histogram(
                    x=cycle_lengths,
                    nbinsx=10,
                    name='Cycle Lengths'
                ),
                row=1, col=2
            )
            
            # Pie chart of severity distribution
            fig.add_trace(
                go.Pie(
                    labels=list(severity_counts.keys()),
                    values=list(severity_counts.values()),
                    marker_colors=['red', 'orange', 'yellow']
                ),
                row=2, col=1
            )
            
            # Table of top circular dependencies
            top_deps = sorted(circular_deps, key=lambda x: (
                {'high': 3, 'medium': 2, 'low': 1}[x.severity],
                x.cycle_length
            ), reverse=True)[:10]
            
            table_data = []
            for dep in top_deps:
                cycle_str = " → ".join(dep.cycle[:3]) + ("..." if len(dep.cycle) > 3 else "")
                table_data.append([dep.severity, dep.cycle_length, cycle_str])
            
            fig.add_trace(
                go.Table(
                    header=dict(values=['Severity', 'Length', 'Cycle']),
                    cells=dict(values=list(zip(*table_data)) if table_data else [[], [], []])
                ),
                row=2, col=2
            )
            
            fig.update_layout(
                title_text="Circular Dependencies Analysis",
                showlegend=False,
                height=800
            )
            
            return fig
        
        except Exception as e:
            logger.error(f"Error creating circular dependency report: {e}")
            return self._create_error_figure(str(e))
    
    def create_dependency_metrics_dashboard(self, metrics: DependencyMetrics, hotspots: List[Dict]) -> go.Figure:
        """Create a comprehensive metrics dashboard."""
        try:
            # Create subplots
            fig = make_subplots(
                rows=2, cols=3,
                subplot_titles=(
                    'Graph Overview',
                    'Dependency Hotspots',
                    'Strongly Connected Components',
                    'Graph Density & Modularity',
                    'Degree Distribution',
                    'Component Sizes'
                ),
                specs=[[{"type": "indicator"}, {"type": "bar"}, {"type": "bar"}],
                       [{"type": "bar"}, {"type": "histogram"}, {"type": "pie"}]]
            )
            
            # Graph overview indicators
            fig.add_trace(
                go.Indicator(
                    mode="number+gauge+delta",
                    value=metrics.total_nodes,
                    title={"text": "Total Files"},
                    gauge={'axis': {'range': [None, metrics.total_nodes * 1.2]}}
                ),
                row=1, col=1
            )
            
            # Dependency hotspots
            if hotspots:
                top_hotspots = hotspots[:10]
                hotspot_names = [Path(h['node']).name for h in top_hotspots]
                hotspot_degrees = [h['total_degree'] for h in top_hotspots]
                
                fig.add_trace(
                    go.Bar(
                        x=hotspot_names,
                        y=hotspot_degrees,
                        name='Hotspots'
                    ),
                    row=1, col=2
                )
            
            # Strongly connected components
            scc_sizes = [len(component) for component in metrics.strongly_connected_components]
            if scc_sizes:
                fig.add_trace(
                    go.Bar(
                        x=list(range(1, len(scc_sizes) + 1)),
                        y=scc_sizes,
                        name='SCC Sizes'
                    ),
                    row=1, col=3
                )
            
            # Density and modularity
            fig.add_trace(
                go.Bar(
                    x=['Density', 'Modularity'],
                    y=[metrics.density, metrics.modularity],
                    name='Graph Metrics'
                ),
                row=2, col=1
            )
            
            # Update layout
            fig.update_layout(
                title_text="Dependency Metrics Dashboard",
                showlegend=False,
                height=800
            )
            
            return fig
        
        except Exception as e:
            logger.error(f"Error creating metrics dashboard: {e}")
            return self._create_error_figure(str(e))
    
    def _create_no_circular_deps_figure(self) -> go.Figure:
        """Create figure for when no circular dependencies are found."""
        fig = go.Figure()
        fig.add_annotation(
            text="✅ No circular dependencies found!<br>Your codebase has a clean dependency structure.",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            xanchor='center', yanchor='middle',
            font=dict(size=16, color='green'),
            bgcolor="rgba(144,238,144,0.2)",
            bordercolor="green",
            borderwidth=2
        )
        fig.update_layout(
            title="Circular Dependencies Analysis",
            xaxis=dict(visible=False),
            yaxis=dict(visible=False)
        )
        return fig
    
    def _create_error_figure(self, error_message: str) -> go.Figure:
        """Create an error figure."""
        fig = go.Figure()
        fig.add_annotation(
            text=f"❌ Error creating visualization:<br>{error_message}",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            xanchor='center', yanchor='middle',
            font=dict(size=14, color='red'),
            bgcolor="rgba(255,182,193,0.2)",
            bordercolor="red",
            borderwidth=2
        )
        fig.update_layout(
            title="Visualization Error",
            xaxis=dict(visible=False),
            yaxis=dict(visible=False)
        )
        return fig
    
    def save_visualization(self, fig: go.Figure, output_path: str, format: str = 'html'):
        """Save visualization to file."""
        try:
            if format.lower() == 'html':
                fig.write_html(output_path)
            elif format.lower() == 'png':
                fig.write_image(output_path)
            elif format.lower() == 'pdf':
                fig.write_image(output_path)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            logger.info(f"Visualization saved to {output_path}")
        
        except Exception as e:
            logger.error(f"Error saving visualization: {e}")
            raise