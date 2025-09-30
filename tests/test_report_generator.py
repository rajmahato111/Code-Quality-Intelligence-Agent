"""Tests for the ReportGenerator and related classes."""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from code_quality_agent.reporting import (
    ReportGenerator, IssuePrioritizer, QualityReport, PrioritizedIssue,
    ReportFormat, FormatterFactory, TextFormatter, JSONFormatter
)
from code_quality_agent.core.models import (
    AnalysisResult, Issue, IssueCategory, Severity, CodeLocation, 
    ParsedFile, QualityMetrics
)
from code_quality_agent.llm import create_llm_service


class TestIssuePrioritizer:
    """Test cases for IssuePrioritizer."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.prioritizer = IssuePrioritizer()
        
        self.test_issues = [
            Issue(
                id="security-critical",
                category=IssueCategory.SECURITY,
                severity=Severity.CRITICAL,
                title="SQL Injection Vulnerability",
                description="Critical security issue",
                location=CodeLocation("app.py", 10, 12),
                affected_files=["app.py"],
                suggestion="Use parameterized queries",
                confidence=0.95
            ),
            Issue(
                id="performance-medium",
                category=IssueCategory.PERFORMANCE,
                severity=Severity.MEDIUM,
                title="Inefficient Loop",
                description="Performance issue in loop",
                location=CodeLocation("utils.py", 25, 30),
                affected_files=["utils.py"],
                suggestion="Optimize algorithm",
                confidence=0.8
            ),
            Issue(
                id="documentation-low",
                category=IssueCategory.DOCUMENTATION,
                severity=Severity.LOW,
                title="Missing Docstring",
                description="Function lacks documentation",
                location=CodeLocation("helpers.py", 5, 5),
                affected_files=["helpers.py"],
                suggestion="Add docstring",
                confidence=0.9
            )
        ]
        
        self.test_parsed_files = [
            ParsedFile(
                path="app.py",
                language="python",
                content="def vulnerable_query(user_id):\n    query = f'SELECT * FROM users WHERE id = {user_id}'\n    return query"
            ),
            ParsedFile(
                path="utils.py",
                language="python",
                content="def inefficient_search(items, target):\n    for i in items:\n        for j in items:\n            if i == j == target:\n                return True\n    return False"
            )
        ]
    
    def test_severity_weights(self):
        """Test severity weight configuration."""
        assert self.prioritizer.severity_weights[Severity.CRITICAL] > self.prioritizer.severity_weights[Severity.HIGH]
        assert self.prioritizer.severity_weights[Severity.HIGH] > self.prioritizer.severity_weights[Severity.MEDIUM]
        assert self.prioritizer.severity_weights[Severity.MEDIUM] > self.prioritizer.severity_weights[Severity.LOW]
        assert self.prioritizer.severity_weights[Severity.LOW] > self.prioritizer.severity_weights[Severity.INFO]
    
    def test_category_weights(self):
        """Test category weight configuration."""
        assert self.prioritizer.category_weights[IssueCategory.SECURITY] > self.prioritizer.category_weights[IssueCategory.PERFORMANCE]
        assert self.prioritizer.category_weights[IssueCategory.DOCUMENTATION] < self.prioritizer.category_weights[IssueCategory.TESTING]
    
    def test_impact_score_calculation(self):
        """Test impact score calculation."""
        critical_security = self.test_issues[0]  # Critical security issue
        medium_performance = self.test_issues[1]  # Medium performance issue
        low_documentation = self.test_issues[2]  # Low documentation issue
        
        critical_impact = self.prioritizer.calculate_impact_score(critical_security, self.test_parsed_files)
        medium_impact = self.prioritizer.calculate_impact_score(medium_performance, self.test_parsed_files)
        low_impact = self.prioritizer.calculate_impact_score(low_documentation, self.test_parsed_files)
        
        # Critical security should have highest impact
        assert critical_impact > medium_impact > low_impact
        assert 0 <= critical_impact <= 10
        assert 0 <= medium_impact <= 10
        assert 0 <= low_impact <= 10
    
    def test_effort_score_calculation(self):
        """Test effort score calculation."""
        security_issue = self.test_issues[0]
        documentation_issue = self.test_issues[2]
        
        security_effort = self.prioritizer.calculate_effort_score(security_issue)
        documentation_effort = self.prioritizer.calculate_effort_score(documentation_issue)
        
        # Security issues should generally require more effort than documentation
        assert security_effort > documentation_effort
        assert 1 <= security_effort <= 10
        assert 1 <= documentation_effort <= 10
    
    def test_frequency_score_calculation(self):
        """Test frequency score calculation."""
        # Create multiple similar issues
        similar_issues = [
            self.test_issues[0],  # Security critical
            Issue(
                id="security-critical-2",
                category=IssueCategory.SECURITY,
                severity=Severity.CRITICAL,
                title="Another Security Issue",
                description="Another critical security issue",
                location=CodeLocation("other.py", 1, 1),
                affected_files=["other.py"],
                suggestion="Fix security",
                confidence=0.9
            )
        ]
        
        frequency_score = self.prioritizer.calculate_frequency_score(
            self.test_issues[0], 
            similar_issues
        )
        
        assert frequency_score > 1.0  # Should be higher for multiple similar issues
        assert 0 <= frequency_score <= 10
    
    def test_priority_score_calculation(self):
        """Test overall priority score calculation."""
        impact = 8.0
        effort = 4.0
        frequency = 6.0
        
        priority = self.prioritizer.calculate_priority_score(impact, effort, frequency)
        
        # Priority = (Impact * Frequency) / Effort = (8 * 6) / 4 = 12, capped at 10
        expected = min((impact * frequency) / effort, 10.0)
        assert priority == expected
        assert 0 <= priority <= 10
    
    def test_prioritize_issues(self):
        """Test complete issue prioritization."""
        prioritized = self.prioritizer.prioritize_issues(self.test_issues, self.test_parsed_files)
        
        assert len(prioritized) == len(self.test_issues)
        
        # Check that all issues are PrioritizedIssue objects
        for p_issue in prioritized:
            assert isinstance(p_issue, PrioritizedIssue)
            assert hasattr(p_issue, 'priority_score')
            assert hasattr(p_issue, 'impact_score')
            assert hasattr(p_issue, 'effort_score')
            assert hasattr(p_issue, 'frequency_score')
        
        # Check that issues are sorted by priority (highest first)
        for i in range(len(prioritized) - 1):
            assert prioritized[i].priority_score >= prioritized[i + 1].priority_score
        
        # Critical security issue should likely be first
        assert prioritized[0].issue.severity == Severity.CRITICAL
        assert prioritized[0].issue.category == IssueCategory.SECURITY
    
    def test_priority_level_property(self):
        """Test priority level property."""
        high_priority = PrioritizedIssue(
            issue=self.test_issues[0],
            priority_score=8.5,
            impact_score=9.0,
            effort_score=3.0,
            frequency_score=5.0
        )
        
        medium_priority = PrioritizedIssue(
            issue=self.test_issues[1],
            priority_score=5.0,
            impact_score=6.0,
            effort_score=4.0,
            frequency_score=3.0
        )
        
        low_priority = PrioritizedIssue(
            issue=self.test_issues[2],
            priority_score=2.0,
            impact_score=2.0,
            effort_score=2.0,
            frequency_score=2.0
        )
        
        assert high_priority.priority_level == "Critical"
        assert medium_priority.priority_level == "Medium"
        assert low_priority.priority_level == "Low"


class TestReportGenerator:
    """Test cases for ReportGenerator."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create mock LLM service
        self.mock_llm_service = create_llm_service(provider="mock")
        
        self.report_generator = ReportGenerator(
            llm_service=self.mock_llm_service,
            enable_llm_enhancements=True,
            max_issues_for_llm=10
        )
        
        # Create test analysis result
        self.test_issues = [
            Issue(
                id="test-issue-1",
                category=IssueCategory.SECURITY,
                severity=Severity.HIGH,
                title="Security Vulnerability",
                description="Test security issue",
                location=CodeLocation("test.py", 10, 12),
                affected_files=["test.py"],
                suggestion="Fix security issue",
                confidence=0.9
            ),
            Issue(
                id="test-issue-2",
                category=IssueCategory.PERFORMANCE,
                severity=Severity.MEDIUM,
                title="Performance Issue",
                description="Test performance issue",
                location=CodeLocation("test.py", 20, 25),
                affected_files=["test.py"],
                suggestion="Optimize performance",
                confidence=0.8
            )
        ]
        
        self.test_parsed_files = [
            ParsedFile(
                path="test.py",
                language="python",
                content="def test_function():\n    # Test code\n    pass"
            )
        ]
        
        self.test_analysis_result = AnalysisResult(
            analysis_id="test-analysis",
            codebase_path="/test/path",
            parsed_files=self.test_parsed_files,
            issues=self.test_issues,
            metrics=QualityMetrics(
                overall_score=75.0,
                maintainability_index=80.0,
                technical_debt_ratio=0.15
            ),
            timestamp=datetime.now()
        )
    
    def test_report_generator_initialization(self):
        """Test report generator initialization."""
        assert self.report_generator.llm_service is not None
        assert self.report_generator.enable_llm_enhancements is True
        assert self.report_generator.max_issues_for_llm == 10
        assert isinstance(self.report_generator.prioritizer, IssuePrioritizer)
    
    def test_generate_summary(self):
        """Test summary generation."""
        prioritized_issues = self.report_generator.prioritizer.prioritize_issues(
            self.test_issues, self.test_parsed_files
        )
        
        summary = self.report_generator._generate_summary(
            self.test_analysis_result, prioritized_issues
        )
        
        assert summary.total_files == 1
        assert summary.total_issues == 2
        assert "security" in summary.issues_by_category
        assert "performance" in summary.issues_by_category
        assert "high" in summary.issues_by_severity
        assert "medium" in summary.issues_by_severity
        assert summary.quality_score == 75.0
        assert len(summary.top_files_by_issues) > 0
    
    def test_enhance_issues_with_llm(self):
        """Test LLM enhancement of issues."""
        prioritized_issues = self.report_generator.prioritizer.prioritize_issues(
            self.test_issues, self.test_parsed_files
        )
        
        enhanced_issues = self.report_generator._enhance_issues_with_llm(
            prioritized_issues, self.test_parsed_files
        )
        
        assert len(enhanced_issues) == len(prioritized_issues)
        
        # Check that top issues have LLM enhancements
        for issue in enhanced_issues[:min(2, self.report_generator.max_issues_for_llm)]:
            assert issue.llm_explanation is not None
            assert issue.llm_suggestion is not None
            assert len(issue.llm_explanation) > 0
            assert len(issue.llm_suggestion) > 0
    
    def test_generate_recommendations(self):
        """Test recommendation generation."""
        prioritized_issues = self.report_generator.prioritizer.prioritize_issues(
            self.test_issues, self.test_parsed_files
        )
        
        summary = self.report_generator._generate_summary(
            self.test_analysis_result, prioritized_issues
        )
        
        recommendations = self.report_generator._generate_recommendations(
            prioritized_issues, summary
        )
        
        assert len(recommendations) > 0
        assert any("security" in rec.lower() for rec in recommendations)
        
        # Check quality score recommendation
        quality_rec = next((rec for rec in recommendations if "quality" in rec.lower()), None)
        assert quality_rec is not None
    
    def test_generate_report(self):
        """Test complete report generation."""
        report = self.report_generator.generate_report(self.test_analysis_result)
        
        assert isinstance(report, QualityReport)
        assert report.analysis_id == "test-analysis"
        assert report.codebase_path == "/test/path"
        assert len(report.prioritized_issues) == 2
        assert report.summary.total_issues == 2
        assert len(report.recommendations) > 0
        assert report.llm_summary is not None  # Should be generated by mock LLM
        
        # Check that issues are prioritized (sorted by priority score)
        for i in range(len(report.prioritized_issues) - 1):
            assert (report.prioritized_issues[i].priority_score >= 
                   report.prioritized_issues[i + 1].priority_score)
    
    def test_report_filtering_methods(self):
        """Test report filtering methods."""
        report = self.report_generator.generate_report(self.test_analysis_result)
        
        # Test get_issues_by_category
        security_issues = report.get_issues_by_category(IssueCategory.SECURITY)
        assert len(security_issues) == 1
        assert security_issues[0].issue.category == IssueCategory.SECURITY
        
        performance_issues = report.get_issues_by_category(IssueCategory.PERFORMANCE)
        assert len(performance_issues) == 1
        assert performance_issues[0].issue.category == IssueCategory.PERFORMANCE
        
        # Test get_issues_by_priority
        high_priority = report.get_issues_by_priority("High")
        assert all(issue.priority_level == "High" for issue in high_priority)
        
        # Test get_top_issues
        top_issues = report.get_top_issues(1)
        assert len(top_issues) == 1
        assert top_issues[0].priority_score >= report.prioritized_issues[1].priority_score
    
    def test_llm_enhancement_disabled(self):
        """Test report generation with LLM enhancements disabled."""
        generator = ReportGenerator(
            llm_service=self.mock_llm_service,
            enable_llm_enhancements=False
        )
        
        report = generator.generate_report(self.test_analysis_result)
        
        assert report.llm_summary is None
        
        # Issues should not have LLM enhancements
        for issue in report.prioritized_issues:
            assert issue.llm_explanation is None
            assert issue.llm_suggestion is None
    
    def test_statistics(self):
        """Test statistics generation."""
        stats = self.report_generator.get_statistics()
        
        assert "llm_enhancements_enabled" in stats
        assert "max_issues_for_llm" in stats
        assert stats["llm_enhancements_enabled"] is True
        assert stats["max_issues_for_llm"] == 10
        
        # Should include LLM service statistics
        assert "total_requests" in stats
        assert "successful_requests" in stats


