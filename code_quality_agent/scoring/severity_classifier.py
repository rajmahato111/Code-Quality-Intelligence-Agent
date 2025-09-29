"""ML-based severity classification for code quality issues."""

import logging
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class SeverityLevel(Enum):
    """Severity levels for code quality issues."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class SeverityScore:
    """Represents a severity score with confidence and reasoning."""
    level: SeverityLevel
    confidence: float  # 0.0 to 1.0
    base_score: float  # Raw numerical score
    reasoning: List[str]  # Factors that influenced the score
    context_adjustments: Dict[str, float]  # Contextual adjustments applied
    business_impact: Optional[float] = None  # Business impact multiplier


@dataclass
class IssueFeatures:
    """Features extracted from a code quality issue for ML classification."""
    # Issue characteristics
    category: str
    issue_type: str
    description_length: int
    has_code_example: bool
    
    # Location features
    file_extension: str
    file_size_lines: int
    function_complexity: Optional[int]
    class_size: Optional[int]
    
    # Context features
    is_test_file: bool
    is_config_file: bool
    is_main_module: bool
    dependency_count: int
    
    # Security features
    involves_user_input: bool
    involves_network: bool
    involves_file_system: bool
    involves_database: bool
    
    # Performance features
    in_loop: bool
    recursive_call: bool
    memory_allocation: bool
    
    # Maintainability features
    code_duplication: bool
    missing_documentation: bool
    complex_logic: bool
    
    # Historical features
    file_change_frequency: Optional[float]
    bug_history: Optional[int]
    

class SeverityClassifier:
    """ML-based classifier for determining issue severity."""
    
    def __init__(self, model_path: Optional[str] = None):
        """Initialize the severity classifier."""
        self.model_path = model_path
        self.feature_weights = self._load_feature_weights()
        self.category_base_scores = self._load_category_base_scores()
        self.severity_thresholds = {
            SeverityLevel.CRITICAL: 0.9,
            SeverityLevel.HIGH: 0.7,
            SeverityLevel.MEDIUM: 0.5,
            SeverityLevel.LOW: 0.3,
            SeverityLevel.INFO: 0.0
        }
    
    def _load_feature_weights(self) -> Dict[str, float]:
        """Load feature weights for severity calculation."""
        # These weights are based on domain expertise and could be learned from data
        return {
            # Security features (high impact)
            'involves_user_input': 0.8,
            'involves_network': 0.7,
            'involves_database': 0.7,
            'involves_file_system': 0.6,
            
            # Performance features (medium-high impact)
            'in_loop': 0.6,
            'recursive_call': 0.5,
            'memory_allocation': 0.4,
            
            # Complexity features (medium impact)
            'function_complexity': 0.5,
            'class_size': 0.4,
            'complex_logic': 0.5,
            
            # Maintainability features (low-medium impact)
            'code_duplication': 0.3,
            'missing_documentation': 0.2,
            
            # Context features
            'is_main_module': 0.4,
            'is_test_file': -0.2,  # Issues in tests are generally less critical
            'is_config_file': 0.3,
            'dependency_count': 0.3,
            
            # File characteristics
            'file_size_lines': 0.2,
            'description_length': 0.1,
            'has_code_example': 0.1,
            
            # Historical features
            'file_change_frequency': 0.3,
            'bug_history': 0.4
        }
    
    def _load_category_base_scores(self) -> Dict[str, float]:
        """Load base severity scores for different issue categories."""
        return {
            'security': 0.8,      # Security issues start with high base score
            'performance': 0.6,   # Performance issues are medium-high
            'reliability': 0.7,   # Reliability issues are high
            'maintainability': 0.4, # Maintainability issues are medium
            'complexity': 0.5,    # Complexity issues are medium
            'duplication': 0.3,   # Duplication is lower priority
            'documentation': 0.2, # Documentation issues are low
            'style': 0.1,         # Style issues are lowest
            'testing': 0.4        # Testing issues are medium
        }
    
    def extract_features(self, issue: Dict[str, Any], context: Dict[str, Any] = None) -> IssueFeatures:
        """Extract features from an issue for classification."""
        if context is None:
            context = {}
        
        # Extract basic issue information
        category = issue.get('category', 'unknown').lower()
        issue_type = issue.get('type', 'unknown').lower()
        description = issue.get('description', '')
        
        # Extract location information
        location = issue.get('location', {})
        file_path = location.get('file_path', '')
        file_extension = Path(file_path).suffix.lower() if file_path else ''
        
        # Extract context information
        file_info = context.get('file_info', {})
        code_context = context.get('code_context', {})
        project_context = context.get('project_context', {})
        
        return IssueFeatures(
            # Issue characteristics
            category=category,
            issue_type=issue_type,
            description_length=len(description),
            has_code_example='```' in description or 'example' in description.lower(),
            
            # Location features
            file_extension=file_extension,
            file_size_lines=file_info.get('line_count', 0),
            function_complexity=code_context.get('function_complexity'),
            class_size=code_context.get('class_size'),
            
            # Context features
            is_test_file=self._is_test_file(file_path),
            is_config_file=self._is_config_file(file_path),
            is_main_module=self._is_main_module(file_path),
            dependency_count=project_context.get('dependency_count', 0),
            
            # Security features
            involves_user_input=self._involves_user_input(description, code_context),
            involves_network=self._involves_network(description, code_context),
            involves_file_system=self._involves_file_system(description, code_context),
            involves_database=self._involves_database(description, code_context),
            
            # Performance features
            in_loop=code_context.get('in_loop', False),
            recursive_call=code_context.get('recursive_call', False),
            memory_allocation=self._involves_memory_allocation(description, code_context),
            
            # Maintainability features
            code_duplication='duplication' in category or 'duplicate' in description.lower(),
            missing_documentation='documentation' in category or 'docstring' in description.lower(),
            complex_logic=code_context.get('cyclomatic_complexity', 0) > 10,
            
            # Historical features
            file_change_frequency=project_context.get('file_change_frequency'),
            bug_history=project_context.get('bug_history')
        )
    
    def _is_test_file(self, file_path: str) -> bool:
        """Check if file is a test file."""
        if not file_path:
            return False
        path_lower = file_path.lower()
        return (
            'test' in path_lower or
            'spec' in path_lower or
            file_path.startswith('tests/') or
            '/test' in path_lower
        )
    
    def _is_config_file(self, file_path: str) -> bool:
        """Check if file is a configuration file."""
        if not file_path:
            return False
        config_extensions = {'.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf'}
        config_names = {'config', 'settings', 'setup', 'requirements'}
        
        file_path_lower = file_path.lower()
        return (
            Path(file_path).suffix.lower() in config_extensions or
            any(name in file_path_lower for name in config_names)
        )
    
    def _is_main_module(self, file_path: str) -> bool:
        """Check if file is a main module."""
        if not file_path:
            return False
        file_name = Path(file_path).name.lower()
        return file_name in {'main.py', 'app.py', 'index.js', 'server.js', '__init__.py'}
    
    def _involves_user_input(self, description: str, code_context: Dict) -> bool:
        """Check if issue involves user input."""
        user_input_keywords = [
            'input', 'request', 'form', 'parameter', 'argument', 'user data',
            'stdin', 'argv', 'query', 'post', 'get', 'cookie', 'header'
        ]
        description_lower = description.lower()
        return any(keyword in description_lower for keyword in user_input_keywords)
    
    def _involves_network(self, description: str, code_context: Dict) -> bool:
        """Check if issue involves network operations."""
        network_keywords = [
            'http', 'https', 'url', 'request', 'response', 'api', 'socket',
            'network', 'connection', 'fetch', 'ajax', 'curl', 'download'
        ]
        description_lower = description.lower()
        return any(keyword in description_lower for keyword in network_keywords)
    
    def _involves_file_system(self, description: str, code_context: Dict) -> bool:
        """Check if issue involves file system operations."""
        file_keywords = [
            'file', 'path', 'directory', 'folder', 'read', 'write', 'open',
            'save', 'load', 'upload', 'download', 'filesystem', 'disk'
        ]
        description_lower = description.lower()
        return any(keyword in description_lower for keyword in file_keywords)
    
    def _involves_database(self, description: str, code_context: Dict) -> bool:
        """Check if issue involves database operations."""
        db_keywords = [
            'sql', 'database', 'query', 'select', 'insert', 'update', 'delete',
            'table', 'schema', 'orm', 'mongodb', 'postgres', 'mysql', 'sqlite'
        ]
        description_lower = description.lower()
        return any(keyword in description_lower for keyword in db_keywords)
    
    def _involves_memory_allocation(self, description: str, code_context: Dict) -> bool:
        """Check if issue involves memory allocation."""
        memory_keywords = [
            'memory', 'allocation', 'malloc', 'new', 'array', 'list',
            'buffer', 'cache', 'heap', 'stack', 'leak'
        ]
        description_lower = description.lower()
        return any(keyword in description_lower for keyword in memory_keywords)
    
    def calculate_base_score(self, features: IssueFeatures) -> Tuple[float, List[str]]:
        """Calculate base severity score from features."""
        reasoning = []
        
        # Start with category base score
        base_score = self.category_base_scores.get(features.category, 0.5)
        reasoning.append(f"Base score for {features.category}: {base_score:.2f}")
        
        # Apply feature weights
        feature_adjustments = 0.0
        
        # Security features (high impact)
        if features.involves_user_input:
            adjustment = self.feature_weights['involves_user_input']
            feature_adjustments += adjustment
            reasoning.append(f"Involves user input: +{adjustment:.2f}")
        
        if features.involves_network:
            adjustment = self.feature_weights['involves_network']
            feature_adjustments += adjustment
            reasoning.append(f"Involves network operations: +{adjustment:.2f}")
        
        if features.involves_database:
            adjustment = self.feature_weights['involves_database']
            feature_adjustments += adjustment
            reasoning.append(f"Involves database operations: +{adjustment:.2f}")
        
        if features.involves_file_system:
            adjustment = self.feature_weights['involves_file_system']
            feature_adjustments += adjustment
            reasoning.append(f"Involves file system: +{adjustment:.2f}")
        
        # Performance features
        if features.in_loop:
            adjustment = self.feature_weights['in_loop']
            feature_adjustments += adjustment
            reasoning.append(f"Issue in loop context: +{adjustment:.2f}")
        
        if features.recursive_call:
            adjustment = self.feature_weights['recursive_call']
            feature_adjustments += adjustment
            reasoning.append(f"Involves recursive calls: +{adjustment:.2f}")
        
        if features.memory_allocation:
            adjustment = self.feature_weights['memory_allocation']
            feature_adjustments += adjustment
            reasoning.append(f"Involves memory allocation: +{adjustment:.2f}")
        
        # Complexity features
        if features.function_complexity and features.function_complexity > 10:
            adjustment = self.feature_weights['function_complexity'] * min(features.function_complexity / 20, 1.0)
            feature_adjustments += adjustment
            reasoning.append(f"High function complexity ({features.function_complexity}): +{adjustment:.2f}")
        
        if features.complex_logic:
            adjustment = self.feature_weights['complex_logic']
            feature_adjustments += adjustment
            reasoning.append(f"Complex logic detected: +{adjustment:.2f}")
        
        # Context adjustments
        if features.is_main_module:
            adjustment = self.feature_weights['is_main_module']
            feature_adjustments += adjustment
            reasoning.append(f"Issue in main module: +{adjustment:.2f}")
        
        if features.is_test_file:
            adjustment = self.feature_weights['is_test_file']
            feature_adjustments += adjustment
            reasoning.append(f"Issue in test file: {adjustment:.2f}")
        
        # File size impact
        if features.file_size_lines > 500:
            adjustment = self.feature_weights['file_size_lines'] * min(features.file_size_lines / 1000, 1.0)
            feature_adjustments += adjustment
            reasoning.append(f"Large file ({features.file_size_lines} lines): +{adjustment:.2f}")
        
        # Historical factors
        if features.bug_history and features.bug_history > 0:
            adjustment = self.feature_weights['bug_history'] * min(features.bug_history / 10, 1.0)
            feature_adjustments += adjustment
            reasoning.append(f"File has bug history ({features.bug_history}): +{adjustment:.2f}")
        
        # Calculate final score
        final_score = base_score + feature_adjustments
        final_score = max(0.0, min(1.0, final_score))  # Clamp to [0, 1]
        
        reasoning.append(f"Final base score: {final_score:.2f}")
        
        return final_score, reasoning
    
    def classify_severity(self, issue: Dict[str, Any], context: Dict[str, Any] = None) -> SeverityScore:
        """Classify the severity of a code quality issue."""
        try:
            # Extract features
            features = self.extract_features(issue, context)
            
            # Calculate base score
            base_score, reasoning = self.calculate_base_score(features)
            
            # Determine severity level
            severity_level = self._score_to_severity_level(base_score)
            
            # Calculate confidence based on feature availability
            confidence = self._calculate_confidence(features)
            
            return SeverityScore(
                level=severity_level,
                confidence=confidence,
                base_score=base_score,
                reasoning=reasoning,
                context_adjustments={},  # Will be filled by contextual scorer
                business_impact=None     # Will be filled by business impact assessor
            )
        
        except Exception as e:
            logger.error(f"Error classifying severity: {e}")
            # Return default medium severity with low confidence
            return SeverityScore(
                level=SeverityLevel.MEDIUM,
                confidence=0.3,
                base_score=0.5,
                reasoning=[f"Error in classification: {str(e)}"],
                context_adjustments={},
                business_impact=None
            )
    
    def _score_to_severity_level(self, score: float) -> SeverityLevel:
        """Convert numerical score to severity level."""
        if score >= self.severity_thresholds[SeverityLevel.CRITICAL]:
            return SeverityLevel.CRITICAL
        elif score >= self.severity_thresholds[SeverityLevel.HIGH]:
            return SeverityLevel.HIGH
        elif score >= self.severity_thresholds[SeverityLevel.MEDIUM]:
            return SeverityLevel.MEDIUM
        elif score >= self.severity_thresholds[SeverityLevel.LOW]:
            return SeverityLevel.LOW
        else:
            return SeverityLevel.INFO
    
    def _calculate_confidence(self, features: IssueFeatures) -> float:
        """Calculate confidence in the severity classification."""
        confidence_factors = []
        
        # Category confidence
        if features.category in self.category_base_scores:
            confidence_factors.append(0.8)
        else:
            confidence_factors.append(0.4)
        
        # Feature availability confidence
        available_features = 0
        total_features = 0
        
        feature_checks = [
            features.involves_user_input,
            features.involves_network,
            features.involves_database,
            features.involves_file_system,
            features.in_loop,
            features.recursive_call,
            features.memory_allocation,
            features.complex_logic,
            features.is_main_module,
            features.is_test_file
        ]
        
        for check in feature_checks:
            total_features += 1
            if check:
                available_features += 1
        
        feature_confidence = available_features / total_features if total_features > 0 else 0.5
        confidence_factors.append(feature_confidence)
        
        # Context confidence
        if features.function_complexity is not None:
            confidence_factors.append(0.9)
        else:
            confidence_factors.append(0.6)
        
        # Calculate overall confidence
        return sum(confidence_factors) / len(confidence_factors)
    
    def batch_classify(self, issues: List[Dict[str, Any]], contexts: List[Dict[str, Any]] = None) -> List[SeverityScore]:
        """Classify severity for multiple issues."""
        if contexts is None:
            contexts = [{}] * len(issues)
        
        results = []
        for issue, context in zip(issues, contexts):
            score = self.classify_severity(issue, context)
            results.append(score)
        
        return results
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance weights."""
        return self.feature_weights.copy()
    
    def update_feature_weights(self, new_weights: Dict[str, float]):
        """Update feature weights (for model training/tuning)."""
        self.feature_weights.update(new_weights)
        logger.info(f"Updated {len(new_weights)} feature weights")
    
    def save_model(self, path: str):
        """Save the current model configuration."""
        model_data = {
            'feature_weights': self.feature_weights,
            'category_base_scores': self.category_base_scores,
            'severity_thresholds': {k.value: v for k, v in self.severity_thresholds.items()}
        }
        
        with open(path, 'w') as f:
            json.dump(model_data, f, indent=2)
        
        logger.info(f"Model saved to {path}")
    
    def load_model(self, path: str):
        """Load model configuration from file."""
        try:
            with open(path, 'r') as f:
                model_data = json.load(f)
            
            self.feature_weights = model_data.get('feature_weights', self.feature_weights)
            self.category_base_scores = model_data.get('category_base_scores', self.category_base_scores)
            
            # Convert severity thresholds back to enum keys
            thresholds = model_data.get('severity_thresholds', {})
            self.severity_thresholds = {
                SeverityLevel(k): v for k, v in thresholds.items()
            }
            
            logger.info(f"Model loaded from {path}")
        
        except Exception as e:
            logger.error(f"Error loading model from {path}: {e}")
            raise