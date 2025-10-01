"""Main CLI interface for the Code Quality Intelligence Agent."""

import sys
import os
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.logging import RichHandler

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv not installed, skip loading
    pass

from ..core.orchestrator import AnalysisOrchestrator
from ..core.models import AnalysisOptions, AnalysisResult, IssueCategory, Severity
from ..reporting.report_generator import ReportGenerator
from ..reporting.formatters import TextFormatter, JSONFormatter, HTMLFormatter
from .interactive import start_interactive_qa
from .validate import validate
from .visualize import visualize
from ..core.error_handling import (
    ErrorHandler, InputValidator, CodeQualityError, 
    InputValidationError, FileAccessError
)


# Configure rich console
console = Console()

# Configure logging
def setup_logging(verbose: bool = False) -> None:
    """Set up logging with rich handler."""
    level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, rich_tracebacks=True)]
    )


@click.group()
@click.version_option(version="1.0.0", prog_name="Code Quality Intelligence Agent")
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="Enable verbose output and debug logging"
)
@click.pass_context
def cli(ctx: click.Context, verbose: bool) -> None:
    """
    Code Quality Intelligence Agent - AI-powered code analysis tool.
    
    Analyze your codebase for security, performance, complexity, and other quality issues
    with intelligent explanations and actionable recommendations.
    """
    # Ensure context object exists
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    
    # Set up logging
    setup_logging(verbose)


