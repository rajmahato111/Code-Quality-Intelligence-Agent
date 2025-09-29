"""Report generator for creating comprehensive code quality reports."""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from ..core.models import (
    AnalysisResult, Issue, IssueCategory, Severity, QualityMetrics, ParsedFile
)
from ..llm.llm_service import LLMService, create_llm_service


logger = logging.getLogger(__name__)


class ReportFormat(Enum):
    """Supported report output formats."""
    TEXT = "text"
    JSON = "json"
    HTML = "html"
    MARKDOWN = "markdown"


@dataclass
class PrioritizedIssue:
    """Issue with priority scoring and enhanced information."""
    issue: Issue
    priority_score: float
    impact_score: float
    effort_score: float
    frequency_score: float
    llm_explanation: Optional[str] = None
    llm_suggestion: Optional[str] = None
    
    @property
    def priority_level(self) -> str:
        """Get human-readable priority level."""
        if self.priority_score >= 8.0:
            return "Critical"
        elif self.priority_score >= 6.0:
            return "High"
        elif self.priority_score >= 4.0:
            return "Medium"
        elif self.priority_score >= 2.0:
            return "Low"
        else:
            return "Info"


@dataclass
class ReportSummary:
    """Summary statistics for the analysis report."""
    total_files: int
    total_issues: int
    issues_by_category: Dict[str, int] = field(default_factory=dict)
    issues_by_severity: Dict[str, int] = field(default_factory=dict)
    issues_by_priority: Dict[str, int] = field(default_factory=dict)
    top_files_by_issues: List[Tuple[str, int]] = field(default_factory=list)
    quality_score: float = 0.0
    maintainability_index: float = 0.0
    technical_debt_ratio: float = 0.0


@dataclass
class QualityReport:
    """Comprehensive quality report with prioritized issues and insights."""
    analysis_id: str
    codebase_path: str
    timestamp: datetime
    summary: ReportSummary
    prioritized_issues: List[PrioritizedIssue]
    metrics: QualityMetrics
    llm_summary: Optional[str] = None
    recommendations: List[str] = field(default_factory=list)
    
    def get_issues_by_priority(self, priority_level: str) -> List[PrioritizedIssue]:
        """Get issues filtered by priority level."""
        return [
            issue for issue in self.prioritized_issues 
            if issue.priority_level.lower() == priority_level.lower()
        ]
    
    def get_issues_by_category(self, category: IssueCategory) -> List[PrioritizedIssue]:
        """Get issues filtered by category."""
        return [
            issue for issue in self.prioritized_issues 
            if issue.issue.category == category
        ]
    
    def get_top_issues(self, limit: int = 10) -> List[PrioritizedIssue]:
        """Get top issues by priority score."""
        return sorted(
            self.prioritized_issues, 
            key=lambda x: x.priority_score, 
            reverse=True
        )[:limit]


