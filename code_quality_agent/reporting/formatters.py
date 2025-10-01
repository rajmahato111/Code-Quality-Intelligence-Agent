"""Report formatters for different output formats."""

import json
import html
from typing import Dict, List, Any, Optional
from datetime import datetime
from abc import ABC, abstractmethod

from .report_generator import QualityReport, PrioritizedIssue, ReportFormat


class BaseFormatter(ABC):
    """Base class for report formatters."""
    
    @abstractmethod
    def format_report(self, report: QualityReport) -> str:
        """Format a quality report."""
        pass
    
    @abstractmethod
    def get_format(self) -> ReportFormat:
        """Get the format type."""
        pass


class TextFormatter(BaseFormatter):
    """Formats reports as plain text for CLI output with enhanced formatting."""
    
    def __init__(self, use_colors: bool = True, max_issues_to_show: int = 20, compact_mode: bool = False, show_progress_bars: bool = True):
        """
        Initialize text formatter.
        
        Args:
            use_colors: Whether to use ANSI color codes
            max_issues_to_show: Maximum number of issues to show in detail
            compact_mode: Whether to use compact formatting
            show_progress_bars: Whether to show ASCII progress bars
        """
        self.use_colors = use_colors
        self.max_issues_to_show = max_issues_to_show
        self.compact_mode = compact_mode
        self.show_progress_bars = show_progress_bars
        
        # ANSI color codes
        self.colors = {
            'red': '\033[91m' if use_colors else '',
            'yellow': '\033[93m' if use_colors else '',
            'green': '\033[92m' if use_colors else '',
            'blue': '\033[94m' if use_colors else '',
            'purple': '\033[95m' if use_colors else '',
            'cyan': '\033[96m' if use_colors else '',
            'white': '\033[97m' if use_colors else '',
            'bold': '\033[1m' if use_colors else '',
            'underline': '\033[4m' if use_colors else '',
            'dim': '\033[2m' if use_colors else '',
            'reset': '\033[0m' if use_colors else ''
        }
        
        # Unicode symbols for better visual appeal
        self.symbols = {
            'check': '✅' if use_colors else '[OK]',
            'warning': '⚠️' if use_colors else '[WARN]',
            'error': '❌' if use_colors else '[ERROR]',
            'info': 'ℹ️' if use_colors else '[INFO]',
            'security': '🔒' if use_colors else '[SEC]',
            'performance': '⚡' if use_colors else '[PERF]',
            'complexity': '🔄' if use_colors else '[COMPLEX]',
            'testing': '🧪' if use_colors else '[TEST]',
            'documentation': '📚' if use_colors else '[DOC]',
            'duplication': '📋' if use_colors else '[DUP]',
            'arrow': '→' if use_colors else '->',
            'bullet': '•' if use_colors else '-'
        }
    
    def get_format(self) -> ReportFormat:
        """Get the format type."""
        return ReportFormat.TEXT
    
    def _format_header(self, report: QualityReport) -> str:
        """Format report header."""
        lines = []
        lines.append("=" * 80)
        lines.append(f"{self.colors['bold']}CODE QUALITY ANALYSIS REPORT{self.colors['reset']}")
        lines.append("=" * 80)
        lines.append(f"Codebase: {report.codebase_path}")
        lines.append(f"Analysis ID: {report.analysis_id}")
        lines.append(f"Generated: {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        return "\n".join(lines)
    
    def _create_progress_bar(self, value: float, max_value: float = 100, width: int = 30) -> str:
        """Create an ASCII progress bar."""
        if not self.show_progress_bars:
            return f"{value:.1f}/{max_value}"
        
        percentage = min(value / max_value, 1.0)
        filled_width = int(width * percentage)
        empty_width = width - filled_width
        
        # Choose color based on value
        if percentage >= 0.85:
            color = self.colors['green']
        elif percentage >= 0.70:
            color = self.colors['yellow']
        else:
            color = self.colors['red']
        
        bar = f"{color}{'█' * filled_width}{'░' * empty_width}{self.colors['reset']}"
        return f"{bar} {value:.1f}/{max_value}"
    
    def _format_summary(self, report: QualityReport) -> str:
        """Format summary section with enhanced visuals."""
        lines = []
        
        if self.compact_mode:
            lines.append(f"{self.colors['bold']}📊 SUMMARY{self.colors['reset']}")
            lines.append("-" * 30)
        else:
            lines.append(f"{self.colors['bold']}{self.colors['underline']}📊 EXECUTIVE SUMMARY{self.colors['reset']}")
            lines.append("=" * 50)
        
        # Quality score with progress bar
        quality_color = self._get_quality_color(report.summary.quality_score)
        quality_symbol = self._get_quality_symbol(report.summary.quality_score)
        
        if self.compact_mode:
            lines.append(f"Quality Score: {quality_color}{report.summary.quality_score:.1f}/100{self.colors['reset']} {quality_symbol}")
        else:
            lines.append(f"{self.colors['bold']}Overall Quality Score:{self.colors['reset']}")
            progress_bar = self._create_progress_bar(report.summary.quality_score)
            lines.append(f"  {progress_bar} {quality_symbol}")
            lines.append("")
        
        # Key metrics
        if not self.compact_mode:
            lines.append(f"{self.colors['bold']}Key Metrics:{self.colors['reset']}")
            lines.append(f"  {self.symbols['bullet']} Maintainability Index: {report.summary.maintainability_index:.1f}")
            lines.append(f"  {self.symbols['bullet']} Technical Debt Ratio: {report.summary.technical_debt_ratio:.3f}")
            lines.append(f"  {self.symbols['bullet']} Files Analyzed: {report.summary.total_files}")
            lines.append(f"  {self.symbols['bullet']} Total Issues Found: {report.summary.total_issues}")
        else:
            lines.append(f"Files: {report.summary.total_files} | Issues: {report.summary.total_issues} | Maintainability: {report.summary.maintainability_index:.1f}")
        
        lines.append("")
        
        # Issues by severity with visual indicators
        if report.summary.issues_by_severity:
            lines.append(f"{self.colors['bold']}Issues by Severity:{self.colors['reset']}")
            severity_order = ['critical', 'high', 'medium', 'low', 'info']
            for severity in severity_order:
                if severity in report.summary.issues_by_severity:
                    count = report.summary.issues_by_severity[severity]
                    severity_color = self._get_severity_color(severity)
                    severity_symbol = self._get_severity_symbol(severity)
                    if self.compact_mode:
                        lines.append(f"  {severity_color}{severity_symbol} {severity.upper()}: {count}{self.colors['reset']}")
                    else:
                        bar = self._create_progress_bar(count, report.summary.total_issues, 20)
                        lines.append(f"  {severity_color}{severity_symbol} {severity.upper():<8}: {count:>3} {bar}{self.colors['reset']}")
            lines.append("")
        
        # Issues by category with symbols
        if report.summary.issues_by_category:
            lines.append(f"{self.colors['bold']}Issues by Category:{self.colors['reset']}")
            for category, count in report.summary.issues_by_category.items():
                category_symbol = self.symbols.get(category, self.symbols['bullet'])
                if self.compact_mode:
                    lines.append(f"  {category_symbol} {category.upper()}: {count}")
                else:
                    bar = self._create_progress_bar(count, report.summary.total_issues, 15)
                    lines.append(f"  {category_symbol} {category.upper():<12}: {count:>3} {bar}")
            lines.append("")
        
        # Top problematic files
        if report.summary.top_files_by_issues and not self.compact_mode:
            lines.append(f"{self.colors['bold']}🔥 Hotspot Files:{self.colors['reset']}")
            for i, (file_path, count) in enumerate(report.summary.top_files_by_issues[:5], 1):
                lines.append(f"  {i}. {self.colors['cyan']}{file_path}{self.colors['reset']}: {count} issues")
            lines.append("")
        
        return "\n".join(lines)
    
    def _get_quality_symbol(self, score: float) -> str:
        """Get symbol for quality score."""
        if score >= 85:
            return self.symbols['check']
        elif score >= 70:
            return self.symbols['warning']
        else:
            return self.symbols['error']
    
    def _get_severity_symbol(self, severity: str) -> str:
        """Get symbol for severity level."""
        severity_symbols = {
            'critical': self.symbols['error'],
            'high': self.symbols['error'],
            'medium': self.symbols['warning'],
            'low': self.symbols['info'],
            'info': self.symbols['info']
        }
        return severity_symbols.get(severity.lower(), self.symbols['bullet'])
    
    def _format_recommendations(self, report: QualityReport) -> str:
        """Format recommendations section."""
        if not report.recommendations:
            return ""
        
        lines = []
        lines.append(f"{self.colors['bold']}💡 RECOMMENDATIONS{self.colors['reset']}")
        lines.append("-" * 40)
        
        for i, recommendation in enumerate(report.recommendations, 1):
            lines.append(f"{i}. {recommendation}")
        
        lines.append("")
        return "\n".join(lines)
    
    def _format_llm_summary(self, report: QualityReport) -> str:
        """Format LLM-generated summary."""
        if not report.llm_summary:
            return ""
        
        lines = []
        lines.append(f"{self.colors['bold']}🤖 AI INSIGHTS{self.colors['reset']}")
        lines.append("-" * 40)
        # Clean markdown formatting for text output
        clean_summary = self._clean_markdown(report.llm_summary)
        lines.append(clean_summary)
        lines.append("")
        return "\n".join(lines)
    
    def _format_top_issues(self, report: QualityReport) -> str:
        """Format top issues section."""
        if not report.prioritized_issues:
            return ""
        
        lines = []
        lines.append(f"{self.colors['bold']}🔍 TOP ISSUES{self.colors['reset']}")
        lines.append("-" * 40)
        
        top_issues = report.get_top_issues(self.max_issues_to_show)
        
        for i, prioritized_issue in enumerate(top_issues, 1):
            issue = prioritized_issue.issue
            
            # Issue header
            severity_color = self._get_severity_color(issue.severity.value)
            priority_color = self._get_priority_color(prioritized_issue.priority_level)
            
            lines.append(f"{i}. {severity_color}{issue.title}{self.colors['reset']}")
            lines.append(f"   Priority: {priority_color}{prioritized_issue.priority_level} ({prioritized_issue.priority_score:.1f}){self.colors['reset']}")
            lines.append(f"   Category: {issue.category.value.upper()}")
            lines.append(f"   Severity: {severity_color}{issue.severity.value.upper()}{self.colors['reset']}")
            lines.append(f"   Location: {issue.location.file_path}:{issue.location.line_start}")
            lines.append("")
            
            # Description
            lines.append(f"   Description: {issue.description}")
            lines.append("")
            
            # LLM explanation if available
            if prioritized_issue.llm_explanation:
                lines.append(f"   {self.colors['cyan']}AI Explanation:{self.colors['reset']}")
                # Clean markdown formatting for text output
                clean_explanation = self._clean_markdown(prioritized_issue.llm_explanation)
                explanation_lines = clean_explanation.split('\n')
                for line in explanation_lines:
                    lines.append(f"   {line}")
                lines.append("")
            
            # Suggestion
            suggestion = prioritized_issue.llm_suggestion or issue.suggestion
            lines.append(f"   {self.colors['green']}Suggestion:{self.colors['reset']}")
            # Convert markdown to plain text for better CLI display
            clean_suggestion = self._clean_markdown(suggestion)
            suggestion_lines = clean_suggestion.split('\n')
            for line in suggestion_lines:
                if line.strip():  # Skip empty lines
                    lines.append(f"   {line}")
            lines.append("")
            lines.append("-" * 60)
            lines.append("")
        
        return "\n".join(lines)
    
    def _clean_markdown(self, text: str) -> str:
        """Convert markdown text to clean plain text for CLI display."""
        if not text:
            return text
        
        import re
        
        # Remove ANSI color codes first
        text = re.sub(r'\x1b\[[0-9;]*m', '', text)
        
        # Remove markdown headers (### -> "")
        text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)
        
        # Convert bold (**text** -> text)
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        
        # Convert italic (*text* -> text)  
        text = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'\1', text)
        
        # Convert code blocks (```code``` -> code)
        text = re.sub(r'```[\w]*\n?(.*?)\n?```', r'\1', text, flags=re.DOTALL)
        
        # Convert inline code (`code` -> code)
        text = re.sub(r'`([^`]+)`', r'\1', text)
        
        # Convert bullet points (- item -> • item)
        text = re.sub(r'^-\s+', '• ', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*•\s+', '• ', text, flags=re.MULTILINE)
        
        # Clean up step formatting (Step 1: -> 1.)
        text = re.sub(r'^Step\s+(\d+):\s*', r'\1. ', text, flags=re.MULTILINE)
        
        # Clean up multiple newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Clean up extra spaces
        text = re.sub(r'  +', ' ', text)
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        return text

    def _get_quality_color(self, score: float) -> str:
        """Get color for quality score."""
        if score >= 85:
            return self.colors['green']
        elif score >= 70:
            return self.colors['yellow']
        else:
            return self.colors['red']
    
    def _get_severity_color(self, severity: str) -> str:
        """Get color for severity level."""
        severity_colors = {
            'critical': self.colors['red'],
            'high': self.colors['red'],
            'medium': self.colors['yellow'],
            'low': self.colors['blue'],
            'info': self.colors['cyan']
        }
        return severity_colors.get(severity.lower(), self.colors['white'])
    
    def _get_priority_color(self, priority: str) -> str:
        """Get color for priority level."""
        priority_colors = {
            'critical': self.colors['red'],
            'high': self.colors['red'],
            'medium': self.colors['yellow'],
            'low': self.colors['blue'],
            'info': self.colors['cyan']
        }
        return priority_colors.get(priority.lower(), self.colors['white'])
    
    def format_report(self, report: QualityReport) -> str:
        """Format a quality report as text."""
        sections = [
            self._format_header(report),
            self._format_summary(report),
            self._format_recommendations(report),
            self._format_llm_summary(report),
            self._format_top_issues(report)
        ]
        
        return "\n".join(section for section in sections if section)


class JSONFormatter(BaseFormatter):
    """Formats reports as JSON for programmatic consumption."""
    
    def __init__(self, indent: int = 2):
        """
        Initialize JSON formatter.
        
        Args:
            indent: JSON indentation level
        """
        self.indent = indent
    
    def get_format(self) -> ReportFormat:
        """Get the format type."""
        return ReportFormat.JSON
    
    def _serialize_prioritized_issue(self, prioritized_issue: PrioritizedIssue) -> Dict[str, Any]:
        """Serialize a prioritized issue to dictionary."""
        return {
            "issue": prioritized_issue.issue.to_dict(),
            "priority_score": prioritized_issue.priority_score,
            "priority_level": prioritized_issue.priority_level,
            "impact_score": prioritized_issue.impact_score,
            "effort_score": prioritized_issue.effort_score,
            "frequency_score": prioritized_issue.frequency_score,
            "llm_explanation": prioritized_issue.llm_explanation,
            "llm_suggestion": prioritized_issue.llm_suggestion
        }
    
    def format_report(self, report: QualityReport) -> str:
        """Format a quality report as JSON."""
        report_dict = {
            "analysis_id": report.analysis_id,
            "codebase_path": report.codebase_path,
            "timestamp": report.timestamp.isoformat(),
            "summary": {
                "total_files": report.summary.total_files,
                "total_issues": report.summary.total_issues,
                "issues_by_category": report.summary.issues_by_category,
                "issues_by_severity": report.summary.issues_by_severity,
                "issues_by_priority": report.summary.issues_by_priority,
                "top_files_by_issues": report.summary.top_files_by_issues,
                "quality_score": report.summary.quality_score,
                "maintainability_index": report.summary.maintainability_index,
                "technical_debt_ratio": report.summary.technical_debt_ratio
            },
            "metrics": report.metrics.to_dict(),
            "prioritized_issues": [
                self._serialize_prioritized_issue(issue) 
                for issue in report.prioritized_issues
            ],
            "recommendations": report.recommendations,
            "llm_summary": report.llm_summary
        }
        
        return json.dumps(report_dict, indent=self.indent, ensure_ascii=False)


class MarkdownFormatter(BaseFormatter):
    """Formats reports as Markdown for documentation."""
    
    def __init__(self, max_issues_to_show: int = 20):
        """
        Initialize Markdown formatter.
        
        Args:
            max_issues_to_show: Maximum number of issues to show in detail
        """
        self.max_issues_to_show = max_issues_to_show
    
    def get_format(self) -> ReportFormat:
        """Get the format type."""
        return ReportFormat.MARKDOWN
    
    def _clean_markdown_for_markdown(self, text: str) -> str:
        """Clean up markdown text for better markdown display."""
        if not text:
            return text
        
        import re
        
        # Clean up excessive newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Ensure proper spacing around headers
        text = re.sub(r'(#{1,6}[^\n]*)\n([^\n#])', r'\1\n\n\2', text)
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def _format_header(self, report: QualityReport) -> str:
        """Format report header."""
        lines = []
        lines.append("# Code Quality Analysis Report")
        lines.append("")
        lines.append(f"**Codebase:** `{report.codebase_path}`")
        lines.append(f"**Analysis ID:** `{report.analysis_id}`")
        lines.append(f"**Generated:** {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        return "\n".join(lines)
    
    def _format_summary(self, report: QualityReport) -> str:
        """Format summary section."""
        lines = []
        lines.append("## 📊 Summary")
        lines.append("")
        
        # Quality metrics table
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| Overall Quality Score | {report.summary.quality_score:.1f}/100 |")
        lines.append(f"| Maintainability Index | {report.summary.maintainability_index:.1f} |")
        lines.append(f"| Technical Debt Ratio | {report.summary.technical_debt_ratio:.3f} |")
        lines.append(f"| Files Analyzed | {report.summary.total_files} |")
        lines.append(f"| Total Issues | {report.summary.total_issues} |")
        lines.append("")
        
        # Issues by severity
        if report.summary.issues_by_severity:
            lines.append("### Issues by Severity")
            lines.append("")
            for severity, count in report.summary.issues_by_severity.items():
                emoji = self._get_severity_emoji(severity)
                lines.append(f"- {emoji} **{severity.upper()}**: {count}")
            lines.append("")
        
        # Issues by category
        if report.summary.issues_by_category:
            lines.append("### Issues by Category")
            lines.append("")
            for category, count in report.summary.issues_by_category.items():
                emoji = self._get_category_emoji(category)
                lines.append(f"- {emoji} **{category.upper()}**: {count}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _format_recommendations(self, report: QualityReport) -> str:
        """Format recommendations section."""
        if not report.recommendations:
            return ""
        
        lines = []
        lines.append("## 💡 Recommendations")
        lines.append("")
        
        for recommendation in report.recommendations:
            lines.append(f"- {recommendation}")
        
        lines.append("")
        return "\n".join(lines)
    
    def _format_llm_summary(self, report: QualityReport) -> str:
        """Format LLM-generated summary."""
        if not report.llm_summary:
            return ""
        
        lines = []
        lines.append("## 🤖 AI Insights")
        lines.append("")
        lines.append(report.llm_summary)
        lines.append("")
        return "\n".join(lines)
    
    def _format_top_issues(self, report: QualityReport) -> str:
        """Format top issues section."""
        if not report.prioritized_issues:
            return ""
        
        lines = []
        lines.append("## 🔍 Top Issues")
        lines.append("")
        
        top_issues = report.get_top_issues(self.max_issues_to_show)
        
        for i, prioritized_issue in enumerate(top_issues, 1):
            issue = prioritized_issue.issue
            
            # Issue header
            severity_emoji = self._get_severity_emoji(issue.severity.value)
            priority_emoji = self._get_priority_emoji(prioritized_issue.priority_level)
            
            lines.append(f"### {i}. {severity_emoji} {issue.title}")
            lines.append("")
            
            # Issue details table
            lines.append("| Property | Value |")
            lines.append("|----------|-------|")
            lines.append(f"| Priority | {priority_emoji} {prioritized_issue.priority_level} ({prioritized_issue.priority_score:.1f}) |")
            lines.append(f"| Category | {issue.category.value.upper()} |")
            lines.append(f"| Severity | {severity_emoji} {issue.severity.value.upper()} |")
            lines.append(f"| Location | `{issue.location.file_path}:{issue.location.line_start}` |")
            lines.append("")
            
            # Description
            lines.append("**Description:**")
            lines.append(f"{issue.description}")
            lines.append("")
            
            # LLM explanation if available
            if prioritized_issue.llm_explanation:
                lines.append("**AI Explanation:**")
                lines.append(f"{prioritized_issue.llm_explanation}")
                lines.append("")
            
            # Suggestion
            suggestion = prioritized_issue.llm_suggestion or issue.suggestion
            lines.append("**Suggestion:**")
            # Clean up the suggestion formatting for markdown
            clean_suggestion = self._clean_markdown_for_markdown(suggestion)
            lines.append(f"{clean_suggestion}")
            lines.append("")
            lines.append("---")
            lines.append("")
        
        return "\n".join(lines)
    
    def _get_severity_emoji(self, severity: str) -> str:
        """Get emoji for severity level."""
        severity_emojis = {
            'critical': '🚨',
            'high': '🔴',
            'medium': '🟡',
            'low': '🔵',
            'info': 'ℹ️'
        }
        return severity_emojis.get(severity.lower(), '❓')
    
    def _get_priority_emoji(self, priority: str) -> str:
        """Get emoji for priority level."""
        priority_emojis = {
            'critical': '🚨',
            'high': '🔴',
            'medium': '🟡',
            'low': '🔵',
            'info': 'ℹ️'
        }
        return priority_emojis.get(priority.lower(), '❓')
    
    def _get_category_emoji(self, category: str) -> str:
        """Get emoji for category."""
        category_emojis = {
            'security': '🔒',
            'performance': '⚡',
            'complexity': '🔄',
            'testing': '🧪',
            'documentation': '📚',
            'duplication': '📋'
        }
        return category_emojis.get(category.lower(), '📝')
    
    def format_report(self, report: QualityReport) -> str:
        """Format a quality report as Markdown."""
        sections = [
            self._format_header(report),
            self._format_summary(report),
            self._format_recommendations(report),
            self._format_llm_summary(report),
            self._format_top_issues(report)
        ]
        
        return "\n".join(section for section in sections if section)


class HTMLFormatter(BaseFormatter):
    """Formats reports as HTML for web display with interactive elements."""
    
    def __init__(self, max_issues_to_show: int = 20, include_css: bool = True, include_javascript: bool = True):
        """
        Initialize HTML formatter.
        
        Args:
            max_issues_to_show: Maximum number of issues to show in detail
            include_css: Whether to include embedded CSS styles
            include_javascript: Whether to include interactive JavaScript
        """
        self.max_issues_to_show = max_issues_to_show
        self.include_css = include_css
        self.include_javascript = include_javascript
    
    def get_format(self) -> ReportFormat:
        """Get the format type."""
        return ReportFormat.HTML
    
    def _get_css_styles(self) -> str:
        """Get embedded CSS styles."""
        if not self.include_css:
            return ""
        
        return """
        <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 40px; line-height: 1.6; background: #fafafa; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .header { border-bottom: 3px solid #007acc; padding-bottom: 20px; margin-bottom: 30px; }
        .header h1 { color: #007acc; margin: 0; font-size: 2.5em; }
        .header-meta { color: #666; margin-top: 10px; }
        .summary { background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); padding: 30px; border-radius: 12px; margin-bottom: 30px; }
        .summary h2 { margin-top: 0; color: #495057; }
        .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }
        .metric-card { background: white; padding: 20px; border-radius: 8px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .metric-value { font-size: 2em; font-weight: bold; margin-bottom: 5px; }
        .metric-label { color: #666; font-size: 0.9em; }
        .metrics-table { width: 100%; border-collapse: collapse; margin: 20px 0; background: white; border-radius: 8px; overflow: hidden; }
        .metrics-table th, .metrics-table td { padding: 15px; text-align: left; border-bottom: 1px solid #eee; }
        .metrics-table th { background: #f8f9fa; font-weight: 600; }
        .quality-score { font-size: 3em; font-weight: bold; text-align: center; margin: 20px 0; }
        .quality-excellent { color: #28a745; }
        .quality-good { color: #ffc107; }
        .quality-poor { color: #dc3545; }
        .severity-critical, .severity-high { color: #dc3545; font-weight: bold; }
        .severity-medium { color: #ffc107; font-weight: bold; }
        .severity-low, .severity-info { color: #28a745; }
        .priority-critical, .priority-high { background: linear-gradient(135deg, #fce8e6 0%, #f8d7da 100%); border-left: 4px solid #dc3545; }
        .priority-medium { background: linear-gradient(135deg, #fef7e0 0%, #fff3cd 100%); border-left: 4px solid #ffc107; }
        .priority-low, .priority-info { background: linear-gradient(135deg, #e6f4ea 0%, #d4edda 100%); border-left: 4px solid #28a745; }
        .issue { margin: 20px 0; padding: 25px; border-radius: 12px; transition: all 0.3s ease; cursor: pointer; }
        .issue:hover { transform: translateY(-2px); box-shadow: 0 6px 12px rgba(0,0,0,0.15); }
        .issue-title { font-size: 1.3em; font-weight: 600; margin-bottom: 15px; display: flex; align-items: center; }
        .issue-number { background: #007acc; color: white; border-radius: 50%; width: 30px; height: 30px; display: flex; align-items: center; justify-content: center; margin-right: 15px; font-size: 0.9em; }
        .issue-meta { display: flex; gap: 15px; margin-bottom: 20px; font-size: 0.9em; flex-wrap: wrap; }
        .issue-meta span { padding: 6px 12px; border-radius: 20px; background: #f8f9fa; border: 1px solid #dee2e6; }
        .issue-content { margin-top: 15px; }
        .issue-description { margin-bottom: 15px; color: #495057; }
        .issue-explanation, .issue-suggestion { margin: 15px 0; padding: 15px; border-radius: 8px; }
        .issue-explanation { background: #e3f2fd; border-left: 4px solid #2196f3; }
        .issue-suggestion { background: #e8f5e8; border-left: 4px solid #28a745; }
        .recommendation { background: linear-gradient(135deg, #e8f5e8 0%, #d4edda 100%); border-left: 4px solid #28a745; padding: 20px; margin: 15px 0; border-radius: 8px; }
        .ai-insight { background: linear-gradient(135deg, #e3f2fd 0%, #cce7ff 100%); border-left: 4px solid #2196f3; padding: 20px; margin: 15px 0; border-radius: 8px; }
        .code-location { font-family: 'Monaco', 'Consolas', monospace; background: #f8f9fa; padding: 4px 8px; border-radius: 4px; border: 1px solid #dee2e6; }
        .filter-controls { margin: 20px 0; padding: 20px; background: #f8f9fa; border-radius: 8px; }
        .filter-button { padding: 8px 16px; margin: 5px; border: none; border-radius: 20px; cursor: pointer; transition: all 0.3s ease; }
        .filter-button.active { background: #007acc; color: white; }
        .filter-button:not(.active) { background: white; color: #495057; border: 1px solid #dee2e6; }
        .filter-button:hover { transform: translateY(-1px); box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .collapsible-content { max-height: 0; overflow: hidden; transition: max-height 0.3s ease; }
        .collapsible-content.expanded { max-height: 1000px; }
        .expand-toggle { background: none; border: none; color: #007acc; cursor: pointer; font-size: 0.9em; margin-left: 10px; }
        .stats-chart { margin: 20px 0; }
        .progress-bar { background: #e9ecef; border-radius: 10px; overflow: hidden; margin: 10px 0; }
        .progress-fill { height: 20px; transition: width 0.5s ease; }
        .progress-fill.excellent { background: linear-gradient(90deg, #28a745, #20c997); }
        .progress-fill.good { background: linear-gradient(90deg, #ffc107, #fd7e14); }
        .progress-fill.poor { background: linear-gradient(90deg, #dc3545, #e83e8c); }
        @media (max-width: 768px) {
            .container { margin: 20px; padding: 20px; }
            .metrics-grid { grid-template-columns: 1fr; }
            .issue-meta { flex-direction: column; gap: 10px; }
        }
        </style>
        """
    
    def _get_javascript(self) -> str:
        """Get embedded JavaScript for interactivity."""
        if not self.include_javascript:
            return ""
        
        return """
        <script>
        document.addEventListener('DOMContentLoaded', function() {
            // Filter functionality
            const filterButtons = document.querySelectorAll('.filter-button');
            const issues = document.querySelectorAll('.issue');
            
            filterButtons.forEach(button => {
                button.addEventListener('click', function() {
                    // Update active button
                    filterButtons.forEach(b => b.classList.remove('active'));
                    this.classList.add('active');
                    
                    const filter = this.dataset.filter;
                    
                    issues.forEach(issue => {
                        if (filter === 'all' || issue.classList.contains(filter)) {
                            issue.style.display = 'block';
                        } else {
                            issue.style.display = 'none';
                        }
                    });
                });
            });
            
            // Collapsible content
            const expandToggles = document.querySelectorAll('.expand-toggle');
            expandToggles.forEach(toggle => {
                toggle.addEventListener('click', function() {
                    const content = this.nextElementSibling;
                    content.classList.toggle('expanded');
                    this.textContent = content.classList.contains('expanded') ? '▼ Collapse' : '▶ Expand';
                });
            });
            
            // Issue click to expand/collapse
            issues.forEach(issue => {
                const content = issue.querySelector('.collapsible-content');
                if (content) {
                    issue.addEventListener('click', function(e) {
                        if (e.target.classList.contains('expand-toggle')) return;
                        content.classList.toggle('expanded');
                    });
                }
            });
            
            // Animate progress bars
            const progressBars = document.querySelectorAll('.progress-fill');
            progressBars.forEach(bar => {
                const width = bar.dataset.width;
                setTimeout(() => {
                    bar.style.width = width + '%';
                }, 500);
            });
            
            // Search functionality
            const searchInput = document.getElementById('issue-search');
            if (searchInput) {
                searchInput.addEventListener('input', function() {
                    const searchTerm = this.value.toLowerCase();
                    issues.forEach(issue => {
                        const title = issue.querySelector('.issue-title').textContent.toLowerCase();
                        const description = issue.querySelector('.issue-description').textContent.toLowerCase();
                        
                        if (title.includes(searchTerm) || description.includes(searchTerm)) {
                            issue.style.display = 'block';
                        } else {
                            issue.style.display = 'none';
                        }
                    });
                });
            }
        });
        </script>
        """
    
    def format_report(self, report: QualityReport) -> str:
        """Format a quality report as HTML with interactive elements."""
        html_parts = []
        
        # HTML document start
        html_parts.append("<!DOCTYPE html>")
        html_parts.append("<html lang='en'>")
        html_parts.append("<head>")
        html_parts.append("<meta charset='UTF-8'>")
        html_parts.append("<meta name='viewport' content='width=device-width, initial-scale=1.0'>")
        html_parts.append("<title>Code Quality Analysis Report</title>")
        html_parts.append(self._get_css_styles())
        html_parts.append("</head>")
        html_parts.append("<body>")
        html_parts.append("<div class='container'>")
        
        # Header
        html_parts.append("<div class='header'>")
        html_parts.append("<h1>🔍 Code Quality Analysis Report</h1>")
        html_parts.append("<div class='header-meta'>")
        html_parts.append(f"<strong>Codebase:</strong> <code>{html.escape(report.codebase_path)}</code><br>")
        html_parts.append(f"<strong>Analysis ID:</strong> <code>{report.analysis_id}</code><br>")
        html_parts.append(f"<strong>Generated:</strong> {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        html_parts.append("</div>")
        html_parts.append("</div>")
        
        # Summary with enhanced metrics
        html_parts.append("<div class='summary'>")
        html_parts.append("<h2>📊 Executive Summary</h2>")
        
        # Quality score with progress bar
        quality_class = self._get_quality_css_class(report.summary.quality_score)
        html_parts.append(f"<div class='quality-score {quality_class}'>{report.summary.quality_score:.1f}/100</div>")
        html_parts.append("<div class='progress-bar'>")
        html_parts.append(f"<div class='progress-fill {quality_class}' data-width='{report.summary.quality_score}'></div>")
        html_parts.append("</div>")
        
        # Metrics grid
        html_parts.append("<div class='metrics-grid'>")
        html_parts.append("<div class='metric-card'>")
        html_parts.append(f"<div class='metric-value'>{report.summary.total_files}</div>")
        html_parts.append("<div class='metric-label'>Files Analyzed</div>")
        html_parts.append("</div>")
        html_parts.append("<div class='metric-card'>")
        html_parts.append(f"<div class='metric-value'>{report.summary.total_issues}</div>")
        html_parts.append("<div class='metric-label'>Total Issues</div>")
        html_parts.append("</div>")
        html_parts.append("<div class='metric-card'>")
        html_parts.append(f"<div class='metric-value'>{report.summary.maintainability_index:.1f}</div>")
        html_parts.append("<div class='metric-label'>Maintainability</div>")
        html_parts.append("</div>")
        html_parts.append("<div class='metric-card'>")
        html_parts.append(f"<div class='metric-value'>{report.summary.technical_debt_ratio:.2f}</div>")
        html_parts.append("<div class='metric-label'>Tech Debt Ratio</div>")
        html_parts.append("</div>")
        html_parts.append("</div>")
        html_parts.append("</div>")
        
        # Recommendations
        if report.recommendations:
            html_parts.append("<h2>💡 Key Recommendations</h2>")
            for i, recommendation in enumerate(report.recommendations, 1):
                html_parts.append(f"<div class='recommendation'><strong>{i}.</strong> {html.escape(recommendation)}</div>")
        
        # AI Insights
        if report.llm_summary:
            html_parts.append("<h2>🤖 AI-Powered Insights</h2>")
            html_parts.append(f"<div class='ai-insight'>{html.escape(report.llm_summary)}</div>")
        
        # Interactive Issues Section
        if report.prioritized_issues:
            html_parts.append("<h2>🔍 Detailed Issues Analysis</h2>")
            
            # Filter controls
            html_parts.append("<div class='filter-controls'>")
            html_parts.append("<h3>Filter Issues:</h3>")
            html_parts.append("<button class='filter-button active' data-filter='all'>All Issues</button>")
            
            # Add filter buttons for each priority level
            priority_levels = set(issue.priority_level.lower() for issue in report.prioritized_issues)
            for priority in ['critical', 'high', 'medium', 'low', 'info']:
                if priority in priority_levels:
                    count = len([i for i in report.prioritized_issues if i.priority_level.lower() == priority])
                    html_parts.append(f"<button class='filter-button' data-filter='priority-{priority}'>{priority.title()} ({count})</button>")
            
            # Add filter buttons for each category
            categories = set(issue.issue.category.value for issue in report.prioritized_issues)
            for category in categories:
                count = len([i for i in report.prioritized_issues if i.issue.category.value == category])
                html_parts.append(f"<button class='filter-button' data-filter='category-{category}'>{category.title()} ({count})</button>")
            
            # Search box
            html_parts.append("<div style='margin-top: 15px;'>")
            html_parts.append("<input type='text' id='issue-search' placeholder='Search issues...' style='padding: 8px; border: 1px solid #ddd; border-radius: 4px; width: 300px;'>")
            html_parts.append("</div>")
            html_parts.append("</div>")
            
            # Issues list
            top_issues = report.get_top_issues(self.max_issues_to_show)
            for i, prioritized_issue in enumerate(top_issues, 1):
                issue = prioritized_issue.issue
                priority_class = f"priority-{prioritized_issue.priority_level.lower()}"
                category_class = f"category-{issue.category.value}"
                
                html_parts.append(f"<div class='issue {priority_class} {category_class}'>")
                
                # Issue header
                html_parts.append("<div class='issue-title'>")
                html_parts.append(f"<div class='issue-number'>{i}</div>")
                html_parts.append(f"<span>{html.escape(issue.title)}</span>")
                html_parts.append("<button class='expand-toggle'>▶ Expand</button>")
                html_parts.append("</div>")
                
                # Issue meta information
                html_parts.append("<div class='issue-meta'>")
                html_parts.append(f"<span>🎯 Priority: {prioritized_issue.priority_level} ({prioritized_issue.priority_score:.1f})</span>")
                html_parts.append(f"<span>📂 Category: {issue.category.value.upper()}</span>")
                severity_class = f"severity-{issue.severity.value.lower()}"
                html_parts.append(f"<span class='{severity_class}'>⚠️ Severity: {issue.severity.value.upper()}</span>")
                html_parts.append(f"<span class='code-location'>📍 {html.escape(issue.location.file_path)}:{issue.location.line_start}</span>")
                html_parts.append("</div>")
                
                # Collapsible content
                html_parts.append("<div class='collapsible-content'>")
                html_parts.append("<div class='issue-content'>")
                
                # Description
                html_parts.append(f"<div class='issue-description'><strong>Description:</strong> {html.escape(issue.description)}</div>")
                
                # LLM explanation if available
                if prioritized_issue.llm_explanation:
                    html_parts.append("<div class='issue-explanation'>")
                    html_parts.append("<strong>🤖 AI Explanation:</strong><br>")
                    html_parts.append(html.escape(prioritized_issue.llm_explanation))
                    html_parts.append("</div>")
                
                # Suggestion
                suggestion = prioritized_issue.llm_suggestion or issue.suggestion
                html_parts.append("<div class='issue-suggestion'>")
                html_parts.append("<strong>💡 Recommended Solution:</strong><br>")
                html_parts.append(html.escape(suggestion))
                html_parts.append("</div>")
                
                html_parts.append("</div>")
                html_parts.append("</div>")
                html_parts.append("</div>")
        
        # JavaScript for interactivity
        html_parts.append(self._get_javascript())
        
        # HTML document end
        html_parts.append("</div>")
        html_parts.append("</body>")
        html_parts.append("</html>")
        
        return "\n".join(html_parts)
    
    def _get_quality_css_class(self, score: float) -> str:
        """Get CSS class for quality score."""
        if score >= 85:
            return "quality-excellent"
        elif score >= 70:
            return "quality-good"
        else:
            return "quality-poor"


class FormatterFactory:
    """Factory for creating report formatters."""
    
    _formatters = {
        ReportFormat.TEXT: TextFormatter,
        ReportFormat.JSON: JSONFormatter,
        ReportFormat.MARKDOWN: MarkdownFormatter,
        ReportFormat.HTML: HTMLFormatter
    }
    
    @classmethod
    def create_formatter(
        self, 
        format_type: ReportFormat, 
        **kwargs
    ) -> BaseFormatter:
        """
        Create a formatter for the specified format.
        
        Args:
            format_type: Format type to create
            **kwargs: Additional arguments for formatter
            
        Returns:
            Formatter instance
        """
        formatter_class = self._formatters.get(format_type)
        if not formatter_class:
            raise ValueError(f"Unsupported format: {format_type}")
        
        return formatter_class(**kwargs)
    
    @classmethod
    def get_supported_formats(cls) -> List[ReportFormat]:
        """Get list of supported formats."""
        return list(cls._formatters.keys())