"""
Accuracy metrics for analyzer validation.
Implements precision, recall, F1-score, and other accuracy measurements.
"""

from dataclasses import dataclass
from typing import List, Dict, Set, Optional, Tuple
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class MatchType(Enum):
    """Types of matches between expected and actual issues."""
    EXACT_MATCH = "exact_match"
    PARTIAL_MATCH = "partial_match"
    NO_MATCH = "no_match"


@dataclass
class IssueMatch:
    """Represents a match between expected and actual issues."""
    expected_issue: Dict
    actual_issue: Optional[Dict]
    match_type: MatchType
    confidence: float
    match_details: Dict


@dataclass
class ValidationResult:
    """Results of accuracy validation."""
    precision: float
    recall: float
    f1_score: float
    accuracy: float
    true_positives: int
    false_positives: int
    false_negatives: int
    true_negatives: int
    total_expected: int
    total_actual: int
    matches: List[IssueMatch]
    category_metrics: Dict[str, Dict[str, float]]
    severity_metrics: Dict[str, Dict[str, float]]


class AccuracyMetrics:
    """Calculate accuracy metrics for code quality analysis."""
    
    def __init__(self, match_threshold: float = 0.7):
        """
        Initialize accuracy metrics calculator.
        
        Args:
            match_threshold: Minimum confidence for considering a match
        """
        self.match_threshold = match_threshold
    
    def calculate_metrics(
        self, 
        expected_issues: List[Dict], 
        actual_issues: List[Dict]
    ) -> ValidationResult:
        """
        Calculate comprehensive accuracy metrics.
        
        Args:
            expected_issues: List of expected issues from test fixtures
            actual_issues: List of actual issues found by analyzer
            
        Returns:
            ValidationResult with all accuracy metrics
        """
        logger.info(f"Calculating metrics for {len(expected_issues)} expected and {len(actual_issues)} actual issues")
        
        # Match expected issues with actual issues
        matches = self._match_issues(expected_issues, actual_issues)
        
        # Calculate basic metrics
        true_positives = sum(1 for match in matches if match.match_type != MatchType.NO_MATCH)
        false_positives = len(actual_issues) - true_positives
        false_negatives = sum(1 for match in matches if match.match_type == MatchType.NO_MATCH)
        true_negatives = 0  # Not applicable for this type of analysis
        
        # Calculate derived metrics
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        accuracy = true_positives / len(expected_issues) if len(expected_issues) > 0 else 0.0
        
        # Calculate category-specific metrics
        category_metrics = self._calculate_category_metrics(matches, expected_issues, actual_issues)
        
        # Calculate severity-specific metrics
        severity_metrics = self._calculate_severity_metrics(matches, expected_issues, actual_issues)
        
        return ValidationResult(
            precision=precision,
            recall=recall,
            f1_score=f1_score,
            accuracy=accuracy,
            true_positives=true_positives,
            false_positives=false_positives,
            false_negatives=false_negatives,
            true_negatives=true_negatives,
            total_expected=len(expected_issues),
            total_actual=len(actual_issues),
            matches=matches,
            category_metrics=category_metrics,
            severity_metrics=severity_metrics
        )
    
    def _match_issues(self, expected_issues: List[Dict], actual_issues: List[Dict]) -> List[IssueMatch]:
        """
        Match expected issues with actual issues.
        
        Args:
            expected_issues: Expected issues from fixtures
            actual_issues: Actual issues from analysis
            
        Returns:
            List of issue matches
        """
        matches = []
        used_actual_indices = set()
        
        for expected in expected_issues:
            best_match = None
            best_confidence = 0.0
            best_actual_index = -1
            
            for i, actual in enumerate(actual_issues):
                if i in used_actual_indices:
                    continue
                
                confidence = self._calculate_match_confidence(expected, actual)
                
                if confidence > best_confidence and confidence >= self.match_threshold:
                    best_confidence = confidence
                    best_match = actual
                    best_actual_index = i
            
            if best_match is not None:
                match_type = MatchType.EXACT_MATCH if best_confidence >= 0.9 else MatchType.PARTIAL_MATCH
                used_actual_indices.add(best_actual_index)
                
                matches.append(IssueMatch(
                    expected_issue=expected,
                    actual_issue=best_match,
                    match_type=match_type,
                    confidence=best_confidence,
                    match_details=self._get_match_details(expected, best_match)
                ))
            else:
                matches.append(IssueMatch(
                    expected_issue=expected,
                    actual_issue=None,
                    match_type=MatchType.NO_MATCH,
                    confidence=0.0,
                    match_details={}
                ))
        
        return matches
    
    def _calculate_match_confidence(self, expected: Dict, actual: Dict) -> float:
        """
        Calculate confidence score for matching two issues.
        
        Args:
            expected: Expected issue
            actual: Actual issue
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        confidence = 0.0
        total_weight = 0.0
        
        # Category match (high weight)
        if expected.get('category') == getattr(actual, 'category', None):
            confidence += 0.4
        total_weight += 0.4
        
        # Severity match (medium weight)
        if expected.get('severity') == getattr(actual, 'severity', None):
            confidence += 0.2
        total_weight += 0.2
        
        # Type match (medium weight)
        if expected.get('type') == getattr(actual, 'type', None):
            confidence += 0.2
        total_weight += 0.2
        
        # Line number proximity (low weight)
        expected_line = expected.get('line', 0)
        actual_line = getattr(actual, 'line_number', 0) if hasattr(actual, 'line_number') else 0
        
        if expected_line > 0 and actual_line > 0:
            line_diff = abs(expected_line - actual_line)
            if line_diff == 0:
                confidence += 0.1
            elif line_diff <= 5:
                confidence += 0.05
            total_weight += 0.1
        
        # Description similarity (low weight)
        expected_desc = expected.get('description', '').lower()
        actual_desc = getattr(actual, 'description', '').lower()
        
        if expected_desc and actual_desc:
            # Simple word overlap check
            expected_words = set(expected_desc.split())
            actual_words = set(actual_desc.split())
            
            if expected_words and actual_words:
                overlap = len(expected_words & actual_words) / len(expected_words | actual_words)
                confidence += overlap * 0.1
            total_weight += 0.1
        
        return confidence / total_weight if total_weight > 0 else 0.0
    
    def _get_match_details(self, expected: Dict, actual: Dict) -> Dict:
        """Get detailed information about the match."""
        return {
            'expected_category': expected.get('category'),
            'actual_category': getattr(actual, 'category', None),
            'expected_severity': expected.get('severity'),
            'actual_severity': getattr(actual, 'severity', None),
            'expected_type': expected.get('type'),
            'actual_type': getattr(actual, 'type', None),
            'expected_line': expected.get('line'),
            'actual_line': getattr(actual, 'line_number', None),
        }
    
    def _calculate_category_metrics(
        self, 
        matches: List[IssueMatch], 
        expected_issues: List[Dict], 
        actual_issues: List[Dict]
    ) -> Dict[str, Dict[str, float]]:
        """Calculate metrics per category."""
        category_metrics = {}
        
        # Get all categories
        expected_categories = {issue.get('category') for issue in expected_issues}
        actual_categories = {getattr(issue, 'category', None) for issue in actual_issues}
        all_categories = expected_categories | actual_categories
        
        for category in all_categories:
            if category is None:
                continue
                
            # Count matches for this category
            category_matches = [m for m in matches if m.expected_issue.get('category') == category]
            category_expected = len([i for i in expected_issues if i.get('category') == category])
            category_actual = len([i for i in actual_issues if getattr(i, 'category', None) == category])
            
            tp = sum(1 for m in category_matches if m.match_type != MatchType.NO_MATCH)
            fp = category_actual - tp
            fn = sum(1 for m in category_matches if m.match_type == MatchType.NO_MATCH)
            
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
            
            category_metrics[category] = {
                'precision': precision,
                'recall': recall,
                'f1_score': f1,
                'true_positives': tp,
                'false_positives': fp,
                'false_negatives': fn,
                'expected_count': category_expected,
                'actual_count': category_actual
            }
        
        return category_metrics
    
    def _calculate_severity_metrics(
        self, 
        matches: List[IssueMatch], 
        expected_issues: List[Dict], 
        actual_issues: List[Dict]
    ) -> Dict[str, Dict[str, float]]:
        """Calculate metrics per severity level."""
        severity_metrics = {}
        
        # Get all severity levels
        expected_severities = {issue.get('severity') for issue in expected_issues}
        actual_severities = {getattr(issue, 'severity', None) for issue in actual_issues}
        all_severities = expected_severities | actual_severities
        
        for severity in all_severities:
            if severity is None:
                continue
                
            # Count matches for this severity
            severity_matches = [m for m in matches if m.expected_issue.get('severity') == severity]
            severity_expected = len([i for i in expected_issues if i.get('severity') == severity])
            severity_actual = len([i for i in actual_issues if getattr(i, 'severity', None) == severity])
            
            tp = sum(1 for m in severity_matches if m.match_type != MatchType.NO_MATCH)
            fp = severity_actual - tp
            fn = sum(1 for m in severity_matches if m.match_type == MatchType.NO_MATCH)
            
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
            
            severity_metrics[severity] = {
                'precision': precision,
                'recall': recall,
                'f1_score': f1,
                'true_positives': tp,
                'false_positives': fp,
                'false_negatives': fn,
                'expected_count': severity_expected,
                'actual_count': severity_actual
            }
        
        return severity_metrics
    
    def generate_accuracy_report(self, result: ValidationResult) -> str:
        """Generate a human-readable accuracy report."""
        report = []
        report.append("=== ACCURACY VALIDATION REPORT ===")
        report.append("")
        
        # Overall metrics
        report.append("Overall Metrics:")
        report.append(f"  Precision: {result.precision:.3f}")
        report.append(f"  Recall: {result.recall:.3f}")
        report.append(f"  F1-Score: {result.f1_score:.3f}")
        report.append(f"  Accuracy: {result.accuracy:.3f}")
        report.append("")
        
        # Confusion matrix
        report.append("Confusion Matrix:")
        report.append(f"  True Positives: {result.true_positives}")
        report.append(f"  False Positives: {result.false_positives}")
        report.append(f"  False Negatives: {result.false_negatives}")
        report.append(f"  Total Expected: {result.total_expected}")
        report.append(f"  Total Actual: {result.total_actual}")
        report.append("")
        
        # Category metrics
        if result.category_metrics:
            report.append("Category Metrics:")
            for category, metrics in result.category_metrics.items():
                report.append(f"  {category}:")
                report.append(f"    Precision: {metrics['precision']:.3f}")
                report.append(f"    Recall: {metrics['recall']:.3f}")
                report.append(f"    F1-Score: {metrics['f1_score']:.3f}")
                report.append(f"    Expected: {metrics['expected_count']}, Actual: {metrics['actual_count']}")
            report.append("")
        
        # Severity metrics
        if result.severity_metrics:
            report.append("Severity Metrics:")
            for severity, metrics in result.severity_metrics.items():
                report.append(f"  {severity}:")
                report.append(f"    Precision: {metrics['precision']:.3f}")
                report.append(f"    Recall: {metrics['recall']:.3f}")
                report.append(f"    F1-Score: {metrics['f1_score']:.3f}")
                report.append(f"    Expected: {metrics['expected_count']}, Actual: {metrics['actual_count']}")
            report.append("")
        
        # Match details
        exact_matches = sum(1 for m in result.matches if m.match_type == MatchType.EXACT_MATCH)
        partial_matches = sum(1 for m in result.matches if m.match_type == MatchType.PARTIAL_MATCH)
        no_matches = sum(1 for m in result.matches if m.match_type == MatchType.NO_MATCH)
        
        report.append("Match Distribution:")
        report.append(f"  Exact Matches: {exact_matches}")
        report.append(f"  Partial Matches: {partial_matches}")
        report.append(f"  No Matches: {no_matches}")
        
        return "\n".join(report)