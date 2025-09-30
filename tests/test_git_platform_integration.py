"""Tests for Git platform integration functionality."""

import pytest
import asyncio
import json
import hmac
import hashlib
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any

try:
    import aiohttp
    from aiohttp import web
    from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop
except ImportError:
    aiohttp = None
    web = None
    AioHTTPTestCase = None
    unittest_run_loop = None

from code_quality_agent.web.git_platform_integration import (
    GitHubPlatformIntegration,
    GitLabPlatformIntegration,
    PullRequestAnalyzer,
    WebhookHandler,
    PullRequestInfo,
    WebhookEvent,
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


class TestGitHubPlatformIntegration:
    """Test GitHub platform integration."""
    
    @pytest.fixture
    def github_integration(self):
        """Create GitHub integration instance."""
        return GitHubPlatformIntegration(token="test_token")
    
    @pytest.fixture
    def mock_session(self):
        """Create mock aiohttp session."""
        session = AsyncMock()
        return session
    
    @pytest.fixture
    def sample_pr_data(self):
        """Sample PR data from GitHub API."""
        return {
            "number": 123,
            "title": "Fix security vulnerability",
            "body": "This PR fixes a critical security issue",
            "user": {"login": "developer"},
            "base": {"ref": "main", "sha": "base123"},
            "head": {"ref": "feature-branch", "sha": "head456"},
            "state": "open",
            "html_url": "https://github.com/owner/repo/pull/123",
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T12:00:00Z"
        }
    
    @pytest.mark.asyncio
    async def test_get_pull_request(self, github_integration, mock_session, sample_pr_data):
        """Test getting pull request information."""
        # Mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=sample_pr_data)
        
        # Mock the context manager properly
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context_manager.__aexit__ = AsyncMock(return_value=None)
        mock_session.get.return_value = mock_context_manager
        
        github_integration.session = mock_session
        
        # Test
        pr_info = await github_integration.get_pull_request("owner", "repo", 123)
        
        # Assertions
        assert pr_info.number == 123
        assert pr_info.title == "Fix security vulnerability"
        assert pr_info.author == "developer"
        assert pr_info.base_branch == "main"
        assert pr_info.head_branch == "feature-branch"
        assert pr_info.head_sha == "head456"
        assert pr_info.base_sha == "base123"
        assert pr_info.state == "open"
        
        # Verify API call
        mock_session.get.assert_called_once_with(
            "https://api.github.com/repos/owner/repo/pulls/123",
            headers={
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "CodeQualityAgent/1.0",
                "Authorization": "token test_token"
            }
        )
    
    @pytest.mark.asyncio
    async def test_get_pull_request_not_found(self, github_integration, mock_session):
        """Test handling of PR not found."""
        # Mock 404 response
        mock_response = AsyncMock()
        mock_response.status = 404
        
        # Mock the context manager properly
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context_manager.__aexit__ = AsyncMock(return_value=None)
        mock_session.get.return_value = mock_context_manager
        
        github_integration.session = mock_session
        
        # Test
        with pytest.raises(ValueError, match="Pull request #123 not found"):
            await github_integration.get_pull_request("owner", "repo", 123)
    
    @pytest.mark.asyncio
    async def test_get_pull_request_files(self, github_integration, mock_session):
        """Test getting PR changed files."""
        # Mock response
        files_data = [
            {"filename": "src/main.py"},
            {"filename": "tests/test_main.py"},
            {"filename": "README.md"}
        ]
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=files_data)
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        github_integration.session = mock_session
        
        # Test
        files = await github_integration.get_pull_request_files("owner", "repo", 123)
        
        # Assertions
        assert files == ["src/main.py", "tests/test_main.py", "README.md"]
        
        # Verify API call
        mock_session.get.assert_called_once_with(
            "https://api.github.com/repos/owner/repo/pulls/123/files",
            headers={
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "CodeQualityAgent/1.0",
                "Authorization": "token test_token"
            }
        )
    
    @pytest.mark.asyncio
    async def test_create_pull_request_comment(self, github_integration, mock_session):
        """Test creating PR comment."""
        # Mock response
        mock_response = AsyncMock()
        mock_response.status = 201
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        github_integration.session = mock_session
        
        # Test inline comment
        comment = PRComment(
            body="This line has a security issue",
            path="src/main.py",
            line=42,
            side="RIGHT"
        )
        
        result = await github_integration.create_pull_request_comment("owner", "repo", 123, comment)
        
        # Assertions
        assert result is True
        
        # Verify API call
        mock_session.post.assert_called_once_with(
            "https://api.github.com/repos/owner/repo/pulls/123/comments",
            headers={
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "CodeQualityAgent/1.0",
                "Authorization": "token test_token"
            },
            json={
                "body": "This line has a security issue",
                "path": "src/main.py",
                "line": 42,
                "side": "RIGHT"
            }
        )
    
    @pytest.mark.asyncio
    async def test_create_pull_request_review(self, github_integration, mock_session):
        """Test creating PR review."""
        # Mock response
        mock_response = AsyncMock()
        mock_response.status = 201
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        github_integration.session = mock_session
        
        # Test review with comments
        review = PRReview(
            event="REQUEST_CHANGES",
            body="Found several issues that need to be addressed",
            comments=[
                PRComment(
                    body="Security vulnerability here",
                    path="src/main.py",
                    line=42,
                    side="RIGHT"
                ),
                PRComment(
                    body="Performance issue",
                    path="src/utils.py",
                    line=15,
                    side="RIGHT"
                )
            ]
        )
        
        result = await github_integration.create_pull_request_review("owner", "repo", 123, review)
        
        # Assertions
        assert result is True
        
        # Verify API call
        expected_payload = {
            "event": "REQUEST_CHANGES",
            "body": "Found several issues that need to be addressed",
            "comments": [
                {
                    "path": "src/main.py",
                    "body": "Security vulnerability here",
                    "line": 42,
                    "side": "RIGHT"
                },
                {
                    "path": "src/utils.py",
                    "body": "Performance issue",
                    "line": 15,
                    "side": "RIGHT"
                }
            ]
        }
        
        mock_session.post.assert_called_once_with(
            "https://api.github.com/repos/owner/repo/pulls/123/reviews",
            headers={
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "CodeQualityAgent/1.0",
                "Authorization": "token test_token"
            },
            json=expected_payload
        )
    
    @pytest.mark.asyncio
    async def test_update_commit_status(self, github_integration, mock_session):
        """Test updating commit status."""
        # Mock response
        mock_response = AsyncMock()
        mock_response.status = 201
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        github_integration.session = mock_session
        
        # Test
        result = await github_integration.update_commit_status(
            "owner", "repo", "abc123", "success", 
            "All quality checks passed", "code-quality/analysis",
            "https://example.com/report"
        )
        
        # Assertions
        assert result is True
        
        # Verify API call
        mock_session.post.assert_called_once_with(
            "https://api.github.com/repos/owner/repo/statuses/abc123",
            headers={
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "CodeQualityAgent/1.0",
                "Authorization": "token test_token"
            },
            json={
                "state": "success",
                "description": "All quality checks passed",
                "context": "code-quality/analysis",
                "target_url": "https://example.com/report"
            }
        )
    
    def test_verify_webhook_signature(self, github_integration):
        """Test webhook signature verification."""
        payload = b'{"test": "data"}'
        secret = "webhook_secret"
        
        # Create valid signature
        signature = "sha256=" + hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        # Test valid signature
        assert github_integration.verify_webhook_signature(payload, signature, secret) is True
        
        # Test invalid signature
        assert github_integration.verify_webhook_signature(payload, "invalid", secret) is False
        
        # Test malformed signature
        assert github_integration.verify_webhook_signature(payload, "malformed", secret) is False


