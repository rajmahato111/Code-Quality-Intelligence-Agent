"""Tests for LLM integration functionality."""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from code_quality_agent.llm import (
    LLMProvider, LLMConfig, LLMResponse, LLMManager, MockLLMProvider,
    PromptTemplate, PromptType, PromptTemplateManager,
    LLMService, create_llm_service
)
from code_quality_agent.core.models import (
    Issue, IssueCategory, Severity, CodeLocation, ParsedFile, AnalysisResult, QualityMetrics
)


class TestLLMProvider:
    """Test cases for LLM provider functionality."""
    
    def test_llm_config_creation(self):
        """Test LLM configuration creation."""
        config = LLMConfig(
            provider=LLMProvider.MOCK,
            model_name="test-model",
            temperature=0.5,
            max_tokens=500
        )
        
        assert config.provider == LLMProvider.MOCK
        assert config.model_name == "test-model"
        assert config.temperature == 0.5
        assert config.max_tokens == 500
        assert config.max_retries == 3  # Default value
    
    def test_mock_llm_provider(self):
        """Test mock LLM provider functionality."""
        config = LLMConfig(
            provider=LLMProvider.MOCK,
            model_name="mock-model"
        )
        
        mock_responses = ["Response 1", "Response 2", "Response 3"]
        provider = MockLLMProvider(config, mock_responses)
        
        # Test first response
        messages = [{"role": "user", "content": "Test message"}]
        response = provider.generate_response(messages)
        
        assert response.success is True
        assert response.content == "Response 1"
        assert response.provider == LLMProvider.MOCK
        assert response.model == "mock-model"
        assert response.response_time is not None
        
        # Test second response (cycling through responses)
        response2 = provider.generate_response(messages)
        assert response2.content == "Response 2"
        
        # Test third response
        response3 = provider.generate_response(messages)
        assert response3.content == "Response 3"
        
        # Test cycling back to first response
        response4 = provider.generate_response(messages)
        assert response4.content == "Response 1"
    
    def test_llm_manager_with_mock_provider(self):
        """Test LLM manager with mock provider."""
        config = LLMConfig(
            provider=LLMProvider.MOCK,
            model_name="mock-model"
        )
        
        manager = LLMManager(config)
        
        messages = [{"role": "user", "content": "Test message"}]
        response = manager.generate_response(messages)
        
        assert response.success is True
        assert response.content != ""
        assert response.provider == LLMProvider.MOCK
        
        # Test statistics
        stats = manager.get_statistics()
        assert stats["total_requests"] == 1
        assert stats["successful_requests"] == 1
        assert stats["failed_requests"] == 0
        assert stats["success_rate_percent"] == 100.0
    
    def test_llm_manager_with_fallback(self):
        """Test LLM manager with fallback provider."""
        # Create a failing primary provider
        primary_config = LLMConfig(
            provider=LLMProvider.MOCK,
            model_name="failing-model",
            max_retries=1
        )
        
        # Create fallback provider
        fallback_config = LLMConfig(
            provider=LLMProvider.MOCK,
            model_name="fallback-model"
        )
        
        # Mock the primary provider to fail
        with patch.object(MockLLMProvider, '_make_request', side_effect=Exception("Primary failed")):
            manager = LLMManager(primary_config, fallback_config)
            
            messages = [{"role": "user", "content": "Test message"}]
            response = manager.generate_response(messages)
            
            # Should succeed with fallback
            assert response.success is True
            assert response.provider == LLMProvider.MOCK
    
    def test_retry_logic(self):
        """Test retry logic for failed requests."""
        config = LLMConfig(
            provider=LLMProvider.MOCK,
            model_name="test-model",
            max_retries=2,
            retry_delay=0.1
        )
        
        # Mock provider to fail twice then succeed
        call_count = 0
        def mock_request(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise Exception(f"Attempt {call_count} failed")
            return "Success on attempt 3"
        
        with patch.object(MockLLMProvider, '_make_request', side_effect=mock_request):
            provider = MockLLMProvider(config)
            
            messages = [{"role": "user", "content": "Test message"}]
            response = provider.generate_response(messages)
            
            assert response.success is True
            assert response.content == "Success on attempt 3"
            assert call_count == 3


class TestPromptTemplates:
    """Test cases for prompt template functionality."""
    
    def test_prompt_template_creation(self):
        """Test prompt template creation."""
        template = PromptTemplate(
            name="test_template",
            prompt_type=PromptType.ISSUE_EXPLANATION,
            system_message="You are a test assistant.",
            user_template="Explain this: {issue}",
            variables=["issue"]
        )
        
        assert template.name == "test_template"
        assert template.prompt_type == PromptType.ISSUE_EXPLANATION
        assert "issue" in template.variables
    
    def test_prompt_template_formatting(self):
        """Test prompt template formatting."""
        template = PromptTemplate(
            name="test_template",
            prompt_type=PromptType.ISSUE_EXPLANATION,
            system_message="You are a test assistant.",
            user_template="Explain this {issue} with severity {severity}",
            variables=["issue", "severity"]
        )
        
        messages = template.format(issue="security vulnerability", severity="high")
        
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "You are a test assistant."
        assert messages[1]["role"] == "user"
        assert "security vulnerability" in messages[1]["content"]
        assert "high" in messages[1]["content"]
    
    def test_prompt_template_missing_variables(self):
        """Test prompt template with missing variables."""
        template = PromptTemplate(
            name="test_template",
            prompt_type=PromptType.ISSUE_EXPLANATION,
            system_message="You are a test assistant.",
            user_template="Explain this {issue} with severity {severity}",
            variables=["issue", "severity"]
        )
        
        with pytest.raises(ValueError, match="Missing required variables"):
            template.format(issue="security vulnerability")  # Missing severity
    
    def test_prompt_template_manager(self):
        """Test prompt template manager."""
        manager = PromptTemplateManager()
        
        # Test default templates are loaded
        templates = manager.list_templates()
        assert "issue_explanation" in templates
        assert "issue_suggestion" in templates
        assert "code_review" in templates
        
        # Test getting template
        explanation_template = manager.get_template("issue_explanation")
        assert explanation_template is not None
        assert explanation_template.prompt_type == PromptType.ISSUE_EXPLANATION
    
    def test_issue_explanation_formatting(self):
        """Test issue explanation prompt formatting."""
        manager = PromptTemplateManager()
        
        issue = Issue(
            id="test-issue",
            category=IssueCategory.SECURITY,
            severity=Severity.HIGH,
            title="SQL Injection Vulnerability",
            description="Potential SQL injection in query",
            location=CodeLocation("test.py", 10, 12),
            affected_files=["test.py"],
            suggestion="Use parameterized queries",
            confidence=0.9
        )
        
        code_snippet = "query = f'SELECT * FROM users WHERE id = {user_id}'"
        
        messages = manager.format_issue_explanation(issue, code_snippet, "python")
        
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert "SQL Injection Vulnerability" in messages[1]["content"]
        assert "security" in messages[1]["content"]
        assert "high" in messages[1]["content"]
        assert code_snippet in messages[1]["content"]


class TestLLMService:
    """Test cases for LLM service functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.llm_service = create_llm_service(provider="mock")
        
        self.test_issue = Issue(
            id="test-issue",
            category=IssueCategory.SECURITY,
            severity=Severity.HIGH,
            title="Test Security Issue",
            description="Test description",
            location=CodeLocation("test.py", 5, 7),
            affected_files=["test.py"],
            suggestion="Fix this issue",
            confidence=0.8
        )
        
        self.test_parsed_file = ParsedFile(
            path="test.py",
            language="python",
            content="""def vulnerable_function(user_id):
    # This is a security vulnerability
    query = f'SELECT * FROM users WHERE id = {user_id}'
    return execute_query(query)

def safe_function(user_id):
    query = 'SELECT * FROM users WHERE id = ?'
    return execute_query(query, [user_id])"""
        )
    
    def test_llm_service_initialization(self):
        """Test LLM service initialization."""
        assert self.llm_service.llm_manager is not None
        assert self.llm_service.prompt_manager is not None
        assert self.llm_service.enable_caching is True
    
    def test_code_snippet_extraction(self):
        """Test code snippet extraction around issue location."""
        code_snippet, language = self.llm_service._get_code_snippet(
            self.test_issue, 
            [self.test_parsed_file],
            context_lines=2
        )
        
        assert language == "python"
        assert "vulnerable_function" in code_snippet
        assert ">>>" in code_snippet  # Issue marker
        assert "query = f'SELECT" in code_snippet
    
    def test_generate_issue_explanation(self):
        """Test issue explanation generation."""
        explanation = self.llm_service.generate_issue_explanation(
            self.test_issue,
            [self.test_parsed_file]
        )
        
        assert explanation is not None
        assert isinstance(explanation, str)
        assert len(explanation) > 0
    
    def test_generate_issue_suggestion(self):
        """Test issue suggestion generation."""
        suggestion = self.llm_service.generate_issue_suggestion(
            self.test_issue,
            [self.test_parsed_file]
        )
        
        assert suggestion is not None
        assert isinstance(suggestion, str)
        assert len(suggestion) > 0
    
    def test_generate_code_review(self):
        """Test code review generation."""
        review = self.llm_service.generate_code_review(
            self.test_parsed_file,
            context="This is a test file with security issues"
        )
        
        assert review is not None
        assert isinstance(review, str)
        assert len(review) > 0
    
    def test_generate_analysis_summary(self):
        """Test analysis summary generation."""
        analysis_result = AnalysisResult(
            analysis_id="test-analysis",
            codebase_path="/test/path",
            parsed_files=[self.test_parsed_file],
            issues=[self.test_issue],
            metrics=QualityMetrics(
                overall_score=75.0,
                maintainability_index=80.0,
                technical_debt_ratio=0.15
            )
        )
        
        summary = self.llm_service.generate_analysis_summary(analysis_result)
        
        assert summary is not None
        assert isinstance(summary, str)
        assert len(summary) > 0
    
    def test_answer_question(self):
        """Test question answering functionality."""
        analysis_result = AnalysisResult(
            analysis_id="test-analysis",
            codebase_path="/test/path",
            parsed_files=[self.test_parsed_file],
            issues=[self.test_issue],
            metrics=QualityMetrics(overall_score=75.0)
        )
        
        answer = self.llm_service.answer_question(
            "What security issues were found?",
            analysis_result,
            additional_context="Focus on SQL injection vulnerabilities"
        )
        
        assert answer is not None
        assert isinstance(answer, str)
        assert len(answer) > 0
    
    def test_enhance_issues_with_llm(self):
        """Test enhancing issues with LLM-generated content."""
        issues = [self.test_issue]
        parsed_files = [self.test_parsed_file]
        
        enhanced_issues = self.llm_service.enhance_issues_with_llm(
            issues,
            parsed_files,
            include_explanations=True,
            include_suggestions=True
        )
        
        assert len(enhanced_issues) == 1
        enhanced_issue = enhanced_issues[0]
        
        # Check if LLM explanation was added
        assert "llm_explanation" in enhanced_issue.metadata
        assert enhanced_issue.metadata["llm_explanation"] != ""
        
        # Check if suggestion was enhanced
        assert enhanced_issue.suggestion != self.test_issue.suggestion
        assert "llm_enhanced" in enhanced_issue.metadata
    
    def test_caching_functionality(self):
        """Test LLM response caching."""
        # First request should generate new response
        explanation1 = self.llm_service.generate_issue_explanation(
            self.test_issue,
            [self.test_parsed_file]
        )
        
        # Second identical request should use cache
        explanation2 = self.llm_service.generate_issue_explanation(
            self.test_issue,
            [self.test_parsed_file]
        )
        
        assert explanation1 == explanation2
        
        # Check cache statistics
        stats = self.llm_service.get_statistics()
        assert stats["cached_responses"] > 0
    
    def test_cache_clearing(self):
        """Test cache clearing functionality."""
        # Generate some cached responses
        self.llm_service.generate_issue_explanation(
            self.test_issue,
            [self.test_parsed_file]
        )
        
        # Verify cache has entries
        assert len(self.llm_service._response_cache) > 0
        
        # Clear cache
        self.llm_service.clear_cache()
        
        # Verify cache is empty
        assert len(self.llm_service._response_cache) == 0
    
    def test_statistics_generation(self):
        """Test statistics generation."""
        # Generate some requests
        self.llm_service.generate_issue_explanation(
            self.test_issue,
            [self.test_parsed_file]
        )
        
        stats = self.llm_service.get_statistics()
        
        assert "total_requests" in stats
        assert "successful_requests" in stats
        assert "cached_responses" in stats
        assert "caching_enabled" in stats
        assert "available_templates" in stats
        assert stats["caching_enabled"] is True
    
    def test_error_handling(self):
        """Test error handling in LLM service."""
        # Test with invalid issue (missing file)
        invalid_issue = Issue(
            id="invalid-issue",
            category=IssueCategory.SECURITY,
            severity=Severity.HIGH,
            title="Invalid Issue",
            description="Test description",
            location=CodeLocation("nonexistent.py", 1, 1),
            affected_files=["nonexistent.py"],
            suggestion="Fix this",
            confidence=0.8
        )
        
        # Should handle gracefully and return None or fallback
        explanation = self.llm_service.generate_issue_explanation(
            invalid_issue,
            [self.test_parsed_file]
        )
        
        # Should either return None or a valid explanation with fallback content
        assert explanation is None or isinstance(explanation, str)


class TestLLMIntegration:
    """Integration tests for LLM functionality."""
    
    def test_create_llm_service_with_different_providers(self):
        """Test creating LLM service with different providers."""
        # Test mock provider
        mock_service = create_llm_service(provider="mock")
        assert mock_service.llm_manager.primary_provider.config.provider == LLMProvider.MOCK
        
        # Test OpenAI provider (should work even without API key due to fallback)
        openai_service = create_llm_service(provider="openai", enable_fallback=True)
        assert openai_service.llm_manager.primary_provider.config.provider == LLMProvider.OPENAI
        
        # Test Anthropic provider (should work even without API key due to fallback)
        anthropic_service = create_llm_service(provider="anthropic", enable_fallback=True)
        assert anthropic_service.llm_manager.primary_provider.config.provider == LLMProvider.ANTHROPIC
    
    def test_end_to_end_issue_enhancement(self):
        """Test end-to-end issue enhancement workflow."""
        llm_service = create_llm_service(provider="mock")
        
        # Create test data
        issue = Issue(
            id="e2e-test",
            category=IssueCategory.PERFORMANCE,
            severity=Severity.MEDIUM,
            title="Inefficient Loop",
            description="Nested loop with O(n²) complexity",
            location=CodeLocation("performance.py", 10, 15),
            affected_files=["performance.py"],
            suggestion="Consider using a more efficient algorithm",
            confidence=0.85
        )
        
        parsed_file = ParsedFile(
            path="performance.py",
            language="python",
            content="""def inefficient_search(items, targets):
    results = []
    for target in targets:
        for item in items:
            if item == target:
                results.append(item)
                break
    return results"""
        )
        
        # Enhance the issue
        enhanced_issues = llm_service.enhance_issues_with_llm(
            [issue],
            [parsed_file],
            include_explanations=True,
            include_suggestions=True
        )
        
        assert len(enhanced_issues) == 1
        enhanced_issue = enhanced_issues[0]
        
        # Verify enhancement
        assert "llm_explanation" in enhanced_issue.metadata
        assert enhanced_issue.metadata["llm_enhanced"] is True
        assert enhanced_issue.suggestion != issue.suggestion


if __name__ == "__main__":
    pytest.main([__file__])