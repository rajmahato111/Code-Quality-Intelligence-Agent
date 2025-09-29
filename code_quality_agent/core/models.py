"""Core data models for the Code Quality Intelligence Agent."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set
from enum import Enum
from datetime import datetime
from pathlib import Path
import json
import uuid


class IssueCategory(Enum):
    """Categories of code quality issues."""
    SECURITY = "security"
    PERFORMANCE = "performance"
    COMPLEXITY = "complexity"
    DUPLICATION = "duplication"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    HOTSPOT = "hotspot"


class Severity(Enum):
    """Severity levels for issues."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AnalysisStatus(Enum):
    """Status of an analysis operation."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class CodeLocation:
    """Represents a location in source code."""
    file_path: str
    line_start: int
    line_end: int
    column_start: Optional[int] = None
    column_end: Optional[int] = None
    
    def __str__(self) -> str:
        """String representation of the code location."""
        if self.column_start is not None and self.column_end is not None:
            return f"{self.file_path}:{self.line_start}:{self.column_start}-{self.line_end}:{self.column_end}"
        return f"{self.file_path}:{self.line_start}-{self.line_end}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "file_path": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "column_start": self.column_start,
            "column_end": self.column_end,
        }


@dataclass
class Issue:
    """Represents a code quality issue."""
    id: str
    category: IssueCategory
    severity: Severity
    title: str
    description: str
    location: CodeLocation
    affected_files: List[str]
    suggestion: str
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Post-initialization validation."""
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError("Confidence must be between 0.0 and 1.0")
        if not self.id:
            self.id = str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "category": self.category.value,
            "severity": self.severity.value,
            "title": self.title,
            "description": self.description,
            "location": self.location.to_dict(),
            "affected_files": self.affected_files,
            "suggestion": self.suggestion,
            "confidence": self.confidence,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Issue':
        """Create Issue from dictionary."""
        location_data = data["location"]
        location = CodeLocation(**location_data)
        
        return cls(
            id=data["id"],
            category=IssueCategory(data["category"]),
            severity=Severity(data["severity"]),
            title=data["title"],
            description=data["description"],
            location=location,
            affected_files=data["affected_files"],
            suggestion=data["suggestion"],
            confidence=data["confidence"],
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"]),
        )


@dataclass
class Function:
    """Represents a function or method in source code."""
    name: str
    line_start: int
    line_end: int
    parameters: List[str] = field(default_factory=list)
    return_type: Optional[str] = None
    docstring: Optional[str] = None
    complexity: int = 0
    is_async: bool = False
    is_method: bool = False
    class_name: Optional[str] = None
    decorators: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "parameters": self.parameters,
            "return_type": self.return_type,
            "docstring": self.docstring,
            "complexity": self.complexity,
            "is_async": self.is_async,
            "is_method": self.is_method,
            "class_name": self.class_name,
            "decorators": self.decorators,
        }


@dataclass
class Class:
    """Represents a class in source code."""
    name: str
    line_start: int
    line_end: int
    methods: List[Function] = field(default_factory=list)
    base_classes: List[str] = field(default_factory=list)
    docstring: Optional[str] = None
    decorators: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "methods": [method.to_dict() for method in self.methods],
            "base_classes": self.base_classes,
            "docstring": self.docstring,
            "decorators": self.decorators,
        }


@dataclass
class Import:
    """Represents an import statement."""
    module: str
    names: List[str] = field(default_factory=list)
    alias: Optional[str] = None
    is_from_import: bool = False
    line_number: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "module": self.module,
            "names": self.names,
            "alias": self.alias,
            "is_from_import": self.is_from_import,
            "line_number": self.line_number,
        }


@dataclass
class FileMetadata:
    """Metadata about a source code file."""
    file_path: str
    language: str
    size_bytes: int
    line_count: int
    encoding: str = "utf-8"
    last_modified: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "file_path": self.file_path,
            "language": self.language,
            "size_bytes": self.size_bytes,
            "line_count": self.line_count,
            "encoding": self.encoding,
            "last_modified": self.last_modified.isoformat() if self.last_modified else None,
        }