class TestGitLabPlatformIntegration:
    """Test GitLab platform integration."""
    
    @pytest.fixture
    def gitlab_integration(self):
        """Create GitLab integration instance."""
        return GitLabPlatformIntegration(token="test_token")
    
    @pytest.fixture
    def mock_session(self):
        """Create mock aiohttp session."""
        session = AsyncMock()
        return session
    
    @pytest.fixture
    def sample_mr_data(self):
        """Sample MR data from GitLab API."""
        return {
            "iid": 123,
            "title": "Fix security vulnerability",
            "description": "This MR fixes a critical security issue",
            "author": {"username": "developer"},
            "target_branch": "main",
            "source_branch": "feature-branch",
            "sha": "head456",
            "diff_refs": {"base_sha": "base123"},
            "state": "opened",
            "web_url": "https://gitlab.com/owner/repo/-/merge_requests/123",
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T12:00:00Z"
        }
    
    @pytest.mark.asyncio
    async def test_get_pull_request(self, gitlab_integration, mock_session, sample_mr_data):
        """Test getting merge request information."""
        # Mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=sample_mr_data)
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        gitlab_integration.session = mock_session
        
        # Test
        pr_info = await gitlab_integration.get_pull_request("owner", "repo", 123)
        
        # Assertions
        assert pr_info.number == 123
        assert pr_info.title == "Fix security vulnerability"
        assert pr_info.author == "developer"
        assert pr_info.base_branch == "main"
        assert pr_info.head_branch == "feature-branch"
        assert pr_info.head_sha == "head456"
        assert pr_info.base_sha == "base123"
        assert pr_info.state == "opened"
        
        # Verify API call
        mock_session.get.assert_called_once_with(
            "https://gitlab.com/api/v4/projects/owner%2Frepo/merge_requests/123",
            headers={
                "User-Agent": "CodeQualityAgent/1.0",
                "Authorization": "Bearer test_token"
            }
        )


