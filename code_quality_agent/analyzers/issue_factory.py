"""Factory for creating standardized quality issues."""

import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime

from .base import IssueCategory, Severity
from ..core.models import Issue, CodeLocation


class IssueFactory:
    """Factory for creating standardized quality issues with consistent formatting."""
    
    @staticmethod
    def create_issue(
        category: IssueCategory,
        severity: Severity,
        title: str,
        description: str,
        file_path: str,
        line_start: int,
        line_end: int,
        suggestion: str,
        confidence: float,
        column_start: Optional[int] = None,
        column_end: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
        affected_files: Optional[List[str]] = None
    ) -> Issue:
        """
        Create a standardized Issue object.
        
        Args:
            category: Issue category
            severity: Issue severity
            title: Brief title describing the issue
            description: Detailed description of the issue
            file_path: Path to the file containing the issue
            line_start: Starting line number
            line_end: Ending line number
            suggestion: Suggested fix for the issue
            confidence: Confidence level (0.0 to 1.0)
            column_start: Optional starting column
            column_end: Optional ending column
            metadata: Optional additional metadata
            affected_files: Optional list of affected files
            
        Returns:
            Standardized Issue object
        """
        location = CodeLocation(
            file_path=file_path,
            line_start=line_start,
            line_end=line_end,
            column_start=column_start,
            column_end=column_end
        )
        
        if affected_files is None:
            affected_files = [file_path]
        
        if metadata is None:
            metadata = {}
        
        # Add creation metadata
        metadata.update({
            'created_by': 'IssueFactory',
            'analyzer_version': '1.0.0',
            'detection_method': 'static_analysis'
        })
        
        return Issue(
            id=str(uuid.uuid4()),
            category=category,
            severity=severity,
            title=title,
            description=description,
            location=location,
            affected_files=affected_files,
            suggestion=suggestion,
            confidence=confidence,
            metadata=metadata,
            created_at=datetime.now()
        )
    
    @staticmethod
    def create_security_issue(
        title: str,
        description: str,
        file_path: str,
        line_start: int,
        line_end: int,
        suggestion: str,
        confidence: float,
        vulnerability_type: str,
        severity: Severity = Severity.HIGH,
        **kwargs
    ) -> Issue:
        """Create a security-specific issue."""
        metadata = kwargs.get('metadata', {})
        metadata.update({
            'vulnerability_type': vulnerability_type,
            'security_impact': IssueFactory._get_security_impact(vulnerability_type),
            'owasp_category': IssueFactory._get_owasp_category(vulnerability_type)
        })
        
        return IssueFactory.create_issue(
            category=IssueCategory.SECURITY,
            severity=severity,
            title=title,
            description=description,
            file_path=file_path,
            line_start=line_start,
            line_end=line_end,
            suggestion=suggestion,
            confidence=confidence,
            metadata=metadata,
            **{k: v for k, v in kwargs.items() if k != 'metadata'}
        )
    
    @staticmethod
    def create_performance_issue(
        title: str,
        description: str,
        file_path: str,
        line_start: int,
        line_end: int,
        suggestion: str,
        confidence: float,
        performance_impact: str,
        severity: Severity = Severity.MEDIUM,
        **kwargs
    ) -> Issue:
        """Create a performance-specific issue."""
        metadata = kwargs.get('metadata', {})
        metadata.update({
            'performance_impact': performance_impact,
            'optimization_category': IssueFactory._get_optimization_category(performance_impact)
        })
        
        return IssueFactory.create_issue(
            category=IssueCategory.PERFORMANCE,
            severity=severity,
            title=title,
            description=description,
            file_path=file_path,
            line_start=line_start,
            line_end=line_end,
            suggestion=suggestion,
            confidence=confidence,
            metadata=metadata,
            **{k: v for k, v in kwargs.items() if k != 'metadata'}
        )
    
    @staticmethod
    def create_complexity_issue(
        title: str,
        description: str,
        file_path: str,
        line_start: int,
        line_end: int,
        suggestion: str,
        confidence: float,
        complexity_metric: str,
        complexity_value: float,
        threshold: float,
        severity: Severity = Severity.MEDIUM,
        **kwargs
    ) -> Issue:
        """Create a complexity-specific issue."""
        metadata = kwargs.get('metadata', {})
        metadata.update({
            'complexity_metric': complexity_metric,
            'complexity_value': complexity_value,
            'threshold': threshold,
            'complexity_ratio': complexity_value / threshold if threshold > 0 else 0
        })
        
        return IssueFactory.create_issue(
            category=IssueCategory.COMPLEXITY,
            severity=severity,
            title=title,
            description=description,
            file_path=file_path,
            line_start=line_start,
            line_end=line_end,
            suggestion=suggestion,
            confidence=confidence,
            metadata=metadata,
            **{k: v for k, v in kwargs.items() if k != 'metadata'}
        )
    
    @staticmethod
    def create_duplication_issue(
        title: str,
        description: str,
        file_path: str,
        line_start: int,
        line_end: int,
        suggestion: str,
        confidence: float,
        duplicate_files: List[str],
        similarity_score: float,
        severity: Severity = Severity.LOW,
        **kwargs
    ) -> Issue:
        """Create a code duplication issue."""
        metadata = kwargs.get('metadata', {})
        metadata.update({
            'duplicate_files': duplicate_files,
            'similarity_score': similarity_score,
            'duplication_type': IssueFactory._get_duplication_type(similarity_score)
        })
        
        affected_files = [file_path] + duplicate_files
        
        return IssueFactory.create_issue(
            category=IssueCategory.DUPLICATION,
            severity=severity,
            title=title,
            description=description,
            file_path=file_path,
            line_start=line_start,
            line_end=line_end,
            suggestion=suggestion,
            confidence=confidence,
            affected_files=affected_files,
            metadata=metadata,
            **{k: v for k, v in kwargs.items() if k not in ['metadata', 'affected_files']}
        )
    
    @staticmethod
    def create_testing_issue(
        title: str,
        description: str,
        file_path: str,
        line_start: int,
        line_end: int,
        suggestion: str,
        confidence: float,
        testing_gap_type: str,
        severity: Severity = Severity.MEDIUM,
        **kwargs
    ) -> Issue:
        """Create a testing-related issue."""
        metadata = kwargs.get('metadata', {})
        metadata.update({
            'testing_gap_type': testing_gap_type,
            'test_priority': IssueFactory._get_test_priority(testing_gap_type)
        })
        
        return IssueFactory.create_issue(
            category=IssueCategory.TESTING,
            severity=severity,
            title=title,
            description=description,
            file_path=file_path,
            line_start=line_start,
            line_end=line_end,
            suggestion=suggestion,
            confidence=confidence,
            metadata=metadata,
            **{k: v for k, v in kwargs.items() if k != 'metadata'}
        )
    
    @staticmethod
    def create_documentation_issue(
        title: str,
        description: str,
        file_path: str,
        line_start: int,
        line_end: int,
        suggestion: str,
        confidence: float,
        documentation_type: str,
        severity: Severity = Severity.LOW,
        **kwargs
    ) -> Issue:
        """Create a documentation-related issue."""
        metadata = kwargs.get('metadata', {})
        metadata.update({
            'documentation_type': documentation_type,
            'documentation_priority': IssueFactory._get_documentation_priority(documentation_type)
        })
        
        return IssueFactory.create_issue(
            category=IssueCategory.DOCUMENTATION,
            severity=severity,
            title=title,
            description=description,
            file_path=file_path,
            line_start=line_start,
            line_end=line_end,
            suggestion=suggestion,
            confidence=confidence,
            metadata=metadata,
            **{k: v for k, v in kwargs.items() if k != 'metadata'}
        )
    
    @staticmethod
    def _get_security_impact(vulnerability_type: str) -> str:
        """Get security impact level for vulnerability type."""
        high_impact = ['sql_injection', 'xss', 'command_injection', 'path_traversal']
        medium_impact = ['hardcoded_secret', 'weak_crypto', 'insecure_random']
        
        if vulnerability_type.lower() in high_impact:
            return 'high'
        elif vulnerability_type.lower() in medium_impact:
            return 'medium'
        else:
            return 'low'
    
    @staticmethod
    def _get_owasp_category(vulnerability_type: str) -> str:
        """Get OWASP Top 10 category for vulnerability type."""
        owasp_mapping = {
            'sql_injection': 'A03:2021 – Injection',
            'xss': 'A03:2021 – Injection',
            'command_injection': 'A03:2021 – Injection',
            'path_traversal': 'A01:2021 – Broken Access Control',
            'hardcoded_secret': 'A07:2021 – Identification and Authentication Failures',
            'weak_crypto': 'A02:2021 – Cryptographic Failures',
            'insecure_random': 'A02:2021 – Cryptographic Failures'
        }
        return owasp_mapping.get(vulnerability_type.lower(), 'Other')
    
    @staticmethod
    def _get_optimization_category(performance_impact: str) -> str:
        """Get optimization category for performance impact."""
        categories = {
            'memory': 'Memory Optimization',
            'cpu': 'CPU Optimization',
            'io': 'I/O Optimization',
            'network': 'Network Optimization',
            'algorithm': 'Algorithm Optimization'
        }
        return categories.get(performance_impact.lower(), 'General Optimization')
    
    @staticmethod
    def _get_duplication_type(similarity_score: float) -> str:
        """Get duplication type based on similarity score."""
        if similarity_score >= 0.95:
            return 'exact_duplicate'
        elif similarity_score >= 0.80:
            return 'near_duplicate'
        elif similarity_score >= 0.60:
            return 'similar_code'
        else:
            return 'potential_duplicate'
    
    @staticmethod
    def _get_test_priority(testing_gap_type: str) -> str:
        """Get test priority for testing gap type."""
        high_priority = ['untested_public_method', 'untested_critical_path']
        medium_priority = ['low_coverage', 'missing_edge_cases']
        
        if testing_gap_type.lower() in high_priority:
            return 'high'
        elif testing_gap_type.lower() in medium_priority:
            return 'medium'
        else:
            return 'low'
    
    @staticmethod
    def _get_documentation_priority(documentation_type: str) -> str:
        """Get documentation priority for documentation type."""
        high_priority = ['missing_public_api_docs', 'outdated_critical_docs']
        medium_priority = ['missing_docstring', 'incomplete_comments']
        
        if documentation_type.lower() in high_priority:
            return 'high'
        elif documentation_type.lower() in medium_priority:
            return 'medium'
        else:
            return 'low'