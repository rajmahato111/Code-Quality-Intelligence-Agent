"""Analysis orchestrator that coordinates the entire analysis workflow."""

from typing import List, Dict, Any, Optional, Callable
from pathlib import Path
import logging
import time
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed, ProcessPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timedelta

from .models import (
    AnalysisResult, AnalysisOptions, AnalysisStatus, ParsedFile, 
    AnalysisContext, QualityMetrics, Issue, IssueCategory
)
from .cache_manager import CacheManager
from .error_handling import (
    ErrorHandler, ParsingError, AnalysisError, ResourceError,
    CodeQualityError
)
from ..analyzers.base import QualityAnalyzer
from ..analyzers.analyzer_registry import analyzer_registry, AnalyzerPriority
from ..analyzers.registry_init import ensure_analyzers_initialized
from ..parsers.unified_parser import UnifiedCodeParser
from ..utils.file_utils import discover_files, detect_language


logger = logging.getLogger(__name__)


@dataclass
class AnalysisProgress:
    """Tracks progress of an analysis operation."""
    analysis_id: str
    status: AnalysisStatus
    current_phase: str
    files_processed: int
    total_files: int
    analyzers_completed: int
    total_analyzers: int
    start_time: datetime
    estimated_completion: Optional[datetime] = None
    error_message: Optional[str] = None
    
    @property
    def progress_percentage(self) -> float:
        """Calculate overall progress percentage."""
        if self.total_files == 0 and self.total_analyzers == 0:
            return 0.0
        
        # Weight parsing and analysis phases
        parsing_weight = 0.3
        analysis_weight = 0.7
        
        parsing_progress = (self.files_processed / max(self.total_files, 1)) * parsing_weight
        analysis_progress = (self.analyzers_completed / max(self.total_analyzers, 1)) * analysis_weight
        
        return min((parsing_progress + analysis_progress) * 100, 100.0)
    
    @property
    def elapsed_time(self) -> timedelta:
        """Get elapsed time since analysis started."""
        return datetime.now() - self.start_time


