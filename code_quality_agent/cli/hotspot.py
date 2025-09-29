"""CLI command for hotspot analysis and visualization."""

import click
import logging
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..analyzers.hotspot_analyzer import HotspotAnalyzer
from ..visualization.hotspot_visualizer import HotspotVisualizer
from ..core.models import AnalysisOptions, AnalysisContext, ParsedFile
from ..parsers.unified_parser import UnifiedCodeParser
from ..utils.file_utils import discover_files

console = Console()
logger = logging.getLogger(__name__)


@click.command()
@click.argument('path', type=click.Path(exists=True))
@click.option(
    '--output-dir', '-o',
    type=click.Path(),
    help='Directory to save hotspot analysis results and visualizations'
)
@click.option(
    '--min-commits', '-m',
    type=int,
    default=5,
    help='Minimum number of commits required to consider a file for hotspot analysis'
)
@click.option(
    '--period-days', '-p',
    type=int,
    default=365,
    help='Number of days to look back for git history analysis'
)
@click.option(
    '--hotspot-threshold', '-t',
    type=float,
    default=0.8,
    help='Percentile threshold for identifying hotspots (0.0-1.0)'
)
@click.option(
    '--visualize/--no-visualize',
    default=True,
    help='Generate visualizations for hotspot analysis'
)
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help='Enable verbose output'
)
def hotspot(
    path: str,
    output_dir: Optional[str],
    min_commits: int,
    period_days: int,
    hotspot_threshold: float,
    visualize: bool,
    verbose: bool
) -> None:
    """
    Analyze code hotspots based on git history and complexity.
    
    This command identifies files that are both complex and frequently changed,
    which are often good candidates for refactoring and increased attention.
    
    PATH: Path to the codebase (file or directory) to analyze
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    console.print(Panel.fit(
        "[bold blue]Code Hotspot Analysis[/bold blue]\n"
        f"Analyzing: {path}\n"
        f"Period: {period_days} days\n"
        f"Min commits: {min_commits}\n"
        f"Hotspot threshold: {hotspot_threshold}",
        border_style="blue"
    ))
    
    try:
        # Set up output directory
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
        else:
            output_path = Path.cwd() / "hotspot_analysis"
            output_path.mkdir(exist_ok=True)
        
        # Initialize analyzer with configuration
        analyzer_config = {
            "min_commits_threshold": min_commits,
            "analysis_period_days": period_days,
            "hotspot_percentile": hotspot_threshold,
            "complexity_weight": 0.6,
            "churn_weight": 0.4
        }
        
        analyzer = HotspotAnalyzer(analyzer_config)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            # Discover files
            task1 = progress.add_task("Discovering files...", total=None)
            
            analysis_options = AnalysisOptions(
                include_patterns=["*.py", "*.js", "*.ts", "*.jsx", "*.tsx"],
                exclude_patterns=[
                    "node_modules/**", ".git/**", "__pycache__/**", "*.pyc",
                    ".venv/**", "venv/**", "build/**", "dist/**"
                ]
            )
            
            files = discover_files(
                Path(path), 
                analysis_options.include_patterns,
                analysis_options.exclude_patterns
            )
            progress.update(task1, description=f"Found {len(files)} files")
            
            # Parse files
            task2 = progress.add_task("Parsing files...", total=len(files))
            
            parser = UnifiedCodeParser()
            parsed_files = []
            
            for i, file_path in enumerate(files):
                try:
                    parsed_file = parser.parse_file(file_path)
                    if parsed_file:
                        parsed_files.append(parsed_file)
                except Exception as e:
                    if verbose:
                        console.print(f"[yellow]Warning: Could not parse {file_path}: {e}[/yellow]")
                
                progress.update(task2, advance=1)
            
            progress.update(task2, description=f"Parsed {len(parsed_files)} files")
            
            # Run hotspot analysis
            task3 = progress.add_task("Analyzing hotspots...", total=None)
            
            context = AnalysisContext(options=analysis_options)
            issues = analyzer.analyze(parsed_files, context)
            
            progress.update(task3, description=f"Found {len(issues)} hotspot issues")
        
        # Display results
        if issues:
            _display_hotspot_results(issues, analyzer, console)
        else:
            console.print("[yellow]No hotspots detected with current thresholds.[/yellow]")
        
        # Generate visualizations if requested
        if visualize and hasattr(context, 'hotspot_analysis'):
            console.print("\n[blue]Generating visualizations...[/blue]")
            
            visualizer = HotspotVisualizer()
            report_data = visualizer.generate_hotspot_report(
                context.hotspot_analysis,
                output_path
            )
            
            console.print(f"[green]Visualizations saved to: {output_path}[/green]")
            
            # Display visualization info
            if report_data.get("visualizations"):
                viz_table = Table(title="Generated Visualizations")
                viz_table.add_column("Type", style="cyan")
                viz_table.add_column("File", style="green")
                
                for viz_type, file_path in report_data["visualizations"].items():
                    viz_table.add_row(viz_type.title(), str(file_path))
                
                console.print(viz_table)
        
        # Save analysis results
        results_file = output_path / "hotspot_analysis.json"
        with open(results_file, 'w') as f:
            import json
            json.dump({
                "issues": [issue.to_dict() for issue in issues],
                "config": analyzer_config,
                "files_analyzed": len(parsed_files),
                "hotspots_found": len(issues)
            }, f, indent=2)
        
        console.print(f"\n[green]Analysis complete! Results saved to: {output_path}[/green]")
        
    except Exception as e:
        console.print(f"[red]Error during hotspot analysis: {e}[/red]")
        if verbose:
            console.print_exception()
        raise click.ClickException(str(e))


def _display_hotspot_results(issues, analyzer, console):
    """Display hotspot analysis results in a formatted table."""
    
    # Create summary table
    summary_table = Table(title="Hotspot Analysis Summary")
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Value", style="green")
    
    summary_table.add_row("Total Hotspots Found", str(len(issues)))
    summary_table.add_row("Analysis Period", f"{analyzer.analysis_period_days} days")
    summary_table.add_row("Min Commits Threshold", str(analyzer.min_commits_threshold))
    summary_table.add_row("Hotspot Percentile", f"{analyzer.hotspot_percentile:.1%}")
    
    console.print(summary_table)
    
    # Create detailed hotspots table
    if issues:
        hotspots_table = Table(title="Detected Hotspots")
        hotspots_table.add_column("File", style="cyan", no_wrap=True)
        hotspots_table.add_column("Hotspot Score", style="red")
        hotspots_table.add_column("Complexity", style="yellow")
        hotspots_table.add_column("Change Freq", style="blue")
        hotspots_table.add_column("Commits", style="green")
        hotspots_table.add_column("Authors", style="magenta")
        
        for issue in sorted(issues, key=lambda x: x.metadata.get("hotspot_score", 0), reverse=True):
            file_name = Path(issue.location.file_path).name
            hotspot_score = issue.metadata.get("hotspot_score", 0)
            complexity_score = issue.metadata.get("complexity_score", 0)
            change_frequency = issue.metadata.get("change_frequency", 0)
            total_commits = issue.metadata.get("total_commits", 0)
            unique_authors = issue.metadata.get("unique_authors", 0)
            
            hotspots_table.add_row(
                file_name,
                f"{hotspot_score:.3f}",
                f"{complexity_score:.1f}",
                f"{change_frequency:.3f}",
                str(total_commits),
                str(unique_authors)
            )
        
        console.print(hotspots_table)
        
        # Show top recommendations
        if issues:
            console.print("\n[bold blue]Top Recommendations:[/bold blue]")
            for i, issue in enumerate(issues[:3], 1):
                console.print(f"{i}. [yellow]{Path(issue.location.file_path).name}[/yellow]")
                console.print(f"   {issue.suggestion}")
                console.print()


if __name__ == "__main__":
    hotspot()