class TestFormatters:
    """Test cases for report formatters."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create a sample report
        issue = Issue(
            id="test-issue",
            category=IssueCategory.SECURITY,
            severity=Severity.HIGH,
            title="Test Security Issue",
            description="Test description",
            location=CodeLocation("test.py", 10, 12),
            affected_files=["test.py"],
            suggestion="Fix this issue",
            confidence=0.9
        )
        
        prioritized_issue = PrioritizedIssue(
            issue=issue,
            priority_score=8.5,
            impact_score=9.0,
            effort_score=3.0,
            frequency_score=5.0,
            llm_explanation="This is a test explanation",
            llm_suggestion="This is a test suggestion"
        )
        
        from code_quality_agent.reporting.report_generator import ReportSummary
        summary = ReportSummary(
            total_files=5,
            total_issues=10,
            issues_by_category={"security": 3, "performance": 2},
            issues_by_severity={"high": 2, "medium": 3},
            quality_score=75.0,
            maintainability_index=80.0,
            technical_debt_ratio=0.15
        )
        
        self.test_report = QualityReport(
            analysis_id="test-analysis",
            codebase_path="/test/path",
            timestamp=datetime.now(),
            summary=summary,
            prioritized_issues=[prioritized_issue],
            metrics=QualityMetrics(overall_score=75.0),
            recommendations=["Fix security issues", "Improve performance"],
            llm_summary="This is a test AI summary"
        )
    
    def test_formatter_factory(self):
        """Test formatter factory."""
        # Test creating different formatters
        text_formatter = FormatterFactory.create_formatter(ReportFormat.TEXT)
        assert isinstance(text_formatter, TextFormatter)
        
        json_formatter = FormatterFactory.create_formatter(ReportFormat.JSON)
        assert isinstance(json_formatter, JSONFormatter)
        
        # Test supported formats
        formats = FormatterFactory.get_supported_formats()
        assert ReportFormat.TEXT in formats
        assert ReportFormat.JSON in formats
        assert ReportFormat.MARKDOWN in formats
        assert ReportFormat.HTML in formats
        
        # Test unsupported format
        with pytest.raises(ValueError):
            FormatterFactory.create_formatter("unsupported")
    
    def test_text_formatter(self):
        """Test text formatter."""
        formatter = TextFormatter(use_colors=False)  # Disable colors for testing
        
        formatted_report = formatter.format_report(self.test_report)
        
        assert isinstance(formatted_report, str)
        assert len(formatted_report) > 0
        assert "CODE QUALITY ANALYSIS REPORT" in formatted_report
        assert "test-analysis" in formatted_report
        assert "/test/path" in formatted_report
        assert "Test Security Issue" in formatted_report
        assert "Fix security issues" in formatted_report
        assert "This is a test AI summary" in formatted_report
    
    def test_json_formatter(self):
        """Test JSON formatter."""
        formatter = JSONFormatter()
        
        formatted_report = formatter.format_report(self.test_report)
        
        assert isinstance(formatted_report, str)
        
        # Parse JSON to verify structure
        import json
        report_data = json.loads(formatted_report)
        
        assert report_data["analysis_id"] == "test-analysis"
        assert report_data["codebase_path"] == "/test/path"
        assert "summary" in report_data
        assert "prioritized_issues" in report_data
        assert "recommendations" in report_data
        assert len(report_data["prioritized_issues"]) == 1
        assert len(report_data["recommendations"]) == 2
    
    def test_markdown_formatter(self):
        """Test Markdown formatter."""
        from code_quality_agent.reporting.formatters import MarkdownFormatter
        formatter = MarkdownFormatter()
        
        formatted_report = formatter.format_report(self.test_report)
        
        assert isinstance(formatted_report, str)
        assert "# Code Quality Analysis Report" in formatted_report
        assert "## 📊 Summary" in formatted_report
        assert "## 💡 Recommendations" in formatted_report
        assert "## 🤖 AI Insights" in formatted_report
        assert "## 🔍 Top Issues" in formatted_report
        assert "Test Security Issue" in formatted_report
    
    def test_html_formatter(self):
        """Test HTML formatter."""
        from code_quality_agent.reporting.formatters import HTMLFormatter
        formatter = HTMLFormatter()
        
        formatted_report = formatter.format_report(self.test_report)
        
        assert isinstance(formatted_report, str)
        assert "<!DOCTYPE html>" in formatted_report
        assert "<title>Code Quality Analysis Report</title>" in formatted_report
        assert "Test Security Issue" in formatted_report
        assert "</html>" in formatted_report
        
        # Check for CSS styles
        assert "<style>" in formatted_report
        assert "body {" in formatted_report


class TestIntegration:
    """Integration tests for report generation."""
    
    def test_end_to_end_report_generation(self):
        """Test complete end-to-end report generation."""
        # Create comprehensive test data
        issues = [
            Issue(
                id="security-1",
                category=IssueCategory.SECURITY,
                severity=Severity.CRITICAL,
                title="SQL Injection",
                description="Critical SQL injection vulnerability",
                location=CodeLocation("app.py", 10, 12),
                affected_files=["app.py"],
                suggestion="Use parameterized queries",
                confidence=0.95
            ),
            Issue(
                id="performance-1",
                category=IssueCategory.PERFORMANCE,
                severity=Severity.HIGH,
                title="Inefficient Algorithm",
                description="O(n²) algorithm in hot path",
                location=CodeLocation("utils.py", 25, 35),
                affected_files=["utils.py"],
                suggestion="Use more efficient algorithm",
                confidence=0.85
            ),
            Issue(
                id="complexity-1",
                category=IssueCategory.COMPLEXITY,
                severity=Severity.MEDIUM,
                title="High Cyclomatic Complexity",
                description="Function has high complexity",
                location=CodeLocation("complex.py", 50, 80),
                affected_files=["complex.py"],
                suggestion="Refactor into smaller functions",
                confidence=0.9
            )
        ]
        
        parsed_files = [
            ParsedFile(
                path="app.py",
                language="python",
                content="def vulnerable_query(user_id):\n    query = f'SELECT * FROM users WHERE id = {user_id}'\n    return query"
            ),
            ParsedFile(
                path="utils.py",
                language="python",
                content="def inefficient_search(items, target):\n    for i in items:\n        for j in items:\n            if i == j == target:\n                return True\n    return False"
            )
        ]
        
        analysis_result = AnalysisResult(
            analysis_id="integration-test",
            codebase_path="/integration/test",
            parsed_files=parsed_files,
            issues=issues,
            metrics=QualityMetrics(
                overall_score=65.0,
                maintainability_index=70.0,
                technical_debt_ratio=0.25
            ),
            timestamp=datetime.now()
        )
        
        # Generate report
        generator = ReportGenerator(
            llm_service=create_llm_service(provider="mock"),
            enable_llm_enhancements=True
        )
        
        report = generator.generate_report(analysis_result)
        
        # Verify report structure
        assert len(report.prioritized_issues) == 3
        assert report.summary.total_issues == 3
        assert len(report.recommendations) > 0
        
        # Critical security issue should be prioritized highest
        top_issue = report.prioritized_issues[0]
        assert top_issue.issue.severity == Severity.CRITICAL
        assert top_issue.issue.category == IssueCategory.SECURITY
        
        # Test different formatters
        text_formatter = FormatterFactory.create_formatter(ReportFormat.TEXT, use_colors=False)
        json_formatter = FormatterFactory.create_formatter(ReportFormat.JSON)
        
        text_report = text_formatter.format_report(report)
        json_report = json_formatter.format_report(report)
        
        assert len(text_report) > 0
        assert len(json_report) > 0
        
        # Verify JSON structure
        import json
        json_data = json.loads(json_report)
        assert json_data["analysis_id"] == "integration-test"
        assert len(json_data["prioritized_issues"]) == 3


if __name__ == "__main__":
    pytest.main([__file__])