class IssuePrioritizer:
    """Handles issue prioritization using multiple scoring algorithms."""
    
    def __init__(self):
        self.severity_weights = {
            Severity.CRITICAL: 10.0,
            Severity.HIGH: 7.5,
            Severity.MEDIUM: 5.0,
            Severity.LOW: 2.5,
            Severity.INFO: 1.0
        }
        
        self.category_weights = {
            IssueCategory.SECURITY: 1.2,
            IssueCategory.PERFORMANCE: 1.0,
            IssueCategory.COMPLEXITY: 0.8,
            IssueCategory.TESTING: 0.9,
            IssueCategory.DOCUMENTATION: 0.6,
            IssueCategory.DUPLICATION: 0.7
        }
    
    def calculate_impact_score(self, issue: Issue, parsed_files: List[ParsedFile]) -> float:
        """
        Calculate impact score based on issue characteristics.
        
        Args:
            issue: Issue to score
            parsed_files: List of parsed files for context
            
        Returns:
            Impact score (0-10)
        """
        base_score = self.severity_weights.get(issue.severity, 1.0)
        category_multiplier = self.category_weights.get(issue.category, 1.0)
        
        # Adjust based on confidence
        confidence_multiplier = issue.confidence
        
        # Adjust based on affected files count
        affected_files_multiplier = min(1.0 + (len(issue.affected_files) - 1) * 0.1, 2.0)
        
        impact_score = base_score * category_multiplier * confidence_multiplier * affected_files_multiplier
        return min(impact_score, 10.0)
    
    def calculate_effort_score(self, issue: Issue) -> float:
        """
        Calculate effort score (lower is easier to fix).
        
        Args:
            issue: Issue to score
            
        Returns:
            Effort score (1-10, where 1 is easy to fix)
        """
        # Base effort by category
        category_effort = {
            IssueCategory.DOCUMENTATION: 2.0,
            IssueCategory.DUPLICATION: 4.0,
            IssueCategory.TESTING: 5.0,
            IssueCategory.COMPLEXITY: 6.0,
            IssueCategory.PERFORMANCE: 7.0,
            IssueCategory.SECURITY: 8.0
        }
        
        base_effort = category_effort.get(issue.category, 5.0)
        
        # Adjust by severity (higher severity often means more complex fix)
        severity_multiplier = {
            Severity.CRITICAL: 1.3,
            Severity.HIGH: 1.2,
            Severity.MEDIUM: 1.0,
            Severity.LOW: 0.8,
            Severity.INFO: 0.6
        }
        
        effort_score = base_effort * severity_multiplier.get(issue.severity, 1.0)
        return min(effort_score, 10.0)
    
    def calculate_frequency_score(self, issue: Issue, all_issues: List[Issue]) -> float:
        """
        Calculate frequency score based on similar issues.
        
        Args:
            issue: Issue to score
            all_issues: All issues for frequency analysis
            
        Returns:
            Frequency score (0-10)
        """
        # Count similar issues (same category and severity)
        similar_issues = [
            i for i in all_issues 
            if i.category == issue.category and i.severity == issue.severity
        ]
        
        # Frequency score based on count
        frequency_count = len(similar_issues)
        if frequency_count <= 1:
            return 1.0
        elif frequency_count <= 3:
            return 3.0
        elif frequency_count <= 5:
            return 5.0
        elif frequency_count <= 10:
            return 7.0
        else:
            return 10.0
    
    def calculate_priority_score(
        self, 
        impact_score: float, 
        effort_score: float, 
        frequency_score: float
    ) -> float:
        """
        Calculate overall priority score.
        
        Args:
            impact_score: Impact score (0-10)
            effort_score: Effort score (1-10, lower is easier)
            frequency_score: Frequency score (0-10)
            
        Returns:
            Priority score (0-10)
        """
        # Priority = (Impact * Frequency) / Effort
        # Normalize to 0-10 scale
        raw_score = (impact_score * frequency_score) / effort_score
        return min(raw_score, 10.0)
    
    def prioritize_issues(
        self, 
        issues: List[Issue], 
        parsed_files: List[ParsedFile]
    ) -> List[PrioritizedIssue]:
        """
        Prioritize a list of issues.
        
        Args:
            issues: Issues to prioritize
            parsed_files: Parsed files for context
            
        Returns:
            List of prioritized issues sorted by priority score
        """
        prioritized_issues = []
        
        for issue in issues:
            impact_score = self.calculate_impact_score(issue, parsed_files)
            effort_score = self.calculate_effort_score(issue)
            frequency_score = self.calculate_frequency_score(issue, issues)
            priority_score = self.calculate_priority_score(
                impact_score, effort_score, frequency_score
            )
            
            prioritized_issue = PrioritizedIssue(
                issue=issue,
                priority_score=priority_score,
                impact_score=impact_score,
                effort_score=effort_score,
                frequency_score=frequency_score
            )
            
            prioritized_issues.append(prioritized_issue)
        
        # Sort by priority score (highest first)
        prioritized_issues.sort(key=lambda x: x.priority_score, reverse=True)
        
        logger.info(f"Prioritized {len(prioritized_issues)} issues")
        return prioritized_issues


