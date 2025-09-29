"""Pydantic models for the web API."""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, HttpUrl, field_validator
from enum import Enum
from datetime import datetime


class AnalysisStatus(str, Enum):
    """Status of an analysis job."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class SeverityLevel(str, Enum):
    """Severity levels for issues."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AnalysisConfiguration(BaseModel):
    """Configuration for analysis."""
    enable_security_analysis: bool = Field(True, description="Enable security analysis")
    enable_performance_analysis: bool = Field(True, description="Enable performance analysis")
    enable_maintainability_analysis: bool = Field(True, description="Enable maintainability analysis")
    enable_complexity_analysis: bool = Field(True, description="Enable complexity analysis")
    enable_duplication_analysis: bool = Field(True, description="Enable duplication analysis")
    enable_ai_explanations: bool = Field(True, description="Enable AI explanations")
    enable_severity_scoring: bool = Field(True, description="Enable automated severity scoring")
    severity_threshold: SeverityLevel = Field(SeverityLevel.LOW, description="Minimum severity to report")
    max_issues_per_file: int = Field(50, ge=1, le=1000, description="Maximum issues per file")
    timeout_seconds: int = Field(300, ge=30, le=3600, description="Analysis timeout")


class RepositoryRequest(BaseModel):
    """Request to analyze a repository."""
    url: HttpUrl = Field(..., description="GitHub/GitLab repository URL")
    branch: Optional[str] = Field("main", description="Branch to analyze")
    include_patterns: Optional[List[str]] = Field(None, description="File patterns to include")
    exclude_patterns: Optional[List[str]] = Field(None, description="File patterns to exclude")
    analysis_types: Optional[List[str]] = Field(None, description="Types of analysis to perform")
    config: Optional[AnalysisConfiguration] = Field(None, description="Analysis configuration")
    
    @field_validator('url')
    @classmethod
    def validate_repository_url(cls, v):
        """Validate that the URL is a supported repository."""
        url_str = str(v)
        if not (url_str.startswith('https://github.com/') or 
                url_str.startswith('https://gitlab.com/') or
                url_str.startswith('https://bitbucket.org/')):
            raise ValueError('Only GitHub, GitLab, and Bitbucket repositories are supported')
        return v


class FileAnalysisRequest(BaseModel):
    """Request to analyze specific files."""
    files: List[str] = Field(..., description="List of file paths to analyze")
    content: Optional[Dict[str, str]] = Field(None, description="File contents (path -> content)")
    analysis_types: Optional[List[str]] = Field(None, description="Types of analysis to perform")


class IssueLocation(BaseModel):
    """Location of an issue in code."""
    file_path: str = Field(..., description="Path to the file")
    line_number: Optional[int] = Field(None, description="Line number")
    column_number: Optional[int] = Field(None, description="Column number")
    function_name: Optional[str] = Field(None, description="Function name")
    class_name: Optional[str] = Field(None, description="Class name")


class Issue(BaseModel):
    """A code quality issue."""
    id: str = Field(..., description="Unique issue identifier")
    category: str = Field(..., description="Issue category")
    type: str = Field(..., description="Specific issue type")
    severity: SeverityLevel = Field(..., description="Issue severity")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in the issue")
    title: str = Field(..., description="Issue title")
    description: str = Field(..., description="Detailed description")
    explanation: Optional[str] = Field(None, description="AI-generated explanation")
    location: IssueLocation = Field(..., description="Issue location")
    code_snippet: Optional[str] = Field(None, description="Relevant code snippet")
    suggestions: Optional[List[str]] = Field(None, description="Fix suggestions")
    business_impact: Optional[float] = Field(None, ge=0.0, le=1.0, description="Business impact score")
    priority_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Overall priority score")
    tags: Optional[List[str]] = Field(None, description="Issue tags")


class AnalysisResult(BaseModel):
    """Result of a code analysis."""
    job_id: str = Field(..., description="Analysis job identifier")
    status: AnalysisStatus = Field(..., description="Analysis status")
    repository_url: Optional[str] = Field(None, description="Repository URL")
    branch: Optional[str] = Field(None, description="Analyzed branch")
    commit_hash: Optional[str] = Field(None, description="Commit hash")
    started_at: datetime = Field(..., description="Analysis start time")
    completed_at: Optional[datetime] = Field(None, description="Analysis completion time")
    duration_seconds: Optional[float] = Field(None, description="Analysis duration")
    
    # Results
    issues: List[Issue] = Field(default_factory=list, description="Found issues")
    summary: Dict[str, Any] = Field(default_factory=dict, description="Analysis summary")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="Code metrics")
    
    # Error information
    error_message: Optional[str] = Field(None, description="Error message if failed")
    error_details: Optional[Dict[str, Any]] = Field(None, description="Detailed error information")