@cli.command()
@click.argument('path', type=click.Path(exists=True, path_type=Path), required=False)
@click.option(
    '--output-format', '-f',
    type=click.Choice(['cli', 'json', 'html'], case_sensitive=False),
    default='cli',
    help='Output format for the analysis report'
)
@click.option(
    '--output-file', '-o',
    type=click.Path(path_type=Path),
    help='Output file path (default: stdout for CLI, auto-generated for others)'
)
@click.option(
    '--languages', '-l',
    multiple=True,
    type=click.Choice(['python', 'javascript', 'typescript'], case_sensitive=False),
    help='Filter analysis to specific programming languages'
)
@click.option(
    '--include-patterns',
    multiple=True,
    help='File patterns to include (e.g., "*.py", "src/**/*.js")'
)
@click.option(
    '--exclude-patterns',
    multiple=True,
    help='File patterns to exclude (e.g., "node_modules/**", "*.test.js")'
)
@click.option(
    '--categories', '-c',
    multiple=True,
    type=click.Choice([cat.value for cat in IssueCategory], case_sensitive=False),
    help='Filter analysis to specific issue categories'
)
@click.option(
    '--min-severity',
    type=click.Choice([sev.value for sev in Severity], case_sensitive=False),
    default='info',
    help='Minimum severity level for reported issues'
)
@click.option(
    '--max-workers',
    type=int,
    default=4,
    help='Maximum number of parallel workers for analysis'
)
@click.option(
    '--no-cache',
    is_flag=True,
    help='Disable caching and force fresh analysis'
)
@click.option(
    '--confidence-threshold',
    type=float,
    default=0.7,
    help='Minimum confidence threshold for reported issues (0.0-1.0)'
)
@click.option(
    '--explanations',
    is_flag=True,
    help='Enable AI-powered explanations (slower but more detailed)'
)
@click.option(
    '--suggestions',
    is_flag=True,
    help='Enable AI-powered fix suggestions (slower but more detailed)'
)
@click.option(
    '--max-issues',
    type=int,
    help='Maximum number of issues to report'
)
@click.option(
    '--github',
    type=str,
    help='Analyze a GitHub repository by URL (e.g., https://github.com/user/repo)'
)
@click.pass_context
def analyze(
    ctx: click.Context,
    path: Optional[Path],
    output_format: str,
    output_file: Optional[Path],
    languages: tuple,
    include_patterns: tuple,
    exclude_patterns: tuple,
    categories: tuple,
    min_severity: str,
    max_workers: int,
    no_cache: bool,
    confidence_threshold: float,
    explanations: bool,
    suggestions: bool,
    max_issues: Optional[int],
    github: Optional[str]
) -> None:
    """
    Analyze code quality for the specified PATH.
    
    PATH can be a file, directory, or repository root. The tool will recursively
    analyze all supported files and generate a comprehensive quality report.
    
    Examples:
    
        # Analyze current directory with default settings
        codeql analyze .
        
        # Analyze specific directory with JSON output
        codeql analyze /path/to/project -f json -o report.json
        
        # Analyze only Python files with high severity issues
        codeql analyze . -l python --min-severity high
        
        # Analyze with custom patterns and categories
        codeql analyze . --include-patterns "src/**/*.py" -c security -c performance
    """
    verbose = ctx.obj.get('verbose', False)
    error_handler = ErrorHandler(verbose=verbose)
    
    try:
        # Validate that either path or github is provided
        if not path and not github:
            raise click.BadParameter("Either PATH argument or --github option must be provided")
        
        if path and github:
            raise click.BadParameter("Cannot use both PATH argument and --github option simultaneously")
        
        # Validate inputs using the error handling system
        InputValidator.validate_numeric_range(confidence_threshold, 0.0, 1.0, "confidence threshold")
        
        if max_workers < 1:
            raise InputValidationError(
                "Max workers must be at least 1",
                suggestions=[
                    "Use a positive integer for max workers",
                    "Try --max-workers 4 for optimal performance"
                ]
            )
        
        # Handle GitHub repository analysis
        if github:
            analysis_path = Path(handle_github_analysis(github))
        else:
            # Validate and convert path
            analysis_path = InputValidator.validate_path(str(path))
        
        # Validate file types
        InputValidator.validate_file_types(analysis_path)
        
        # Display analysis start message
        console.print(Panel.fit(
            f"[bold blue]Code Quality Intelligence Agent[/bold blue]\n"
            f"Analyzing: [cyan]{analysis_path}[/cyan]\n"
            f"Output format: [green]{output_format.upper()}[/green]",
            title="Analysis Started",
            border_style="blue"
        ))
        
        # Create analysis options
        options = create_analysis_options(
            languages=list(languages),
            include_patterns=list(include_patterns) if include_patterns else None,
            exclude_patterns=list(exclude_patterns) if exclude_patterns else None,
            categories=list(categories) if categories else None,
            min_severity=Severity(min_severity),
            max_workers=max_workers,
            use_cache=not no_cache,
            confidence_threshold=confidence_threshold,
            include_explanations=explanations,
            include_suggestions=suggestions
        )
        
        # Run analysis with progress tracking
        result = run_analysis_with_progress(str(analysis_path), options, verbose)
        
        # Generate and output report
        output_report(result, output_format, output_file, verbose, max_issues, categories, min_severity, explanations, suggestions)
        
        # Display summary
        display_analysis_summary(result)
        
    except (CodeQualityError, click.BadParameter) as e:
        # Handle known errors with user-friendly feedback
        if isinstance(e, click.BadParameter):
            # Convert Click errors to our error system
            error_handler.handle_error(InputValidationError(str(e)))
        else:
            error_handler.handle_error(e, "Analysis command")
        
        error_handler.display_error_summary()
        sys.exit(1)
        
    except Exception as e:
        # Handle unexpected errors
        recoverable = error_handler.handle_error(e, "Analysis command")
        error_handler.display_error_summary()
        
        if not recoverable:
            console.print("\n[red]This appears to be a serious error. Please report this issue.[/red]")
        
        sys.exit(1)


def create_analysis_options(
    languages: Optional[List[str]] = None,
    include_patterns: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None,
    categories: Optional[List[str]] = None,
    min_severity: Severity = Severity.INFO,
    max_workers: int = 4,
    use_cache: bool = True,
    confidence_threshold: float = 0.7,
    include_explanations: bool = True,
    include_suggestions: bool = True
) -> AnalysisOptions:
    """Create analysis options from CLI parameters."""
    
    # Default include patterns
    default_include = ['*.py', '*.js', '*.ts', '*.jsx', '*.tsx']
    if languages:
        # Filter patterns based on selected languages
        lang_patterns = {
            'python': ['*.py'],
            'javascript': ['*.js', '*.jsx'],
            'typescript': ['*.ts', '*.tsx']
        }
        default_include = []
        for lang in languages:
            default_include.extend(lang_patterns.get(lang, []))
    
    # Default exclude patterns
    default_exclude = [
        'node_modules/**', '.git/**', '__pycache__/**', '*.pyc',
        '.venv/**', 'venv/**', 'build/**', 'dist/**', '.pytest_cache/**',
        'coverage/**', '.coverage', '*.egg-info/**'
    ]
    
    return AnalysisOptions(
        include_patterns=include_patterns or default_include,
        exclude_patterns=(exclude_patterns or []) + default_exclude,
        parallel_processing=max_workers > 1,
        max_workers=max_workers,
        use_cache=use_cache,
        confidence_threshold=confidence_threshold,
        max_file_size_mb=10,
        include_explanations=include_explanations,
        include_suggestions=include_suggestions
    )


