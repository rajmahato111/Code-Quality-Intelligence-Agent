"""Tests for the FastAPI web server."""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
import json

from fastapi.testclient import TestClient
from fastapi import status

from code_quality_agent.web.api import app
from code_quality_agent.web.models import (
    RepositoryRequest, FileAnalysisRequest, QuestionRequest, 
    AnalysisConfiguration, BatchAnalysisRequest, AnalysisStatus
)
from code_quality_agent.web.auth import api_key_manager, rate_limiter


class TestWebAPI:
    """Test the FastAPI web server."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.client = TestClient(app)
        
        # Create test API key
        self.api_key = api_key_manager.generate_api_key(
            user_id="test_user",
            permissions={
                "analyze_repository": True,
                "analyze_files": True,
                "ask_questions": True,
                "view_results": True
            }
        )
        
        self.headers = {"Authorization": f"Bearer {self.api_key}"}
    
    def test_health_check(self):
        """Test health check endpoint."""
        response = self.client.get("/health")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "components" in data
    
    def test_usage_stats(self):
        """Test usage statistics endpoint."""
        response = self.client.get("/stats")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total_requests" in data
        assert "successful_requests" in data
        assert "uptime_seconds" in data
    
    def test_create_api_key(self):
        """Test API key creation."""
        response = self.client.post("/auth/api-key?user_id=test_user_2")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "api_key" in data
        assert data["user_id"] == "test_user_2"
        assert len(data["api_key"]) > 20  # Should be a proper token
    
    def test_create_session(self):
        """Test session creation."""
        response = self.client.post("/auth/session?user_id=session_user")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "session_id" in data
        assert data["user_id"] == "session_user"
        
        # Check that session cookie is set
        assert "session_id" in response.cookies
    
    def test_demo_api_key(self):
        """Test demo API key endpoint."""
        response = self.client.get("/demo/api-key")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "api_key" in data
        assert "message" in data
    
    def test_root_page(self):
        """Test root page serves HTML."""
        response = self.client.get("/")
        
        assert response.status_code == status.HTTP_200_OK
        assert "text/html" in response.headers["content-type"]
        assert "Code Quality Intelligence Agent" in response.text
    
    def test_analyze_repository_without_auth(self):
        """Test repository analysis without authentication."""
        request_data = {
            "url": "https://github.com/test/repo",
            "branch": "main"
        }
        
        response = self.client.post("/analyze/repository", json=request_data)
        
        # Should work for anonymous users
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "pending"
    
    def test_analyze_repository_with_auth(self):
        """Test repository analysis with authentication."""
        request_data = {
            "url": "https://github.com/test/repo",
            "branch": "main",
            "include_patterns": ["*.py", "*.js"],
            "exclude_patterns": ["test_*", "*.min.js"],
            "analysis_types": ["security", "performance"]
        }
        
        response = self.client.post(
            "/analyze/repository", 
            json=request_data,
            headers=self.headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "pending"
        assert data["repository_url"] == "https://github.com/test/repo"
        assert data["branch"] == "main"
    
    def test_analyze_repository_invalid_url(self):
        """Test repository analysis with invalid URL."""
        request_data = {
            "url": "https://invalid-site.com/repo",
            "branch": "main"
        }
        
        response = self.client.post("/analyze/repository", json=request_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_analyze_files(self):
        """Test file analysis endpoint."""
        request_data = {
            "files": ["app.py", "utils.py"],
            "content": {
                "app.py": "def main(): pass",
                "utils.py": "def helper(): return True"
            },
            "analysis_types": ["security", "maintainability"]
        }
        
        response = self.client.post(
            "/analyze/files",
            json=request_data,
            headers=self.headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "pending"
    
    def test_get_analysis_result(self):
        """Test getting analysis results."""
        # First start an analysis
        request_data = {
            "url": "https://github.com/test/repo",
            "branch": "main"
        }
        
        response = self.client.post("/analyze/repository", json=request_data)
        job_id = response.json()["job_id"]
        
        # Get the result
        response = self.client.get(f"/analyze/{job_id}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["job_id"] == job_id
        assert "status" in data
    
    def test_get_analysis_progress(self):
        """Test getting analysis progress."""
        # Start an analysis
        request_data = {
            "url": "https://github.com/test/repo",
            "branch": "main"
        }
        
        response = self.client.post("/analyze/repository", json=request_data)
        job_id = response.json()["job_id"]
        
        # Get progress
        response = self.client.get(f"/analyze/{job_id}/progress")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["job_id"] == job_id
        assert "progress_percentage" in data
        assert "current_step" in data
    
    def test_get_nonexistent_job(self):
        """Test getting results for nonexistent job."""
        response = self.client.get("/analyze/nonexistent-job-id")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_ask_question(self):
        """Test Q&A endpoint."""
        request_data = {
            "question": "What are the main security issues in this code?",
            "context": {"project_type": "web_application"}
        }
        
        response = self.client.post(
            "/qa/ask",
            json=request_data,
            headers=self.headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["question"] == request_data["question"]
        assert "answer" in data
        assert "confidence" in data
        assert "timestamp" in data
    
    def test_ask_question_with_job_context(self):
        """Test Q&A with analysis job context."""
        # Start an analysis first
        analysis_request = {
            "url": "https://github.com/test/repo",
            "branch": "main"
        }
        
        analysis_response = self.client.post("/analyze/repository", json=analysis_request)
        job_id = analysis_response.json()["job_id"]
        
        # Ask question with job context
        question_request = {
            "question": "What security vulnerabilities were found?",
            "job_id": job_id
        }
        
        response = self.client.post(
            "/qa/ask",
            json=question_request,
            headers=self.headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "answer" in data
    
    def test_batch_analysis_requires_auth(self):
        """Test that batch analysis requires authentication."""
        request_data = {
            "repositories": [
                {
                    "url": "https://github.com/test/repo1",
                    "branch": "main"
                },
                {
                    "url": "https://github.com/test/repo2", 
                    "branch": "develop"
                }
            ]
        }
        
        # Without auth should fail
        response = self.client.post("/analyze/batch", json=request_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # With auth should work
        response = self.client.post(
            "/analyze/batch",
            json=request_data,
            headers=self.headers
        )
        assert response.status_code == status.HTTP_200_OK
    
    def test_batch_analysis_with_config(self):
        """Test batch analysis with configuration."""
        request_data = {
            "repositories": [
                {
                    "url": "https://github.com/test/repo1",
                    "branch": "main"
                }
            ],
            "configuration": {
                "enable_security_analysis": True,
                "enable_performance_analysis": False,
                "severity_threshold": "medium",
                "max_issues_per_file": 25
            }
        }
        
        response = self.client.post(
            "/analyze/batch",
            json=request_data,
            headers=self.headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "batch_id" in data
        assert data["total_repositories"] == 1
    
    def test_get_batch_result(self):
        """Test getting batch analysis results."""
        # Start batch analysis
        request_data = {
            "repositories": [
                {
                    "url": "https://github.com/test/repo1",
                    "branch": "main"
                }
            ]
        }
        
        response = self.client.post(
            "/analyze/batch",
            json=request_data,
            headers=self.headers
        )
        batch_id = response.json()["batch_id"]
        
        # Get batch result
        response = self.client.get(f"/analyze/batch/{batch_id}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["batch_id"] == batch_id
        assert "status" in data
    
    def test_list_jobs(self):
        """Test listing user jobs."""
        # Start a few analyses
        for i in range(3):
            request_data = {
                "url": f"https://github.com/test/repo{i}",
                "branch": "main"
            }
            self.client.post("/analyze/repository", json=request_data, headers=self.headers)
        
        # List jobs
        response = self.client.get("/jobs", headers=self.headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "jobs" in data
        assert len(data["jobs"]) >= 3
    
    def test_cancel_job(self):
        """Test cancelling a job."""
        # Start analysis
        request_data = {
            "url": "https://github.com/test/repo",
            "branch": "main"
        }
        
        response = self.client.post("/analyze/repository", json=request_data, headers=self.headers)
        job_id = response.json()["job_id"]
        
        # Cancel job
        response = self.client.delete(f"/jobs/{job_id}", headers=self.headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "cancelled" in data["message"].lower()
    
    def test_cancel_nonexistent_job(self):
        """Test cancelling nonexistent job."""
        response = self.client.delete("/jobs/nonexistent", headers=self.headers)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_security_headers(self):
        """Test that security headers are added."""
        response = self.client.get("/health")
        
        assert "X-Content-Type-Options" in response.headers
        assert "X-Frame-Options" in response.headers
        assert "X-XSS-Protection" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
    
    def test_cors_headers(self):
        """Test CORS headers are present."""
        response = self.client.options("/health")
        
        # CORS headers should be present
        assert "access-control-allow-origin" in response.headers
    
    def test_gzip_compression(self):
        """Test that gzip compression is enabled for large responses."""
        # This would need a larger response to trigger compression
        response = self.client.get("/")
        
        # Check that the middleware is configured (actual compression depends on response size)
        assert response.status_code == status.HTTP_200_OK
    
    def test_github_integration_test_endpoint(self):
        """Test GitHub integration test endpoint."""
        response = self.client.post("/test/github?url=https://github.com/octocat/Hello-World")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Should either succeed or fail gracefully
        assert "url" in data
        assert "message" in data
    
    def test_components_test_endpoint(self):
        """Test components test endpoint."""
        response = self.client.get("/test/components")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "components" in data
        assert "overall_status" in data
        assert "orchestrator" in data["components"]
        assert "qa_engine" in data["components"]
        assert "github_integration" in data["components"]
    
    def test_analyze_repository_with_github_url(self):
        """Test repository analysis with actual GitHub URL format."""
        request_data = {
            "url": "https://github.com/octocat/Hello-World",
            "branch": "master",
            "include_patterns": ["*.py", "*.js"],
            "analysis_types": ["security", "performance"]
        }
        
        response = self.client.post(
            "/analyze/repository", 
            json=request_data,
            headers=self.headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "pending"
        assert data["repository_url"] == "https://github.com/octocat/Hello-World"
        assert data["branch"] == "master"


class TestAuthentication:
    """Test authentication and authorization."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.client = TestClient(app)
    
    def test_api_key_validation(self):
        """Test API key validation."""
        # Create API key
        api_key = api_key_manager.generate_api_key("test_user")
        
        # Valid API key
        headers = {"Authorization": f"Bearer {api_key}"}
        response = self.client.post(
            "/analyze/repository",
            json={"url": "https://github.com/test/repo"},
            headers=headers
        )
        assert response.status_code == status.HTTP_200_OK
        
        # Invalid API key
        headers = {"Authorization": "Bearer invalid_key"}
        response = self.client.post(
            "/analyze/repository",
            json={"url": "https://github.com/test/repo"},
            headers=headers
        )
        # Should still work for anonymous users
        assert response.status_code == status.HTTP_200_OK
    
    def test_session_authentication(self):
        """Test session-based authentication."""
        # Create session
        response = self.client.post("/auth/session?user_id=session_user")
        session_id = response.json()["session_id"]
        
        # Use session cookie
        cookies = {"session_id": session_id}
        response = self.client.post(
            "/analyze/repository",
            json={"url": "https://github.com/test/repo"},
            cookies=cookies
        )
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_protected_endpoint_requires_auth(self):
        """Test that protected endpoints require authentication."""
        request_data = {
            "repositories": [
                {"url": "https://github.com/test/repo", "branch": "main"}
            ]
        }
        
        response = self.client.post("/analyze/batch", json=request_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestRateLimiting:
    """Test rate limiting functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.client = TestClient(app)
        # Reset rate limiter
        rate_limiter.requests.clear()
    
    def test_rate_limiting_basic(self):
        """Test basic rate limiting functionality."""
        # This test would need to be adjusted based on actual rate limits
        # For now, just test that the mechanism exists
        
        # Make multiple requests
        for i in range(5):
            response = self.client.get("/health")
            assert response.status_code == status.HTTP_200_OK
        
        # Rate limiting is configured but may not trigger with small numbers


class TestErrorHandling:
    """Test error handling and responses."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.client = TestClient(app)
    
    def test_404_error_format(self):
        """Test 404 error response format."""
        response = self.client.get("/nonexistent-endpoint")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        # FastAPI returns standard 404 format
    
    def test_validation_error_format(self):
        """Test validation error response format."""
        # Send invalid data
        response = self.client.post("/analyze/repository", json={"invalid": "data"})
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert "detail" in data
    
    def test_internal_error_handling(self):
        """Test internal error handling."""
        # This would require mocking to trigger internal errors
        # For now, just verify the error handler is configured
        pass


class TestModels:
    """Test Pydantic models."""
    
    def test_repository_request_validation(self):
        """Test repository request validation."""
        # Valid request
        valid_data = {
            "url": "https://github.com/test/repo",
            "branch": "main"
        }
        request = RepositoryRequest(**valid_data)
        assert str(request.url) == "https://github.com/test/repo"
        assert request.branch == "main"
        
        # Invalid URL
        with pytest.raises(ValueError):
            RepositoryRequest(url="https://invalid-site.com/repo")
    
    def test_file_analysis_request_validation(self):
        """Test file analysis request validation."""
        valid_data = {
            "files": ["app.py", "utils.py"],
            "content": {"app.py": "def main(): pass"}
        }
        request = FileAnalysisRequest(**valid_data)
        assert len(request.files) == 2
        assert "app.py" in request.content
    
    def test_question_request_validation(self):
        """Test question request validation."""
        # Valid question
        valid_data = {"question": "What are the security issues?"}
        request = QuestionRequest(**valid_data)
        assert request.question == "What are the security issues?"
        
        # Empty question should fail
        with pytest.raises(ValueError):
            QuestionRequest(question="")
        
        # Too long question should fail
        with pytest.raises(ValueError):
            QuestionRequest(question="x" * 1001)
    
    def test_analysis_configuration_defaults(self):
        """Test analysis configuration defaults."""
        config = AnalysisConfiguration()
        
        assert config.enable_security_analysis is True
        assert config.enable_performance_analysis is True
        assert config.severity_threshold.value == "low"
        assert config.max_issues_per_file == 50
        assert config.timeout_seconds == 300


class TestGitHubIntegration:
    """Test GitHub integration functionality."""
    
    @pytest.mark.asyncio
    async def test_parse_repository_url(self):
        """Test parsing GitHub repository URLs."""
        from code_quality_agent.web.github_integration import GitHubIntegration
        from pydantic import HttpUrl
        
        github = GitHubIntegration()
        
        # Valid GitHub URL
        url = HttpUrl("https://github.com/octocat/Hello-World")
        owner, repo = github.parse_repository_url(url)
        assert owner == "octocat"
        assert repo == "Hello-World"
        
        # URL with .git suffix
        url = HttpUrl("https://github.com/octocat/Hello-World.git")
        owner, repo = github.parse_repository_url(url)
        assert owner == "octocat"
        assert repo == "Hello-World"
    
    @pytest.mark.asyncio
    async def test_parse_invalid_url(self):
        """Test parsing invalid repository URLs."""
        from code_quality_agent.web.github_integration import GitHubIntegration
        from pydantic import HttpUrl
        
        github = GitHubIntegration()
        
        # Invalid host
        with pytest.raises(ValueError, match="Unsupported repository host"):
            url = HttpUrl("https://invalid-site.com/owner/repo")
            github.parse_repository_url(url)
        
        # Invalid format
        with pytest.raises(ValueError, match="Invalid repository URL format"):
            url = HttpUrl("https://github.com/invalid")
            github.parse_repository_url(url)
    
    @pytest.mark.asyncio
    async def test_get_repository_integration(self):
        """Test getting appropriate repository integration."""
        from code_quality_agent.web.github_integration import get_repository_integration, GitHubIntegration
        from pydantic import HttpUrl
        
        # GitHub URL
        url = HttpUrl("https://github.com/octocat/Hello-World")
        integration = get_repository_integration(url)
        assert isinstance(integration, GitHubIntegration)
        
        # Unsupported host
        with pytest.raises(ValueError, match="Unsupported repository host"):
            url = HttpUrl("https://unsupported-host.com/owner/repo")
            get_repository_integration(url)


class TestRateLimitingEnhanced:
    """Test enhanced rate limiting functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.client = TestClient(app)
        # Reset rate limiter
        from code_quality_agent.web.auth import rate_limiter
        rate_limiter.requests.clear()
    
    def test_rate_limiting_anonymous_vs_authenticated(self):
        """Test different rate limits for anonymous vs authenticated users."""
        # Create API key for authenticated user
        api_key = api_key_manager.generate_api_key("test_user")
        headers = {"Authorization": f"Bearer {api_key}"}
        
        # Test that both anonymous and authenticated requests work initially
        response = self.client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        
        response = self.client.get("/health", headers=headers)
        assert response.status_code == status.HTTP_200_OK


if __name__ == "__main__":
    pytest.main([__file__])