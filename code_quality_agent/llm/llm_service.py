"""LLM service for generating explanations and suggestions."""

import logging
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

from .llm_provider import LLMManager, LLMConfig, LLMProvider, create_default_llm_manager
from .prompt_templates import PromptTemplateManager
from .prompt_templates import prompt_manager as global_prompt_manager
from ..core.models import Issue, ParsedFile, AnalysisResult


logger = logging.getLogger(__name__)


class LLMService:
    """Service for LLM-powered code quality explanations and suggestions."""
    
    def __init__(
        self, 
        llm_manager: Optional[LLMManager] = None,
        prompt_manager: Optional[PromptTemplateManager] = None,
        enable_caching: bool = True
    ):
        """
        Initialize LLM service.
        
        Args:
            llm_manager: LLM manager instance (creates default if None)
            prompt_manager: Prompt template manager (uses global if None)
            enable_caching: Whether to cache LLM responses
        """
        self.llm_manager = llm_manager or create_default_llm_manager()
        self.prompt_manager = prompt_manager or global_prompt_manager
        self.enable_caching = enable_caching
        self._response_cache: Dict[str, str] = {}
        
        logger.info("LLM service initialized")
    
    def _get_cache_key(self, messages: List[Dict[str, str]]) -> str:
        """Generate cache key for LLM request."""
        import hashlib
        content = str(messages)
        return hashlib.md5(content.encode()).hexdigest()
    
    def _get_code_snippet(self, issue: Issue, parsed_files: List[ParsedFile], context_lines: int = 3) -> Tuple[str, str]:
        """
        Extract code snippet around an issue location.
        
        Args:
            issue: Issue object
            parsed_files: List of parsed files
            context_lines: Number of context lines to include
            
        Returns:
            Tuple of (code_snippet, language)
        """
        # Find the relevant parsed file
        target_file = None
        for parsed_file in parsed_files:
            if parsed_file.path == issue.location.file_path:
                target_file = parsed_file
                break
        
        if not target_file:
            return "Code snippet not available", "text"
        
        lines = target_file.content.splitlines()
        start_line = max(0, issue.location.line_start - context_lines - 1)
        end_line = min(len(lines), issue.location.line_end + context_lines)
        
        snippet_lines = lines[start_line:end_line]
        
        # Add line numbers
        numbered_lines = []
        for i, line in enumerate(snippet_lines, start=start_line + 1):
            marker = ">>> " if issue.location.line_start <= i <= issue.location.line_end else "    "
            numbered_lines.append(f"{marker}{i:4d}: {line}")
        
        return "\n".join(numbered_lines), target_file.language
    
    def generate_issue_explanation(
        self, 
        issue: Issue, 
        parsed_files: List[ParsedFile],
        use_cache: bool = True
    ) -> Optional[str]:
        """
        Generate an explanation for a code quality issue.
        
        Args:
            issue: Issue to explain
            parsed_files: List of parsed files for context
            use_cache: Whether to use cached responses
            
        Returns:
            Generated explanation or None if failed
        """
        try:
            # Get code snippet
            code_snippet, language = self._get_code_snippet(issue, parsed_files)
            
            # Format prompt
            messages = self.prompt_manager.format_issue_explanation(
                issue, code_snippet, language
            )
            
            # Check cache
            cache_key = self._get_cache_key(messages)
            if use_cache and self.enable_caching and cache_key in self._response_cache:
                logger.debug(f"Using cached explanation for issue {issue.id}")
                return self._response_cache[cache_key]
            
            # Generate response
            response = self.llm_manager.generate_response(messages)
            
            if response.success:
                explanation = response.content.strip()
                
                # Cache the response
                if self.enable_caching:
                    self._response_cache[cache_key] = explanation
                
                logger.debug(f"Generated explanation for issue {issue.id}")
                return explanation
            else:
                logger.error(f"Failed to generate explanation for issue {issue.id}: {response.error_message}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating explanation for issue {issue.id}: {e}")
            return None
    
    def generate_issue_suggestion(
        self, 
        issue: Issue, 
        parsed_files: List[ParsedFile],
        use_cache: bool = True
    ) -> Optional[str]:
        """
        Generate actionable suggestions for fixing a code quality issue.
        
        Args:
            issue: Issue to provide suggestions for
            parsed_files: List of parsed files for context
            use_cache: Whether to use cached responses
            
        Returns:
            Generated suggestions or None if failed
        """
        try:
            # Get code snippet
            code_snippet, language = self._get_code_snippet(issue, parsed_files)
            
            # Format prompt
            messages = self.prompt_manager.format_issue_suggestion(
                issue, code_snippet, language
            )
            
            # Check cache
            cache_key = self._get_cache_key(messages)
            if use_cache and self.enable_caching and cache_key in self._response_cache:
                logger.debug(f"Using cached suggestion for issue {issue.id}")
                return self._response_cache[cache_key]
            
            # Generate response
            response = self.llm_manager.generate_response(messages)
            
            if response.success:
                suggestion = response.content.strip()
                
                # Cache the response
                if self.enable_caching:
                    self._response_cache[cache_key] = suggestion
                
                logger.debug(f"Generated suggestion for issue {issue.id}")
                return suggestion
            else:
                logger.error(f"Failed to generate suggestion for issue {issue.id}: {response.error_message}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating suggestion for issue {issue.id}: {e}")
            return None
    
    def generate_code_review(
        self, 
        parsed_file: ParsedFile, 
        context: str = "",
        use_cache: bool = True
    ) -> Optional[str]:
        """
        Generate a comprehensive code review for a file.
        
        Args:
            parsed_file: File to review
            context: Additional context about the code
            use_cache: Whether to use cached responses
            
        Returns:
            Generated code review or None if failed
        """
        try:
            # Format prompt
            messages = self.prompt_manager.format_code_review(parsed_file, context)
            
            # Check cache
            cache_key = self._get_cache_key(messages)
            if use_cache and self.enable_caching and cache_key in self._response_cache:
                logger.debug(f"Using cached review for file {parsed_file.path}")
                return self._response_cache[cache_key]
            
            # Generate response
            response = self.llm_manager.generate_response(messages)
            
            if response.success:
                review = response.content.strip()
                
                # Cache the response
                if self.enable_caching:
                    self._response_cache[cache_key] = review
                
                logger.debug(f"Generated review for file {parsed_file.path}")
                return review
            else:
                logger.error(f"Failed to generate review for file {parsed_file.path}: {response.error_message}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating review for file {parsed_file.path}: {e}")
            return None
    
    def generate_analysis_summary(
        self, 
        analysis_result: AnalysisResult,
        use_cache: bool = True
    ) -> Optional[str]:
        """
        Generate a comprehensive summary of analysis results.
        
        Args:
            analysis_result: Analysis results to summarize
            use_cache: Whether to use cached responses
            
        Returns:
            Generated summary or None if failed
        """
        try:
            # Prepare quality metrics
            quality_metrics = {
                "overall_score": analysis_result.metrics.overall_score,
                "maintainability_index": analysis_result.metrics.maintainability_index,
                "technical_debt_ratio": analysis_result.metrics.technical_debt_ratio
            }
            
            # Format prompt
            messages = self.prompt_manager.format_summary_generation(
                analysis_result.codebase_path,
                len(analysis_result.parsed_files),
                analysis_result.issues,
                quality_metrics
            )
            
            # Check cache
            cache_key = self._get_cache_key(messages)
            if use_cache and self.enable_caching and cache_key in self._response_cache:
                logger.debug(f"Using cached summary for analysis {analysis_result.analysis_id}")
                return self._response_cache[cache_key]
            
            # Generate response
            response = self.llm_manager.generate_response(messages)
            
            if response.success:
                summary = response.content.strip()
                
                # Cache the response
                if self.enable_caching:
                    self._response_cache[cache_key] = summary
                
                logger.debug(f"Generated summary for analysis {analysis_result.analysis_id}")
                return summary
            else:
                logger.error(f"Failed to generate summary for analysis {analysis_result.analysis_id}: {response.error_message}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating summary for analysis {analysis_result.analysis_id}: {e}")
            return None
    
    def answer_question(
        self,
        question: str,
        analysis_result: AnalysisResult,
        additional_context: str = "",
        use_cache: bool = True
    ) -> Optional[str]:
        """
        Answer a question about the analysis results.
        
        Args:
            question: User's question
            analysis_result: Analysis results for context
            additional_context: Additional context information
            use_cache: Whether to use cached responses
            
        Returns:
            Generated answer or None if failed
        """
        try:
            # Format prompt
            messages = self.prompt_manager.format_question_answering(
                question,
                analysis_result.codebase_path,
                len(analysis_result.parsed_files),
                analysis_result.issues,
                analysis_result.metrics.overall_score,
                additional_context
            )
            
            # Check cache
            cache_key = self._get_cache_key(messages)
            if use_cache and self.enable_caching and cache_key in self._response_cache:
                logger.debug(f"Using cached answer for question")
                return self._response_cache[cache_key]
            
            # Generate response
            response = self.llm_manager.generate_response(messages)
            
            if response.success:
                answer = response.content.strip()
                
                # Cache the response
                if self.enable_caching:
                    self._response_cache[cache_key] = answer
                
                logger.debug(f"Generated answer for question")
                return answer
            else:
                logger.error(f"Failed to generate answer: {response.error_message}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            return None
    
    def enhance_issues_with_llm(
        self, 
        issues: List[Issue], 
        parsed_files: List[ParsedFile],
        include_explanations: bool = True,
        include_suggestions: bool = True
    ) -> List[Issue]:
        """
        Enhance issues with LLM-generated explanations and suggestions.
        
        Args:
            issues: List of issues to enhance
            parsed_files: List of parsed files for context
            include_explanations: Whether to generate explanations
            include_suggestions: Whether to generate suggestions
            
        Returns:
            List of enhanced issues
        """
        enhanced_issues = []
        
        for issue in issues:
            enhanced_issue = issue
            
            try:
                # Generate explanation
                if include_explanations:
                    explanation = self.generate_issue_explanation(issue, parsed_files)
                    if explanation:
                        # Add explanation to metadata
                        enhanced_issue.metadata["llm_explanation"] = explanation
                
                # Generate improved suggestion
                if include_suggestions:
                    suggestion = self.generate_issue_suggestion(issue, parsed_files)
                    if suggestion:
                        # Update the suggestion
                        enhanced_issue.suggestion = suggestion
                        enhanced_issue.metadata["llm_enhanced"] = True
                
                enhanced_issues.append(enhanced_issue)
                
            except Exception as e:
                logger.warning(f"Failed to enhance issue {issue.id}: {e}")
                enhanced_issues.append(issue)  # Add original issue if enhancement fails
        
        logger.info(f"Enhanced {len(enhanced_issues)} issues with LLM")
        return enhanced_issues
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get LLM service statistics."""
        llm_stats = self.llm_manager.get_statistics()
        
        return {
            **llm_stats,
            "cached_responses": len(self._response_cache),
            "caching_enabled": self.enable_caching,
            "available_templates": len(self.prompt_manager.templates)
        }
    
    def clear_cache(self) -> None:
        """Clear the response cache."""
        self._response_cache.clear()
        logger.info("LLM response cache cleared")


def create_llm_service(
    provider: str = "openai",
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    enable_fallback: bool = True,
    enable_caching: bool = True
) -> LLMService:
    """
    Create an LLM service with default configuration.
    
    Args:
        provider: LLM provider ("openai", "anthropic", or "mock")
        model: Model name to use
        api_key: API key (if not provided, will use environment variables)
        enable_fallback: Whether to enable fallback provider
        enable_caching: Whether to enable response caching
        
    Returns:
        Configured LLMService instance
    """
    llm_manager = create_default_llm_manager(
        provider=provider,
        model=model,
        api_key=api_key,
        enable_fallback=enable_fallback
    )
    
    return LLMService(
        llm_manager=llm_manager,
        enable_caching=enable_caching
    )