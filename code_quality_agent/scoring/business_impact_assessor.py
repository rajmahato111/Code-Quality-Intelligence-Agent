"""Business impact assessment for code quality issues."""

import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import math

from .severity_classifier import SeverityScore, SeverityLevel

logger = logging.getLogger(__name__)


class BusinessImpactCategory(Enum):
    """Categories of business impact."""
    REVENUE_LOSS = "revenue_loss"
    CUSTOMER_EXPERIENCE = "customer_experience"
    SECURITY_BREACH = "security_breach"
    COMPLIANCE_VIOLATION = "compliance_violation"
    OPERATIONAL_DISRUPTION = "operational_disruption"
    REPUTATION_DAMAGE = "reputation_damage"
    DEVELOPMENT_VELOCITY = "development_velocity"
    MAINTENANCE_COST = "maintenance_cost"


@dataclass
class BusinessImpactMetrics:
    """Metrics for assessing business impact."""
    # Financial metrics
    potential_revenue_loss: Optional[float] = None  # $ per incident
    cost_to_fix: Optional[float] = None  # $ to resolve
    downtime_cost_per_hour: Optional[float] = None  # $ per hour
    
    # User metrics
    affected_users: Optional[int] = None  # Number of users affected
    user_satisfaction_impact: Optional[float] = None  # -1.0 to 1.0
    churn_risk: Optional[float] = None  # 0.0 to 1.0
    
    # Operational metrics
    mean_time_to_detect: Optional[float] = None  # Hours
    mean_time_to_resolve: Optional[float] = None  # Hours
    incident_frequency: Optional[float] = None  # Per month
    
    # Development metrics
    development_velocity_impact: Optional[float] = None  # -1.0 to 1.0
    technical_debt_score: Optional[float] = None  # 0.0 to 1.0
    maintenance_burden: Optional[float] = None  # Hours per month


@dataclass
class BusinessContext:
    """Business context for impact assessment."""
    industry: str  # 'fintech', 'healthcare', 'retail', etc.
    company_size: str  # 'startup', 'small', 'medium', 'enterprise'
    revenue_model: str  # 'subscription', 'transaction', 'advertising', etc.
    customer_base_size: int
    average_revenue_per_user: Optional[float] = None
    compliance_requirements: List[str] = None
    uptime_sla: Optional[float] = None  # 0.99, 0.999, etc.
    brand_sensitivity: float = 0.5  # 0.0 to 1.0