def run_analysis_with_progress(
    path: str,
    options: AnalysisOptions,
    verbose: bool = False
) -> AnalysisResult:
    """Run analysis with rich progress indicators."""
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
        transient=False
    ) as progress:
        
        # Create orchestrator
        orchestrator = AnalysisOrchestrator()
        
        # Add progress tracking
        main_task = progress.add_task("Initializing analysis...", total=100)
        
        try:
            # Update progress for different phases
            progress.update(main_task, description="Discovering files...", completed=10)
            
            # Start analysis
            progress.update(main_task, description="Parsing code...", completed=25)
            
            # Run the actual analysis
            result = orchestrator.analyze_codebase(path, options)
            
            progress.update(main_task, description="Running quality analyzers...", completed=60)
            
            # Simulate progress updates (in real implementation, orchestrator would provide callbacks)
            progress.update(main_task, description="Generating explanations...", completed=80)
            
            progress.update(main_task, description="Finalizing report...", completed=95)
            
            progress.update(main_task, description="Analysis complete!", completed=100)
            
            return result
            
        except Exception as e:
            progress.update(main_task, description=f"Analysis failed: {str(e)}")
            raise


def output_report(
    result: AnalysisResult,
    output_format: str,
    output_file: Optional[Path],
    verbose: bool = False,
    max_issues: Optional[int] = None,
    categories: Optional[List[str]] = None,
    min_severity: Optional[Severity] = None,
    explanations: bool = False,
    suggestions: bool = False
) -> None:
    """Generate and output the analysis report."""
    
    # Apply category filtering
    if categories:
        category_enums = [IssueCategory(cat) for cat in categories]
        result.issues = [issue for issue in result.issues if issue.category in category_enums]
    
    # Apply severity filtering
    if min_severity:
        # Convert string to Severity enum if needed
        if isinstance(min_severity, str):
            min_severity = Severity(min_severity)
        
        severity_levels = {
            Severity.INFO: 0,
            Severity.LOW: 1, 
            Severity.MEDIUM: 2,
            Severity.HIGH: 3,
            Severity.CRITICAL: 4
        }
        min_level = severity_levels.get(min_severity, 0)
        result.issues = [issue for issue in result.issues 
                        if severity_levels.get(issue.severity, 0) >= min_level]
    
    # Recalculate metrics after filtering
    if categories or min_severity:
        from ..core.orchestrator import AnalysisOrchestrator
        orchestrator = AnalysisOrchestrator()
        result.metrics = orchestrator._calculate_quality_metrics(result.issues, result.parsed_files)
    
    # Limit issues if max_issues is specified
    if max_issues is not None and max_issues > 0:
        result.issues = result.issues[:max_issues]
    
    # Create report generator
    # Disable LLM enhancements if both explanations and suggestions are disabled
    enable_llm = explanations or suggestions
    report_generator = ReportGenerator(enable_llm_enhancements=enable_llm)
    report = report_generator.generate_report(
        result,
        include_explanations=explanations,
        include_suggestions=suggestions
    )
    
    # Select formatter
    if output_format == 'cli':
        formatter = TextFormatter(use_colors=False)
        content = formatter.format_report(report)
        
        if output_file:
            output_file.write_text(content)
            console.print(f"[green]Report saved to:[/green] {output_file}")
        else:
            console.print(content)
            
    elif output_format == 'json':
        formatter = JSONFormatter()
        content = formatter.format_report(report)
        
        if not output_file:
            output_file = Path(f"quality_report_{result.analysis_id[:8]}.json")
        
        output_file.write_text(content)
        console.print(f"[green]JSON report saved to:[/green] {output_file}")
        
    elif output_format == 'html':
        formatter = HTMLFormatter()
        content = formatter.format_report(report)
        
        if not output_file:
            output_file = Path(f"quality_report_{result.analysis_id[:8]}.html")
        
        output_file.write_text(content)
        console.print(f"[green]HTML report saved to:[/green] {output_file}")