class TestPullRequestAnalyzer:
    """Test pull request analyzer."""
    
    @pytest.fixture
    def mock_platform(self):
        """Create mock platform integration."""
        platform = AsyncMock()
        return platform
    
    @pytest.fixture
    def pr_analyzer(self, mock_platform):
        """Create PR analyzer instance."""
        return PullRequestAnalyzer(mock_platform)
    
    @pytest.fixture
    def sample_pr_info(self):
        """Sample PR info."""
        return PullRequestInfo(
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
    
    @pytest.fixture
    def sample_analysis_result(self):
        """Sample analysis result with issues."""
        return AnalysisResult(
            job_id="test-job-123",
            status=AnalysisStatus.COMPLETED,
            started_at=datetime.now(),
            issues=[
                Issue(
                    id="issue-1",
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
                ),
                Issue(
                    id="issue-2",
                    category="performance",
                    type="inefficient_loop",
                    severity=SeverityLevel.HIGH,
                    confidence=0.85,
                    title="Inefficient Loop",
                    description="Nested loop with O(n²) complexity",
                    location=IssueLocation(
                        file_path="src/utils.py",
                        line_number=15,
                        function_name="process_data"
                    ),
                    suggestions=["Use dictionary lookup", "Optimize algorithm"]
                ),
                Issue(
                    id="issue-3",
                    category="style",
                    type="missing_docstring",
                    severity=SeverityLevel.LOW,
                    confidence=0.90,
                    title="Missing Docstring",
                    description="Function lacks documentation",
                    location=IssueLocation(
                        file_path="src/other.py",
                        line_number=10,
                        function_name="helper"
                    ),
                    suggestions=["Add docstring"]
                )
            ]
        )
    
    @pytest.mark.asyncio
    async def test_analyze_pull_request(self, pr_analyzer, mock_platform, sample_pr_info, sample_analysis_result):
        """Test PR analysis and review creation."""
        # Mock platform responses
        mock_platform.get_pull_request.return_value = sample_pr_info
        mock_platform.get_pull_request_files.return_value = ["src/main.py", "src/utils.py"]
        mock_platform.create_pull_request_review.return_value = True
        mock_platform.update_commit_status.return_value = True
        
        # Test
        result = await pr_analyzer.analyze_pull_request(
            "owner", "repo", 123, sample_analysis_result
        )
        
        # Assertions
        assert result["pr_number"] == 123
        assert result["pr_title"] == "Fix security issues"
        assert result["files_changed"] == 2
        assert result["issues_found"] == 2  # Only issues in changed files
        assert result["critical_issues"] == 1
        assert result["high_issues"] == 1
        assert result["medium_issues"] == 0
        assert result["low_issues"] == 0
        assert result["review_event"] == "REQUEST_CHANGES"  # Due to critical issue
        assert result["review_created"] is True
        assert result["status_updated"] is True
        
        # Verify platform calls
        mock_platform.get_pull_request.assert_called_once_with("owner", "repo", 123)
        mock_platform.get_pull_request_files.assert_called_once_with("owner", "repo", 123)
        mock_platform.create_pull_request_review.assert_called_once()
        mock_platform.update_commit_status.assert_called_once_with(
            "owner", "repo", "head456", "failure", 
            "Found 2 quality issues", "code-quality/analysis"
        )
    
    def test_create_review_summary(self, pr_analyzer, sample_pr_info):
        """Test review summary creation."""
        # Create sample issues
        critical = [Mock()] * 2
        high = [Mock()] * 1
        medium = [Mock()] * 3
        low = [Mock()] * 0
        
        # Test
        summary = pr_analyzer._create_review_summary(
            sample_pr_info, 5, critical, high, medium, low
        )
        
        # Assertions
        assert "Code Quality Analysis Results" in summary
        assert "Fix security issues" in summary
        assert "Files Changed:** 5" in summary
        assert "Total Issues Found:** 6" in summary
        assert "Critical:** 2 issues" in summary
        assert "High:** 1 issues" in summary
        assert "Medium:** 3 issues" in summary
        assert "Action Required" in summary
    
    def test_create_review_summary_no_issues(self, pr_analyzer, sample_pr_info):
        """Test review summary with no issues."""
        summary = pr_analyzer._create_review_summary(
            sample_pr_info, 3, [], [], [], []
        )
        
        assert "Great job!" in summary
        assert "No quality issues found" in summary
    
    def test_create_inline_comment(self, pr_analyzer):
        """Test inline comment creation."""
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
        
        # Test
        comment = pr_analyzer._create_inline_comment(issue)
        
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
    
    def test_create_inline_comment_no_line(self, pr_analyzer):
        """Test inline comment creation for issue without line number."""
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
        
        # Test
        comment = pr_analyzer._create_inline_comment(issue)
        
        # Assertions
        assert comment is None


class TestWebhookHandler:
    """Test webhook handler."""
    
    @pytest.fixture
    def webhook_handler(self):
        """Create webhook handler instance."""
        return WebhookHandler(
            github_secret="github_secret",
            gitlab_secret="gitlab_secret"
        )
    
    @pytest.fixture
    def github_webhook_payload(self):
        """Sample GitHub webhook payload."""
        return {
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
    
    @pytest.fixture
    def gitlab_webhook_payload(self):
        """Sample GitLab webhook payload."""
        return {
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
    
    def test_verify_github_webhook(self, webhook_handler):
        """Test GitHub webhook verification."""
        payload = b'{"test": "data"}'
        
        # Create valid signature
        signature = "sha256=" + hmac.new(
            "github_secret".encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        # Test
        assert webhook_handler.verify_github_webhook(payload, signature) is True
        assert webhook_handler.verify_github_webhook(payload, "invalid") is False
    
    def test_verify_gitlab_webhook(self, webhook_handler):
        """Test GitLab webhook verification."""
        assert webhook_handler.verify_gitlab_webhook("gitlab_secret") is True
        assert webhook_handler.verify_gitlab_webhook("invalid") is False
    
    def test_parse_github_webhook(self, webhook_handler, github_webhook_payload):
        """Test GitHub webhook parsing."""
        event = webhook_handler.parse_github_webhook(github_webhook_payload, "pull_request")
        
        assert event is not None
        assert event.event_type == "pull_request"
        assert event.action == "opened"
        assert event.pull_request["number"] == 123
        assert event.repository["full_name"] == "owner/repo"
        assert event.sender["login"] == "developer"
    
    def test_parse_gitlab_webhook(self, webhook_handler, gitlab_webhook_payload):
        """Test GitLab webhook parsing."""
        event = webhook_handler.parse_gitlab_webhook(gitlab_webhook_payload)
        
        assert event is not None
        assert event.event_type == "merge_request"
        assert event.action == "open"
        assert event.pull_request["iid"] == 123
        assert event.repository["path_with_namespace"] == "owner/repo"
        assert event.sender["username"] == "developer"
    
    def test_should_trigger_analysis(self, webhook_handler):
        """Test analysis trigger logic."""
        # PR events that should trigger
        pr_event = WebhookEvent(
            event_type="pull_request",
            repository={},
            sender={},
            action="opened"
        )
        assert webhook_handler.should_trigger_analysis(pr_event) is True
        
        # PR events that shouldn't trigger
        pr_event_closed = WebhookEvent(
            event_type="pull_request",
            repository={},
            sender={},
            action="closed"
        )
        assert webhook_handler.should_trigger_analysis(pr_event_closed) is False
        
        # Push to main branch should trigger
        push_main = WebhookEvent(
            event_type="push",
            repository={},
            sender={},
            ref="refs/heads/main"
        )
        assert webhook_handler.should_trigger_analysis(push_main) is True
        
        # Push to feature branch shouldn't trigger
        push_feature = WebhookEvent(
            event_type="push",
            repository={},
            sender={},
            ref="refs/heads/feature"
        )
        assert webhook_handler.should_trigger_analysis(push_feature) is False
    
    def test_extract_repository_info_github(self, webhook_handler):
        """Test repository info extraction from GitHub event."""
        event = WebhookEvent(
            event_type="pull_request",
            repository={
                "full_name": "owner/repo",
                "clone_url": "https://github.com/owner/repo.git",
                "default_branch": "main"
            },
            sender={}
        )
        
        repo_info = webhook_handler.extract_repository_info(event)
        
        assert repo_info["owner"] == "owner"
        assert repo_info["name"] == "repo"
        assert repo_info["url"] == "https://github.com/owner/repo.git"
        assert repo_info["default_branch"] == "main"
    
    def test_extract_repository_info_gitlab(self, webhook_handler):
        """Test repository info extraction from GitLab event."""
        event = WebhookEvent(
            event_type="merge_request",
            repository={
                "path_with_namespace": "owner/repo",
                "http_url_to_repo": "https://gitlab.com/owner/repo.git",
                "default_branch": "main"
            },
            sender={}
        )
        
        repo_info = webhook_handler.extract_repository_info(event)
        
        assert repo_info["owner"] == "owner"
        assert repo_info["name"] == "repo"
        assert repo_info["url"] == "https://gitlab.com/owner/repo.git"
        assert repo_info["default_branch"] == "main"


class TestPlatformIntegrationFactory:
    """Test platform integration factory function."""
    
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


@pytest.mark.skipif(aiohttp is None, reason="aiohttp not available")
class TestWebhookEndpoints(AioHTTPTestCase):
    """Test webhook endpoints with real HTTP server."""
    
    async def get_application(self):
        """Create test application."""
        app = web.Application()
        
        # Add simple webhook endpoint for testing
        async def github_webhook(request):
            return web.json_response({"status": "ok"})
        
        app.router.add_post('/webhooks/github', github_webhook)
        return app
    
    @unittest_run_loop
    async def test_github_webhook_endpoint(self):
        """Test GitHub webhook endpoint."""
        payload = {"action": "opened", "pull_request": {"number": 123}}
        
        resp = await self.client.request(
            "POST", 
            "/webhooks/github",
            json=payload,
            headers={"X-GitHub-Event": "pull_request"}
        )
        
        assert resp.status == 200
        data = await resp.json()
        assert data["status"] == "ok"


if __name__ == "__main__":
    pytest.main([__file__])