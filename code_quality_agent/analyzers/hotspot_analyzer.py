"""Hotspot analyzer for identifying code churn and complexity hotspots."""

import logging
import subprocess
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import re

from .base import QualityAnalyzer, IssueCategory
from ..core.models import (
    Issue, ParsedFile, AnalysisContext, CodeLocation, Severity,
    GitCommit, FileChurnMetrics, HotspotAnalysis
)

logger = logging.getLogger(__name__)


class HotspotAnalyzer(QualityAnalyzer):
    """Analyzer for detecting code hotspots based on churn and complexity."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the hotspot analyzer."""
        super().__init__(config)
        config = config or {}
        self.min_commits_threshold = config.get("min_commits_threshold", 5)
        self.hotspot_percentile = config.get("hotspot_percentile", 0.8)
        self.analysis_period_days = config.get("analysis_period_days", 365)
        self.complexity_weight = config.get("complexity_weight", 0.6)
        self.churn_weight = config.get("churn_weight", 0.4)
    
    def get_supported_languages(self) -> List[str]:
        """Return supported programming languages."""
        return ["python", "javascript", "typescript", "java", "cpp", "c", "go", "rust"]
    
    def get_category(self) -> IssueCategory:
        """Return the issue category."""
        return IssueCategory.HOTSPOT
    
    def analyze(self, parsed_files: List[ParsedFile], context: AnalysisContext) -> List[Issue]:
        """
        Analyze files for hotspots based on git history and complexity.
        
        Args:
            parsed_files: List of parsed code files
            context: Analysis context
            
        Returns:
            List of hotspot-related issues
        """
        issues = []
        
        try:
            # Get git repository root
            repo_root = self._find_git_root(context.options.to_dict().get("codebase_path", "."))
            if not repo_root:
                logger.warning("No git repository found, skipping hotspot analysis")
                return issues
            
            # Analyze git history for churn metrics
            churn_metrics = self._analyze_git_churn(repo_root, parsed_files)
            
            # Calculate complexity scores for files
            complexity_scores = self._calculate_complexity_scores(parsed_files)
            
            # Combine churn and complexity to identify hotspots
            hotspot_analysis = self._identify_hotspots(churn_metrics, complexity_scores)
            
            # Generate issues for hotspots
            issues.extend(self._generate_hotspot_issues(hotspot_analysis, parsed_files))
            
            # Store hotspot analysis in context for reporting
            if hasattr(context, 'hotspot_analysis'):
                context.hotspot_analysis = hotspot_analysis
            
        except Exception as e:
            logger.error(f"Error in hotspot analysis: {e}")
        
        return issues
    
    def _find_git_root(self, start_path: str) -> Optional[str]:
        """Find the git repository root directory."""
        current_path = Path(start_path).resolve()
        
        while current_path != current_path.parent:
            if (current_path / ".git").exists():
                return str(current_path)
            current_path = current_path.parent
        
        return None
    
    def _analyze_git_churn(self, repo_root: str, parsed_files: List[ParsedFile]) -> Dict[str, FileChurnMetrics]:
        """Analyze git history to calculate file churn metrics."""
        churn_metrics = {}
        
        # Get cutoff date for analysis
        cutoff_date = datetime.now() - timedelta(days=self.analysis_period_days)
        cutoff_str = cutoff_date.strftime("%Y-%m-%d")
        
        for parsed_file in parsed_files:
            try:
                file_path = parsed_file.path
                relative_path = os.path.relpath(file_path, repo_root)
                
                # Get git log for the file
                cmd = [
                    "git", "-C", repo_root, "log",
                    f"--since={cutoff_str}",
                    "--numstat",
                    "--pretty=format:%H|%an|%ad|%s",
                    "--date=iso",
                    "--", relative_path
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                if result.returncode != 0:
                    logger.debug(f"Git log failed for {relative_path}: {result.stderr}")
                    continue
                
                commits = self._parse_git_log_output(result.stdout)
                if not commits:
                    continue
                
                # Calculate churn metrics
                metrics = self._calculate_file_churn_metrics(file_path, commits)
                if metrics.total_commits >= self.min_commits_threshold:
                    churn_metrics[file_path] = metrics
                
            except Exception as e:
                logger.debug(f"Error analyzing churn for {parsed_file.path}: {e}")
        
        return churn_metrics
    
    def _parse_git_log_output(self, output: str) -> List[GitCommit]:
        """Parse git log output into commit objects."""
        commits = []
        lines = output.strip().split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue
            
            # Parse commit info line
            if '|' in line:
                parts = line.split('|', 3)
                if len(parts) >= 4:
                    commit_hash = parts[0]
                    author = parts[1]
                    date_str = parts[2]
                    message = parts[3]
                    
                    try:
                        # Parse date
                        date = datetime.fromisoformat(date_str.replace(' +', '+').replace(' -', '-'))
                        
                        # Look for numstat lines (next non-empty lines)
                        files_changed = []
                        i += 1
                        while i < len(lines):
                            if i >= len(lines):
                                break
                            stat_line = lines[i].strip()
                            if not stat_line:
                                # Empty line indicates end of this commit's stats
                                break
                            if '\t' in stat_line:
                                # This is a numstat line: additions\tdeletions\tfilename
                                stat_parts = stat_line.split('\t', 2)
                                if len(stat_parts) >= 3:
                                    files_changed.append(stat_parts[2])
                                i += 1
                            elif '|' in stat_line:
                                # This is the next commit line, don't increment i
                                break
                            else:
                                i += 1
                        
                        commit = GitCommit(
                            hash=commit_hash,
                            author=author,
                            date=date,
                            message=message,
                            files_changed=files_changed
                        )
                        commits.append(commit)
                        
                        # Don't increment i here as it might be pointing to the next commit
                        continue
                        
                    except Exception as e:
                        logger.debug(f"Error parsing commit {commit_hash}: {e}")
            
            i += 1
        
        return commits
    
    def _calculate_file_churn_metrics(self, file_path: str, commits: List[GitCommit]) -> FileChurnMetrics:
        """Calculate churn metrics for a file based on its commit history."""
        if not commits:
            return FileChurnMetrics(
                file_path=file_path,
                total_commits=0,
                unique_authors=0,
                lines_added=0,
                lines_deleted=0,
                first_commit_date=datetime.now(),
                last_commit_date=datetime.now(),
                change_frequency=0.0
            )
        
        # Sort commits by date
        sorted_commits = sorted(commits, key=lambda c: c.date)
        
        # Calculate basic metrics
        total_commits = len(commits)
        unique_authors = len(set(commit.author for commit in commits))
        first_commit_date = sorted_commits[0].date
        last_commit_date = sorted_commits[-1].date
        
        # Calculate change frequency (commits per day)
        time_span = (last_commit_date - first_commit_date).days
        change_frequency = total_commits / max(time_span, 1)
        
        # Get detailed stats using git log --numstat
        lines_added, lines_deleted = self._get_detailed_churn_stats(file_path, commits)
        
        return FileChurnMetrics(
            file_path=file_path,
            total_commits=total_commits,
            unique_authors=unique_authors,
            lines_added=lines_added,
            lines_deleted=lines_deleted,
            first_commit_date=first_commit_date,
            last_commit_date=last_commit_date,
            change_frequency=change_frequency
        )
    
    def _get_detailed_churn_stats(self, file_path: str, commits: List[GitCommit]) -> Tuple[int, int]:
        """Get detailed line addition/deletion statistics for a file."""
        try:
            repo_root = self._find_git_root(file_path)
            if not repo_root:
                return 0, 0
            
            relative_path = os.path.relpath(file_path, repo_root)
            
            # Get cutoff date
            cutoff_date = datetime.now() - timedelta(days=self.analysis_period_days)
            cutoff_str = cutoff_date.strftime("%Y-%m-%d")
            
            cmd = [
                "git", "-C", repo_root, "log",
                f"--since={cutoff_str}",
                "--numstat",
                "--pretty=format:",
                "--", relative_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                return 0, 0
            
            lines_added = 0
            lines_deleted = 0
            
            for line in result.stdout.strip().split('\n'):
                line = line.strip()
                if line and '\t' in line:
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        try:
                            added = int(parts[0]) if parts[0] != '-' else 0
                            deleted = int(parts[1]) if parts[1] != '-' else 0
                            lines_added += added
                            lines_deleted += deleted
                        except ValueError:
                            continue
            
            return lines_added, lines_deleted
            
        except Exception as e:
            logger.debug(f"Error getting detailed churn stats for {file_path}: {e}")
            return 0, 0
    
    def _calculate_complexity_scores(self, parsed_files: List[ParsedFile]) -> Dict[str, float]:
        """Calculate complexity scores for parsed files."""
        complexity_scores = {}
        
        for parsed_file in parsed_files:
            try:
                total_complexity = 0
                total_functions = 0
                
                # Calculate average complexity from functions
                for function in parsed_file.functions:
                    total_complexity += function.complexity
                    total_functions += 1
                
                # Add class method complexity
                for cls in parsed_file.classes:
                    for method in cls.methods:
                        total_complexity += method.complexity
                        total_functions += 1
                
                # Calculate average complexity
                if total_functions > 0:
                    avg_complexity = total_complexity / total_functions
                else:
                    # Use line count as a proxy for complexity
                    avg_complexity = len(parsed_file.content.splitlines()) / 100.0
                
                complexity_scores[parsed_file.path] = avg_complexity
                
            except Exception as e:
                logger.debug(f"Error calculating complexity for {parsed_file.path}: {e}")
                complexity_scores[parsed_file.path] = 0.0
        
        return complexity_scores
    
    def _identify_hotspots(
        self, 
        churn_metrics: Dict[str, FileChurnMetrics], 
        complexity_scores: Dict[str, float]
    ) -> HotspotAnalysis:
        """Identify hotspots by combining churn and complexity metrics."""
        
        # Normalize churn scores
        if churn_metrics:
            max_churn = max(metrics.change_frequency for metrics in churn_metrics.values())
            max_commits = max(metrics.total_commits for metrics in churn_metrics.values())
        else:
            max_churn = max_commits = 1.0
        
        # Normalize complexity scores
        if complexity_scores:
            max_complexity = max(complexity_scores.values())
        else:
            max_complexity = 1.0
        
        # Calculate hotspot scores
        hotspot_scores = {}
        
        for file_path in set(churn_metrics.keys()) | set(complexity_scores.keys()):
            churn_score = 0.0
            complexity_score = 0.0
            
            if file_path in churn_metrics:
                metrics = churn_metrics[file_path]
                churn_score = (
                    (metrics.change_frequency / max_churn) * 0.5 +
                    (metrics.total_commits / max_commits) * 0.5
                )
                # Update the churn metrics with complexity score
                metrics.complexity_score = complexity_scores.get(file_path, 0.0)
            
            if file_path in complexity_scores:
                complexity_score = complexity_scores[file_path] / max_complexity
            
            # Combined hotspot score
            hotspot_score = (
                self.churn_weight * churn_score +
                self.complexity_weight * complexity_score
            )
            
            hotspot_scores[file_path] = hotspot_score
            
            # Update churn metrics with hotspot score
            if file_path in churn_metrics:
                churn_metrics[file_path].hotspot_score = hotspot_score
        
        # Identify hotspots based on percentile threshold
        if hotspot_scores:
            sorted_scores = sorted(hotspot_scores.values(), reverse=True)
            threshold_index = int(len(sorted_scores) * (1 - self.hotspot_percentile))
            threshold_score = sorted_scores[threshold_index] if threshold_index < len(sorted_scores) else 0
            
            hotspot_files = [
                file_path for file_path, score in hotspot_scores.items()
                if score >= threshold_score
            ]
        else:
            hotspot_files = []
        
        # Separate complexity and churn hotspots
        complexity_hotspots = []
        churn_hotspots = []
        
        if complexity_scores:
            complexity_threshold = sorted(complexity_scores.values(), reverse=True)[
                int(len(complexity_scores) * (1 - self.hotspot_percentile))
            ] if complexity_scores else 0
            
            complexity_hotspots = [
                file_path for file_path, score in complexity_scores.items()
                if score >= complexity_threshold
            ]
        
        if churn_metrics:
            churn_scores = {path: metrics.change_frequency for path, metrics in churn_metrics.items()}
            churn_threshold = sorted(churn_scores.values(), reverse=True)[
                int(len(churn_scores) * (1 - self.hotspot_percentile))
            ] if churn_scores else 0
            
            churn_hotspots = [
                file_path for file_path, score in churn_scores.items()
                if score >= churn_threshold
            ]
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            hotspot_files, complexity_hotspots, churn_hotspots, churn_metrics
        )
        
        return HotspotAnalysis(
            file_churn_metrics=list(churn_metrics.values()),
            hotspot_files=hotspot_files,
            complexity_hotspots=complexity_hotspots,
            churn_hotspots=churn_hotspots,
            recommendations=recommendations
        )
    
    def _generate_recommendations(
        self,
        hotspot_files: List[str],
        complexity_hotspots: List[str],
        churn_hotspots: List[str],
        churn_metrics: Dict[str, FileChurnMetrics]
    ) -> List[str]:
        """Generate recommendations based on hotspot analysis."""
        recommendations = []
        
        if hotspot_files:
            recommendations.append(
                f"Found {len(hotspot_files)} hotspot files that combine high complexity with frequent changes. "
                "These files should be prioritized for refactoring and increased test coverage."
            )
        
        if complexity_hotspots:
            recommendations.append(
                f"Identified {len(complexity_hotspots)} files with high complexity. "
                "Consider breaking down large functions and classes to improve maintainability."
            )
        
        if churn_hotspots:
            recommendations.append(
                f"Found {len(churn_hotspots)} files with high change frequency. "
                "These files may benefit from additional documentation and code reviews."
            )
        
        # Specific recommendations for high-churn files
        high_churn_files = [
            path for path, metrics in churn_metrics.items()
            if metrics.change_frequency > 0.1  # More than 1 change per 10 days
        ]
        
        if high_churn_files:
            recommendations.append(
                f"Files with very high change frequency ({len(high_churn_files)} files) "
                "should be monitored closely and may indicate design issues or unstable requirements."
            )
        
        # Multi-author files
        multi_author_files = [
            path for path, metrics in churn_metrics.items()
            if metrics.unique_authors > 5
        ]
        
        if multi_author_files:
            recommendations.append(
                f"Files modified by many developers ({len(multi_author_files)} files) "
                "should have clear coding standards and comprehensive documentation."
            )
        
        return recommendations
    
    def _generate_hotspot_issues(
        self, 
        hotspot_analysis: HotspotAnalysis, 
        parsed_files: List[ParsedFile]
    ) -> List[Issue]:
        """Generate issues for identified hotspots."""
        issues = []
        
        # Create a mapping of file paths to parsed files
        file_map = {pf.path: pf for pf in parsed_files}
        
        # Generate issues for hotspot files
        for file_path in hotspot_analysis.hotspot_files:
            if file_path in file_map:
                parsed_file = file_map[file_path]
                
                # Find corresponding churn metrics
                churn_metrics = None
                for metrics in hotspot_analysis.file_churn_metrics:
                    if metrics.file_path == file_path:
                        churn_metrics = metrics
                        break
                
                # Only flag as hotspot if it meets substantial criteria
                should_flag = False
                severity = Severity.LOW
                
                if churn_metrics:
                    # Flag if high churn or complexity
                    if churn_metrics.total_changes > 10 or churn_metrics.complexity_score > 15:
                        should_flag = True
                        severity = Severity.MEDIUM if churn_metrics.total_changes > 20 else Severity.LOW
                else:
                    # Fallback: only flag files with substantial complexity
                    function_count = len(parsed_file.functions)
                    class_count = len(parsed_file.classes)
                    line_count = parsed_file.metadata.line_count if parsed_file.metadata else 0
                    
                    if function_count >= 5 or class_count >= 3 or line_count >= 100:
                        should_flag = True
                        severity = Severity.LOW
                
                if not should_flag:
                    continue  # Skip this file
                
                issue = Issue(
                    id="",  # Will be auto-generated
                    category=IssueCategory.HOTSPOT,
                    severity=severity,
                    title=f"Code Hotspot Detected: {os.path.basename(file_path)}",
                    description=self._create_hotspot_description(churn_metrics, parsed_file),
                    location=CodeLocation(
                        file_path=file_path,
                        line_start=1,
                        line_end=len(parsed_file.content.splitlines())
                    ),
                    affected_files=[file_path],
                    suggestion=self._create_hotspot_suggestion(churn_metrics, parsed_file),
                    confidence=0.8,
                    metadata={
                        "hotspot_score": churn_metrics.hotspot_score if churn_metrics else 0.0,
                        "complexity_score": churn_metrics.complexity_score if churn_metrics else 0.0,
                        "change_frequency": churn_metrics.change_frequency if churn_metrics else 0.0,
                        "total_commits": churn_metrics.total_commits if churn_metrics else 0,
                        "unique_authors": churn_metrics.unique_authors if churn_metrics else 0,
                    }
                )
                issues.append(issue)
        
        return issues
    
    def _create_hotspot_description(
        self, 
        churn_metrics: Optional[FileChurnMetrics], 
        parsed_file: ParsedFile
    ) -> str:
        """Create a description for a hotspot issue."""
        description = f"This file has been identified as a code hotspot due to a combination of high complexity and frequent changes."
        
        if churn_metrics:
            description += f"\n\nChurn Analysis:"
            description += f"\n- Total commits in last {self.analysis_period_days} days: {churn_metrics.total_commits}"
            description += f"\n- Unique authors: {churn_metrics.unique_authors}"
            description += f"\n- Change frequency: {churn_metrics.change_frequency:.3f} commits/day"
            description += f"\n- Lines added: {churn_metrics.lines_added}"
            description += f"\n- Lines deleted: {churn_metrics.lines_deleted}"
            description += f"\n- Hotspot score: {churn_metrics.hotspot_score:.3f}"
        
        description += f"\n\nComplexity Analysis:"
        description += f"\n- Functions: {len(parsed_file.functions)}"
        description += f"\n- Classes: {len(parsed_file.classes)}"
        description += f"\n- Lines of code: {len(parsed_file.content.splitlines())}"
        
        return description
    
    def _create_hotspot_suggestion(
        self, 
        churn_metrics: Optional[FileChurnMetrics], 
        parsed_file: ParsedFile
    ) -> str:
        """Create a suggestion for addressing a hotspot."""
        suggestions = []
        
        if churn_metrics and churn_metrics.change_frequency > 0.1:
            suggestions.append("Consider stabilizing the API and requirements for this frequently changing file")
        
        if churn_metrics and churn_metrics.unique_authors > 3:
            suggestions.append("Establish clear coding standards and review processes for this multi-author file")
        
        if len(parsed_file.functions) > 10:
            suggestions.append("Break down large functions into smaller, more focused units")
        
        if len(parsed_file.classes) > 5:
            suggestions.append("Consider splitting this file into multiple modules")
        
        if len(parsed_file.content.splitlines()) > 500:
            suggestions.append("This file is quite large; consider refactoring into smaller modules")
        
        suggestions.extend([
            "Increase test coverage for this critical file",
            "Add comprehensive documentation",
            "Consider implementing design patterns to reduce coupling",
            "Monitor this file closely in code reviews"
        ])
        
        return " • ".join(suggestions)