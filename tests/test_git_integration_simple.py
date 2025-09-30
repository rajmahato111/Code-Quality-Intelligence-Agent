"""Simple integration tests for Git platform integration."""

import pytest
import json
import hmac
import hashlib
from datetime import datetime
from unittest.mock import Mock, patch

from code_quality_agent.web.git_platform_integration import (
    GitHubPlatformIntegration,
    GitLabPlatformIntegration,
    WebhookHandler,
    PullRequestAnalyzer,
    WebhookEvent,
    PullRequestInfo,
    PRComment,
    PRReview,
    get_platform_integration
)
from code_quality_agent.web.models import (
    AnalysisResult,
    Issue,
    IssueLocation,
    SeverityLevel,
    AnalysisStatus
)


class TestWebhookSignatureVerification:
    """Test webhook signature verification."""
    
    def test_github_webhook_signature_verification(self):
        """Test GitHub webhook signature verification."""
        integration = GitHubPlatformIntegration()
        payload = b'{"test": "data"}'
        secret = "webhook_secret"
        
        # Create valid signature
        signature = "sha256=" + hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        # Test valid signature
        assert integration.verify_webhook_signature(payload, signature, secret) is True
        
        # Test invalid signature
        assert integration.verify_webhook_signature(payload, "invalid", secret) is False
        
        # Test malformed signature
        assert integration.verify_webhook_signature(payload, "malformed", secret) is False
    
    def test_gitlab_webhook_token_verification(self):
        """Test GitLab webhook token verification."""
        integration = GitLabPlatformIntegration()
        secret = "webhook_token"
        
        # Test valid token
        assert integration.verify_webhook_signature(b"", secret, secret) is True
        
        # Test invalid token
        assert integration.verify_webhook_signature(b"", "invalid", secret) is False


class TestWebhookEventParsing:
    """Test webhook event parsing."""
    
    def test_github_webhook_parsing(self):
        """Test GitHub webhook parsing."""
        handler = WebhookHandler()
        
        payload = {
            "action": "opened",
            "pull_request": {
                "number": 123,
                "head": {"ref": "feature-branch"},
                "base": {"ref": "main"}
            },
            "repository": {
                "full_name": "owner/repo",
                "clone_url": "https://github.com/owner/repo.git",
                "default_branch": "main"
            },
            "sender": {"login": "developer"}
        }
        
        event = handler.parse_github_webhook(payload, "pull_request")
        
        assert event is not None
        assert event.event_type == "pull_request"
        assert event.action == "opened"
        assert event.pull_request["number"] == 123
        assert event.repository["full_name"] == "owner/repo"
        assert event.sender["login"] == "developer"
    
    def test_gitlab_webhook_parsing(self):
        """Test GitLab webhook parsing."""
        handler = WebhookHandler()
        
        payload = {
            "object_kind": "merge_request",
            "action": "open",
            "merge_request": {
                "iid": 123,
                "source_branch": "feature-branch",
                "target_branch": "main"
            },
            "project": {
                "path_with_namespace": "owner/repo",
                "http_url_to_repo": "https://gitlab.com/owner/repo.git",
                "default_branch": "main"
            },
            "user": {"username": "developer"}
        }
        
        event = handler.parse_gitlab_webhook(payload)
        
        assert event is not None
        assert event.event_type == "merge_request"
        assert event.action == "open"
        assert event.pull_request["iid"] == 123
        assert event.repository["path_with_namespace"] == "owner/repo"
        assert event.sender["username"] == "developer"