class QuestionRequest(BaseModel):
    """Request for Q&A about analysis results."""
    question: str = Field(..., min_length=1, max_length=1000, description="Question about the code")
    job_id: Optional[str] = Field(None, description="Analysis job ID for context")
    file_path: Optional[str] = Field(None, description="Specific file to ask about")
    issue_id: Optional[str] = Field(None, description="Specific issue to ask about")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class Answer(BaseModel):
    """Answer to a question about code quality."""
    question: str = Field(..., description="Original question")
    answer: str = Field(..., description="AI-generated answer")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in the answer")
    sources: Optional[List[str]] = Field(None, description="Source references")
    related_issues: Optional[List[str]] = Field(None, description="Related issue IDs")
    suggestions: Optional[List[str]] = Field(None, description="Additional suggestions")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Answer timestamp")


class AnalysisProgress(BaseModel):
    """Progress information for an ongoing analysis."""
    job_id: str = Field(..., description="Analysis job identifier")
    status: AnalysisStatus = Field(..., description="Current status")
    progress_percentage: float = Field(..., ge=0.0, le=100.0, description="Progress percentage")
    current_step: str = Field(..., description="Current analysis step")
    steps_completed: int = Field(..., description="Number of completed steps")
    total_steps: int = Field(..., description="Total number of steps")
    files_processed: int = Field(default=0, description="Number of files processed")
    total_files: int = Field(default=0, description="Total number of files to process")
    issues_found: int = Field(default=0, description="Number of issues found so far")
    estimated_time_remaining: Optional[float] = Field(None, description="Estimated time remaining in seconds")
    message: Optional[str] = Field(None, description="Current status message")


class HealthCheck(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")
    components: Dict[str, str] = Field(default_factory=dict, description="Component status")


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    request_id: Optional[str] = Field(None, description="Request identifier")


class BatchAnalysisRequest(BaseModel):
    """Request for batch analysis of multiple repositories."""
    repositories: List[RepositoryRequest] = Field(..., min_length=1, max_length=10, description="Repositories to analyze")
    configuration: Optional[AnalysisConfiguration] = Field(None, description="Analysis configuration")
    callback_url: Optional[HttpUrl] = Field(None, description="Webhook URL for completion notification")


class BatchAnalysisResult(BaseModel):
    """Result of batch analysis."""
    batch_id: str = Field(..., description="Batch job identifier")
    status: AnalysisStatus = Field(..., description="Batch status")
    total_repositories: int = Field(..., description="Total number of repositories")
    completed_repositories: int = Field(default=0, description="Number of completed repositories")
    failed_repositories: int = Field(default=0, description="Number of failed repositories")
    results: List[AnalysisResult] = Field(default_factory=list, description="Individual analysis results")
    started_at: datetime = Field(..., description="Batch start time")
    completed_at: Optional[datetime] = Field(None, description="Batch completion time")


class WebhookPayload(BaseModel):
    """Webhook payload for analysis completion."""
    event_type: str = Field(..., description="Event type")
    job_id: str = Field(..., description="Job identifier")
    status: AnalysisStatus = Field(..., description="Final status")
    result: Optional[AnalysisResult] = Field(None, description="Analysis result")
    error: Optional[ErrorResponse] = Field(None, description="Error information")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")


class UserSession(BaseModel):
    """User session information."""
    session_id: str = Field(..., description="Session identifier")
    user_id: Optional[str] = Field(None, description="User identifier")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Session creation time")
    last_activity: datetime = Field(default_factory=datetime.utcnow, description="Last activity time")
    analysis_jobs: List[str] = Field(default_factory=list, description="Associated analysis jobs")
    preferences: Dict[str, Any] = Field(default_factory=dict, description="User preferences")


class APIUsageStats(BaseModel):
    """API usage statistics."""
    total_requests: int = Field(default=0, description="Total number of requests")
    successful_requests: int = Field(default=0, description="Number of successful requests")
    failed_requests: int = Field(default=0, description="Number of failed requests")
    average_response_time: float = Field(default=0.0, description="Average response time in seconds")
    analyses_completed: int = Field(default=0, description="Number of completed analyses")
    questions_answered: int = Field(default=0, description="Number of questions answered")
    uptime_seconds: float = Field(default=0.0, description="Service uptime in seconds")
    last_reset: datetime = Field(default_factory=datetime.utcnow, description="Last stats reset time")