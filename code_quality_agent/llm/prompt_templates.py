"""Prompt templates for LLM-powered explanations and suggestions."""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

from ..core.models import Issue, IssueCategory, Severity, ParsedFile


class PromptType(Enum):
    """Types of prompts for different use cases."""
    ISSUE_EXPLANATION = "issue_explanation"
    ISSUE_SUGGESTION = "issue_suggestion"
    CODE_REVIEW = "code_review"
    SUMMARY_GENERATION = "summary_generation"
    QUESTION_ANSWERING = "question_answering"


@dataclass
class PromptTemplate:
    """Template for generating LLM prompts."""
    name: str
    prompt_type: PromptType
    system_message: str
    user_template: str
    variables: List[str]
    
    def format(self, **kwargs) -> List[Dict[str, str]]:
        """
        Format the template with provided variables.
        
        Args:
            **kwargs: Variables to substitute in the template
            
        Returns:
            List of message dictionaries for LLM
        """
        # Validate required variables
        missing_vars = [var for var in self.variables if var not in kwargs]
        if missing_vars:
            raise ValueError(f"Missing required variables: {missing_vars}")
        
        # Format the user message
        user_message = self.user_template.format(**kwargs)
        
        return [
            {"role": "system", "content": self.system_message},
            {"role": "user", "content": user_message}
        ]


