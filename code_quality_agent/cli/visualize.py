"""
CLI commands for dependency graph visualization.
"""

import click
import logging
from pathlib import Path
from typing import Optional

from code_quality_agent.visualization import (
    DependencyGraphGenerator, DependencyAnalyzer, GraphVisualizer
)

logger = logging.getLogger(__name__)


@click.group()
def visualize():
    """Dependency visualization commands."""
    pass


@visualize.command()
@click.argument('codebase_path', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='Output file for visualization')
@click.option('--format', '-f', type=click.Choice(['html', 'png', 'pdf']), default='html', help='Output format')
@click.option('--layout', '-l', type=click.Choice(['spring', 'circular', 'hierarchical']), default='spring', help='Graph layout algorithm')
@click.option('--color-scheme', '-c', type=click.Choice(['default', 'dark']), default='default', help='Color scheme')
@click.option('--max-nodes', '-n', type=int, default=100, help='Maximum number of nodes to display')
@click.option('--languages', help='Comma-separated list of languages to analyze (e.g., python,javascript)')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def dependencies(codebase_path: str, output: Optional[str], format: str, layout: str, 
                color_scheme: str, max_nodes: int, languages: Optional[str], verbose: bool):
    """Generate interactive dependency graph visualization."""
    
    if verbose:
        logging.basicConfig(level=logging.INFO)
    
    click.echo("🔍 Analyzing codebase dependencies...")
    
    try:
        # Determine file patterns
        if languages:
            lang_patterns = {
                'python': '*.py',
                'javascript': '*.js',
                'typescript': '*.ts',
                'java': '*.java',
                'cpp': '*.cpp',
                'c': '*.c'
            }
            
            selected_langs = [lang.strip().lower() for lang in languages.split(',')]
            include_patterns = []
            
            for lang in selected_langs:
                if lang in lang_patterns:
                    include_patterns.append(lang_patterns[lang])
                else:
                    click.echo(f"⚠️  Unknown language: {lang}")
            
            if not include_patterns:
                include_patterns = ['*.py']  # Default to Python
        else:
            include_patterns = ['*.py', '*.js', '*.ts']  # Default patterns
        
        click.echo(f"📁 Analyzing files: {', '.join(include_patterns)}")
        
        # Generate dependency graph
        generator = DependencyGraphGenerator()
        graph = generator.analyze_codebase(codebase_path, include_patterns)
        
        if graph.number_of_nodes() == 0:
            click.echo("❌ No dependencies found in the codebase")
            click.echo("   Make sure the codebase contains files with the specified patterns")
            return
        
        click.echo(f"📊 Found {graph.number_of_nodes()} files with {graph.number_of_edges()} dependencies")
        
        # Analyze dependencies
        analyzer = DependencyAnalyzer(graph)
        metrics = analyzer.calculate_metrics()
        circular_deps = analyzer.find_circular_dependencies()
        hotspots = analyzer.find_dependency_hotspots()
        
        # Display analysis summary
        click.echo(f"\n📈 Dependency Analysis Summary:")
        click.echo(f"   Total files: {metrics.total_nodes}")
        click.echo(f"   Total dependencies: {metrics.total_edges}")
        click.echo(f"   Circular dependencies: {len(circular_deps)}")
        click.echo(f"   Dependency hotspots: {len(hotspots)}")
        click.echo(f"   Graph density: {metrics.density:.3f}")
        click.echo(f"   Average degree: {metrics.average_degree:.1f}")
        
        if circular_deps:
            click.echo(f"\n🔄 Circular Dependencies Found:")
            for i, dep in enumerate(circular_deps[:5], 1):
                cycle_str = " → ".join(dep.cycle[:3]) + ("..." if len(dep.cycle) > 3 else "")
                click.echo(f"   {i}. [{dep.severity.upper()}] {cycle_str}")
            
            if len(circular_deps) > 5:
                click.echo(f"   ... and {len(circular_deps) - 5} more")
        
        if hotspots:
            click.echo(f"\n🔥 Top Dependency Hotspots:")
            for i, hotspot in enumerate(hotspots[:5], 1):
                file_name = Path(hotspot['node']).name
                click.echo(f"   {i}. {file_name} (degree: {hotspot['total_degree']})")
        
        # Create visualization
        try:
            visualizer = GraphVisualizer()
            
            click.echo(f"\n🎨 Creating visualization...")
            fig = visualizer.create_dependency_visualization(
                graph, 
                analyzer,
                layout=layout,
                color_scheme=color_scheme,
                highlight_circular=True,
                highlight_hotspots=True,
                max_nodes=max_nodes
            )
            
            # Save visualization
            if output:
                output_path = output
            else:
                codebase_name = Path(codebase_path).name
                output_path = f"dependency_graph_{codebase_name}.{format}"
            
            visualizer.save_visualization(fig, output_path, format)
            click.echo(f"💾 Visualization saved to: {output_path}")
            
            if format == 'html':
                click.echo("🌐 Open the HTML file in your browser to view the interactive graph")
            
        except ImportError as e:
            click.echo(f"❌ Visualization library not available: {e}")
            click.echo("   Install plotly with: pip install plotly")
            
            # Still show text-based analysis
            click.echo(f"\n📋 Text-based Analysis:")
            if circular_deps:
                click.echo(f"\nCircular Dependencies:")
                for dep in circular_deps:
                    click.echo(f"  - {dep.description}")
        
        click.echo("✅ Dependency analysis completed successfully!")
    
    except Exception as e:
        click.echo(f"❌ Analysis failed: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        raise click.ClickException(str(e))


@visualize.command()
@click.argument('codebase_path', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='Output file for circular dependency report')
@click.option('--format', '-f', type=click.Choice(['html', 'png', 'pdf']), default='html', help='Output format')
@click.option('--languages', help='Comma-separated list of languages to analyze')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def circular(codebase_path: str, output: Optional[str], format: str, 
            languages: Optional[str], verbose: bool):
    """Analyze and visualize circular dependencies."""
    
    if verbose:
        logging.basicConfig(level=logging.INFO)
    
    click.echo("🔄 Analyzing circular dependencies...")
    
    try:
        # Determine file patterns
        if languages:
            lang_patterns = {
                'python': '*.py',
                'javascript': '*.js',
                'typescript': '*.ts'
            }
            
            selected_langs = [lang.strip().lower() for lang in languages.split(',')]
            include_patterns = [lang_patterns.get(lang, '*.py') for lang in selected_langs]
        else:
            include_patterns = ['*.py', '*.js', '*.ts']
        
        # Generate dependency graph
        generator = DependencyGraphGenerator()
        graph = generator.analyze_codebase(codebase_path, include_patterns)
        
        if graph.number_of_nodes() == 0:
            click.echo("❌ No dependencies found in the codebase")
            return
        
        # Analyze for circular dependencies
        analyzer = DependencyAnalyzer(graph)
        circular_deps = analyzer.find_circular_dependencies()
        
        if not circular_deps:
            click.echo("✅ No circular dependencies found!")
            click.echo("   Your codebase has a clean dependency structure.")
            return
        
        # Display circular dependencies
        click.echo(f"🔄 Found {len(circular_deps)} circular dependencies:")
        
        severity_counts = {'high': 0, 'medium': 0, 'low': 0}
        for dep in circular_deps:
            severity_counts[dep.severity] += 1
        
        click.echo(f"   High severity: {severity_counts['high']}")
        click.echo(f"   Medium severity: {severity_counts['medium']}")
        click.echo(f"   Low severity: {severity_counts['low']}")
        
        click.echo(f"\nTop circular dependencies:")
        for i, dep in enumerate(circular_deps[:10], 1):
            cycle_str = " → ".join(dep.cycle)
            click.echo(f"   {i}. [{dep.severity.upper()}] {cycle_str}")
        
        # Create visualization
        try:
            visualizer = GraphVisualizer()
            
            click.echo(f"\n🎨 Creating circular dependency report...")
            fig = visualizer.create_circular_dependency_report(circular_deps)
            
            # Save report
            if output:
                output_path = output
            else:
                codebase_name = Path(codebase_path).name
                output_path = f"circular_dependencies_{codebase_name}.{format}"
            
            visualizer.save_visualization(fig, output_path, format)
            click.echo(f"💾 Report saved to: {output_path}")
            
        except ImportError as e:
            click.echo(f"❌ Visualization library not available: {e}")
            click.echo("   Install plotly with: pip install plotly")
        
        click.echo("✅ Circular dependency analysis completed!")
    
    except Exception as e:
        click.echo(f"❌ Analysis failed: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        raise click.ClickException(str(e))


@visualize.command()
@click.argument('codebase_path', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='Output file for metrics dashboard')
@click.option('--format', '-f', type=click.Choice(['html', 'png', 'pdf']), default='html', help='Output format')
@click.option('--languages', help='Comma-separated list of languages to analyze')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def metrics(codebase_path: str, output: Optional[str], format: str, 
           languages: Optional[str], verbose: bool):
    """Generate dependency metrics dashboard."""
    
    if verbose:
        logging.basicConfig(level=logging.INFO)
    
    click.echo("📊 Generating dependency metrics dashboard...")
    
    try:
        # Determine file patterns
        if languages:
            lang_patterns = {
                'python': '*.py',
                'javascript': '*.js',
                'typescript': '*.ts'
            }
            
            selected_langs = [lang.strip().lower() for lang in languages.split(',')]
            include_patterns = [lang_patterns.get(lang, '*.py') for lang in selected_langs]
        else:
            include_patterns = ['*.py', '*.js', '*.ts']
        
        # Generate dependency graph
        generator = DependencyGraphGenerator()
        graph = generator.analyze_codebase(codebase_path, include_patterns)
        
        if graph.number_of_nodes() == 0:
            click.echo("❌ No dependencies found in the codebase")
            return
        
        # Analyze dependencies
        analyzer = DependencyAnalyzer(graph)
        metrics = analyzer.calculate_metrics()
        hotspots = analyzer.find_dependency_hotspots()
        
        # Display metrics
        click.echo(f"\n📈 Dependency Metrics:")
        click.echo(f"   Total files: {metrics.total_nodes}")
        click.echo(f"   Total dependencies: {metrics.total_edges}")
        click.echo(f"   Graph density: {metrics.density:.3f}")
        click.echo(f"   Average degree: {metrics.average_degree:.1f}")
        click.echo(f"   Max depth: {metrics.max_depth}")
        click.echo(f"   Modularity: {metrics.modularity:.3f}")
        click.echo(f"   Strongly connected components: {len(metrics.strongly_connected_components)}")
        
        # Create dashboard
        try:
            visualizer = GraphVisualizer()
            
            click.echo(f"\n🎨 Creating metrics dashboard...")
            fig = visualizer.create_dependency_metrics_dashboard(metrics, hotspots)
            
            # Save dashboard
            if output:
                output_path = output
            else:
                codebase_name = Path(codebase_path).name
                output_path = f"dependency_metrics_{codebase_name}.{format}"
            
            visualizer.save_visualization(fig, output_path, format)
            click.echo(f"💾 Dashboard saved to: {output_path}")
            
        except ImportError as e:
            click.echo(f"❌ Visualization library not available: {e}")
            click.echo("   Install plotly with: pip install plotly")
        
        click.echo("✅ Metrics dashboard generated successfully!")
    
    except Exception as e:
        click.echo(f"❌ Analysis failed: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        raise click.ClickException(str(e))


if __name__ == '__main__':
    visualize()