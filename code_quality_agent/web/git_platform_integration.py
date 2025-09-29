"""Git platform integration for pull request analysis and CI/CD webhooks."""

import os
import json
import logging
import asyncio
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from urllib.parse import urlparse
import hmac
import hashlib

try:
    import aiohttp
except ImportError:
    aiohttp = None

from pydantic import BaseModel, Field, HttpUrl

from .models import AnalysisResult, Issue, SeverityLevel, AnalysisStatus
from .github_integration import GitHubIntegration

logger = logging.getLogger(__name__)


class PullRequestInfo(BaseModel):
    """Pull request information."""
    number: int = Field(..., description="Pull request number")
    title: str = Field(..., description="Pull request title")
    description: Optional[str] = Field(None, description="Pull request description")
    author: str = Field(..., description="Pull request author")
    base_branch: str = Field(..., description="Base branch")
    head_branch: str = Field(..., description="Head branch")
    head_sha: str = Field(..., description="Head commit SHA")
    base_sha: str = Field(..., description="Base commit SHA")
    state: str = Field(..., description="Pull request state")
    url: str = Field(..., description="Pull request URL")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class WebhookEvent(BaseModel):
    """Webhook event data."""
    event_type: str = Field(..., description="Event type (push, pull_request, etc.)")
    repository: Dict[str, Any] = Field(..., description="Repository information")
    sender: Dict[str, Any] = Field(..., description="Event sender information")
    action: Optional[str] = Field(None, description="Event action")
    pull_request: Optional[Dict[str, Any]] = Field(None, description="Pull request data")
    commits: Optional[List[Dict[str, Any]]] = Field(None, description="Commit data")
    ref: Optional[str] = Field(None, description="Git reference")
    before: Optional[str] = Field(None, description="Before commit SHA")
    after: Optional[str] = Field(None, description="After commit SHA")


class PRComment(BaseModel):
    """Pull request comment."""
    body: str = Field(..., description="Comment body")
    path: Optional[str] = Field(None, description="File path for inline comments")
    line: Optional[int] = Field(None, description="Line number for inline comments")
    side: str = Field("RIGHT", description="Side of diff (LEFT/RIGHT)")
    start_line: Optional[int] = Field(None, description="Start line for multi-line comments")
    start_side: Optional[str] = Field(None, description="Start side for multi-line comments")


class PRReview(BaseModel):
    """Pull request review."""
    event: str = Field(..., description="Review event (APPROVE, REQUEST_CHANGES, COMMENT)")
    body: Optional[str] = Field(None, description="Review body")
    comments: List[PRComment] = Field(default_factory=list, description="Review comments")


class GitPlatformIntegration:
    """Base class for Git platform integrations."""
    
    def __init__(self, token: Optional[str] = None):
        """Initialize Git platform integration.
        
        Args:
            token: Platform API token
        """
        self.token = token
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        if not aiohttp:
            raise RuntimeError("aiohttp is required for Git platform integration")
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def get_pull_request(self, owner: str, repo: str, pr_number: int) -> PullRequestInfo:
        """Get pull request information."""
        raise NotImplementedError
    
    async def get_pull_request_files(self, owner: str, repo: str, pr_number: int) -> List[str]:
        """Get list of files changed in pull request."""
        raise NotImplementedError
    
    async def create_pull_request_comment(self, owner: str, repo: str, pr_number: int, comment: PRComment) -> bool:
        """Create a comment on a pull request."""
        raise NotImplementedError
    
    async def create_pull_request_review(self, owner: str, repo: str, pr_number: int, review: PRReview) -> bool:
        """Create a review on a pull request."""
        raise NotImplementedError
    
    async def update_commit_status(self, owner: str, repo: str, sha: str, state: str, 
                                 description: str, context: str, target_url: Optional[str] = None) -> bool:
        """Update commit status."""
        raise NotImplementedError
    
    def verify_webhook_signature(self, payload: bytes, signature: str, secret: str) -> bool:
        """Verify webhook signature."""
        raise NotImplementedError