class PromptTemplateManager:
    """Manager for prompt templates."""
    
    def __init__(self):
        self.templates: Dict[str, PromptTemplate] = {}
        self._initialize_default_templates()
    
    def _initialize_default_templates(self) -> None:
        """Initialize default prompt templates."""
        
        # Issue Explanation Template
        self.templates["issue_explanation"] = PromptTemplate(
            name="issue_explanation",
            prompt_type=PromptType.ISSUE_EXPLANATION,
            system_message="""You are a senior software engineer and code quality expert. Your task is to explain code quality issues in a clear, educational manner that helps developers understand why something is problematic and how it impacts their codebase.

Guidelines:
- Provide clear, concise explanations
- Focus on the impact and consequences of the issue
- Use technical language appropriate for developers
- Be specific about the problem without being condescending
- Include relevant context about best practices
- Keep explanations under 200 words""",
            user_template="""Please explain this code quality issue:

**Issue Type:** {category}
**Severity:** {severity}
**Title:** {title}
**Description:** {description}
**File:** {file_path}
**Lines:** {line_start}-{line_end}

**Code Context:**
```{language}
{code_snippet}
```

Explain why this is a problem and what impact it could have on the codebase.""",
            variables=["category", "severity", "title", "description", "file_path", "line_start", "line_end", "language", "code_snippet"]
        )
        
        # Issue Suggestion Template
        self.templates["issue_suggestion"] = PromptTemplate(
            name="issue_suggestion",
            prompt_type=PromptType.ISSUE_SUGGESTION,
            system_message="""You are a senior software engineer providing actionable code improvement suggestions. Your task is to provide specific, practical solutions that developers can implement immediately.

Guidelines:
- Provide concrete, actionable steps
- Include code examples when helpful
- Prioritize solutions by impact and effort
- Consider multiple approaches when applicable
- Be specific about implementation details
- Keep suggestions focused and practical
- Limit response to 250 words""",
            user_template="""Please provide actionable suggestions to fix this code quality issue:

**Issue Type:** {category}
**Severity:** {severity}
**Title:** {title}
**Description:** {description}
**File:** {file_path}
**Lines:** {line_start}-{line_end}

**Code Context:**
```{language}
{code_snippet}
```

**Current Suggestion:** {current_suggestion}

Provide specific, actionable steps to resolve this issue. Include code examples if helpful.""",
            variables=["category", "severity", "title", "description", "file_path", "line_start", "line_end", "language", "code_snippet", "current_suggestion"]
        )
        
        # Code Review Template
        self.templates["code_review"] = PromptTemplate(
            name="code_review",
            prompt_type=PromptType.CODE_REVIEW,
            system_message="""You are conducting a comprehensive code review. Analyze the provided code for quality, maintainability, security, and best practices. Provide constructive feedback that helps improve the codebase.

Guidelines:
- Focus on significant issues, not minor style preferences
- Provide balanced feedback (both positive and areas for improvement)
- Be specific about recommendations
- Consider security, performance, and maintainability
- Suggest concrete improvements
- Keep review professional and constructive""",
            user_template="""Please review this code:

**File:** {file_path}
**Language:** {language}

```{language}
{code_content}
```

**Context:** {context}

Provide a comprehensive code review focusing on quality, security, performance, and maintainability.""",
            variables=["file_path", "language", "code_content", "context"]
        )
        
        # Summary Generation Template
        self.templates["summary_generation"] = PromptTemplate(
            name="summary_generation",
            prompt_type=PromptType.SUMMARY_GENERATION,
            system_message="""You are generating executive summaries of code quality analysis results. Create concise, informative summaries that highlight key findings and provide actionable insights for development teams.

Guidelines:
- Summarize key findings and trends
- Highlight critical issues that need immediate attention
- Provide overall quality assessment
- Include actionable recommendations
- Use clear, professional language
- Structure information logically
- Keep summary concise but comprehensive""",
            user_template="""Please generate a summary of this code quality analysis:

**Codebase:** {codebase_path}
**Total Files Analyzed:** {total_files}
**Total Issues Found:** {total_issues}

**Issues by Category:**
{issues_by_category}

**Issues by Severity:**
{issues_by_severity}

**Quality Metrics:**
- Overall Score: {overall_score}/100
- Maintainability Index: {maintainability_index}
- Technical Debt Ratio: {technical_debt_ratio}

**Top Issues:**
{top_issues}

Generate a comprehensive summary with key findings and recommendations.""",
            variables=["codebase_path", "total_files", "total_issues", "issues_by_category", "issues_by_severity", "overall_score", "maintainability_index", "technical_debt_ratio", "top_issues"]
        )
        
        # Question Answering Template
        self.templates["question_answering"] = PromptTemplate(
            name="question_answering",
            prompt_type=PromptType.QUESTION_ANSWERING,
            system_message="""You are a code quality expert assistant helping developers understand their codebase analysis results. Answer questions clearly and provide helpful insights based on the analysis data.

Guidelines:
- Answer questions directly and accurately
- Provide context and explanations when helpful
- Reference specific findings from the analysis
- Offer actionable advice when appropriate
- Be conversational but professional
- If you don't have enough information, say so clearly
- Keep responses focused and relevant""",
            user_template="""Based on the code quality analysis results, please answer this question:

**Question:** {question}

**Analysis Context:**
- Codebase: {codebase_path}
- Total Files: {total_files}
- Total Issues: {total_issues}
- Overall Quality Score: {overall_score}/100

**Relevant Issues:**
{relevant_issues}

**Additional Context:**
{additional_context}

Please provide a helpful answer based on the analysis results.""",
            variables=["question", "codebase_path", "total_files", "total_issues", "overall_score", "relevant_issues", "additional_context"]
        )
    
    def get_template(self, template_name: str) -> Optional[PromptTemplate]:
        """Get a template by name."""
        return self.templates.get(template_name)
    
    def add_template(self, template: PromptTemplate) -> None:
        """Add a custom template."""
        self.templates[template.name] = template
    
    def list_templates(self) -> List[str]:
        """List all available template names."""
        return list(self.templates.keys())
    
    def format_issue_explanation(self, issue: Issue, code_snippet: str, language: str = "python") -> List[Dict[str, str]]:
        """
        Format an issue explanation prompt.
        
        Args:
            issue: Issue object to explain
            code_snippet: Code snippet showing the issue
            language: Programming language of the code
            
        Returns:
            Formatted messages for LLM
        """
        template = self.get_template("issue_explanation")
        if not template:
            raise ValueError("Issue explanation template not found")
        
        return template.format(
            category=issue.category.value,
            severity=issue.severity.value,
            title=issue.title,
            description=issue.description,
            file_path=issue.location.file_path,
            line_start=issue.location.line_start,
            line_end=issue.location.line_end,
            language=language,
            code_snippet=code_snippet
        )
    
    def format_issue_suggestion(self, issue: Issue, code_snippet: str, language: str = "python") -> List[Dict[str, str]]:
        """
        Format an issue suggestion prompt.
        
        Args:
            issue: Issue object to provide suggestions for
            code_snippet: Code snippet showing the issue
            language: Programming language of the code
            
        Returns:
            Formatted messages for LLM
        """
        template = self.get_template("issue_suggestion")
        if not template:
            raise ValueError("Issue suggestion template not found")
        
        return template.format(
            category=issue.category.value,
            severity=issue.severity.value,
            title=issue.title,
            description=issue.description,
            file_path=issue.location.file_path,
            line_start=issue.location.line_start,
            line_end=issue.location.line_end,
            language=language,
            code_snippet=code_snippet,
            current_suggestion=issue.suggestion
        )
    
    def format_code_review(self, parsed_file: ParsedFile, context: str = "") -> List[Dict[str, str]]:
        """
        Format a code review prompt.
        
        Args:
            parsed_file: ParsedFile object to review
            context: Additional context about the code
            
        Returns:
            Formatted messages for LLM
        """
        template = self.get_template("code_review")
        if not template:
            raise ValueError("Code review template not found")
        
        return template.format(
            file_path=parsed_file.path,
            language=parsed_file.language,
            code_content=parsed_file.content,
            context=context
        )
    
    def format_summary_generation(
        self, 
        codebase_path: str,
        total_files: int,
        issues: List[Issue],
        quality_metrics: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """
        Format a summary generation prompt.
        
        Args:
            codebase_path: Path to the analyzed codebase
            total_files: Number of files analyzed
            issues: List of all issues found
            quality_metrics: Quality metrics dictionary
            
        Returns:
            Formatted messages for LLM
        """
        template = self.get_template("summary_generation")
        if not template:
            raise ValueError("Summary generation template not found")
        
        # Organize issues by category and severity
        issues_by_category = {}
        issues_by_severity = {}
        
        for issue in issues:
            # By category
            category = issue.category.value
            if category not in issues_by_category:
                issues_by_category[category] = 0
            issues_by_category[category] += 1
            
            # By severity
            severity = issue.severity.value
            if severity not in issues_by_severity:
                issues_by_severity[severity] = 0
            issues_by_severity[severity] += 1
        
        # Format category and severity summaries
        category_summary = "\n".join([f"- {cat}: {count}" for cat, count in issues_by_category.items()])
        severity_summary = "\n".join([f"- {sev}: {count}" for sev, count in issues_by_severity.items()])
        
        # Get top 5 issues by severity
        severity_order = {"critical": 5, "high": 4, "medium": 3, "low": 2, "info": 1}
        top_issues = sorted(issues, key=lambda x: severity_order.get(x.severity.value, 0), reverse=True)[:5]
        top_issues_summary = "\n".join([f"- {issue.title} ({issue.severity.value})" for issue in top_issues])
        
        return template.format(
            codebase_path=codebase_path,
            total_files=total_files,
            total_issues=len(issues),
            issues_by_category=category_summary,
            issues_by_severity=severity_summary,
            overall_score=quality_metrics.get("overall_score", 0),
            maintainability_index=quality_metrics.get("maintainability_index", 0),
            technical_debt_ratio=quality_metrics.get("technical_debt_ratio", 0),
            top_issues=top_issues_summary
        )
    
    def format_question_answering(
        self,
        question: str,
        codebase_path: str,
        total_files: int,
        issues: List[Issue],
        overall_score: float,
        additional_context: str = ""
    ) -> List[Dict[str, str]]:
        """
        Format a question answering prompt.
        
        Args:
            question: User's question
            codebase_path: Path to the analyzed codebase
            total_files: Number of files analyzed
            issues: List of relevant issues
            overall_score: Overall quality score
            additional_context: Additional context information
            
        Returns:
            Formatted messages for LLM
        """
        template = self.get_template("question_answering")
        if not template:
            raise ValueError("Question answering template not found")
        
        # Format relevant issues
        relevant_issues_summary = "\n".join([
            f"- {issue.title} ({issue.category.value}, {issue.severity.value}) in {issue.location.file_path}"
            for issue in issues[:10]  # Limit to top 10 relevant issues
        ])
        
        return template.format(
            question=question,
            codebase_path=codebase_path,
            total_files=total_files,
            total_issues=len(issues),
            overall_score=overall_score,
            relevant_issues=relevant_issues_summary,
            additional_context=additional_context
        )


# Global instance
prompt_manager = PromptTemplateManager()