@dataclass
class ParsedFile:
    """Represents a parsed source code file."""
    path: str
    language: str
    content: str
    ast: Any = None
    metadata: FileMetadata = None
    functions: List[Function] = field(default_factory=list)
    classes: List[Class] = field(default_factory=list)
    imports: List[Import] = field(default_factory=list)
    
    def __post_init__(self):
        """Post-initialization setup."""
        if self.metadata is None:
            self.metadata = FileMetadata(
                file_path=self.path,
                language=self.language,
                size_bytes=len(self.content.encode('utf-8')),
                line_count=len(self.content.splitlines()),
            )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization (excluding AST and content)."""
        return {
            "path": self.path,
            "language": self.language,
            "metadata": self.metadata.to_dict() if self.metadata else None,
            "functions": [func.to_dict() for func in self.functions],
            "classes": [cls.to_dict() for cls in self.classes],
            "imports": [imp.to_dict() for imp in self.imports],
        }


@dataclass
class DependencyGraph:
    """Represents dependencies between files and modules."""
    nodes: Set[str] = field(default_factory=set)
    edges: List[tuple] = field(default_factory=list)  # (from, to) pairs
    
    def add_dependency(self, from_file: str, to_file: str) -> None:
        """Add a dependency relationship."""
        self.nodes.add(from_file)
        self.nodes.add(to_file)
        if (from_file, to_file) not in self.edges:
            self.edges.append((from_file, to_file))
    
    def get_dependencies(self, file_path: str) -> List[str]:
        """Get all dependencies for a given file."""
        return [to_file for from_file, to_file in self.edges if from_file == file_path]
    
    def get_dependents(self, file_path: str) -> List[str]:
        """Get all files that depend on the given file."""
        return [from_file for from_file, to_file in self.edges if to_file == file_path]
    
    def has_circular_dependencies(self) -> bool:
        """Check if the graph has circular dependencies."""
        # Simple cycle detection using DFS
        visited = set()
        rec_stack = set()
        
        def has_cycle(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            
            for _, neighbor in [edge for edge in self.edges if edge[0] == node]:
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(node)
            return False
        
        for node in self.nodes:
            if node not in visited:
                if has_cycle(node):
                    return True
        
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "nodes": list(self.nodes),
            "edges": self.edges,
        }


@dataclass
class ComplexityMetrics:
    """Code complexity metrics."""
    cyclomatic_complexity: float = 0.0
    cognitive_complexity: float = 0.0
    nesting_depth: int = 0
    lines_of_code: int = 0
    maintainability_index: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "cyclomatic_complexity": self.cyclomatic_complexity,
            "cognitive_complexity": self.cognitive_complexity,
            "nesting_depth": self.nesting_depth,
            "lines_of_code": self.lines_of_code,
            "maintainability_index": self.maintainability_index,
        }


@dataclass
class CoverageMetrics:
    """Test coverage metrics."""
    line_coverage: float = 0.0
    branch_coverage: float = 0.0
    function_coverage: float = 0.0
    uncovered_lines: List[int] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "line_coverage": self.line_coverage,
            "branch_coverage": self.branch_coverage,
            "function_coverage": self.function_coverage,
            "uncovered_lines": self.uncovered_lines,
        }


@dataclass
class QualityMetrics:
    """Overall quality metrics for a codebase."""
    overall_score: float = 0.0
    category_scores: Dict[IssueCategory, float] = field(default_factory=dict)
    complexity_metrics: ComplexityMetrics = field(default_factory=ComplexityMetrics)
    coverage_metrics: CoverageMetrics = field(default_factory=CoverageMetrics)
    maintainability_index: float = 0.0
    technical_debt_ratio: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "overall_score": self.overall_score,
            "category_scores": {cat.value: score for cat, score in self.category_scores.items()},
            "complexity_metrics": self.complexity_metrics.to_dict(),
            "coverage_metrics": self.coverage_metrics.to_dict(),
            "maintainability_index": self.maintainability_index,
            "technical_debt_ratio": self.technical_debt_ratio,
        }


@dataclass
class AnalysisOptions:
    """Configuration options for analysis."""
    include_patterns: List[str] = field(default_factory=lambda: ["*.py", "*.js", "*.ts", "*.jsx", "*.tsx"])
    exclude_patterns: List[str] = field(default_factory=lambda: [
        "node_modules/**", ".git/**", "__pycache__/**", "*.pyc",
        ".venv/**", "venv/**", "build/**", "dist/**"
    ])
    categories: Optional[List[str]] = None
    min_severity: Optional['Severity'] = None
    use_cache: bool = True
    parallel_processing: bool = True
    max_workers: int = 4
    confidence_threshold: float = 0.7
    max_file_size_mb: int = 10
    include_explanations: bool = True
    include_suggestions: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "include_patterns": self.include_patterns,
            "exclude_patterns": self.exclude_patterns,
            "categories": self.categories,
            "min_severity": self.min_severity.value if self.min_severity else None,
            "use_cache": self.use_cache,
            "parallel_processing": self.parallel_processing,
            "max_workers": self.max_workers,
            "confidence_threshold": self.confidence_threshold,
            "max_file_size_mb": self.max_file_size_mb,
            "include_explanations": self.include_explanations,
            "include_suggestions": self.include_suggestions,
        }


@dataclass
class AnalysisContext:
    """Context information for analysis operations."""
    options: AnalysisOptions
    dependency_graph: Optional[DependencyGraph] = None
    file_metadata: Dict[str, FileMetadata] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "options": self.options.to_dict(),
            "dependency_graph": self.dependency_graph.to_dict() if self.dependency_graph else None,
            "file_metadata": {path: meta.to_dict() for path, meta in self.file_metadata.items()},
        }


@dataclass
class GitCommit:
    """Represents a git commit."""
    hash: str
    author: str
    date: datetime
    message: str
    files_changed: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "hash": self.hash,
            "author": self.author,
            "date": self.date.isoformat(),
            "message": self.message,
            "files_changed": self.files_changed,
        }


@dataclass
class FileChurnMetrics:
    """Metrics about file change frequency and patterns."""
    file_path: str
    total_commits: int
    unique_authors: int
    lines_added: int
    lines_deleted: int
    first_commit_date: datetime
    last_commit_date: datetime
    change_frequency: float  # commits per day
    complexity_score: float = 0.0
    hotspot_score: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "file_path": self.file_path,
            "total_commits": self.total_commits,
            "unique_authors": self.unique_authors,
            "lines_added": self.lines_added,
            "lines_deleted": self.lines_deleted,
            "first_commit_date": self.first_commit_date.isoformat(),
            "last_commit_date": self.last_commit_date.isoformat(),
            "change_frequency": self.change_frequency,
            "complexity_score": self.complexity_score,
            "hotspot_score": self.hotspot_score,
        }


@dataclass
class HotspotAnalysis:
    """Results of hotspot analysis."""
    file_churn_metrics: List[FileChurnMetrics] = field(default_factory=list)
    hotspot_files: List[str] = field(default_factory=list)
    complexity_hotspots: List[str] = field(default_factory=list)
    churn_hotspots: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "file_churn_metrics": [metrics.to_dict() for metrics in self.file_churn_metrics],
            "hotspot_files": self.hotspot_files,
            "complexity_hotspots": self.complexity_hotspots,
            "churn_hotspots": self.churn_hotspots,
            "recommendations": self.recommendations,
        }


@dataclass
class AnalysisResult:
    """Complete results of a codebase analysis."""
    analysis_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    codebase_path: str = ""
    parsed_files: List[ParsedFile] = field(default_factory=list)
    issues: List[Issue] = field(default_factory=list)
    metrics: QualityMetrics = field(default_factory=QualityMetrics)
    dependency_graph: DependencyGraph = field(default_factory=DependencyGraph)
    hotspot_analysis: Optional[HotspotAnalysis] = None
    options: AnalysisOptions = field(default_factory=AnalysisOptions)
    
    def get_issues_by_category(self, category: IssueCategory) -> List[Issue]:
        """Get all issues of a specific category."""
        return [issue for issue in self.issues if issue.category == category]
    
    def get_issues_by_severity(self, severity: Severity) -> List[Issue]:
        """Get all issues of a specific severity."""
        return [issue for issue in self.issues if issue.severity == severity]
    
    def get_issues_by_file(self, file_path: str) -> List[Issue]:
        """Get all issues for a specific file."""
        return [issue for issue in self.issues if issue.location.file_path == file_path]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "analysis_id": self.analysis_id,
            "timestamp": self.timestamp.isoformat(),
            "codebase_path": self.codebase_path,
            "parsed_files": [file.to_dict() for file in self.parsed_files],
            "issues": [issue.to_dict() for issue in self.issues],
            "metrics": self.metrics.to_dict(),
            "dependency_graph": self.dependency_graph.to_dict(),
            "options": self.options.to_dict(),
        }
    
    def save_to_file(self, file_path: Path) -> None:
        """Save analysis results to a JSON file."""
        with open(file_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load_from_file(cls, file_path: Path) -> 'AnalysisResult':
        """Load analysis results from a JSON file."""
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Reconstruct objects from dictionaries
        parsed_files = []
        for file_data in data["parsed_files"]:
            # Reconstruct ParsedFile (simplified, without AST and content)
            parsed_file = ParsedFile(
                path=file_data["path"],
                language=file_data["language"],
                content="",  # Content not stored in serialization
            )
            parsed_files.append(parsed_file)
        
        issues = [Issue.from_dict(issue_data) for issue_data in data["issues"]]
        
        return cls(
            analysis_id=data["analysis_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            codebase_path=data["codebase_path"],
            parsed_files=parsed_files,
            issues=issues,
            # Note: Full reconstruction of all nested objects would require more complex logic
        )