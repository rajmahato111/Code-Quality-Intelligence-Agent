"""
Regression tester for validating analysis consistency across codebase versions.
"""

import json
import hashlib
import logging
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime
import pickle

logger = logging.getLogger(__name__)


@dataclass
class AnalysisSnapshot:
    """Represents a snapshot of analysis results."""
    timestamp: datetime
    codebase_hash: str
    version: str
    total_files: int
    total_issues: int
    issues_by_category: Dict[str, int]
    issues_by_severity: Dict[str, int]
    overall_score: float
    detailed_issues: List[Dict]


@dataclass
class RegressionResult:
    """Results of regression testing."""
    baseline_snapshot: AnalysisSnapshot
    current_snapshot: AnalysisSnapshot
    issues_added: List[Dict]
    issues_removed: List[Dict]
    issues_changed: List[Dict]
    score_change: float
    category_changes: Dict[str, int]
    severity_changes: Dict[str, int]
    regression_detected: bool
    improvement_detected: bool


class RegressionTester:
    """Tests for regressions in analysis results across codebase versions."""
    
    def __init__(self, snapshots_dir: Optional[str] = None):
        """
        Initialize regression tester.
        
        Args:
            snapshots_dir: Directory to store analysis snapshots
        """
        self.snapshots_dir = Path(snapshots_dir) if snapshots_dir else Path.home() / ".code_quality_agent" / "snapshots"
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)
    
    def create_snapshot(
        self, 
        codebase_path: str, 
        analysis_result, 
        version: str = "unknown"
    ) -> AnalysisSnapshot:
        """
        Create a snapshot of analysis results.
        
        Args:
            codebase_path: Path to the analyzed codebase
            analysis_result: AnalysisResult object
            version: Version identifier for the codebase
            
        Returns:
            AnalysisSnapshot object
        """
        # Calculate codebase hash
        codebase_hash = self._calculate_codebase_hash(codebase_path)
        
        # Extract issue details
        detailed_issues = []
        issues_by_category = {}
        issues_by_severity = {}
        
        for issue in analysis_result.issues:
            issue_dict = {
                'category': issue.category.value if hasattr(issue.category, 'value') else str(issue.category),
                'severity': issue.severity.value if hasattr(issue.severity, 'value') else str(issue.severity),
                'type': getattr(issue, 'type', 'unknown'),
                'description': issue.description,
                'file_path': issue.location.file_path if issue.location else None,
                'line_number': issue.location.line_start if issue.location else None,
            }
            detailed_issues.append(issue_dict)
            
            # Count by category
            category = issue.category.value if hasattr(issue.category, 'value') else str(issue.category)
            issues_by_category[category] = issues_by_category.get(category, 0) + 1
            
            # Count by severity
            severity = issue.severity.value if hasattr(issue.severity, 'value') else str(issue.severity)
            issues_by_severity[severity] = issues_by_severity.get(severity, 0) + 1
        
        snapshot = AnalysisSnapshot(
            timestamp=datetime.now(),
            codebase_hash=codebase_hash,
            version=version,
            total_files=len(analysis_result.parsed_files),
            total_issues=len(analysis_result.issues),
            issues_by_category=issues_by_category,
            issues_by_severity=issues_by_severity,
            overall_score=analysis_result.metrics.overall_score if analysis_result.metrics else 0.0,
            detailed_issues=detailed_issues
        )
        
        # Save snapshot
        self._save_snapshot(snapshot, codebase_path)
        
        return snapshot
    
    def _calculate_codebase_hash(self, codebase_path: str) -> str:
        """Calculate a hash of the codebase content."""
        hasher = hashlib.sha256()
        
        codebase_dir = Path(codebase_path)
        
        # Get all relevant files sorted for consistent hashing
        files = []
        for pattern in ['*.py', '*.js', '*.ts', '*.java', '*.cpp', '*.c', '*.cs']:
            files.extend(codebase_dir.rglob(pattern))
        
        files = sorted(files)
        
        for file_path in files:
            try:
                with open(file_path, 'rb') as f:
                    hasher.update(f.read())
                # Include file path in hash for structure changes
                hasher.update(str(file_path.relative_to(codebase_dir)).encode())
            except Exception as e:
                logger.warning(f"Could not hash file {file_path}: {e}")
        
        return hasher.hexdigest()
    
    def _save_snapshot(self, snapshot: AnalysisSnapshot, codebase_path: str):
        """Save snapshot to disk."""
        # Create filename based on codebase path and timestamp
        codebase_name = Path(codebase_path).name
        timestamp_str = snapshot.timestamp.strftime("%Y%m%d_%H%M%S")
        filename = f"{codebase_name}_{timestamp_str}_{snapshot.version}.json"
        
        snapshot_file = self.snapshots_dir / filename
        
        try:
            with open(snapshot_file, 'w') as f:
                # Convert snapshot to dict for JSON serialization
                snapshot_dict = asdict(snapshot)
                snapshot_dict['timestamp'] = snapshot.timestamp.isoformat()
                json.dump(snapshot_dict, f, indent=2)
            
            logger.info(f"Saved snapshot to {snapshot_file}")
        except Exception as e:
            logger.error(f"Failed to save snapshot: {e}")
    
    def load_snapshot(self, snapshot_file: str) -> Optional[AnalysisSnapshot]:
        """Load snapshot from file."""
        try:
            with open(snapshot_file, 'r') as f:
                data = json.load(f)
            
            # Convert timestamp back from ISO format
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
            
            return AnalysisSnapshot(**data)
        except Exception as e:
            logger.error(f"Failed to load snapshot from {snapshot_file}: {e}")
            return None
    
    def find_baseline_snapshot(self, codebase_path: str, version: Optional[str] = None) -> Optional[AnalysisSnapshot]:
        """
        Find the most appropriate baseline snapshot for comparison.
        
        Args:
            codebase_path: Path to the codebase
            version: Specific version to look for, or None for latest
            
        Returns:
            Baseline snapshot or None if not found
        """
        codebase_name = Path(codebase_path).name
        
        # Find all snapshots for this codebase
        pattern = f"{codebase_name}_*.json"
        snapshot_files = list(self.snapshots_dir.glob(pattern))
        
        if not snapshot_files:
            return None
        
        # Load all snapshots
        snapshots = []
        for file_path in snapshot_files:
            snapshot = self.load_snapshot(file_path)
            if snapshot:
                snapshots.append(snapshot)
        
        if not snapshots:
            return None
        
        # Filter by version if specified
        if version:
            version_snapshots = [s for s in snapshots if s.version == version]
            if version_snapshots:
                snapshots = version_snapshots
        
        # Return the most recent snapshot
        return max(snapshots, key=lambda s: s.timestamp)
    
    def compare_snapshots(
        self, 
        baseline: AnalysisSnapshot, 
        current: AnalysisSnapshot
    ) -> RegressionResult:
        """
        Compare two snapshots to detect regressions or improvements.
        
        Args:
            baseline: Baseline snapshot for comparison
            current: Current snapshot
            
        Returns:
            RegressionResult with detailed comparison
        """
        # Find issue differences
        issues_added, issues_removed, issues_changed = self._compare_issues(
            baseline.detailed_issues, 
            current.detailed_issues
        )
        
        # Calculate score change
        score_change = current.overall_score - baseline.overall_score
        
        # Calculate category changes
        category_changes = {}
        all_categories = set(baseline.issues_by_category.keys()) | set(current.issues_by_category.keys())
        for category in all_categories:
            baseline_count = baseline.issues_by_category.get(category, 0)
            current_count = current.issues_by_category.get(category, 0)
            category_changes[category] = current_count - baseline_count
        
        # Calculate severity changes
        severity_changes = {}
        all_severities = set(baseline.issues_by_severity.keys()) | set(current.issues_by_severity.keys())
        for severity in all_severities:
            baseline_count = baseline.issues_by_severity.get(severity, 0)
            current_count = current.issues_by_severity.get(severity, 0)
            severity_changes[severity] = current_count - baseline_count
        
        # Detect regression or improvement
        regression_detected = self._detect_regression(baseline, current, issues_added, score_change)
        improvement_detected = self._detect_improvement(baseline, current, issues_removed, score_change)
        
        return RegressionResult(
            baseline_snapshot=baseline,
            current_snapshot=current,
            issues_added=issues_added,
            issues_removed=issues_removed,
            issues_changed=issues_changed,
            score_change=score_change,
            category_changes=category_changes,
            severity_changes=severity_changes,
            regression_detected=regression_detected,
            improvement_detected=improvement_detected
        )
    
    def _compare_issues(
        self, 
        baseline_issues: List[Dict], 
        current_issues: List[Dict]
    ) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """Compare issues between two snapshots."""
        # Create issue signatures for comparison
        baseline_signatures = {self._create_issue_signature(issue): issue for issue in baseline_issues}
        current_signatures = {self._create_issue_signature(issue): issue for issue in current_issues}
        
        # Find added, removed, and changed issues
        baseline_sigs = set(baseline_signatures.keys())
        current_sigs = set(current_signatures.keys())
        
        added_sigs = current_sigs - baseline_sigs
        removed_sigs = baseline_sigs - current_sigs
        common_sigs = baseline_sigs & current_sigs
        
        issues_added = [current_signatures[sig] for sig in added_sigs]
        issues_removed = [baseline_signatures[sig] for sig in removed_sigs]
        
        # Check for changes in common issues
        issues_changed = []
        for sig in common_sigs:
            baseline_issue = baseline_signatures[sig]
            current_issue = current_signatures[sig]
            
            if self._issues_differ(baseline_issue, current_issue):
                issues_changed.append({
                    'baseline': baseline_issue,
                    'current': current_issue,
                    'changes': self._get_issue_changes(baseline_issue, current_issue)
                })
        
        return issues_added, issues_removed, issues_changed
    
    def _create_issue_signature(self, issue: Dict) -> str:
        """Create a unique signature for an issue."""
        # Use category, type, file path, and line number for signature
        signature_parts = [
            issue.get('category', ''),
            issue.get('type', ''),
            issue.get('file_path', ''),
            str(issue.get('line_number', 0))
        ]
        return '|'.join(signature_parts)
    
    def _issues_differ(self, issue1: Dict, issue2: Dict) -> bool:
        """Check if two issues differ in important ways."""
        # Compare severity and description
        return (
            issue1.get('severity') != issue2.get('severity') or
            issue1.get('description') != issue2.get('description')
        )
    
    def _get_issue_changes(self, baseline_issue: Dict, current_issue: Dict) -> Dict[str, Tuple]:
        """Get specific changes between two issues."""
        changes = {}
        
        for key in ['severity', 'description']:
            baseline_value = baseline_issue.get(key)
            current_value = current_issue.get(key)
            
            if baseline_value != current_value:
                changes[key] = (baseline_value, current_value)
        
        return changes
    
    def _detect_regression(
        self, 
        baseline: AnalysisSnapshot, 
        current: AnalysisSnapshot, 
        issues_added: List[Dict], 
        score_change: float
    ) -> bool:
        """Detect if there's a regression in code quality."""
        # Regression indicators:
        # 1. Significant score decrease
        # 2. New critical or high severity issues
        # 3. Significant increase in total issues
        
        # Score regression
        if score_change < -5.0:  # 5 point decrease
            return True
        
        # New critical issues
        critical_added = sum(1 for issue in issues_added if issue.get('severity') == 'critical')
        if critical_added > 0:
            return True
        
        # New high severity issues
        high_added = sum(1 for issue in issues_added if issue.get('severity') == 'high')
        if high_added > 2:  # More than 2 new high severity issues
            return True
        
        # Significant increase in total issues
        issue_increase = current.total_issues - baseline.total_issues
        if issue_increase > max(5, baseline.total_issues * 0.2):  # 20% increase or 5 issues
            return True
        
        return False
    
    def _detect_improvement(
        self, 
        baseline: AnalysisSnapshot, 
        current: AnalysisSnapshot, 
        issues_removed: List[Dict], 
        score_change: float
    ) -> bool:
        """Detect if there's an improvement in code quality."""
        # Improvement indicators:
        # 1. Significant score increase
        # 2. Removal of critical or high severity issues
        # 3. Significant decrease in total issues
        
        # Score improvement
        if score_change > 5.0:  # 5 point increase
            return True
        
        # Removed critical issues
        critical_removed = sum(1 for issue in issues_removed if issue.get('severity') == 'critical')
        if critical_removed > 0:
            return True
        
        # Removed high severity issues
        high_removed = sum(1 for issue in issues_removed if issue.get('severity') == 'high')
        if high_removed > 1:
            return True
        
        # Significant decrease in total issues
        issue_decrease = baseline.total_issues - current.total_issues
        if issue_decrease > max(3, baseline.total_issues * 0.15):  # 15% decrease or 3 issues
            return True
        
        return False
    
    def generate_regression_report(self, result: RegressionResult) -> str:
        """Generate a regression testing report."""
        report = []
        report.append("=== REGRESSION TESTING REPORT ===")
        report.append("")
        
        # Basic comparison
        report.append("Snapshot Comparison:")
        report.append(f"  Baseline: {result.baseline_snapshot.version} ({result.baseline_snapshot.timestamp.strftime('%Y-%m-%d %H:%M')})")
        report.append(f"  Current:  {result.current_snapshot.version} ({result.current_snapshot.timestamp.strftime('%Y-%m-%d %H:%M')})")
        report.append("")
        
        # Overall changes
        report.append("Overall Changes:")
        report.append(f"  Score Change: {result.score_change:+.2f}")
        report.append(f"  Issues Added: {len(result.issues_added)}")
        report.append(f"  Issues Removed: {len(result.issues_removed)}")
        report.append(f"  Issues Changed: {len(result.issues_changed)}")
        report.append("")
        
        # Regression/Improvement detection
        if result.regression_detected:
            report.append("🔴 REGRESSION DETECTED")
        elif result.improvement_detected:
            report.append("🟢 IMPROVEMENT DETECTED")
        else:
            report.append("⚪ NO SIGNIFICANT CHANGE")
        report.append("")
        
        # Category changes
        if result.category_changes:
            report.append("Changes by Category:")
            for category, change in result.category_changes.items():
                if change != 0:
                    report.append(f"  {category}: {change:+d}")
            report.append("")
        
        # Severity changes
        if result.severity_changes:
            report.append("Changes by Severity:")
            for severity, change in result.severity_changes.items():
                if change != 0:
                    report.append(f"  {severity}: {change:+d}")
            report.append("")
        
        # New issues details
        if result.issues_added:
            report.append("New Issues:")
            for issue in result.issues_added[:10]:  # Show first 10
                report.append(f"  + [{issue.get('severity', 'unknown')}] {issue.get('category', 'unknown')}: {issue.get('description', 'No description')}")
            if len(result.issues_added) > 10:
                report.append(f"  ... and {len(result.issues_added) - 10} more")
            report.append("")
        
        # Removed issues details
        if result.issues_removed:
            report.append("Removed Issues:")
            for issue in result.issues_removed[:10]:  # Show first 10
                report.append(f"  - [{issue.get('severity', 'unknown')}] {issue.get('category', 'unknown')}: {issue.get('description', 'No description')}")
            if len(result.issues_removed) > 10:
                report.append(f"  ... and {len(result.issues_removed) - 10} more")
            report.append("")
        
        return "\n".join(report)