class TestAnalysisTriggerLogic:
    """Test analysis trigger logic."""
    
    def test_should_trigger_analysis_pr_events(self):
        """Test PR events that should trigger analysis."""
        handler = WebhookHandler()
        
        # PR events that should trigger
        trigger_actions = ["opened", "synchronize", "reopened", "open", "update"]
        
        for action in trigger_actions:
            event = WebhookEvent(
                event_type="pull_request",
                repository={},
                sender={},
                action=action
            )
            assert handler.should_trigger_analysis(event) is True, f"Action {action} should trigger"
        
        # PR events that shouldn't trigger
        no_trigger_actions = ["closed", "merged", "locked"]
        
        for action in no_trigger_actions:
            event = WebhookEvent(
                event_type="pull_request",
                repository={},
                sender={},
                action=action
            )
            assert handler.should_trigger_analysis(event) is False, f"Action {action} should not trigger"
    
    def test_should_trigger_analysis_push_events(self):
        """Test push events that should trigger analysis."""
        handler = WebhookHandler()
        
        # Push to main branches should trigger
        main_branches = ["refs/heads/main", "refs/heads/master", "refs/heads/develop"]
        
        for branch in main_branches:
            event = WebhookEvent(
                event_type="push",
                repository={},
                sender={},
                ref=branch
            )
            assert handler.should_trigger_analysis(event) is True, f"Push to {branch} should trigger"
        
        # Push to feature branches shouldn't trigger
        feature_branches = ["refs/heads/feature", "refs/heads/bugfix", "refs/heads/hotfix"]
        
        for branch in feature_branches:
            event = WebhookEvent(
                event_type="push",
                repository={},
                sender={},
                ref=branch
            )
            assert handler.should_trigger_analysis(event) is False, f"Push to {branch} should not trigger"


class TestRepositoryInfoExtraction:
    """Test repository information extraction."""
    
    def test_extract_github_repository_info(self):
        """Test GitHub repository info extraction."""
        handler = WebhookHandler()
        
        event = WebhookEvent(
            event_type="pull_request",
            repository={
                "full_name": "owner/repo",
                "clone_url": "https://github.com/owner/repo.git",
                "default_branch": "main"
            },
            sender={}
        )
        
        repo_info = handler.extract_repository_info(event)
        
        assert repo_info["owner"] == "owner"
        assert repo_info["name"] == "repo"
        assert repo_info["url"] == "https://github.com/owner/repo.git"
        assert repo_info["default_branch"] == "main"
    
    def test_extract_gitlab_repository_info(self):
        """Test GitLab repository info extraction."""
        handler = WebhookHandler()
        
        event = WebhookEvent(
            event_type="merge_request",
            repository={
                "path_with_namespace": "owner/repo",
                "http_url_to_repo": "https://gitlab.com/owner/repo.git",
                "default_branch": "main"
            },
            sender={}
        )
        
        repo_info = handler.extract_repository_info(event)
        
        assert repo_info["owner"] == "owner"
        assert repo_info["name"] == "repo"
        assert repo_info["url"] == "https://gitlab.com/owner/repo.git"
        assert repo_info["default_branch"] == "main"


