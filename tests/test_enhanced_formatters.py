"""Tests for enhanced report formatters."""

import pytest
import json
from datetime import datetime

from code_quality_agent.reporting import (
    FormatterFactory, ReportFormat, TextFormatter, JSONFormatter, 
    MarkdownFormatter, HTMLFormatter
)
from code_quality_agent.reporting.report_generator import (
    QualityReport, PrioritizedIssue, ReportSummary
)
from code_quality_agent.core.models import (
    Issue, IssueCategory, Severity, CodeLocation, QualityMetrics
)


class TestEnhancedFormatters:
    """Test cases for enhanced report formatters."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create comprehensive test data
        self.issues = [
            Issue(
                id="security-critical",
                category=IssueCategory.SECURITY,
                severity=Severity.CRITICAL,
                title="SQL Injection Vulnerability",
                description="Critical SQL injection vulnerability in user authentication",
                location=CodeLocation("auth.py", 45, 50),
                affected_files=["auth.py"],
                suggestion="Use parameterized queries to prevent SQL injection",
                confidence=0.95
            ),
            Issue(
                id="performance-high",
                category=IssueCategory.PERFORMANCE,
                severity=Severity.HIGH,
                title="Inefficient Database Query",
                description="N+1 query problem in user data retrieval",
                location=CodeLocation("models.py", 120, 135),
                affected_files=["models.py"],
                suggestion="Use eager loading or batch queries",
                confidence=0.88
            ),
            Issue(
                id="complexity-medium",
                category=IssueCategory.COMPLEXITY,
                severity=Severity.MEDIUM,
                title="High Cyclomatic Complexity",
                description="Function has cyclomatic complexity of 15",
                location=CodeLocation("utils.py", 200, 250),
                affected_files=["utils.py"],
                suggestion="Break down into smaller functions",
                confidence=0.92
            ),
            Issue(
                id="testing-low",
                category=IssueCategory.TESTING,
                severity=Severity.LOW,
                title="Missing Unit Tests",
                description="Critical function lacks unit test coverage",
                location=CodeLocation("core.py", 80, 100),
                affected_files=["core.py"],
                suggestion="Add comprehensive unit tests",
                confidence=0.85
            )
        ]
        
        self.prioritized_issues = [
            PrioritizedIssue(
                issue=self.issues[0],
                priority_score=9.2,
                impact_score=9.5,
                effort_score=4.0,
                frequency_score=3.0,
                llm_explanation="This SQL injection vulnerability allows attackers to manipulate database queries by injecting malicious SQL code through user input fields.",
                llm_suggestion="Implement parameterized queries using prepared statements. Replace string concatenation with parameter binding to ensure user input is properly escaped."
            ),
            PrioritizedIssue(
                issue=self.issues[1],
                priority_score=7.8,
                impact_score=8.0,
                effort_score=5.0,
                frequency_score=4.0,
                llm_explanation="The N+1 query problem occurs when the application executes one query to fetch a list of records and then executes additional queries for each record.",
                llm_suggestion="Use ORM eager loading features or implement batch queries to fetch related data in a single database round trip."
            ),
            PrioritizedIssue(
                issue=self.issues[2],
                priority_score=5.5,
                impact_score=6.0,
                effort_score=6.0,
                frequency_score=5.0,
                llm_explanation="High cyclomatic complexity makes code difficult to understand, test, and maintain, increasing the likelihood of bugs.",
                llm_suggestion="Refactor the function by extracting logical blocks into separate methods. Consider using design patterns like Strategy or Command to reduce complexity."
            ),
            PrioritizedIssue(
                issue=self.issues[3],
                priority_score=3.2,
                impact_score=4.0,
                effort_score=3.0,
                frequency_score=2.0,
                llm_explanation="Missing unit tests reduce confidence in code changes and make it harder to catch regressions during development.",
                llm_suggestion="Write unit tests covering all code paths, edge cases, and error conditions. Aim for at least 80% code coverage."
            )
        ]
        
        self.summary = ReportSummary(
            total_files=25,
            total_issues=47,
            issues_by_category={
                "security": 8,
                "performance": 12,
                "complexity": 15,
                "testing": 7,
                "documentation": 3,
                "duplication": 2
            },
            issues_by_severity={
                "critical": 3,
                "high": 8,
                "medium": 18,
                "low": 12,
                "info": 6
            },
            issues_by_priority={
                "Critical": 5,
                "High": 12,
                "Medium": 20,
                "Low": 8,
                "Info": 2
            },
            top_files_by_issues=[
                ("auth.py", 8),
                ("models.py", 6),
                ("utils.py", 5),
                ("core.py", 4),
                ("api.py", 3)
            ],
            quality_score=68.5,
            maintainability_index=72.3,
            technical_debt_ratio=0.23
        )
        
        self.test_report = QualityReport(
            analysis_id="enhanced-formatter-test",
            codebase_path="/test/enhanced/project",
            timestamp=datetime.now(),
            summary=self.summary,
            prioritized_issues=self.prioritized_issues,
            metrics=QualityMetrics(
                overall_score=68.5,
                maintainability_index=72.3,
                technical_debt_ratio=0.23
            ),
            recommendations=[
                "🚨 Critical: Address 3 critical security vulnerabilities immediately",
                "⚡ Performance: Optimize 12 performance bottlenecks to improve response times",
                "🔄 Complexity: Refactor 15 overly complex functions to improve maintainability",
                "🧪 Testing: Add unit tests for 7 untested critical functions",
                "📚 Documentation: Document 3 public APIs to improve developer experience"
            ],
            llm_summary="This codebase shows moderate quality with significant security concerns that require immediate attention. The high number of performance issues suggests the need for optimization, while the complexity issues indicate opportunities for refactoring to improve long-term maintainability."
        )
    
    def test_enhanced_text_formatter_standard_mode(self):
        """Test enhanced text formatter in standard mode."""
        formatter = TextFormatter(
            use_colors=True,
            max_issues_to_show=10,
            compact_mode=False,
            show_progress_bars=True
        )
        
        formatted_report = formatter.format_report(self.test_report)
        
        assert isinstance(formatted_report, str)
        assert len(formatted_report) > 0
        
        # Check for enhanced formatting elements
        assert "📊 EXECUTIVE SUMMARY" in formatted_report
        assert "🔥 Hotspot Files:" in formatted_report
        assert "SQL Injection Vulnerability" in formatted_report
        assert "🤖 AI Explanation:" in formatted_report
        assert "💡 Recommended Solution:" in formatted_report
        
        # Check for progress bars (represented by Unicode blocks)
        assert "█" in formatted_report or "░" in formatted_report or "68.5/100" in formatted_report
        
        # Check for symbols and colors (ANSI codes)
        assert "✅" in formatted_report or "[OK]" in formatted_report
        assert "⚠️" in formatted_report or "[WARN]" in formatted_report
    
    def test_enhanced_text_formatter_compact_mode(self):
        """Test enhanced text formatter in compact mode."""
        formatter = TextFormatter(
            use_colors=False,
            max_issues_to_show=5,
            compact_mode=True,
            show_progress_bars=False
        )
        
        formatted_report = formatter.format_report(self.test_report)
        
        assert isinstance(formatted_report, str)
        assert len(formatted_report) > 0
        
        # Compact mode should be shorter
        standard_formatter = TextFormatter(compact_mode=False, use_colors=False)
        standard_report = standard_formatter.format_report(self.test_report)
        assert len(formatted_report) < len(standard_report)
        
        # Check for compact formatting
        assert "📊 SUMMARY" in formatted_report
        assert "Files: 25 | Issues: 47" in formatted_report
    
    def test_enhanced_html_formatter_with_interactivity(self):
        """Test enhanced HTML formatter with interactive elements."""
        formatter = HTMLFormatter(
            max_issues_to_show=10,
            include_css=True,
            include_javascript=True
        )
        
        formatted_report = formatter.format_report(self.test_report)
        
        assert isinstance(formatted_report, str)
        assert "<!DOCTYPE html>" in formatted_report
        assert "</html>" in formatted_report
        
        # Check for enhanced CSS
        assert "container" in formatted_report
        assert "metrics-grid" in formatted_report
        assert "progress-bar" in formatted_report
        assert "filter-controls" in formatted_report
        
        # Check for interactive elements
        assert "filter-button" in formatted_report
        assert "expand-toggle" in formatted_report
        assert "collapsible-content" in formatted_report
        assert "issue-search" in formatted_report
        
        # Check for JavaScript
        assert "<script>" in formatted_report
        assert "addEventListener" in formatted_report
        assert "filter-button" in formatted_report
        
        # Check for enhanced styling
        assert "🔍 Code Quality Analysis Report" in formatted_report
        assert "📊 Executive Summary" in formatted_report
        assert "🤖 AI-Powered Insights" in formatted_report
        
        # Check for filter buttons
        assert "All Issues" in formatted_report
        assert "Critical" in formatted_report
        assert "Security" in formatted_report
    
    def test_html_formatter_without_javascript(self):
        """Test HTML formatter with JavaScript disabled."""
        formatter = HTMLFormatter(
            include_javascript=False,
            include_css=True
        )
        
        formatted_report = formatter.format_report(self.test_report)
        
        assert "<script>" not in formatted_report
        assert "addEventListener" not in formatted_report
        assert "filter-button" in formatted_report  # Buttons still present, just not functional
    
    def test_json_formatter_enhanced_structure(self):
        """Test JSON formatter with enhanced data structure."""
        formatter = JSONFormatter(indent=2)
        
        formatted_report = formatter.format_report(self.test_report)
        
        # Parse JSON to verify structure
        report_data = json.loads(formatted_report)
        
        # Check main structure
        assert "analysis_id" in report_data
        assert "summary" in report_data
        assert "prioritized_issues" in report_data
        assert "recommendations" in report_data
        assert "llm_summary" in report_data
        
        # Check enhanced summary data
        summary = report_data["summary"]
        assert "issues_by_priority" in summary
        assert "top_files_by_issues" in summary
        assert len(summary["issues_by_category"]) == 6
        assert len(summary["issues_by_severity"]) == 5
        
        # Check prioritized issues structure
        issues = report_data["prioritized_issues"]
        assert len(issues) == 4
        
        first_issue = issues[0]
        assert "priority_score" in first_issue
        assert "priority_level" in first_issue
        assert "llm_explanation" in first_issue
        assert "llm_suggestion" in first_issue
        assert "impact_score" in first_issue
        assert "effort_score" in first_issue
        assert "frequency_score" in first_issue
        
        # Verify LLM enhancements are included
        assert first_issue["llm_explanation"] is not None
        assert first_issue["llm_suggestion"] is not None
        assert len(first_issue["llm_explanation"]) > 0
        assert len(first_issue["llm_suggestion"]) > 0
    
    def test_markdown_formatter_enhanced_structure(self):
        """Test Markdown formatter with enhanced structure."""
        formatter = MarkdownFormatter(max_issues_to_show=10)
        
        formatted_report = formatter.format_report(self.test_report)
        
        assert isinstance(formatted_report, str)
        
        # Check for enhanced Markdown structure
        assert "# Code Quality Analysis Report" in formatted_report
        assert "## 📊 Summary" in formatted_report
        assert "## 💡 Recommendations" in formatted_report
        assert "## 🤖 AI Insights" in formatted_report
        assert "## 🔍 Top Issues" in formatted_report
        
        # Check for tables
        assert "| Metric | Value |" in formatted_report
        assert "|--------|-------|" in formatted_report
        
        # Check for emojis and formatting
        assert "🔒" in formatted_report or "⚡" in formatted_report  # Category emojis
        assert "🚨" in formatted_report or "🔴" in formatted_report  # Severity emojis
        
        # Check for issue details
        assert "### 1. 🚨 SQL Injection Vulnerability" in formatted_report
        assert "**AI Explanation:**" in formatted_report
        assert "**Suggestion:**" in formatted_report
        
        # Check for code formatting
        assert "`auth.py:45`" in formatted_report
    
    def test_formatter_factory_enhanced_options(self):
        """Test formatter factory with enhanced options."""
        # Test creating formatters with various options
        text_formatter = FormatterFactory.create_formatter(
            ReportFormat.TEXT,
            use_colors=True,
            compact_mode=True,
            show_progress_bars=True
        )
        assert isinstance(text_formatter, TextFormatter)
        assert text_formatter.compact_mode is True
        assert text_formatter.show_progress_bars is True
        
        html_formatter = FormatterFactory.create_formatter(
            ReportFormat.HTML,
            include_javascript=True,
            include_css=True
        )
        assert isinstance(html_formatter, HTMLFormatter)
        assert html_formatter.include_javascript is True
        assert html_formatter.include_css is True
        
        json_formatter = FormatterFactory.create_formatter(
            ReportFormat.JSON,
            indent=4
        )
        assert isinstance(json_formatter, JSONFormatter)
        assert json_formatter.indent == 4
    
    def test_all_formatters_handle_empty_data(self):
        """Test that all formatters handle empty or minimal data gracefully."""
        # Create minimal report
        minimal_summary = ReportSummary(
            total_files=0,
            total_issues=0,
            quality_score=100.0,
            maintainability_index=100.0,
            technical_debt_ratio=0.0
        )
        
        minimal_report = QualityReport(
            analysis_id="minimal-test",
            codebase_path="/empty/project",
            timestamp=datetime.now(),
            summary=minimal_summary,
            prioritized_issues=[],
            metrics=QualityMetrics(overall_score=100.0),
            recommendations=[],
            llm_summary=None
        )
        
        # Test all formatters
        formatters = [
            (ReportFormat.TEXT, {}),
            (ReportFormat.JSON, {}),
            (ReportFormat.MARKDOWN, {}),
            (ReportFormat.HTML, {})
        ]
        
        for format_type, kwargs in formatters:
            formatter = FormatterFactory.create_formatter(format_type, **kwargs)
            formatted_report = formatter.format_report(minimal_report)
            
            assert isinstance(formatted_report, str)
            assert len(formatted_report) > 0
            assert "minimal-test" in formatted_report
            assert "/empty/project" in formatted_report
    
    def test_formatter_performance_with_large_dataset(self):
        """Test formatter performance with a large number of issues."""
        # Create a large dataset
        large_issues = []
        for i in range(100):
            issue = Issue(
                id=f"issue-{i}",
                category=list(IssueCategory)[i % len(IssueCategory)],
                severity=list(Severity)[i % len(Severity)],
                title=f"Test Issue {i}",
                description=f"Description for issue {i}",
                location=CodeLocation(f"file{i % 10}.py", i, i + 5),
                affected_files=[f"file{i % 10}.py"],
                suggestion=f"Fix issue {i}",
                confidence=0.8
            )
            large_issues.append(issue)
        
        large_prioritized_issues = [
            PrioritizedIssue(
                issue=issue,
                priority_score=9.0 - (i * 0.05),
                impact_score=8.0,
                effort_score=4.0,
                frequency_score=3.0
            )
            for i, issue in enumerate(large_issues)
        ]
        
        large_summary = ReportSummary(
            total_files=50,
            total_issues=100,
            quality_score=60.0,
            maintainability_index=65.0,
            technical_debt_ratio=0.4
        )
        
        large_report = QualityReport(
            analysis_id="performance-test",
            codebase_path="/large/project",
            timestamp=datetime.now(),
            summary=large_summary,
            prioritized_issues=large_prioritized_issues,
            metrics=QualityMetrics(overall_score=60.0),
            recommendations=["Test recommendation"],
            llm_summary="Large dataset test"
        )
        
        # Test that formatters can handle large datasets
        text_formatter = FormatterFactory.create_formatter(ReportFormat.TEXT, max_issues_to_show=50)
        json_formatter = FormatterFactory.create_formatter(ReportFormat.JSON)
        
        text_report = text_formatter.format_report(large_report)
        json_report = json_formatter.format_report(large_report)
        
        assert len(text_report) > 0
        assert len(json_report) > 0
        
        # Verify JSON structure is valid
        json_data = json.loads(json_report)
        assert len(json_data["prioritized_issues"]) == 100


if __name__ == "__main__":
    pytest.main([__file__])