class AnalysisOrchestrator:
    """Coordinates the entire analysis workflow with parallel processing and progress tracking."""
    
    def __init__(
        self, 
        enable_caching: bool = True,
        cache_dir: Optional[Path] = None,
        cache_ttl_hours: int = 24,
        enable_incremental_analysis: bool = True
    ):
        """
        Initialize the orchestrator.
        
        Args:
            enable_caching: Whether to enable analysis result caching
            cache_dir: Directory for persistent cache storage
            cache_ttl_hours: Time-to-live for cache entries in hours
            enable_incremental_analysis: Whether to enable incremental analysis
        """
        # Ensure analyzers are initialized
        ensure_analyzers_initialized()
        
        self.unified_parser = UnifiedCodeParser()
        self.analyzer_registry = analyzer_registry
        self._progress_trackers: Dict[str, AnalysisProgress] = {}
        self._progress_callbacks: Dict[str, List[Callable]] = {}
        
        # Initialize cache manager
        self.cache_manager = CacheManager(
            cache_dir=cache_dir,
            ttl_hours=cache_ttl_hours,
            enable_persistent_cache=enable_caching
        )
        self.enable_incremental_analysis = enable_incremental_analysis
    
    def register_parser(self, parser) -> None:
        """Register a code parser for specific languages."""
        self.unified_parser.register_parser(parser)
        logger.info(f"Registered parser: {parser.__class__.__name__}")
    
    def register_analyzer(
        self, 
        analyzer: QualityAnalyzer, 
        priority: AnalyzerPriority = AnalyzerPriority.MEDIUM
    ) -> None:
        """
        Register a quality analyzer with the registry.
        
        Args:
            analyzer: The analyzer to register
            priority: Execution priority for the analyzer
        """
        self.analyzer_registry.register_analyzer(analyzer, priority)
    
    def add_progress_callback(self, analysis_id: str, callback: Callable[[AnalysisProgress], None]) -> None:
        """
        Add a progress callback for an analysis.
        
        Args:
            analysis_id: ID of the analysis to track
            callback: Function to call with progress updates
        """
        if analysis_id not in self._progress_callbacks:
            self._progress_callbacks[analysis_id] = []
        self._progress_callbacks[analysis_id].append(callback)
    
    def _update_progress(self, analysis_id: str, **kwargs) -> None:
        """Update progress for an analysis and notify callbacks."""
        if analysis_id in self._progress_trackers:
            progress = self._progress_trackers[analysis_id]
            
            # Update progress attributes
            for key, value in kwargs.items():
                if hasattr(progress, key):
                    setattr(progress, key, value)
            
            # Estimate completion time
            if progress.progress_percentage > 0:
                elapsed = progress.elapsed_time.total_seconds()
                estimated_total = elapsed / (progress.progress_percentage / 100)
                progress.estimated_completion = progress.start_time + timedelta(seconds=estimated_total)
            
            # Notify callbacks
            if analysis_id in self._progress_callbacks:
                for callback in self._progress_callbacks[analysis_id]:
                    try:
                        callback(progress)
                    except Exception as e:
                        logger.warning(f"Progress callback failed: {e}")
    
    def _generate_cache_key(self, path: str, options: AnalysisOptions) -> str:
        """Generate a cache key for analysis results."""
        return self.cache_manager._get_cache_key(path, options)
    
    def analyze_codebase(
        self, 
        path: str, 
        options: AnalysisOptions = None,
        progress_callback: Optional[Callable[[AnalysisProgress], None]] = None
    ) -> AnalysisResult:
        """
        Analyze a codebase and return comprehensive results.
        
        Args:
            path: Path to the codebase (file or directory)
            options: Analysis configuration options
            progress_callback: Optional callback for progress updates
            
        Returns:
            Complete analysis results
        """
        if options is None:
            options = AnalysisOptions()
        
        # Generate analysis ID and check cache (if enabled)
        cache_key = self._generate_cache_key(path, options)
        if options.use_cache:
            cached_result = self.cache_manager.get_cached_analysis_result(cache_key)
            if cached_result:
                logger.info(f"Returning cached analysis result for: {path}")
                return cached_result
        else:
            logger.info(f"Cache disabled, performing fresh analysis for: {path}")
        
        # Initialize progress tracking
        analysis_id = f"analysis_{int(time.time())}"
        progress = AnalysisProgress(
            analysis_id=analysis_id,
            status=AnalysisStatus.IN_PROGRESS,
            current_phase="Initializing",
            files_processed=0,
            total_files=0,
            analyzers_completed=0,
            total_analyzers=0,
            start_time=datetime.now()
        )
        self._progress_trackers[analysis_id] = progress
        
        if progress_callback:
            self.add_progress_callback(analysis_id, progress_callback)
        
        # Initialize error handler for graceful degradation
        error_handler = ErrorHandler(verbose=False)
        parsing_errors = []
        analysis_errors = []
        
        try:
            logger.info(f"Starting analysis of: {path}")
            self._update_progress(analysis_id, current_phase="Discovering files")
            
            # Discover files to analyze
            try:
                files_to_analyze = self._discover_files(Path(path), options)
                logger.info(f"Found {len(files_to_analyze)} files to analyze")
            except Exception as e:
                raise ResourceError(
                    f"Failed to discover files in {path}",
                    resource_type="file_system",
                    suggestions=[
                        "Check that the path exists and is accessible",
                        "Ensure you have read permissions for the directory",
                        "Try with a different path or smaller directory"
                    ]
                ) from e
            
            self._update_progress(
                analysis_id, 
                total_files=len(files_to_analyze),
                current_phase="Parsing files"
            )
            
            # Determine which files need analysis (incremental analysis)
            if self.enable_incremental_analysis:
                changed_files, unchanged_files = self.cache_manager.get_changed_files(files_to_analyze)
                self._update_progress(analysis_id, current_phase=f"Incremental analysis: {len(changed_files)} changed files")
                logger.info(f"Incremental analysis: {len(changed_files)} changed, {len(unchanged_files)} unchanged")
            else:
                changed_files = files_to_analyze
                unchanged_files = []
            
            # Parse files using unified parser with progress tracking and error handling
            parsed_files, parsing_errors = self._parse_files_with_progress_and_errors(
                changed_files, unchanged_files, options, analysis_id
            )
            
            # Handle parsing errors gracefully
            if parsing_errors:
                logger.warning(f"Encountered {len(parsing_errors)} parsing errors")
                for error in parsing_errors[:5]:  # Show first 5 errors
                    error_handler.handle_error(error, "File parsing")
                
                if len(parsing_errors) > 5:
                    logger.warning(f"... and {len(parsing_errors) - 5} more parsing errors")
            
            if not parsed_files:
                raise AnalysisError(
                    "No files could be parsed successfully",
                    analyzer_name="file_parser",
                    technical_details=f"All {len(changed_files)} files failed to parse"
                )
            
            logger.info(f"Successfully parsed {len(parsed_files)} files ({len(parsing_errors)} failed)")
            
            # Get enabled analyzers
            enabled_analyzers = self.analyzer_registry.get_enabled_analyzers()
            self._update_progress(
                analysis_id,
                total_analyzers=len(enabled_analyzers),
                current_phase="Running quality analysis"
            )
            
            # Run quality analysis with progress tracking and error handling
            all_issues, analysis_errors = self._run_analysis_with_progress_and_errors(
                parsed_files, options, analysis_id
            )
            
            # Handle analysis errors gracefully
            if analysis_errors:
                logger.warning(f"Encountered {len(analysis_errors)} analysis errors")
                for error in analysis_errors[:3]:  # Show first 3 errors
                    error_handler.handle_error(error, "Quality analysis")
                
                if len(analysis_errors) > 3:
                    logger.warning(f"... and {len(analysis_errors) - 3} more analysis errors")
            
            logger.info(f"Found {len(all_issues)} total issues ({len(analysis_errors)} analyzer failures)")
            
            self._update_progress(analysis_id, current_phase="Building dependency graph")
            
            # Build dependency graph
            dependency_graph = self.unified_parser.build_dependency_graph(parsed_files)
            
            self._update_progress(analysis_id, current_phase="Calculating metrics")
            
            # Calculate quality metrics
            metrics = self._calculate_quality_metrics(all_issues, parsed_files)
            
            # Create analysis result
            result = AnalysisResult(
                analysis_id=analysis_id,
                codebase_path=path,
                parsed_files=parsed_files,
                issues=all_issues,
                metrics=metrics,
                dependency_graph=dependency_graph,
                options=options
            )
            
            # Cache the result
            if cache_key:
                self.cache_manager.cache_analysis_result(cache_key, result)
            
            self._update_progress(
                analysis_id, 
                status=AnalysisStatus.COMPLETED,
                current_phase="Completed"
            )
            
            logger.info("Analysis completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            self._update_progress(
                analysis_id,
                status=AnalysisStatus.FAILED,
                error_message=str(e)
            )
            raise
        finally:
            # Clean up progress tracking
            if analysis_id in self._progress_callbacks:
                del self._progress_callbacks[analysis_id]
    
    def get_analysis_status(self, analysis_id: str) -> Optional[AnalysisProgress]:
        """
        Get the progress/status of a running analysis.
        
        Args:
            analysis_id: ID of the analysis to check
            
        Returns:
            AnalysisProgress object or None if not found
        """
        return self._progress_trackers.get(analysis_id)
    
    def _discover_files(self, path: Path, options: AnalysisOptions) -> List[Path]:
        """Discover all files that should be analyzed."""
        return discover_files(path, options.include_patterns, options.exclude_patterns)
    
    def _parse_files_with_progress_and_errors(
        self, 
        changed_files: List[Path],
        unchanged_files: List[Path],
        options: AnalysisOptions,
        analysis_id: str
    ) -> tuple[List[ParsedFile], List[CodeQualityError]]:
        """Parse files with progress tracking, incremental analysis, and error handling."""
        parsed_files = []
        parsing_errors = []
        
        # First, load cached results for unchanged files
        for file_path in unchanged_files:
            cached_result = self.cache_manager.get_cached_file_analysis(file_path)
            if cached_result:
                parsed_file, _ = cached_result  # We'll get issues separately
                if parsed_file:
                    parsed_files.append(parsed_file)
        
        logger.info(f"Loaded {len(parsed_files)} files from cache")
        
        # Parse changed files
        if changed_files:
            if options.parallel_processing and len(changed_files) > 1:
                # Use parallel processing for large file sets
                with ThreadPoolExecutor(max_workers=options.max_workers) as executor:
                    future_to_file = {
                        executor.submit(self.unified_parser.parse_file, file_path): file_path
                        for file_path in changed_files
                    }
                    
                    for future in as_completed(future_to_file):
                        file_path = future_to_file[future]
                        try:
                            parsed_file = future.result()
                            if parsed_file:
                                parsed_files.append(parsed_file)
                            
                            # Update progress
                            self._update_progress(
                                analysis_id,
                                files_processed=len(unchanged_files) + len([f for f in parsed_files if f.path in [str(cf) for cf in changed_files]])
                            )
                            
                        except Exception as e:
                            logger.warning(f"Failed to parse {file_path}: {e}")
                            parsing_errors.append(ParsingError(
                                f"Failed to parse {file_path.name}",
                                file_path=str(file_path),
                                technical_details=str(e)
                            ))
            else:
                # Sequential processing
                for i, file_path in enumerate(changed_files):
                    try:
                        parsed_file = self.unified_parser.parse_file(file_path)
                        if parsed_file:
                            parsed_files.append(parsed_file)
                        
                        # Update progress
                        self._update_progress(
                            analysis_id,
                            files_processed=len(unchanged_files) + i + 1
                        )
                        
                    except Exception as e:
                        logger.warning(f"Failed to parse {file_path}: {e}")
                        parsing_errors.append(ParsingError(
                            f"Failed to parse {file_path.name}",
                            file_path=str(file_path),
                            technical_details=str(e)
                        ))
        
        return parsed_files, parsing_errors
    
    def _run_analysis_with_progress_and_errors(
        self, 
        parsed_files: List[ParsedFile], 
        options: AnalysisOptions,
        analysis_id: str
    ) -> tuple[List[Issue], List[CodeQualityError]]:
        """Run all registered analyzers with progress tracking, incremental analysis, and error handling."""
        context = AnalysisContext(options=options)
        all_issues = []
        analysis_errors = []
        
        # Separate files that need analysis from those we can load from cache
        files_needing_analysis = []
        cached_issues = []
        
        if self.enable_incremental_analysis:
            for parsed_file in parsed_files:
                file_path = Path(parsed_file.path)
                cached_result = self.cache_manager.get_cached_file_analysis(file_path)
                
                if cached_result:
                    _, issues = cached_result
                    cached_issues.extend(issues)
                    logger.debug(f"Loaded {len(issues)} cached issues for {file_path}")
                else:
                    files_needing_analysis.append(parsed_file)
            
            all_issues.extend(cached_issues)
            logger.info(f"Loaded {len(cached_issues)} issues from cache")
        else:
            files_needing_analysis = parsed_files
        
        # Run analysis on files that need it
        if files_needing_analysis:
            enabled_analyzers = self.analyzer_registry.get_sorted_analyzers()
            
            if options.parallel_processing and len(enabled_analyzers) > 1:
                # Run analyzers in parallel
                with ThreadPoolExecutor(max_workers=min(options.max_workers, len(enabled_analyzers))) as executor:
                    future_to_analyzer = {}
                    
                    for analyzer in enabled_analyzers:
                        # Filter files by supported languages
                        supported_languages = analyzer.get_supported_languages()
                        relevant_files = [
                            f for f in files_needing_analysis 
                            if f.language in supported_languages
                        ]
                        
                        if relevant_files:
                            future = executor.submit(analyzer.analyze, relevant_files, context)
                            future_to_analyzer[future] = analyzer
                    
                    completed_count = 0
                    for future in as_completed(future_to_analyzer):
                        analyzer = future_to_analyzer[future]
                        try:
                            issues = future.result()
                            all_issues.extend(issues)
                            
                            # Cache issues by file
                            if self.enable_incremental_analysis:
                                self._cache_issues_by_file(issues, files_needing_analysis)
                            
                            logger.debug(f"{analyzer.get_name()} found {len(issues)} issues")
                            
                        except Exception as e:
                            logger.error(f"Analyzer {analyzer.get_name()} failed: {e}")
                            analysis_errors.append(AnalysisError(
                                f"Analyzer '{analyzer.get_name()}' failed to complete",
                                analyzer_name=analyzer.get_name(),
                                technical_details=str(e)
                            ))
                        
                        completed_count += 1
                        self._update_progress(
                            analysis_id,
                            analyzers_completed=completed_count
                        )
            else:
                # Sequential analysis
                for i, analyzer in enumerate(enabled_analyzers):
                    try:
                        # Filter files by supported languages
                        supported_languages = analyzer.get_supported_languages()
                        relevant_files = [
                            f for f in files_needing_analysis 
                            if f.language in supported_languages
                        ]
                        
                        if relevant_files:
                            issues = analyzer.analyze(relevant_files, context)
                            all_issues.extend(issues)
                            
                            # Cache issues by file
                            if self.enable_incremental_analysis:
                                self._cache_issues_by_file(issues, files_needing_analysis)
                            
                            logger.debug(f"{analyzer.get_name()} found {len(issues)} issues")
                        
                        # Update progress
                        self._update_progress(
                            analysis_id,
                            analyzers_completed=i + 1
                        )
                        
                    except Exception as e:
                        logger.error(f"Analyzer {analyzer.get_name()} failed: {e}")
                        analysis_errors.append(AnalysisError(
                            f"Analyzer '{analyzer.get_name()}' failed to complete",
                            analyzer_name=analyzer.get_name(),
                            technical_details=str(e)
                        ))
        
        return all_issues, analysis_errors
    
    def _cache_issues_by_file(self, issues: List[Issue], parsed_files: List[ParsedFile]) -> None:
        """Cache issues organized by file."""
        # Group issues by file
        issues_by_file = {}
        for issue in issues:
            file_path = issue.location.file_path
            if file_path not in issues_by_file:
                issues_by_file[file_path] = []
            issues_by_file[file_path].append(issue)
        
        # Cache each file's analysis results
        for parsed_file in parsed_files:
            file_path = Path(parsed_file.path)
            file_issues = issues_by_file.get(parsed_file.path, [])
            self.cache_manager.cache_file_analysis(file_path, parsed_file, file_issues)
    
    def _calculate_quality_metrics(self, issues: List[Issue], parsed_files: List[ParsedFile]) -> QualityMetrics:
        """Calculate overall quality metrics from analysis results."""
        metrics = QualityMetrics()
        
        if not issues:
            metrics.overall_score = 100.0
            return metrics
        
        # Calculate category scores
        total_issues = len(issues)
        category_counts = {}
        severity_weights = {
            'critical': 10,
            'high': 5,
            'medium': 2,
            'low': 1,
            'info': 0.5
        }
        
        total_weight = 0
        for issue in issues:
            category = issue.category
            if category not in category_counts:
                category_counts[category] = 0
            category_counts[category] += 1
            total_weight += severity_weights.get(issue.severity.value, 1)
        
        # Calculate scores (higher is better, 0-100 scale)
        total_lines = sum(len(f.content.splitlines()) for f in parsed_files)
        if total_lines > 0:
            # Base score calculation: fewer issues per line = higher score
            issue_density = total_weight / total_lines
            metrics.overall_score = max(0, 100 - (issue_density * 1000))  # Scale factor
        
        # Calculate category-specific scores
        for category in IssueCategory:
            category_issues = category_counts.get(category, 0)
            if total_issues > 0:
                category_ratio = category_issues / total_issues
                metrics.category_scores[category] = max(0, 100 - (category_ratio * 100))
            else:
                metrics.category_scores[category] = 100.0
        
        # Calculate maintainability index (simplified)
        avg_complexity = sum(
            len(f.functions) + len(f.classes) for f in parsed_files
        ) / max(len(parsed_files), 1)
        
        metrics.maintainability_index = max(0, 100 - (avg_complexity * 2) - (total_weight / 10))
        
        # Calculate technical debt ratio (issues per 1000 lines)
        if total_lines > 0:
            metrics.technical_debt_ratio = (total_weight / total_lines) * 1000
        
        return metrics
    
    def clear_cache(self) -> None:
        """Clear the analysis cache."""
        self.cache_manager.clear_cache()
        logger.info("Analysis cache cleared")
    
    def cleanup_cache(self) -> int:
        """Clean up expired cache entries."""
        return self.cache_manager.cleanup_expired_entries()
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get detailed statistics about the analysis cache."""
        stats = self.cache_manager.get_cache_statistics()
        stats['incremental_analysis_enabled'] = self.enable_incremental_analysis
        return stats
    
    def force_full_analysis(
        self, 
        path: str, 
        options: AnalysisOptions = None,
        progress_callback: Optional[Callable[[AnalysisProgress], None]] = None
    ) -> AnalysisResult:
        """
        Force a full analysis, bypassing all caches.
        
        Args:
            path: Path to the codebase
            options: Analysis options
            progress_callback: Optional progress callback
            
        Returns:
            Fresh analysis results
        """
        # Temporarily disable incremental analysis
        original_incremental = self.enable_incremental_analysis
        self.enable_incremental_analysis = False
        
        try:
            return self.analyze_codebase(path, options, progress_callback)
        finally:
            self.enable_incremental_analysis = original_incremental