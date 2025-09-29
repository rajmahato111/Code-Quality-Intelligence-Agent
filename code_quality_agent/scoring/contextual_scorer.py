"""Contextual scoring algorithms that adjust severity based on project context."""

import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path
import re

from .severity_classifier import SeverityScore, SeverityLevel

logger = logging.getLogger(__name__)


@dataclass
class ProjectContext:
    """Context information about the project being analyzed."""
    project_type: str  # 'web_app', 'library', 'cli_tool', 'microservice', etc.
    framework: Optional[str]  # 'django', 'flask', 'react', 'express', etc.
    domain: Optional[str]  # 'fintech', 'healthcare', 'ecommerce', etc.
    team_size: Optional[int]
    project_maturity: str  # 'prototype', 'development', 'production'
    compliance_requirements: List[str]  # ['PCI', 'HIPAA', 'SOX', etc.]
    performance_critical: bool
    security_sensitive: bool
    public_facing: bool
    

@dataclass
class FileContext:
    """Context information about the specific file containing the issue."""
    file_role: str  # 'controller', 'model', 'view', 'utility', 'config', etc.
    is_entry_point: bool
    is_public_api: bool
    test_coverage: Optional[float]  # 0.0 to 1.0
    change_frequency: Optional[float]  # Changes per month
    bug_density: Optional[float]  # Bugs per KLOC
    dependencies: List[str]
    dependents: List[str]
    

@dataclass
class CodeContext:
    """Context information about the specific code location."""
    function_name: Optional[str]
    class_name: Optional[str]
    is_public_method: bool
    is_constructor: bool
    is_error_handler: bool
    execution_frequency: str  # 'rare', 'occasional', 'frequent', 'critical_path'
    user_facing: bool
    data_sensitive: bool
    