class TestPullRequestAnalyzer:
    """Test pull request analyzer functionality."""
    
    def test_create_review_summary_with_issues(self):
        """Test review summary creation with issues."""
        mock_platform = Mock()
        analyzer = PullRequestAnalyzer(mock_platform)
        
        pr_info = PullRequestInfo(
            number=123,
            title="Fix security issues",
            description="This PR addresses several security vulnerabilities",
            author="developer",
            base_branch="main",
            head_branch="security-fixes",
            head_sha="head456",
            base_sha="base123",
            state="open",
            url="https://github.com/owner/repo/pull/123",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Create sample issues
        critical = [Mock()] * 2
        high = [Mock()] * 1
        medium = [Mock()] * 3
        low = [Mock()] * 0
        
        summary = analyzer._create_review_summary(pr_info, 5, critical, high, medium, low)
        
        # Assertions
        assert "Code Quality Analysis Results" in summary
        assert "Fix security issues" in summary
        assert "Files Changed:** 5" in summary
        assert "Total Issues Found:** 6" in summary
        assert "Critical:** 2 issues" in summary
        assert "High:** 1 issues" in summary
        assert "Medium:** 3 issues" in summary
        assert "Action Required" in summary
    
    def test_create_review_summary_no_issues(self):
        """Test review summary with no issues."""
        mock_platform = Mock()
        analyzer = PullRequestAnalyzer(mock_platform)
        
        pr_info = PullRequestInfo(
            number=123,
            title="Clean up code",
            description="Minor cleanup",
            author="developer",
            base_branch="main",
            head_branch="cleanup",
            head_sha="head456",
            base_sha="base123",
            state="open",
            url="https://github.com/owner/repo/pull/123",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        summary = analyzer._create_review_summary(pr_info, 3, [], [], [], [])
        
        assert "Great job!" in summary
        assert "No quality issues found" in summary
    
    def test_create_inline_comment(self):
        """Test inline comment creation."""
        mock_platform = Mock()
        analyzer = PullRequestAnalyzer(mock_platform)
        
        issue = Issue(
            id="test-issue",
            category="security",
            type="sql_injection",
            severity=SeverityLevel.CRITICAL,
            confidence=0.95,
            title="SQL Injection Vulnerability",
            description="Potential SQL injection in user input handling",
            explanation="This code directly concatenates user input into SQL queries",
            location=IssueLocation(
                file_path="src/main.py",
                line_number=42,
                function_name="get_user"
            ),
            suggestions=["Use parameterized queries", "Validate input"]
        )
        
        comment = analyzer._create_inline_comment(issue)
        
        # Assertions
        assert comment is not None
        assert comment.path == "src/main.py"
        assert comment.line == 42
        assert comment.side == "RIGHT"
        assert "**CRITICAL:** SQL Injection Vulnerability" in comment.body
        assert "Potential SQL injection" in comment.body
        assert "This code directly concatenates" in comment.body
        assert "Use parameterized queries" in comment.body
        assert "Confidence: 95.0%" in comment.body
    
    def test_create_inline_comment_no_line(self):
        """Test inline comment creation for issue without line number."""
        mock_platform = Mock()
        analyzer = PullRequestAnalyzer(mock_platform)
        
        issue = Issue(
            id="test-issue",
            category="security",
            type="general",
            severity=SeverityLevel.HIGH,
            confidence=0.80,
            title="General Security Issue",
            description="General security concern",
            location=IssueLocation(
                file_path="src/main.py"
                # No line_number
            )
        )
        
        comment = analyzer._create_inline_comment(issue)
        
        # Should return None for issues without line numbers
        assert comment is None


class TestPlatformIntegrationFactory:
    """Test platform integration factory."""
    
    def test_get_github_integration(self):
        """Test getting GitHub integration."""
        integration = get_platform_integration("https://github.com/owner/repo")
        assert isinstance(integration, GitHubPlatformIntegration)
    
    def test_get_gitlab_integration(self):
        """Test getting GitLab integration."""
        integration = get_platform_integration("https://gitlab.com/owner/repo")
        assert isinstance(integration, GitLabPlatformIntegration)
    
    def test_unsupported_platform(self):
        """Test unsupported platform."""
        with pytest.raises(ValueError, match="Unsupported Git platform"):
            get_platform_integration("https://bitbucket.org/owner/repo")


class TestPRCommentAndReviewModels:
    """Test PR comment and review models."""
    
    def test_pr_comment_creation(self):
        """Test PR comment model creation."""
        comment = PRComment(
            body="This is a test comment",
            path="src/main.py",
            line=42,
            side="RIGHT"
        )
        
        assert comment.body == "This is a test comment"
        assert comment.path == "src/main.py"
        assert comment.line == 42
        assert comment.side == "RIGHT"
        assert comment.start_line is None
        assert comment.start_side is None
    
    def test_pr_comment_multiline(self):
        """Test PR comment with multi-line range."""
        comment = PRComment(
            body="Multi-line issue",
            path="src/utils.py",
            line=50,
            side="RIGHT",
            start_line=45,
            start_side="RIGHT"
        )
        
        assert comment.start_line == 45
        assert comment.start_side == "RIGHT"
    
    def test_pr_review_creation(self):
        """Test PR review model creation."""
        comments = [
            PRComment(body="Issue 1", path="file1.py", line=10, side="RIGHT"),
            PRComment(body="Issue 2", path="file2.py", line=20, side="RIGHT")
        ]
        
        review = PRReview(
            event="REQUEST_CHANGES",
            body="Found several issues",
            comments=comments
        )
        
        assert review.event == "REQUEST_CHANGES"
        assert review.body == "Found several issues"
        assert len(review.comments) == 2
        assert review.comments[0].body == "Issue 1"
        assert review.comments[1].body == "Issue 2"


if __name__ == "__main__":
    pytest.main([__file__])