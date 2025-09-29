"""Serialization utilities for data models."""

import json
import pickle
from pathlib import Path
from typing import Any, Dict, List, Union, Type, TypeVar
from datetime import datetime
from enum import Enum

from ..core.models import (
    AnalysisResult, Issue, ParsedFile, QualityMetrics,
    IssueCategory, Severity, CodeLocation
)

T = TypeVar('T')


class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for handling special types."""
    
    def default(self, obj: Any) -> Any:
        """Handle special object types."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, Enum):
            return obj.value
        elif isinstance(obj, Path):
            return str(obj)
        elif hasattr(obj, 'to_dict'):
            return obj.to_dict()
        return super().default(obj)


def serialize_to_json(obj: Any, file_path: Path = None, indent: int = 2) -> Union[str, None]:
    """
    Serialize an object to JSON format.
    
    Args:
        obj: Object to serialize
        file_path: Optional file path to save JSON to
        indent: JSON indentation level
        
    Returns:
        JSON string if no file_path provided, None otherwise
    """
    json_str = json.dumps(obj, cls=CustomJSONEncoder, indent=indent, ensure_ascii=False)
    
    if file_path:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(json_str)
        return None
    
    return json_str


def deserialize_from_json(json_data: Union[str, Path], target_type: Type[T] = None) -> Union[Dict[str, Any], T]:
    """
    Deserialize JSON data to Python objects.
    
    Args:
        json_data: JSON string or path to JSON file
        target_type: Optional target type for deserialization
        
    Returns:
        Deserialized object
    """
    if isinstance(json_data, Path):
        with open(json_data, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        data = json.loads(json_data)
    
    if target_type and hasattr(target_type, 'from_dict'):
        return target_type.from_dict(data)
    
    return data


def serialize_to_pickle(obj: Any, file_path: Path) -> None:
    """
    Serialize an object to pickle format.
    
    Args:
        obj: Object to serialize
        file_path: Path to save pickle file
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'wb') as f:
        pickle.dump(obj, f)


def deserialize_from_pickle(file_path: Path) -> Any:
    """
    Deserialize an object from pickle format.
    
    Args:
        file_path: Path to pickle file
        
    Returns:
        Deserialized object
    """
    with open(file_path, 'rb') as f:
        return pickle.load(f)


def create_analysis_summary(analysis_result: AnalysisResult) -> Dict[str, Any]:
    """
    Create a summary of analysis results for quick overview.
    
    Args:
        analysis_result: Complete analysis results
        
    Returns:
        Summary dictionary
    """
    issue_counts_by_category = {}
    issue_counts_by_severity = {}
    
    for issue in analysis_result.issues:
        # Count by category
        category = issue.category.value
        issue_counts_by_category[category] = issue_counts_by_category.get(category, 0) + 1
        
        # Count by severity
        severity = issue.severity.value
        issue_counts_by_severity[severity] = issue_counts_by_severity.get(severity, 0) + 1
    
    return {
        "analysis_id": analysis_result.analysis_id,
        "timestamp": analysis_result.timestamp.isoformat(),
        "codebase_path": analysis_result.codebase_path,
        "total_files": len(analysis_result.parsed_files),
        "total_issues": len(analysis_result.issues),
        "issues_by_category": issue_counts_by_category,
        "issues_by_severity": issue_counts_by_severity,
        "overall_score": analysis_result.metrics.overall_score,
        "maintainability_index": analysis_result.metrics.maintainability_index,
        "has_circular_dependencies": analysis_result.dependency_graph.has_circular_dependencies(),
    }


def export_issues_to_csv(issues: List[Issue], file_path: Path) -> None:
    """
    Export issues to CSV format.
    
    Args:
        issues: List of issues to export
        file_path: Path to save CSV file
    """
    import csv
    
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'id', 'category', 'severity', 'title', 'description',
            'file_path', 'line_start', 'line_end', 'suggestion', 'confidence'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for issue in issues:
            writer.writerow({
                'id': issue.id,
                'category': issue.category.value,
                'severity': issue.severity.value,
                'title': issue.title,
                'description': issue.description,
                'file_path': issue.location.file_path,
                'line_start': issue.location.line_start,
                'line_end': issue.location.line_end,
                'suggestion': issue.suggestion,
                'confidence': issue.confidence,
            })


def create_metrics_report(metrics: QualityMetrics) -> Dict[str, Any]:
    """
    Create a formatted metrics report.
    
    Args:
        metrics: Quality metrics to format
        
    Returns:
        Formatted metrics dictionary
    """
    return {
        "overall_quality": {
            "score": round(metrics.overall_score, 2),
            "grade": _score_to_grade(metrics.overall_score),
            "maintainability_index": round(metrics.maintainability_index, 2),
            "technical_debt_ratio": round(metrics.technical_debt_ratio, 2),
        },
        "category_scores": {
            category.value: round(score, 2)
            for category, score in metrics.category_scores.items()
        },
        "complexity": {
            "cyclomatic_complexity": round(metrics.complexity_metrics.cyclomatic_complexity, 2),
            "cognitive_complexity": round(metrics.complexity_metrics.cognitive_complexity, 2),
            "nesting_depth": metrics.complexity_metrics.nesting_depth,
            "lines_of_code": metrics.complexity_metrics.lines_of_code,
        },
        "coverage": {
            "line_coverage": round(metrics.coverage_metrics.line_coverage, 2),
            "branch_coverage": round(metrics.coverage_metrics.branch_coverage, 2),
            "function_coverage": round(metrics.coverage_metrics.function_coverage, 2),
        }
    }


def _score_to_grade(score: float) -> str:
    """Convert numeric score to letter grade."""
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    else:
        return "F"


def validate_serialized_data(data: Dict[str, Any], expected_fields: List[str]) -> bool:
    """
    Validate that serialized data contains expected fields.
    
    Args:
        data: Serialized data dictionary
        expected_fields: List of required field names
        
    Returns:
        True if all expected fields are present
    """
    return all(field in data for field in expected_fields)


def migrate_analysis_result(data: Dict[str, Any], from_version: str, to_version: str) -> Dict[str, Any]:
    """
    Migrate analysis result data between versions.
    
    Args:
        data: Analysis result data
        from_version: Source version
        to_version: Target version
        
    Returns:
        Migrated data
    """
    # Placeholder for future version migration logic
    # This would handle schema changes between versions
    if from_version == "0.1.0" and to_version == "0.2.0":
        # Example migration logic
        if "new_field" not in data:
            data["new_field"] = "default_value"
    
    return data