class GitHubPlatformIntegration(GitPlatformIntegration):
    """GitHub platform integration for PR analysis and CI/CD."""
    
    def __init__(self, token: Optional[str] = None):
        """Initialize GitHub integration.
        
        Args:
            token: GitHub personal access token
        """
        super().__init__(token or os.getenv('GITHUB_TOKEN'))
        self.api_base = "https://api.github.com"
    
    def _get_headers(self) -> Dict[str, str]:
        """Get API headers."""
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "CodeQualityAgent/1.0"
        }
        if self.token:
            headers["Authorization"] = f"token {self.token}"
        return headers
    
    async def get_pull_request(self, owner: str, repo: str, pr_number: int) -> PullRequestInfo:
        """Get pull request information from GitHub API."""
        if not self.session:
            raise RuntimeError("Session not initialized")
        
        url = f"{self.api_base}/repos/{owner}/{repo}/pulls/{pr_number}"
        
        async with self.session.get(url, headers=self._get_headers()) as response:
            if response.status == 404:
                raise ValueError(f"Pull request #{pr_number} not found")
            elif response.status != 200:
                raise ValueError(f"GitHub API error: {response.status}")
            
            data = await response.json()
            
            return PullRequestInfo(
                number=data["number"],
                title=data["title"],
                description=data.get("body"),
                author=data["user"]["login"],
                base_branch=data["base"]["ref"],
                head_branch=data["head"]["ref"],
                head_sha=data["head"]["sha"],
                base_sha=data["base"]["sha"],
                state=data["state"],
                url=data["html_url"],
                created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00")),
                updated_at=datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00"))
            )
    
    async def get_pull_request_files(self, owner: str, repo: str, pr_number: int) -> List[str]:
        """Get list of files changed in pull request."""
        if not self.session:
            raise RuntimeError("Session not initialized")
        
        url = f"{self.api_base}/repos/{owner}/{repo}/pulls/{pr_number}/files"
        
        async with self.session.get(url, headers=self._get_headers()) as response:
            if response.status != 200:
                raise ValueError(f"GitHub API error: {response.status}")
            
            files_data = await response.json()
            return [file_info["filename"] for file_info in files_data]
    
    async def create_pull_request_comment(self, owner: str, repo: str, pr_number: int, comment: PRComment) -> bool:
        """Create a comment on a pull request."""
        if not self.session:
            raise RuntimeError("Session not initialized")
        
        # Choose endpoint based on comment type
        if comment.path and comment.line:
            # Inline comment
            url = f"{self.api_base}/repos/{owner}/{repo}/pulls/{pr_number}/comments"
            payload = {
                "body": comment.body,
                "path": comment.path,
                "line": comment.line,
                "side": comment.side
            }
            if comment.start_line:
                payload["start_line"] = comment.start_line
                payload["start_side"] = comment.start_side or comment.side
        else:
            # General comment
            url = f"{self.api_base}/repos/{owner}/{repo}/issues/{pr_number}/comments"
            payload = {"body": comment.body}
        
        async with self.session.post(url, headers=self._get_headers(), json=payload) as response:
            if response.status in [200, 201]:
                logger.info(f"Created PR comment on {owner}/{repo}#{pr_number}")
                return True
            else:
                logger.error(f"Failed to create PR comment: {response.status}")
                return False
    
    async def create_pull_request_review(self, owner: str, repo: str, pr_number: int, review: PRReview) -> bool:
        """Create a review on a pull request."""
        if not self.session:
            raise RuntimeError("Session not initialized")
        
        url = f"{self.api_base}/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
        
        payload = {
            "event": review.event,
            "body": review.body or "",
            "comments": []
        }
        
        # Add inline comments
        for comment in review.comments:
            comment_data = {
                "path": comment.path,
                "body": comment.body,
                "line": comment.line,
                "side": comment.side
            }
            if comment.start_line:
                comment_data["start_line"] = comment.start_line
                comment_data["start_side"] = comment.start_side or comment.side
            payload["comments"].append(comment_data)
        
        async with self.session.post(url, headers=self._get_headers(), json=payload) as response:
            if response.status in [200, 201]:
                logger.info(f"Created PR review on {owner}/{repo}#{pr_number}")
                return True
            else:
                logger.error(f"Failed to create PR review: {response.status}")
                return False
    
    async def update_commit_status(self, owner: str, repo: str, sha: str, state: str, 
                                 description: str, context: str, target_url: Optional[str] = None) -> bool:
        """Update commit status on GitHub."""
        if not self.session:
            raise RuntimeError("Session not initialized")
        
        url = f"{self.api_base}/repos/{owner}/{repo}/statuses/{sha}"
        
        payload = {
            "state": state,  # pending, success, error, failure
            "description": description,
            "context": context
        }
        
        if target_url:
            payload["target_url"] = target_url
        
        async with self.session.post(url, headers=self._get_headers(), json=payload) as response:
            if response.status in [200, 201]:
                logger.info(f"Updated commit status for {owner}/{repo}@{sha}")
                return True
            else:
                logger.error(f"Failed to update commit status: {response.status}")
                return False
    
    def verify_webhook_signature(self, payload: bytes, signature: str, secret: str) -> bool:
        """Verify GitHub webhook signature."""
        if not signature.startswith("sha256="):
            return False
        
        expected_signature = "sha256=" + hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)