class BusinessImpactAssessor:
    """Assesses business impact of code quality issues."""
    
    def __init__(self):
        """Initialize the business impact assessor."""
        self.industry_multipliers = {
            'fintech': 2.0,
            'healthcare': 1.8,
            'ecommerce': 1.5,
            'saas': 1.4,
            'gaming': 1.2,
            'media': 1.1,
            'internal': 0.8,
            'education': 0.9
        }
        
        self.company_size_multipliers = {
            'startup': 0.8,
            'small': 1.0,
            'medium': 1.2,
            'enterprise': 1.5
        }
        
        self.impact_category_weights = {
            BusinessImpactCategory.REVENUE_LOSS: 1.0,
            BusinessImpactCategory.SECURITY_BREACH: 0.9,
            BusinessImpactCategory.COMPLIANCE_VIOLATION: 0.8,
            BusinessImpactCategory.CUSTOMER_EXPERIENCE: 0.7,
            BusinessImpactCategory.OPERATIONAL_DISRUPTION: 0.6,
            BusinessImpactCategory.REPUTATION_DAMAGE: 0.5,
            BusinessImpactCategory.DEVELOPMENT_VELOCITY: 0.4,
            BusinessImpactCategory.MAINTENANCE_COST: 0.3
        }
    
    def assess_business_impact(self, 
                             severity_score: SeverityScore,
                             issue: Dict[str, Any],
                             business_context: Optional[BusinessContext] = None,
                             impact_metrics: Optional[BusinessImpactMetrics] = None) -> float:
        """Assess the business impact of a code quality issue."""
        
        try:
            # Determine impact categories for this issue
            impact_categories = self._identify_impact_categories(issue, severity_score)
            
            # Calculate base business impact
            base_impact = self._calculate_base_business_impact(
                severity_score, impact_categories, impact_metrics
            )
            
            # Apply business context adjustments
            if business_context:
                context_multiplier = self._calculate_context_multiplier(business_context)
                base_impact *= context_multiplier
            
            # Apply issue-specific adjustments
            issue_multiplier = self._calculate_issue_multiplier(issue, impact_categories)
            base_impact *= issue_multiplier
            
            # Normalize to 0.0-1.0 range
            final_impact = max(0.0, min(1.0, base_impact))
            
            logger.debug(f"Business impact calculated: {final_impact:.3f} for issue: {issue.get('type', 'unknown')}")
            
            return final_impact
            
        except Exception as e:
            logger.error(f"Error assessing business impact: {e}")
            # Return moderate impact as fallback
            return 0.5
    
    def _identify_impact_categories(self, issue: Dict[str, Any], 
                                  severity_score: SeverityScore) -> List[BusinessImpactCategory]:
        """Identify which business impact categories apply to this issue."""
        categories = []
        
        issue_type = issue.get('type', '').lower()
        issue_category = issue.get('category', '').lower()
        description = issue.get('description', '').lower()
        
        # Security-related impacts
        if ('security' in issue_category or 
            any(keyword in description for keyword in ['vulnerability', 'injection', 'xss', 'csrf', 'auth'])):
            categories.append(BusinessImpactCategory.SECURITY_BREACH)
            categories.append(BusinessImpactCategory.COMPLIANCE_VIOLATION)
            categories.append(BusinessImpactCategory.REPUTATION_DAMAGE)
        
        # Performance-related impacts
        if ('performance' in issue_category or 
            any(keyword in description for keyword in ['slow', 'timeout', 'memory', 'cpu', 'latency'])):
            categories.append(BusinessImpactCategory.CUSTOMER_EXPERIENCE)
            categories.append(BusinessImpactCategory.REVENUE_LOSS)
        
        # Reliability-related impacts
        if ('reliability' in issue_category or 
            any(keyword in description for keyword in ['crash', 'error', 'exception', 'failure'])):
            categories.append(BusinessImpactCategory.OPERATIONAL_DISRUPTION)
            categories.append(BusinessImpactCategory.CUSTOMER_EXPERIENCE)
        
        # Maintainability-related impacts
        if ('maintainability' in issue_category or 
            any(keyword in description for keyword in ['complex', 'duplicate', 'debt', 'refactor'])):
            categories.append(BusinessImpactCategory.DEVELOPMENT_VELOCITY)
            categories.append(BusinessImpactCategory.MAINTENANCE_COST)
        
        # High severity issues generally have broader impact
        if severity_score.level in [SeverityLevel.CRITICAL, SeverityLevel.HIGH]:
            if BusinessImpactCategory.REVENUE_LOSS not in categories:
                categories.append(BusinessImpactCategory.REVENUE_LOSS)
            if BusinessImpactCategory.CUSTOMER_EXPERIENCE not in categories:
                categories.append(BusinessImpactCategory.CUSTOMER_EXPERIENCE)
        
        # Ensure at least one category
        if not categories:
            categories.append(BusinessImpactCategory.MAINTENANCE_COST)
        
        return categories
    
    def _calculate_base_business_impact(self, 
                                      severity_score: SeverityScore,
                                      impact_categories: List[BusinessImpactCategory],
                                      impact_metrics: Optional[BusinessImpactMetrics]) -> float:
        """Calculate base business impact score."""
        
        # Start with severity-based impact
        severity_impact = {
            SeverityLevel.CRITICAL: 0.9,
            SeverityLevel.HIGH: 0.7,
            SeverityLevel.MEDIUM: 0.5,
            SeverityLevel.LOW: 0.3,
            SeverityLevel.INFO: 0.1
        }.get(severity_score.level, 0.5)
        
        # Weight by impact categories
        category_weight = sum(
            self.impact_category_weights[category] 
            for category in impact_categories
        ) / len(impact_categories) if impact_categories else 0.5
        
        base_impact = severity_impact * category_weight
        
        # Apply metrics-based adjustments if available
        if impact_metrics:
            metrics_multiplier = self._calculate_metrics_multiplier(impact_metrics, impact_categories)
            base_impact *= metrics_multiplier
        
        return base_impact
    
    def _calculate_metrics_multiplier(self, 
                                    metrics: BusinessImpactMetrics,
                                    impact_categories: List[BusinessImpactCategory]) -> float:
        """Calculate multiplier based on business metrics."""
        multiplier = 1.0
        
        # Revenue impact
        if (BusinessImpactCategory.REVENUE_LOSS in impact_categories and 
            metrics.potential_revenue_loss is not None):
            # Scale based on potential revenue loss
            if metrics.potential_revenue_loss > 100000:  # $100k+
                multiplier *= 1.5
            elif metrics.potential_revenue_loss > 10000:  # $10k+
                multiplier *= 1.3
            elif metrics.potential_revenue_loss > 1000:  # $1k+
                multiplier *= 1.1
        
        # User impact
        if (BusinessImpactCategory.CUSTOMER_EXPERIENCE in impact_categories and 
            metrics.affected_users is not None):
            # Scale based on number of affected users
            if metrics.affected_users > 10000:
                multiplier *= 1.4
            elif metrics.affected_users > 1000:
                multiplier *= 1.2
            elif metrics.affected_users > 100:
                multiplier *= 1.1
        
        # Operational impact
        if (BusinessImpactCategory.OPERATIONAL_DISRUPTION in impact_categories and 
            metrics.mean_time_to_resolve is not None):
            # Scale based on resolution time
            if metrics.mean_time_to_resolve > 24:  # More than 24 hours
                multiplier *= 1.3
            elif metrics.mean_time_to_resolve > 4:  # More than 4 hours
                multiplier *= 1.2
            elif metrics.mean_time_to_resolve > 1:  # More than 1 hour
                multiplier *= 1.1
        
        # Development velocity impact
        if (BusinessImpactCategory.DEVELOPMENT_VELOCITY in impact_categories and 
            metrics.development_velocity_impact is not None):
            # Scale based on velocity impact (negative values increase multiplier)
            velocity_impact = abs(metrics.development_velocity_impact)
            if velocity_impact > 0.5:
                multiplier *= 1.3
            elif velocity_impact > 0.2:
                multiplier *= 1.2
            elif velocity_impact > 0.1:
                multiplier *= 1.1
        
        return multiplier
    
    def _calculate_context_multiplier(self, context: BusinessContext) -> float:
        """Calculate multiplier based on business context."""
        multiplier = 1.0
        
        # Industry multiplier
        if context.industry in self.industry_multipliers:
            multiplier *= self.industry_multipliers[context.industry]
        
        # Company size multiplier
        if context.company_size in self.company_size_multipliers:
            multiplier *= self.company_size_multipliers[context.company_size]
        
        # Revenue model considerations
        if context.revenue_model == 'transaction':
            multiplier *= 1.2  # Transaction-based models are more sensitive to issues
        elif context.revenue_model == 'subscription':
            multiplier *= 1.1  # Subscription models care about retention
        
        # Customer base size
        if context.customer_base_size > 1000000:  # 1M+ customers
            multiplier *= 1.3
        elif context.customer_base_size > 100000:  # 100k+ customers
            multiplier *= 1.2
        elif context.customer_base_size > 10000:  # 10k+ customers
            multiplier *= 1.1
        
        # SLA requirements
        if context.uptime_sla is not None:
            if context.uptime_sla >= 0.999:  # 99.9%+ uptime
                multiplier *= 1.3
            elif context.uptime_sla >= 0.99:  # 99%+ uptime
                multiplier *= 1.2
            elif context.uptime_sla >= 0.95:  # 95%+ uptime
                multiplier *= 1.1
        
        # Brand sensitivity
        brand_multiplier = 1.0 + (context.brand_sensitivity * 0.3)
        multiplier *= brand_multiplier
        
        # Compliance requirements
        if context.compliance_requirements:
            compliance_multiplier = 1.0 + (len(context.compliance_requirements) * 0.1)
            multiplier *= compliance_multiplier
        
        return multiplier
    
    def _calculate_issue_multiplier(self, 
                                  issue: Dict[str, Any], 
                                  impact_categories: List[BusinessImpactCategory]) -> float:
        """Calculate multiplier based on specific issue characteristics."""
        multiplier = 1.0
        
        # Location-based adjustments
        location = issue.get('location', {})
        file_path = location.get('file_path', '')
        
        # Critical file paths
        critical_paths = [
            'auth', 'payment', 'security', 'api', 'controller',
            'main', 'index', 'app', 'server', 'config'
        ]
        
        if any(path in file_path.lower() for path in critical_paths):
            multiplier *= 1.2
        
        # Public-facing code
        if any(keyword in file_path.lower() for keyword in ['public', 'api', 'web', 'frontend']):
            multiplier *= 1.15
        
        # Database-related code
        if any(keyword in file_path.lower() for keyword in ['db', 'database', 'model', 'schema']):
            multiplier *= 1.1
        
        # Issue frequency/pattern
        if 'recurring' in issue.get('description', '').lower():
            multiplier *= 1.3
        
        if 'widespread' in issue.get('description', '').lower():
            multiplier *= 1.2
        
        return multiplier
    
    def create_business_context(self, context_info: Dict[str, Any]) -> BusinessContext:
        """Create business context from context information."""
        return BusinessContext(
            industry=context_info.get('industry', 'unknown'),
            company_size=context_info.get('company_size', 'medium'),
            revenue_model=context_info.get('revenue_model', 'unknown'),
            customer_base_size=context_info.get('customer_base_size', 1000),
            average_revenue_per_user=context_info.get('arpu'),
            compliance_requirements=context_info.get('compliance_requirements', []),
            uptime_sla=context_info.get('uptime_sla'),
            brand_sensitivity=context_info.get('brand_sensitivity', 0.5)
        )
    
    def create_impact_metrics(self, metrics_info: Dict[str, Any]) -> BusinessImpactMetrics:
        """Create impact metrics from metrics information."""
        return BusinessImpactMetrics(
            potential_revenue_loss=metrics_info.get('potential_revenue_loss'),
            cost_to_fix=metrics_info.get('cost_to_fix'),
            downtime_cost_per_hour=metrics_info.get('downtime_cost_per_hour'),
            affected_users=metrics_info.get('affected_users'),
            user_satisfaction_impact=metrics_info.get('user_satisfaction_impact'),
            churn_risk=metrics_info.get('churn_risk'),
            mean_time_to_detect=metrics_info.get('mean_time_to_detect'),
            mean_time_to_resolve=metrics_info.get('mean_time_to_resolve'),
            incident_frequency=metrics_info.get('incident_frequency'),
            development_velocity_impact=metrics_info.get('development_velocity_impact'),
            technical_debt_score=metrics_info.get('technical_debt_score'),
            maintenance_burden=metrics_info.get('maintenance_burden')
        )
    
    def get_impact_categories_for_issue(self, issue: Dict[str, Any], 
                                      severity_score: SeverityScore) -> List[BusinessImpactCategory]:
        """Get business impact categories for a specific issue."""
        return self._identify_impact_categories(issue, severity_score)
    
    def estimate_financial_impact(self, 
                                business_impact: float,
                                business_context: BusinessContext,
                                impact_metrics: Optional[BusinessImpactMetrics] = None) -> Dict[str, float]:
        """Estimate financial impact in monetary terms."""
        estimates = {}
        
        # Base financial impact calculation
        if business_context.average_revenue_per_user:
            # Estimate based on ARPU and customer base
            base_revenue_at_risk = (
                business_context.average_revenue_per_user * 
                business_context.customer_base_size * 
                business_impact * 0.01  # 1% of revenue at risk per 0.01 impact
            )
            estimates['revenue_at_risk'] = base_revenue_at_risk
        
        # Use specific metrics if available
        if impact_metrics:
            if impact_metrics.potential_revenue_loss:
                estimates['direct_revenue_loss'] = impact_metrics.potential_revenue_loss * business_impact
            
            if impact_metrics.cost_to_fix:
                estimates['remediation_cost'] = impact_metrics.cost_to_fix
            
            if impact_metrics.downtime_cost_per_hour and impact_metrics.mean_time_to_resolve:
                estimates['downtime_cost'] = (
                    impact_metrics.downtime_cost_per_hour * 
                    impact_metrics.mean_time_to_resolve * 
                    business_impact
                )
        
        return estimates
    
    def get_priority_score(self, severity_score: SeverityScore, business_impact: float) -> float:
        """Calculate overall priority score combining severity and business impact."""
        # Weight severity and business impact
        severity_weight = 0.6
        business_weight = 0.4
        
        # Convert severity to numerical score
        severity_numerical = {
            SeverityLevel.CRITICAL: 1.0,
            SeverityLevel.HIGH: 0.8,
            SeverityLevel.MEDIUM: 0.6,
            SeverityLevel.LOW: 0.4,
            SeverityLevel.INFO: 0.2
        }.get(severity_score.level, 0.6)
        
        # Calculate weighted priority
        priority = (severity_numerical * severity_weight) + (business_impact * business_weight)
        
        # Apply confidence factor
        priority *= severity_score.confidence
        
        return priority