def display_analysis_summary(result: AnalysisResult) -> None:
    """Display a summary of the analysis results."""
    
    # Create summary table
    table = Table(title="Analysis Summary", show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", style="green")
    
    # Add summary rows
    table.add_row("Files Analyzed", str(len(result.parsed_files)))
    table.add_row("Total Issues", str(len(result.issues)))
    
    # Use smart score priority: maintainability_index if overall_score is 0
    display_score = result.metrics.overall_score
    if display_score <= 0 and hasattr(result.metrics, 'maintainability_index'):
        display_score = result.metrics.maintainability_index
    
    # Round to match Web UI display (87 instead of 87.1)
    table.add_row("Overall Quality Score", f"{round(display_score)}/100")
    
    # Add issue breakdown by category
    category_counts = {}
    severity_counts = {}
    
    for issue in result.issues:
        category_counts[issue.category.value] = category_counts.get(issue.category.value, 0) + 1
        severity_counts[issue.severity.value] = severity_counts.get(issue.severity.value, 0) + 1
    
    # Add category breakdown
    if category_counts:
        table.add_section()
        for category, count in sorted(category_counts.items()):
            table.add_row(f"{category.title()} Issues", str(count))
    
    # Add severity breakdown
    if severity_counts:
        table.add_section()
        for severity, count in sorted(severity_counts.items(), 
                                    key=lambda x: ['critical', 'high', 'medium', 'low', 'info'].index(x[0])):
            table.add_row(f"{severity.title()} Severity", str(count))
    
    console.print(table)
    
    # Add recommendations
    if result.issues:
        high_priority_issues = [i for i in result.issues if i.severity in [Severity.CRITICAL, Severity.HIGH]]
        if high_priority_issues:
            console.print(Panel(
                f"[bold red]⚠️  Found {len(high_priority_issues)} high-priority issues that need immediate attention![/bold red]",
                title="Recommendations",
                border_style="red"
            ))
        else:
            console.print(Panel(
                "[bold green]✅ No critical issues found. Consider addressing medium and low priority items for improved code quality.[/bold green]",
                title="Recommendations",
                border_style="green"
            ))
    else:
        console.print(Panel(
            "[bold green]🎉 Excellent! No quality issues detected in your codebase.[/bold green]",
            title="Results",
            border_style="green"
        ))


@cli.command()
@click.argument('path', type=click.Path(exists=True, path_type=Path))
@click.option(
    '--languages', '-l',
    multiple=True,
    type=click.Choice(['python', 'javascript', 'typescript'], case_sensitive=False),
    help='Filter analysis to specific programming languages'
)
@click.option(
    '--max-workers',
    type=int,
    default=4,
    help='Maximum number of parallel workers for analysis'
)
@click.option(
    '--no-cache',
    is_flag=True,
    help='Disable caching and force fresh analysis'
)
@click.pass_context
def qa(
    ctx: click.Context,
    path: Path,
    languages: tuple,
    max_workers: int,
    no_cache: bool
) -> None:
    """
    Start interactive Q&A session for the specified PATH.
    
    This command will analyze the codebase and then start an interactive shell
    where you can ask natural language questions about your code quality,
    issues, and get AI-powered insights.
    
    Examples:
    
        # Start Q&A session for current directory
        codeql qa .
        
        # Analyze only Python files and start Q&A
        codeql qa /path/to/project -l python
        
        # Force fresh analysis and start Q&A
        codeql qa . --no-cache
    """
    verbose = ctx.obj.get('verbose', False)
    error_handler = ErrorHandler(verbose=verbose)
    
    try:
        # Validate and convert path
        analysis_path = InputValidator.validate_path(str(path))
        
        # Validate file types
        InputValidator.validate_file_types(analysis_path)
        
        # Display analysis start message
        console.print(Panel.fit(
            f"[bold blue]Code Quality Intelligence Agent - Q&A Mode[/bold blue]\n"
            f"Analyzing: [cyan]{analysis_path}[/cyan]\n"
            f"Preparing interactive Q&A session...",
            title="Analysis & Q&A Setup",
            border_style="blue"
        ))
        
        # Create analysis options (simplified for Q&A mode)
        options = create_analysis_options(
            languages=list(languages),
            max_workers=max_workers,
            use_cache=not no_cache,
            include_explanations=True,  # Always include for Q&A
            include_suggestions=True   # Always include for Q&A
        )
        
        # Run analysis with progress tracking
        result = run_analysis_with_progress(str(analysis_path), options, verbose)
        
        console.print("[green]✅ Analysis complete! Starting interactive Q&A session...[/green]")
        
        # Start interactive Q&A session
        start_interactive_qa(result)
        
    except CodeQualityError as e:
        # Handle known errors with user-friendly feedback
        error_handler.handle_error(e, "Q&A command")
        error_handler.display_error_summary()
        sys.exit(1)
        
    except Exception as e:
        # Handle unexpected errors
        recoverable = error_handler.handle_error(e, "Q&A command")
        error_handler.display_error_summary()
        
        if not recoverable:
            console.print("\n[red]This appears to be a serious error. Please report this issue.[/red]")
        
        sys.exit(1)


@cli.command()
@click.argument('path', type=click.Path(exists=True, path_type=Path))
@click.pass_context
def info(ctx: click.Context, path: Path) -> None:
    """
    Display information about a codebase without running full analysis.
    
    Shows basic statistics like file count, languages detected, and estimated analysis time.
    """
    verbose = ctx.obj.get('verbose', False)
    error_handler = ErrorHandler(verbose=verbose)
    
    try:
        # Validate path
        analysis_path = InputValidator.validate_path(str(path))
        
        console.print(Panel.fit(
            f"[bold blue]Codebase Information[/bold blue]\n"
            f"Path: [cyan]{analysis_path}[/cyan]",
            title="Info",
            border_style="blue"
        ))
        
        # Quick file discovery
        from ..core.file_discovery import discover_files
        
        files = discover_files(str(analysis_path))
        
        # Language detection
        languages = set()
        total_size = 0
        
        for file_path in files:
            try:
                file_size = os.path.getsize(file_path)
                total_size += file_size
                
                # Simple language detection based on extension
                ext = Path(file_path).suffix.lower()
                if ext == '.py':
                    languages.add('Python')
                elif ext in ['.js', '.jsx']:
                    languages.add('JavaScript')
                elif ext in ['.ts', '.tsx']:
                    languages.add('TypeScript')
                    
            except (OSError, IOError):
                continue
        
        # Display info table
        info_table = Table(show_header=True, header_style="bold magenta")
        info_table.add_column("Property", style="cyan")
        info_table.add_column("Value", style="green")
        
        info_table.add_row("Total Files", str(len(files)))
        info_table.add_row("Languages", ", ".join(sorted(languages)) if languages else "Unknown")
        info_table.add_row("Total Size", f"{total_size / 1024:.1f} KB")
        
        # Estimate analysis time
        estimated_time = max(5, len(files) * 0.1)  # Rough estimate
        info_table.add_row("Estimated Analysis Time", f"~{estimated_time:.0f} seconds")
        
        console.print(info_table)
        
    except CodeQualityError as e:
        # Handle known errors with user-friendly feedback
        error_handler.handle_error(e, "Info command")
        error_handler.display_error_summary()
        sys.exit(1)
        
    except Exception as e:
        # Handle unexpected errors
        recoverable = error_handler.handle_error(e, "Info command")
        error_handler.display_error_summary()
        
        if not recoverable:
            console.print("\n[red]This appears to be a serious error. Please report this issue.[/red]")
        
        sys.exit(1)


def handle_github_analysis(github_url: str) -> str:
    """Handle GitHub repository analysis by cloning the repo."""
    import tempfile
    import subprocess
    
    try:
        from ..utils.validation import validate_github_url
        
        console.print(f"[blue]Cloning GitHub repository:[/blue] {github_url}")
        
        # Validate GitHub URL
        validate_github_url(github_url)
        
        # Create temporary directory for cloning
        temp_dir = tempfile.mkdtemp(prefix="cqa_github_")
        
        # Clone repository using git directly
        cmd = [
            'git', 'clone',
            '--depth', '1',  # Shallow clone for faster download
            '--single-branch',
            github_url,
            temp_dir
        ]
        
        console.print("[blue]Downloading repository...[/blue]")
        
        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if process.returncode != 0:
            error_msg = process.stderr if process.stderr else "Unknown git error"
            raise RuntimeError(f"Git clone failed: {error_msg}")
        
        console.print(f"[green]Repository cloned to:[/green] {temp_dir}")
        return temp_dir
        
    except Exception as e:
        console.print(f"[red]Failed to clone GitHub repository:[/red] {e}")
        sys.exit(1)


# Add validation commands
cli.add_command(validate)

# Add visualization commands
cli.add_command(visualize)

# Add hotspot analysis command
from .hotspot import hotspot
cli.add_command(hotspot)

# Add server command
from .server import server
cli.add_command(server)


if __name__ == '__main__':
    cli()