class ReportGenerator:
    """Generates comprehensive code quality reports with AI-powered insights."""
    
    def __init__(
        self, 
        llm_service: Optional[LLMService] = None,
        enable_llm_enhancements: bool = True,
        max_issues_for_llm: int = 50
    ):
        """
        Initialize report generator.
        
        Args:
            llm_service: LLM service for generating explanations
            enable_llm_enhancements: Whether to use LLM for issue enhancement
            max_issues_for_llm: Maximum number of issues to enhance with LLM
        """
        # Use provided LLM service or create one with OpenAI if API key is available
        if llm_service:
            self.llm_service = llm_service
        else:
            import os
            openai_key = os.getenv("OPENAI_API_KEY")
            if openai_key:
                self.llm_service = create_llm_service(provider="openai", api_key=openai_key)
            else:
                self.llm_service = create_llm_service(provider="mock")
        self.enable_llm_enhancements = enable_llm_enhancements
        self.max_issues_for_llm = max_issues_for_llm
        self.prioritizer = IssuePrioritizer()
        
        logger.info("Report generator initialized")
    
    def _generate_summary(
        self, 
        analysis_result: AnalysisResult, 
        prioritized_issues: List[PrioritizedIssue]
    ) -> ReportSummary:
        """Generate report summary statistics."""
        issues_by_category = {}
        issues_by_severity = {}
        issues_by_priority = {}
        files_issue_count = {}
        
        for prioritized_issue in prioritized_issues:
            issue = prioritized_issue.issue
            
            # Count by category
            category = issue.category.value
            issues_by_category[category] = issues_by_category.get(category, 0) + 1
            
            # Count by severity
            severity = issue.severity.value
            issues_by_severity[severity] = issues_by_severity.get(severity, 0) + 1
            
            # Count by priority
            priority = prioritized_issue.priority_level
            issues_by_priority[priority] = issues_by_priority.get(priority, 0) + 1
            
            # Count by file
            file_path = issue.location.file_path
            files_issue_count[file_path] = files_issue_count.get(file_path, 0) + 1
        
        # Get top files by issue count
        top_files = sorted(
            files_issue_count.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10]
        
        return ReportSummary(
            total_files=len(analysis_result.parsed_files),
            total_issues=len(prioritized_issues),
            issues_by_category=issues_by_category,
            issues_by_severity=issues_by_severity,
            issues_by_priority=issues_by_priority,
            top_files_by_issues=top_files,
            quality_score=analysis_result.metrics.overall_score,
            maintainability_index=analysis_result.metrics.maintainability_index,
            technical_debt_ratio=analysis_result.metrics.technical_debt_ratio
        )
    
    def _enhance_issues_with_llm(
        self, 
        prioritized_issues: List[PrioritizedIssue], 
        parsed_files: List[ParsedFile],
        include_explanations: bool = True,
        include_suggestions: bool = True
    ) -> List[PrioritizedIssue]:
        """Enhance top issues with LLM-generated explanations and suggestions."""
        if not self.enable_llm_enhancements or not self.llm_service:
            return prioritized_issues
        
        # Skip LLM enhancement if both explanations and suggestions are disabled
        if not include_explanations and not include_suggestions:
            logger.info("Skipping LLM enhancement (both explanations and suggestions disabled)")
            return prioritized_issues
        
        # Enhance only top issues to manage API costs
        issues_to_enhance = prioritized_issues[:self.max_issues_for_llm]
        
        enhancement_types = []
        if include_explanations:
            enhancement_types.append("explanations")
        if include_suggestions:
            enhancement_types.append("suggestions")
        
        logger.info(f"Enhancing {len(issues_to_enhance)} issues with LLM ({', '.join(enhancement_types)})")
        
        for prioritized_issue in issues_to_enhance:
            try:
                # Generate explanation only if requested
                if include_explanations:
                    explanation = self.llm_service.generate_issue_explanation(
                        prioritized_issue.issue, parsed_files
                    )
                    if explanation:
                        prioritized_issue.llm_explanation = explanation
                
                # Generate improved suggestion only if requested
                if include_suggestions:
                    suggestion = self.llm_service.generate_issue_suggestion(
                        prioritized_issue.issue, parsed_files
                    )
                    if suggestion:
                        prioritized_issue.llm_suggestion = suggestion
                
            except Exception as e:
                logger.warning(f"Failed to enhance issue {prioritized_issue.issue.id}: {e}")
        
        return prioritized_issues
    
    def _generate_recommendations(
        self, 
        prioritized_issues: List[PrioritizedIssue], 
        summary: ReportSummary
    ) -> List[str]:
        """Generate high-level recommendations based on analysis results."""
        recommendations = []
        
        # Quality score recommendations
        if summary.quality_score < 50:
            recommendations.append(
                "🚨 Critical: Overall code quality is very low. Consider immediate refactoring of high-priority issues."
            )
        elif summary.quality_score < 70:
            recommendations.append(
                "⚠️ Warning: Code quality needs improvement. Focus on security and performance issues first."
            )
        elif summary.quality_score < 85:
            recommendations.append(
                "📈 Good: Code quality is acceptable but has room for improvement. Address complexity and testing gaps."
            )
        else:
            recommendations.append(
                "✅ Excellent: Code quality is high. Continue maintaining current standards."
            )
        
        # Category-specific recommendations
        if summary.issues_by_category.get("security", 0) > 0:
            recommendations.append(
                f"🔒 Security: Found {summary.issues_by_category['security']} security issues. "
                "Prioritize fixing these immediately to prevent vulnerabilities."
            )
        
        if summary.issues_by_category.get("performance", 0) > 5:
            recommendations.append(
                f"⚡ Performance: {summary.issues_by_category['performance']} performance issues detected. "
                "Consider profiling and optimizing critical paths."
            )
        
        if summary.issues_by_category.get("testing", 0) > 10:
            recommendations.append(
                f"🧪 Testing: {summary.issues_by_category['testing']} testing gaps found. "
                "Improve test coverage to reduce bugs and improve maintainability."
            )
        
        if summary.issues_by_category.get("complexity", 0) > 10:
            recommendations.append(
                f"🔄 Complexity: {summary.issues_by_category['complexity']} complexity issues found. "
                "Refactor complex functions to improve readability and maintainability."
            )
        
        # Technical debt recommendations
        if summary.technical_debt_ratio > 0.5:
            recommendations.append(
                f"💳 Technical Debt: High technical debt ratio ({summary.technical_debt_ratio:.2f}). "
                "Allocate time for refactoring to prevent future development slowdown."
            )
        
        # File-specific recommendations
        if summary.top_files_by_issues:
            top_file, issue_count = summary.top_files_by_issues[0]
            if issue_count > 10:
                recommendations.append(
                    f"📁 Hotspot: File '{top_file}' has {issue_count} issues. "
                    "Consider refactoring this file as it may be a maintenance bottleneck."
                )
        
        return recommendations
    
    def generate_report(
        self, 
        analysis_result: AnalysisResult,
        include_explanations: bool = True,
        include_suggestions: bool = True
    ) -> QualityReport:
        """
        Generate a comprehensive quality report.
        
        Args:
            analysis_result: Analysis results to generate report from
            include_explanations: Whether to generate AI explanations
            include_suggestions: Whether to generate AI suggestions
            
        Returns:
            Comprehensive quality report
        """
        logger.info(f"Generating report for analysis {analysis_result.analysis_id}")
        
        # Prioritize issues
        prioritized_issues = self.prioritizer.prioritize_issues(
            analysis_result.issues, 
            analysis_result.parsed_files
        )
        
        # Generate summary
        summary = self._generate_summary(analysis_result, prioritized_issues)
        
        # Enhance issues with LLM
        enhanced_issues = self._enhance_issues_with_llm(
            prioritized_issues, 
            analysis_result.parsed_files,
            include_explanations=include_explanations,
            include_suggestions=include_suggestions
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(enhanced_issues, summary)
        
        # Generate LLM summary if enabled
        llm_summary = None
        if self.enable_llm_enhancements and self.llm_service:
            try:
                llm_summary = self.llm_service.generate_analysis_summary(analysis_result)
            except Exception as e:
                logger.warning(f"Failed to generate LLM summary: {e}")
        
        # Create report
        report = QualityReport(
            analysis_id=analysis_result.analysis_id,
            codebase_path=analysis_result.codebase_path,
            timestamp=analysis_result.timestamp,
            summary=summary,
            prioritized_issues=enhanced_issues,
            metrics=analysis_result.metrics,
            llm_summary=llm_summary,
            recommendations=recommendations
        )
        
        logger.info(f"Generated report with {len(enhanced_issues)} prioritized issues")
        return report
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get report generator statistics."""
        llm_stats = {}
        if self.llm_service:
            llm_stats = self.llm_service.get_statistics()
        
        return {
            "llm_enhancements_enabled": self.enable_llm_enhancements,
            "max_issues_for_llm": self.max_issues_for_llm,
            **llm_stats
        }