class ContextualScorer:
    """Adjusts severity scores based on project, file, and code context."""
    
    def __init__(self):
        """Initialize the contextual scorer."""
        self.project_type_multipliers = {
            'fintech_app': 1.3,
            'healthcare_app': 1.3,
            'security_tool': 1.4,
            'web_app': 1.1,
            'microservice': 1.2,
            'library': 1.0,
            'cli_tool': 0.9,
            'prototype': 0.7,
            'internal_tool': 0.8
        }
        
        self.domain_multipliers = {
            'fintech': 1.3,
            'healthcare': 1.3,
            'government': 1.2,
            'ecommerce': 1.1,
            'education': 1.0,
            'gaming': 0.9,
            'internal': 0.8
        }
        
        self.file_role_multipliers = {
            'authentication': 1.4,
            'authorization': 1.4,
            'payment': 1.5,
            'data_access': 1.3,
            'api_controller': 1.2,
            'security_config': 1.3,
            'main_entry': 1.2,
            'utility': 0.9,
            'test': 0.6,
            'documentation': 0.3
        }
    
    def adjust_severity(self, base_score: SeverityScore, 
                       project_context: Optional[ProjectContext] = None,
                       file_context: Optional[FileContext] = None,
                       code_context: Optional[CodeContext] = None) -> SeverityScore:
        """Adjust severity score based on contextual factors."""
        
        adjusted_score = base_score.base_score
        adjustments = {}
        reasoning = base_score.reasoning.copy()
        
        # Project-level adjustments
        if project_context:
            project_adjustment = self._calculate_project_adjustment(project_context)
            adjusted_score *= project_adjustment['multiplier']
            adjustments.update(project_adjustment['details'])
            reasoning.extend(project_adjustment['reasoning'])
        
        # File-level adjustments
        if file_context:
            file_adjustment = self._calculate_file_adjustment(file_context)
            adjusted_score *= file_adjustment['multiplier']
            adjustments.update(file_adjustment['details'])
            reasoning.extend(file_adjustment['reasoning'])
        
        # Code-level adjustments
        if code_context:
            code_adjustment = self._calculate_code_adjustment(code_context)
            adjusted_score *= code_adjustment['multiplier']
            adjustments.update(code_adjustment['details'])
            reasoning.extend(code_adjustment['reasoning'])
        
        # Clamp the adjusted score
        adjusted_score = max(0.0, min(1.0, adjusted_score))
        
        # Determine new severity level
        new_level = self._score_to_severity_level(adjusted_score)
        
        # Adjust confidence based on context availability
        confidence_adjustment = self._calculate_confidence_adjustment(
            project_context, file_context, code_context
        )
        new_confidence = min(1.0, base_score.confidence + confidence_adjustment)
        
        return SeverityScore(
            level=new_level,
            confidence=new_confidence,
            base_score=adjusted_score,
            reasoning=reasoning,
            context_adjustments=adjustments,
            business_impact=base_score.business_impact
        ) 
   
    def _calculate_project_adjustment(self, context: ProjectContext) -> Dict[str, Any]:
        """Calculate project-level severity adjustments."""
        multiplier = 1.0
        details = {}
        reasoning = []
        
        # Project type adjustment
        if context.project_type in self.project_type_multipliers:
            type_multiplier = self.project_type_multipliers[context.project_type]
            multiplier *= type_multiplier
            details['project_type'] = type_multiplier
            reasoning.append(f"Project type ({context.project_type}): {type_multiplier:.2f}x")
        
        # Domain adjustment
        if context.domain and context.domain in self.domain_multipliers:
            domain_multiplier = self.domain_multipliers[context.domain]
            multiplier *= domain_multiplier
            details['domain'] = domain_multiplier
            reasoning.append(f"Domain ({context.domain}): {domain_multiplier:.2f}x")
        
        # Security sensitivity
        if context.security_sensitive:
            security_multiplier = 1.2
            multiplier *= security_multiplier
            details['security_sensitive'] = security_multiplier
            reasoning.append(f"Security sensitive application: {security_multiplier:.2f}x")
        
        # Performance criticality
        if context.performance_critical:
            perf_multiplier = 1.15
            multiplier *= perf_multiplier
            details['performance_critical'] = perf_multiplier
            reasoning.append(f"Performance critical application: {perf_multiplier:.2f}x")
        
        # Public facing
        if context.public_facing:
            public_multiplier = 1.1
            multiplier *= public_multiplier
            details['public_facing'] = public_multiplier
            reasoning.append(f"Public facing application: {public_multiplier:.2f}x")
        
        # Compliance requirements
        if context.compliance_requirements:
            compliance_multiplier = 1.0 + (len(context.compliance_requirements) * 0.1)
            multiplier *= compliance_multiplier
            details['compliance'] = compliance_multiplier
            reasoning.append(f"Compliance requirements ({len(context.compliance_requirements)}): {compliance_multiplier:.2f}x")
        
        # Project maturity
        maturity_multipliers = {
            'prototype': 0.8,
            'development': 1.0,
            'production': 1.3
        }
        if context.project_maturity in maturity_multipliers:
            maturity_multiplier = maturity_multipliers[context.project_maturity]
            multiplier *= maturity_multiplier
            details['maturity'] = maturity_multiplier
            reasoning.append(f"Project maturity ({context.project_maturity}): {maturity_multiplier:.2f}x")
        
        return {
            'multiplier': multiplier,
            'details': details,
            'reasoning': reasoning
        }
    
    def _calculate_file_adjustment(self, context: FileContext) -> Dict[str, Any]:
        """Calculate file-level severity adjustments."""
        multiplier = 1.0
        details = {}
        reasoning = []
        
        # File role adjustment
        if context.file_role in self.file_role_multipliers:
            role_multiplier = self.file_role_multipliers[context.file_role]
            multiplier *= role_multiplier
            details['file_role'] = role_multiplier
            reasoning.append(f"File role ({context.file_role}): {role_multiplier:.2f}x")
        
        # Entry point adjustment
        if context.is_entry_point:
            entry_multiplier = 1.2
            multiplier *= entry_multiplier
            details['entry_point'] = entry_multiplier
            reasoning.append(f"Entry point file: {entry_multiplier:.2f}x")
        
        # Public API adjustment
        if context.is_public_api:
            api_multiplier = 1.15
            multiplier *= api_multiplier
            details['public_api'] = api_multiplier
            reasoning.append(f"Public API file: {api_multiplier:.2f}x")
        
        # Test coverage adjustment
        if context.test_coverage is not None:
            if context.test_coverage < 0.5:
                coverage_multiplier = 1.2
                multiplier *= coverage_multiplier
                details['low_coverage'] = coverage_multiplier
                reasoning.append(f"Low test coverage ({context.test_coverage:.1%}): {coverage_multiplier:.2f}x")
            elif context.test_coverage > 0.9:
                coverage_multiplier = 0.9
                multiplier *= coverage_multiplier
                details['high_coverage'] = coverage_multiplier
                reasoning.append(f"High test coverage ({context.test_coverage:.1%}): {coverage_multiplier:.2f}x")
        
        # Change frequency adjustment
        if context.change_frequency is not None:
            if context.change_frequency > 10:  # More than 10 changes per month
                change_multiplier = 1.1
                multiplier *= change_multiplier
                details['high_change_frequency'] = change_multiplier
                reasoning.append(f"High change frequency ({context.change_frequency:.1f}/month): {change_multiplier:.2f}x")
        
        # Bug density adjustment
        if context.bug_density is not None:
            if context.bug_density > 5:  # More than 5 bugs per KLOC
                bug_multiplier = 1.15
                multiplier *= bug_multiplier
                details['high_bug_density'] = bug_multiplier
                reasoning.append(f"High bug density ({context.bug_density:.1f}/KLOC): {bug_multiplier:.2f}x")
        
        # Dependency impact
        if len(context.dependents) > 10:
            dependency_multiplier = 1.1
            multiplier *= dependency_multiplier
            details['high_dependents'] = dependency_multiplier
            reasoning.append(f"Many dependents ({len(context.dependents)}): {dependency_multiplier:.2f}x")
        
        return {
            'multiplier': multiplier,
            'details': details,
            'reasoning': reasoning
        }
    
    def _calculate_code_adjustment(self, context: CodeContext) -> Dict[str, Any]:
        """Calculate code-level severity adjustments."""
        multiplier = 1.0
        details = {}
        reasoning = []
        
        # Public method adjustment
        if context.is_public_method:
            public_multiplier = 1.1
            multiplier *= public_multiplier
            details['public_method'] = public_multiplier
            reasoning.append(f"Public method: {public_multiplier:.2f}x")
        
        # Constructor adjustment
        if context.is_constructor:
            constructor_multiplier = 1.15
            multiplier *= constructor_multiplier
            details['constructor'] = constructor_multiplier
            reasoning.append(f"Constructor method: {constructor_multiplier:.2f}x")
        
        # Error handler adjustment
        if context.is_error_handler:
            error_multiplier = 1.2
            multiplier *= error_multiplier
            details['error_handler'] = error_multiplier
            reasoning.append(f"Error handler: {error_multiplier:.2f}x")
        
        # Execution frequency adjustment
        frequency_multipliers = {
            'critical_path': 1.3,
            'frequent': 1.2,
            'occasional': 1.0,
            'rare': 0.9
        }
        if context.execution_frequency in frequency_multipliers:
            freq_multiplier = frequency_multipliers[context.execution_frequency]
            multiplier *= freq_multiplier
            details['execution_frequency'] = freq_multiplier
            reasoning.append(f"Execution frequency ({context.execution_frequency}): {freq_multiplier:.2f}x")
        
        # User facing adjustment
        if context.user_facing:
            user_multiplier = 1.15
            multiplier *= user_multiplier
            details['user_facing'] = user_multiplier
            reasoning.append(f"User facing code: {user_multiplier:.2f}x")
        
        # Data sensitive adjustment
        if context.data_sensitive:
            data_multiplier = 1.2
            multiplier *= data_multiplier
            details['data_sensitive'] = data_multiplier
            reasoning.append(f"Data sensitive code: {data_multiplier:.2f}x")
        
        return {
            'multiplier': multiplier,
            'details': details,
            'reasoning': reasoning
        }
    
    def _calculate_confidence_adjustment(self, project_context: Optional[ProjectContext],
                                       file_context: Optional[FileContext],
                                       code_context: Optional[CodeContext]) -> float:
        """Calculate confidence adjustment based on available context."""
        adjustment = 0.0
        
        if project_context:
            adjustment += 0.1
        if file_context:
            adjustment += 0.1
        if code_context:
            adjustment += 0.1
        
        return adjustment
    
    def _score_to_severity_level(self, score: float) -> SeverityLevel:
        """Convert numerical score to severity level."""
        if score >= 0.9:
            return SeverityLevel.CRITICAL
        elif score >= 0.7:
            return SeverityLevel.HIGH
        elif score >= 0.5:
            return SeverityLevel.MEDIUM
        elif score >= 0.3:
            return SeverityLevel.LOW
        else:
            return SeverityLevel.INFO   
 
    def create_project_context(self, project_info: Dict[str, Any]) -> ProjectContext:
        """Create project context from project information."""
        return ProjectContext(
            project_type=project_info.get('type', 'unknown'),
            framework=project_info.get('framework'),
            domain=project_info.get('domain'),
            team_size=project_info.get('team_size'),
            project_maturity=project_info.get('maturity', 'development'),
            compliance_requirements=project_info.get('compliance_requirements', []),
            performance_critical=project_info.get('performance_critical', False),
            security_sensitive=project_info.get('security_sensitive', False),
            public_facing=project_info.get('public_facing', False)
        )
    
    def create_file_context(self, file_info: Dict[str, Any]) -> FileContext:
        """Create file context from file information."""
        return FileContext(
            file_role=file_info.get('role', 'unknown'),
            is_entry_point=file_info.get('is_entry_point', False),
            is_public_api=file_info.get('is_public_api', False),
            test_coverage=file_info.get('test_coverage'),
            change_frequency=file_info.get('change_frequency'),
            bug_density=file_info.get('bug_density'),
            dependencies=file_info.get('dependencies', []),
            dependents=file_info.get('dependents', [])
        )
    
    def create_code_context(self, code_info: Dict[str, Any]) -> CodeContext:
        """Create code context from code information."""
        return CodeContext(
            function_name=code_info.get('function_name'),
            class_name=code_info.get('class_name'),
            is_public_method=code_info.get('is_public_method', False),
            is_constructor=code_info.get('is_constructor', False),
            is_error_handler=code_info.get('is_error_handler', False),
            execution_frequency=code_info.get('execution_frequency', 'occasional'),
            user_facing=code_info.get('user_facing', False),
            data_sensitive=code_info.get('data_sensitive', False)
        )
    
    def get_adjustment_factors(self) -> Dict[str, Dict[str, float]]:
        """Get all adjustment factors for inspection."""
        return {
            'project_type_multipliers': self.project_type_multipliers,
            'domain_multipliers': self.domain_multipliers,
            'file_role_multipliers': self.file_role_multipliers
        }
    
    def update_adjustment_factors(self, factor_type: str, updates: Dict[str, float]):
        """Update adjustment factors."""
        if factor_type == 'project_type':
            self.project_type_multipliers.update(updates)
        elif factor_type == 'domain':
            self.domain_multipliers.update(updates)
        elif factor_type == 'file_role':
            self.file_role_multipliers.update(updates)
        else:
            raise ValueError(f"Unknown factor type: {factor_type}")
        
        logger.info(f"Updated {factor_type} adjustment factors: {updates}")