class GitLabPlatformIntegration(GitPlatformIntegration):
    """GitLab platform integration for PR analysis and CI/CD."""
    
    def __init__(self, token: Optional[str] = None, gitlab_url: str = "https://gitlab.com"):
        """Initialize GitLab integration.
        
        Args:
            token: GitLab personal access token
            gitlab_url: GitLab instance URL
        """
        super().__init__(token or os.getenv('GITLAB_TOKEN'))
        self.api_base = f"{gitlab_url}/api/v4"
    
    def _get_headers(self) -> Dict[str, str]:
        """Get API headers."""
        headers = {"User-Agent": "CodeQualityAgent/1.0"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    async def get_pull_request(self, owner: str, repo: str, pr_number: int) -> PullRequestInfo:
        """Get merge request information from GitLab API."""
        if not self.session:
            raise RuntimeError("Session not initialized")
        
        # GitLab uses project ID or path, construct project path
        project_path = f"{owner}/{repo}"
        url = f"{self.api_base}/projects/{project_path.replace('/', '%2F')}/merge_requests/{pr_number}"
        
        async with self.session.get(url, headers=self._get_headers()) as response:
            if response.status == 404:
                raise ValueError(f"Merge request !{pr_number} not found")
            elif response.status != 200:
                raise ValueError(f"GitLab API error: {response.status}")
            
            data = await response.json()
            
            return PullRequestInfo(
                number=data["iid"],
                title=data["title"],
                description=data.get("description"),
                author=data["author"]["username"],
                base_branch=data["target_branch"],
                head_branch=data["source_branch"],
                head_sha=data["sha"],
                base_sha=data.get("diff_refs", {}).get("base_sha", ""),
                state=data["state"],
                url=data["web_url"],
                created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00")),
                updated_at=datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00"))
            )
    
    async def get_pull_request_files(self, owner: str, repo: str, pr_number: int) -> List[str]:
        """Get list of files changed in merge request."""
        if not self.session:
            raise RuntimeError("Session not initialized")
        
        project_path = f"{owner}/{repo}"
        url = f"{self.api_base}/projects/{project_path.replace('/', '%2F')}/merge_requests/{pr_number}/changes"
        
        async with self.session.get(url, headers=self._get_headers()) as response:
            if response.status != 200:
                raise ValueError(f"GitLab API error: {response.status}")
            
            data = await response.json()
            return [change["new_path"] for change in data.get("changes", [])]
    
    async def create_pull_request_comment(self, owner: str, repo: str, pr_number: int, comment: PRComment) -> bool:
        """Create a note on a merge request."""
        if not self.session:
            raise RuntimeError("Session not initialized")
        
        project_path = f"{owner}/{repo}"
        url = f"{self.api_base}/projects/{project_path.replace('/', '%2F')}/merge_requests/{pr_number}/notes"
        
        payload = {"body": comment.body}
        
        async with self.session.post(url, headers=self._get_headers(), json=payload) as response:
            if response.status in [200, 201]:
                logger.info(f"Created MR note on {owner}/{repo}!{pr_number}")
                return True
            else:
                logger.error(f"Failed to create MR note: {response.status}")
                return False
    
    async def create_pull_request_review(self, owner: str, repo: str, pr_number: int, review: PRReview) -> bool:
        """Create a review on a merge request (GitLab doesn't have reviews, use notes)."""
        # GitLab doesn't have the same review concept, so we'll create a note
        comment = PRComment(body=review.body or "Code quality review completed")
        return await self.create_pull_request_comment(owner, repo, pr_number, comment)
    
    async def update_commit_status(self, owner: str, repo: str, sha: str, state: str, 
                                 description: str, context: str, target_url: Optional[str] = None) -> bool:
        """Update commit status on GitLab."""
        if not self.session:
            raise RuntimeError("Session not initialized")
        
        project_path = f"{owner}/{repo}"
        url = f"{self.api_base}/projects/{project_path.replace('/', '%2F')}/statuses/{sha}"
        
        # Map GitHub states to GitLab states
        state_mapping = {
            "pending": "running",
            "success": "success",
            "error": "failed",
            "failure": "failed"
        }
        
        payload = {
            "state": state_mapping.get(state, state),
            "description": description,
            "name": context
        }
        
        if target_url:
            payload["target_url"] = target_url
        
        async with self.session.post(url, headers=self._get_headers(), json=payload) as response:
            if response.status in [200, 201]:
                logger.info(f"Updated commit status for {owner}/{repo}@{sha}")
                return True
            else:
                logger.error(f"Failed to update commit status: {response.status}")
                return False
    
    def verify_webhook_signature(self, payload: bytes, signature: str, secret: str) -> bool:
        """Verify GitLab webhook signature."""
        # GitLab uses X-Gitlab-Token header for verification
        return signature == secret


class PullRequestAnalyzer:
    """Analyzer for pull request code quality."""
    
    def __init__(self, platform_integration: GitPlatformIntegration):
        """Initialize PR analyzer.
        
        Args:
            platform_integration: Git platform integration instance
        """
        self.platform = platform_integration
    
    async def analyze_pull_request(self, owner: str, repo: str, pr_number: int, 
                                 analysis_result: AnalysisResult) -> Dict[str, Any]:
        """Analyze pull request and generate review comments.
        
        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: Pull request number
            analysis_result: Code quality analysis result
            
        Returns:
            Dictionary with analysis summary and actions taken
        """
        try:
            # Get PR information
            pr_info = await self.platform.get_pull_request(owner, repo, pr_number)
            changed_files = await self.platform.get_pull_request_files(owner, repo, pr_number)
            
            # Filter issues to only those in changed files
            relevant_issues = [
                issue for issue in analysis_result.issues
                if issue.location.file_path in changed_files
            ]
            
            # Group issues by severity
            critical_issues = [i for i in relevant_issues if i.severity == SeverityLevel.CRITICAL]
            high_issues = [i for i in relevant_issues if i.severity == SeverityLevel.HIGH]
            medium_issues = [i for i in relevant_issues if i.severity == SeverityLevel.MEDIUM]
            low_issues = [i for i in relevant_issues if i.severity == SeverityLevel.LOW]
            
            # Create review summary
            summary = self._create_review_summary(
                pr_info, len(changed_files), critical_issues, high_issues, medium_issues, low_issues
            )
            
            # Create inline comments for critical and high severity issues
            inline_comments = []
            for issue in critical_issues + high_issues:
                comment = self._create_inline_comment(issue)
                if comment:
                    inline_comments.append(comment)
            
            # Determine review event
            if critical_issues:
                review_event = "REQUEST_CHANGES"
            elif high_issues:
                review_event = "COMMENT"
            else:
                review_event = "APPROVE"
            
            # Create review
            review = PRReview(
                event=review_event,
                body=summary,
                comments=inline_comments
            )
            
            # Submit review
            review_created = await self.platform.create_pull_request_review(
                owner, repo, pr_number, review
            )
            
            # Update commit status
            status_state = "failure" if critical_issues else "success" if not high_issues else "pending"
            status_description = f"Found {len(relevant_issues)} quality issues"
            
            status_updated = await self.platform.update_commit_status(
                owner, repo, pr_info.head_sha, status_state, 
                status_description, "code-quality/analysis"
            )
            
            return {
                "pr_number": pr_number,
                "pr_title": pr_info.title,
                "files_changed": len(changed_files),
                "issues_found": len(relevant_issues),
                "critical_issues": len(critical_issues),
                "high_issues": len(high_issues),
                "medium_issues": len(medium_issues),
                "low_issues": len(low_issues),
                "review_event": review_event,
                "review_created": review_created,
                "status_updated": status_updated,
                "analysis_job_id": analysis_result.job_id
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze PR {owner}/{repo}#{pr_number}: {e}")
            raise
    
    def _create_review_summary(self, pr_info: PullRequestInfo, files_changed: int,
                             critical: List[Issue], high: List[Issue], 
                             medium: List[Issue], low: List[Issue]) -> str:
        """Create review summary comment."""
        total_issues = len(critical) + len(high) + len(medium) + len(low)
        
        summary = f"## 🔍 Code Quality Analysis Results\n\n"
        summary += f"**Pull Request:** {pr_info.title}\n"
        summary += f"**Files Changed:** {files_changed}\n"
        summary += f"**Total Issues Found:** {total_issues}\n\n"
        
        if total_issues == 0:
            summary += "✅ **Great job!** No quality issues found in the changed files.\n"
            return summary
        
        summary += "### Issue Breakdown\n\n"
        
        if critical:
            summary += f"🚨 **Critical:** {len(critical)} issues - These should be fixed before merging\n"
        if high:
            summary += f"⚠️ **High:** {len(high)} issues - Recommended to fix\n"
        if medium:
            summary += f"🔶 **Medium:** {len(medium)} issues - Consider fixing\n"
        if low:
            summary += f"ℹ️ **Low:** {len(low)} issues - Optional improvements\n"
        
        summary += "\n### Recommendations\n\n"
        
        if critical:
            summary += "- **Action Required:** Please address the critical issues before merging\n"
        elif high:
            summary += "- **Recommended:** Consider fixing high-priority issues for better code quality\n"
        else:
            summary += "- **Optional:** Review medium and low priority suggestions when convenient\n"
        
        summary += "\n---\n*Generated by Code Quality Intelligence Agent*"
        
        return summary
    
    def _create_inline_comment(self, issue: Issue) -> Optional[PRComment]:
        """Create inline comment for an issue."""
        if not issue.location.line_number:
            return None
        
        # Create comment body with issue details
        body = f"**{issue.severity.upper()}:** {issue.title}\n\n"
        body += f"{issue.description}\n\n"
        
        if issue.explanation:
            body += f"**Explanation:** {issue.explanation}\n\n"
        
        if issue.suggestions:
            body += "**Suggestions:**\n"
            for suggestion in issue.suggestions:
                body += f"- {suggestion}\n"
            body += "\n"
        
        body += f"*Category: {issue.category} | Confidence: {issue.confidence:.1%}*"
        
        return PRComment(
            body=body,
            path=issue.location.file_path,
            line=issue.location.line_number,
            side="RIGHT"
        )


class WebhookHandler:
    """Handler for Git platform webhooks."""
    
    def __init__(self, github_secret: Optional[str] = None, gitlab_secret: Optional[str] = None):
        """Initialize webhook handler.
        
        Args:
            github_secret: GitHub webhook secret
            gitlab_secret: GitLab webhook secret
        """
        self.github_secret = github_secret or os.getenv('GITHUB_WEBHOOK_SECRET')
        self.gitlab_secret = gitlab_secret or os.getenv('GITLAB_WEBHOOK_SECRET')
        self.github_integration = GitHubPlatformIntegration()
        self.gitlab_integration = GitLabPlatformIntegration()
    
    def verify_github_webhook(self, payload: bytes, signature: str) -> bool:
        """Verify GitHub webhook signature."""
        if not self.github_secret:
            logger.warning("GitHub webhook secret not configured")
            return False
        return self.github_integration.verify_webhook_signature(payload, signature, self.github_secret)
    
    def verify_gitlab_webhook(self, token: str) -> bool:
        """Verify GitLab webhook token."""
        if not self.gitlab_secret:
            logger.warning("GitLab webhook secret not configured")
            return False
        return token == self.gitlab_secret
    
    def parse_github_webhook(self, payload: Dict[str, Any], event_type: str) -> Optional[WebhookEvent]:
        """Parse GitHub webhook payload."""
        try:
            return WebhookEvent(
                event_type=event_type,
                repository=payload.get("repository", {}),
                sender=payload.get("sender", {}),
                action=payload.get("action"),
                pull_request=payload.get("pull_request"),
                commits=payload.get("commits"),
                ref=payload.get("ref"),
                before=payload.get("before"),
                after=payload.get("after")
            )
        except Exception as e:
            logger.error(f"Failed to parse GitHub webhook: {e}")
            return None
    
    def parse_gitlab_webhook(self, payload: Dict[str, Any]) -> Optional[WebhookEvent]:
        """Parse GitLab webhook payload."""
        try:
            event_type = payload.get("object_kind", "unknown")
            
            return WebhookEvent(
                event_type=event_type,
                repository=payload.get("project", {}),
                sender=payload.get("user", {}),
                action=payload.get("action"),
                pull_request=payload.get("merge_request"),
                commits=payload.get("commits"),
                ref=payload.get("ref"),
                before=payload.get("before"),
                after=payload.get("after")
            )
        except Exception as e:
            logger.error(f"Failed to parse GitLab webhook: {e}")
            return None
    
    def should_trigger_analysis(self, event: WebhookEvent) -> bool:
        """Determine if webhook event should trigger analysis."""
        # Trigger on pull request events
        if event.event_type in ["pull_request", "merge_request"]:
            return event.action in ["opened", "synchronize", "reopened", "open", "update"]
        
        # Trigger on push to main branches
        if event.event_type == "push":
            if event.ref in ["refs/heads/main", "refs/heads/master", "refs/heads/develop"]:
                return True
        
        return False
    
    def extract_repository_info(self, event: WebhookEvent) -> Dict[str, str]:
        """Extract repository information from webhook event."""
        repo_info = event.repository
        
        # Handle different repository info formats
        if "full_name" in repo_info:
            # GitHub format
            owner, name = repo_info["full_name"].split("/", 1)
        elif "path_with_namespace" in repo_info:
            # GitLab format
            owner, name = repo_info["path_with_namespace"].split("/", 1)
        else:
            # Fallback
            owner = repo_info.get("owner", {}).get("login", "unknown")
            name = repo_info.get("name", "unknown")
        
        return {
            "owner": owner,
            "name": name,
            "url": repo_info.get("clone_url", repo_info.get("http_url_to_repo", "")),
            "default_branch": repo_info.get("default_branch", "main")
        }


def get_platform_integration(repository_url: str) -> GitPlatformIntegration:
    """Get appropriate platform integration based on repository URL.
    
    Args:
        repository_url: Repository URL
        
    Returns:
        Platform integration instance
        
    Raises:
        ValueError: If platform is not supported
    """
    parsed = urlparse(repository_url)
    
    if parsed.netloc in ["github.com", "www.github.com"]:
        return GitHubPlatformIntegration()
    elif parsed.netloc in ["gitlab.com", "www.gitlab.com"]:
        return GitLabPlatformIntegration()
    else:
        raise ValueError(f"Unsupported Git platform: {parsed.netloc}")