"""Main scoring engine that orchestrates severity classification, contextual scoring, and business impact assessment."""

import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import json
from pathlib import Path

from .severity_classifier import SeverityClassifier, SeverityScore, SeverityLevel
from .contextual_scorer import ContextualScorer, ProjectContext, FileContext, CodeContext
from .business_impact_assessor import BusinessImpactAssessor, BusinessContext, BusinessImpactMetrics

logger = logging.getLogger(__name__)


@dataclass
class ComprehensiveScore:
    """Complete scoring result including all components."""
    severity_score: SeverityScore
    business_impact: float
    priority_score: float
    financial_estimates: Dict[str, float]
    recommendations: List[str]
    metadata: Dict[str, Any]


@dataclass
class ScoringConfiguration:
    """Configuration for the scoring engine."""
    enable_ml_classification: bool = True
    enable_contextual_adjustment: bool = True
    enable_business_impact: bool = True
    severity_model_path: Optional[str] = None
    confidence_threshold: float = 0.5
    priority_weights: Dict[str, float] = None
    
    def __post_init__(self):
        if self.priority_weights is None:
            self.priority_weights = {
                'severity': 0.6,
                'business_impact': 0.4
            }


class ScoringEngine:
    """Main engine for comprehensive code quality issue scoring."""
    
    def __init__(self, config: Optional[ScoringConfiguration] = None):
        """Initialize the scoring engine."""
        self.config = config or ScoringConfiguration()
        
        # Initialize components
        self.severity_classifier = SeverityClassifier(
            model_path=self.config.severity_model_path
        ) if self.config.enable_ml_classification else None
        
        self.contextual_scorer = ContextualScorer() if self.config.enable_contextual_adjustment else None
        
        self.business_impact_assessor = BusinessImpactAssessor() if self.config.enable_business_impact else None
        
        logger.info(f"Scoring engine initialized with config: {asdict(self.config)}")
    
    def score_issue(self, 
                   issue: Dict[str, Any],
                   context: Optional[Dict[str, Any]] = None) -> ComprehensiveScore:
        """Score a single code quality issue comprehensively."""
        
        try:
            # Extract context components
            project_context = None
            file_context = None
            code_context = None
            business_context = None
            impact_metrics = None
            
            if context:
                if 'project' in context and self.contextual_scorer:
                    project_context = self.contextual_scorer.create_project_context(context['project'])
                
                if 'file' in context and self.contextual_scorer:
                    file_context = self.contextual_scorer.create_file_context(context['file'])
                
                if 'code' in context and self.contextual_scorer:
                    code_context = self.contextual_scorer.create_code_context(context['code'])
                
                if 'business' in context and self.business_impact_assessor:
                    business_context = self.business_impact_assessor.create_business_context(context['business'])
                
                if 'impact_metrics' in context and self.business_impact_assessor:
                    impact_metrics = self.business_impact_assessor.create_impact_metrics(context['impact_metrics'])
            
            # Step 1: Base severity classification
            if self.severity_classifier:
                severity_score = self.severity_classifier.classify_severity(issue, context)
            else:
                # Fallback to simple rule-based scoring
                severity_score = self._fallback_severity_scoring(issue)
            
            # Step 2: Contextual adjustment
            if self.contextual_scorer and severity_score.confidence >= self.config.confidence_threshold:
                severity_score = self.contextual_scorer.adjust_severity(
                    severity_score, project_context, file_context, code_context
                )
            
            # Step 3: Business impact assessment
            business_impact = 0.5  # Default moderate impact
            financial_estimates = {}
            
            if self.business_impact_assessor:
                business_impact = self.business_impact_assessor.assess_business_impact(
                    severity_score, issue, business_context, impact_metrics
                )
                
                # Update severity score with business impact
                severity_score.business_impact = business_impact
                
                # Calculate financial estimates
                if business_context:
                    financial_estimates = self.business_impact_assessor.estimate_financial_impact(
                        business_impact, business_context, impact_metrics
                    )
            
            # Step 4: Calculate overall priority score
            priority_score = self._calculate_priority_score(severity_score, business_impact)
            
            # Step 5: Generate recommendations
            recommendations = self._generate_recommendations(
                issue, severity_score, business_impact, context
            )
            
            # Step 6: Compile metadata
            metadata = self._compile_metadata(
                issue, severity_score, business_impact, context
            )
            
            return ComprehensiveScore(
                severity_score=severity_score,
                business_impact=business_impact,
                priority_score=priority_score,
                financial_estimates=financial_estimates,
                recommendations=recommendations,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error scoring issue: {e}")
            # Return fallback score
            return self._create_fallback_score(issue)
    
    def score_issues_batch(self, 
                          issues: List[Dict[str, Any]],
                          contexts: Optional[List[Dict[str, Any]]] = None) -> List[ComprehensiveScore]:
        """Score multiple issues in batch."""
        
        if contexts is None:
            contexts = [{}] * len(issues)
        
        results = []
        for issue, context in zip(issues, contexts):
            score = self.score_issue(issue, context)
            results.append(score)
        
        return results
    
    def _fallback_severity_scoring(self, issue: Dict[str, Any]) -> SeverityScore:
        """Fallback severity scoring when ML classifier is not available."""
        
        category = issue.get('category', '').lower()
        description = issue.get('description', '').lower()
        
        # Simple rule-based scoring
        if 'security' in category or any(word in description for word in ['vulnerability', 'injection', 'xss']):
            level = SeverityLevel.HIGH
            base_score = 0.8
        elif 'performance' in category or any(word in description for word in ['slow', 'timeout', 'memory']):
            level = SeverityLevel.MEDIUM
            base_score = 0.6
        elif 'reliability' in category or any(word in description for word in ['crash', 'error', 'exception']):
            level = SeverityLevel.MEDIUM
            base_score = 0.6
        elif 'maintainability' in category or any(word in description for word in ['complex', 'duplicate']):
            level = SeverityLevel.LOW
            base_score = 0.4
        else:
            level = SeverityLevel.MEDIUM
            base_score = 0.5
        
        return SeverityScore(
            level=level,
            confidence=0.6,  # Lower confidence for rule-based scoring
            base_score=base_score,
            reasoning=[f"Rule-based classification: {category}"],
            context_adjustments={},
            business_impact=None
        )
    
    def _calculate_priority_score(self, severity_score: SeverityScore, business_impact: float) -> float:
        """Calculate overall priority score."""
        
        # Convert severity to numerical score
        severity_numerical = {
            SeverityLevel.CRITICAL: 1.0,
            SeverityLevel.HIGH: 0.8,
            SeverityLevel.MEDIUM: 0.6,
            SeverityLevel.LOW: 0.4,
            SeverityLevel.INFO: 0.2
        }.get(severity_score.level, 0.6)
        
        # Calculate weighted priority
        priority = (
            severity_numerical * self.config.priority_weights['severity'] +
            business_impact * self.config.priority_weights['business_impact']
        )
        
        # Apply confidence factor
        priority *= severity_score.confidence
        
        return priority
    
    def _generate_recommendations(self, 
                                issue: Dict[str, Any],
                                severity_score: SeverityScore,
                                business_impact: float,
                                context: Optional[Dict[str, Any]]) -> List[str]:
        """Generate actionable recommendations based on the scoring."""
        
        recommendations = []
        
        # Severity-based recommendations
        if severity_score.level == SeverityLevel.CRITICAL:
            recommendations.append("🚨 CRITICAL: Address immediately - halt deployment if necessary")
            recommendations.append("Assign senior developer and conduct code review")
            recommendations.append("Implement monitoring and alerting for this issue type")
        
        elif severity_score.level == SeverityLevel.HIGH:
            recommendations.append("⚠️ HIGH: Prioritize in current sprint")
            recommendations.append("Conduct thorough testing after fix")
            recommendations.append("Consider adding automated tests to prevent regression")
        
        elif severity_score.level == SeverityLevel.MEDIUM:
            recommendations.append("📋 MEDIUM: Include in next sprint planning")
            recommendations.append("Document the issue and potential impact")
        
        elif severity_score.level == SeverityLevel.LOW:
            recommendations.append("📝 LOW: Add to technical debt backlog")
            recommendations.append("Consider addressing during refactoring")
        
        # Business impact recommendations
        if business_impact > 0.8:
            recommendations.append("💰 High business impact - consider emergency fix")
            recommendations.append("Notify stakeholders and prepare communication plan")
        
        elif business_impact > 0.6:
            recommendations.append("📊 Significant business impact - track resolution metrics")
        
        # Context-specific recommendations
        if context:
            project_info = context.get('project', {})
            
            if project_info.get('security_sensitive'):
                recommendations.append("🔒 Security-sensitive project - involve security team")
            
            if project_info.get('public_facing'):
                recommendations.append("🌐 Public-facing application - consider user impact")
            
            if project_info.get('compliance_requirements'):
                recommendations.append("📋 Compliance requirements - document remediation")
        
        # Category-specific recommendations
        category = issue.get('category', '').lower()
        
        if 'security' in category:
            recommendations.append("🔐 Security issue - conduct security review")
            recommendations.append("Update security documentation and training")
        
        elif 'performance' in category:
            recommendations.append("⚡ Performance issue - benchmark before and after fix")
            recommendations.append("Consider load testing in staging environment")
        
        elif 'maintainability' in category:
            recommendations.append("🔧 Maintainability issue - improve code documentation")
            recommendations.append("Consider refactoring surrounding code")
        
        return recommendations
    
    def _compile_metadata(self, 
                         issue: Dict[str, Any],
                         severity_score: SeverityScore,
                         business_impact: float,
                         context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Compile metadata about the scoring process."""
        
        metadata = {
            'scoring_timestamp': None,  # Would be set to current timestamp in real implementation
            'scoring_version': '1.0.0',
            'components_used': {
                'ml_classifier': self.config.enable_ml_classification,
                'contextual_scorer': self.config.enable_contextual_adjustment,
                'business_impact': self.config.enable_business_impact
            },
            'confidence_factors': {
                'base_confidence': severity_score.confidence,
                'context_availability': bool(context),
                'feature_completeness': self._assess_feature_completeness(issue, context)
            },
            'scoring_factors': {
                'severity_level': severity_score.level.value,
                'business_impact_score': business_impact,
                'context_adjustments': severity_score.context_adjustments
            }
        }
        
        # Add context metadata if available
        if context:
            metadata['context_types'] = list(context.keys())
            
            if 'project' in context:
                metadata['project_type'] = context['project'].get('type')
                metadata['project_domain'] = context['project'].get('domain')
            
            if 'business' in context:
                metadata['industry'] = context['business'].get('industry')
                metadata['company_size'] = context['business'].get('company_size')
        
        return metadata
    
    def _assess_feature_completeness(self, issue: Dict[str, Any], context: Optional[Dict[str, Any]]) -> float:
        """Assess how complete the feature set is for scoring."""
        
        completeness_factors = []
        
        # Issue completeness
        required_fields = ['category', 'type', 'description', 'location']
        available_fields = sum(1 for field in required_fields if field in issue and issue[field])
        completeness_factors.append(available_fields / len(required_fields))
        
        # Context completeness
        if context:
            context_types = ['project', 'file', 'code', 'business']
            available_contexts = sum(1 for ctx_type in context_types if ctx_type in context)
            completeness_factors.append(available_contexts / len(context_types))
        else:
            completeness_factors.append(0.0)
        
        return sum(completeness_factors) / len(completeness_factors)
    
    def _create_fallback_score(self, issue: Dict[str, Any]) -> ComprehensiveScore:
        """Create a fallback score when scoring fails."""
        
        fallback_severity = SeverityScore(
            level=SeverityLevel.MEDIUM,
            confidence=0.3,
            base_score=0.5,
            reasoning=["Fallback scoring due to error"],
            context_adjustments={},
            business_impact=0.5
        )
        
        return ComprehensiveScore(
            severity_score=fallback_severity,
            business_impact=0.5,
            priority_score=0.5,
            financial_estimates={},
            recommendations=["⚠️ Scoring error - manual review recommended"],
            metadata={'error': True, 'fallback_used': True}
        )
    
    def get_scoring_statistics(self, scores: List[ComprehensiveScore]) -> Dict[str, Any]:
        """Get statistics about a batch of scores."""
        
        if not scores:
            return {}
        
        severity_counts = {}
        for score in scores:
            level = score.severity_score.level.value
            severity_counts[level] = severity_counts.get(level, 0) + 1
        
        business_impacts = [score.business_impact for score in scores]
        priority_scores = [score.priority_score for score in scores]
        confidences = [score.severity_score.confidence for score in scores]
        
        return {
            'total_issues': len(scores),
            'severity_distribution': severity_counts,
            'business_impact_stats': {
                'mean': sum(business_impacts) / len(business_impacts),
                'max': max(business_impacts),
                'min': min(business_impacts)
            },
            'priority_stats': {
                'mean': sum(priority_scores) / len(priority_scores),
                'max': max(priority_scores),
                'min': min(priority_scores)
            },
            'confidence_stats': {
                'mean': sum(confidences) / len(confidences),
                'max': max(confidences),
                'min': min(confidences)
            },
            'high_priority_count': sum(1 for score in scores if score.priority_score > 0.7),
            'low_confidence_count': sum(1 for score in scores if score.severity_score.confidence < 0.5)
        }
    
    def export_scores(self, scores: List[ComprehensiveScore], output_path: str):
        """Export scores to JSON file."""
        
        export_data = {
            'scores': [
                {
                    'severity': {
                        'level': score.severity_score.level.value,
                        'confidence': score.severity_score.confidence,
                        'base_score': score.severity_score.base_score,
                        'reasoning': score.severity_score.reasoning,
                        'context_adjustments': score.severity_score.context_adjustments
                    },
                    'business_impact': score.business_impact,
                    'priority_score': score.priority_score,
                    'financial_estimates': score.financial_estimates,
                    'recommendations': score.recommendations,
                    'metadata': score.metadata
                }
                for score in scores
            ],
            'statistics': self.get_scoring_statistics(scores),
            'configuration': asdict(self.config)
        }
        
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        logger.info(f"Exported {len(scores)} scores to {output_path}")
    
    def update_configuration(self, new_config: ScoringConfiguration):
        """Update the scoring engine configuration."""
        self.config = new_config
        
        # Reinitialize components if needed
        if new_config.enable_ml_classification and not self.severity_classifier:
            self.severity_classifier = SeverityClassifier(new_config.severity_model_path)
        elif not new_config.enable_ml_classification:
            self.severity_classifier = None
        
        if new_config.enable_contextual_adjustment and not self.contextual_scorer:
            self.contextual_scorer = ContextualScorer()
        elif not new_config.enable_contextual_adjustment:
            self.contextual_scorer = None
        
        if new_config.enable_business_impact and not self.business_impact_assessor:
            self.business_impact_assessor = BusinessImpactAssessor()
        elif not new_config.enable_business_impact:
            self.business_impact_assessor = None
        
        logger.info("Scoring engine configuration updated")