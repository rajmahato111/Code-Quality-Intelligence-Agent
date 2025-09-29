"""
Explanation validator for assessing the quality of issue explanations and suggestions.
"""

import re
import logging
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ExplanationQuality(Enum):
    """Quality levels for explanations."""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


@dataclass
class ExplanationAssessment:
    """Assessment of an explanation's quality."""
    issue_id: str
    explanation_text: str
    suggestion_text: str
    quality_score: float
    quality_level: ExplanationQuality
    strengths: List[str]
    weaknesses: List[str]
    missing_elements: List[str]
    readability_score: float
    completeness_score: float
    actionability_score: float


class ExplanationValidator:
    """Validates the quality of issue explanations and suggestions."""
    
    def __init__(self):
        """Initialize explanation validator."""
        # Keywords that indicate good explanations
        self.positive_indicators = {
            'technical_accuracy': [
                'vulnerability', 'security risk', 'performance impact', 'memory leak',
                'algorithm complexity', 'best practice', 'code smell', 'anti-pattern'
            ],
            'clarity': [
                'because', 'due to', 'results in', 'leads to', 'causes', 'means that',
                'for example', 'specifically', 'in other words'
            ],
            'context': [
                'in this code', 'this function', 'this method', 'this variable',
                'line', 'file', 'module', 'class'
            ],
            'impact': [
                'can lead to', 'may cause', 'could result in', 'impact', 'affect',
                'consequence', 'risk', 'problem'
            ]
        }
        
        # Keywords that indicate good suggestions
        self.suggestion_indicators = {
            'actionable': [
                'use', 'replace', 'change', 'modify', 'add', 'remove', 'implement',
                'consider', 'try', 'instead', 'alternatively'
            ],
            'specific': [
                'function', 'method', 'variable', 'parameter', 'library', 'framework',
                'pattern', 'approach', 'technique'
            ],
            'examples': [
                'example', 'for instance', 'such as', 'like', 'e.g.', 'i.e.'
            ]
        }
        
        # Common explanation weaknesses
        self.weakness_patterns = {
            'too_vague': [
                r'\bthis\b(?!\s+\w+)', r'\bthat\b(?!\s+\w+)', r'\bit\b(?!\s+\w+)',
                r'\bsomething\b', r'\bstuff\b', r'\bthings\b'
            ],
            'too_short': lambda text: len(text.split()) < 10,
            'no_context': lambda text: not any(word in text.lower() for word in 
                ['line', 'function', 'method', 'variable', 'class', 'file']),
            'no_impact': lambda text: not any(word in text.lower() for word in 
                ['can', 'may', 'could', 'will', 'might', 'lead', 'cause', 'result'])
        }
    
    def assess_explanation(
        self, 
        issue: Dict, 
        explanation: str, 
        suggestion: str = ""
    ) -> ExplanationAssessment:
        """
        Assess the quality of an issue explanation and suggestion.
        
        Args:
            issue: The issue dictionary
            explanation: The explanation text
            suggestion: The suggestion text
            
        Returns:
            ExplanationAssessment with detailed quality metrics
        """
        issue_id = f"{issue.get('category', 'unknown')}_{issue.get('type', 'unknown')}"
        
        # Calculate component scores
        readability_score = self._assess_readability(explanation)
        completeness_score = self._assess_completeness(explanation, issue)
        actionability_score = self._assess_actionability(suggestion) if suggestion else 0.0
        
        # Calculate overall quality score
        quality_score = (readability_score * 0.3 + completeness_score * 0.4 + actionability_score * 0.3)
        
        # Determine quality level
        quality_level = self._determine_quality_level(quality_score)
        
        # Identify strengths and weaknesses
        strengths = self._identify_strengths(explanation, suggestion)
        weaknesses = self._identify_weaknesses(explanation, suggestion)
        missing_elements = self._identify_missing_elements(explanation, suggestion, issue)
        
        return ExplanationAssessment(
            issue_id=issue_id,
            explanation_text=explanation,
            suggestion_text=suggestion,
            quality_score=quality_score,
            quality_level=quality_level,
            strengths=strengths,
            weaknesses=weaknesses,
            missing_elements=missing_elements,
            readability_score=readability_score,
            completeness_score=completeness_score,
            actionability_score=actionability_score
        )
    
    def _assess_readability(self, text: str) -> float:
        """Assess the readability of explanation text."""
        if not text:
            return 0.0
        
        score = 0.0
        
        # Length check (not too short, not too long)
        word_count = len(text.split())
        if 15 <= word_count <= 100:
            score += 0.3
        elif 10 <= word_count <= 150:
            score += 0.2
        elif word_count >= 5:
            score += 0.1
        
        # Sentence structure
        sentences = text.split('.')
        if len(sentences) > 1:
            score += 0.2  # Multiple sentences
        
        # Clarity indicators
        clarity_words = sum(1 for word in self.positive_indicators['clarity'] 
                          if word in text.lower())
        score += min(clarity_words * 0.1, 0.3)
        
        # Technical terminology (shows expertise)
        tech_words = sum(1 for word in self.positive_indicators['technical_accuracy'] 
                        if word in text.lower())
        score += min(tech_words * 0.05, 0.2)
        
        return min(score, 1.0)
    
    def _assess_completeness(self, explanation: str, issue: Dict) -> float:
        """Assess how complete the explanation is."""
        if not explanation:
            return 0.0
        
        score = 0.0
        text_lower = explanation.lower()
        
        # Context provision
        context_words = sum(1 for word in self.positive_indicators['context'] 
                           if word in text_lower)
        score += min(context_words * 0.1, 0.3)
        
        # Impact explanation
        impact_words = sum(1 for word in self.positive_indicators['impact'] 
                          if word in text_lower)
        score += min(impact_words * 0.1, 0.3)
        
        # Technical accuracy
        tech_words = sum(1 for word in self.positive_indicators['technical_accuracy'] 
                        if word in text_lower)
        score += min(tech_words * 0.05, 0.2)
        
        # Category-specific completeness
        category = issue.get('category', '').lower()
        if category == 'security':
            security_terms = ['vulnerability', 'attack', 'exploit', 'malicious', 'unauthorized']
            if any(term in text_lower for term in security_terms):
                score += 0.2
        elif category == 'performance':
            perf_terms = ['slow', 'inefficient', 'memory', 'cpu', 'optimization', 'bottleneck']
            if any(term in text_lower for term in perf_terms):
                score += 0.2
        
        return min(score, 1.0)
    
    def _assess_actionability(self, suggestion: str) -> float:
        """Assess how actionable the suggestion is."""
        if not suggestion:
            return 0.0
        
        score = 0.0
        text_lower = suggestion.lower()
        
        # Action words
        action_words = sum(1 for word in self.suggestion_indicators['actionable'] 
                          if word in text_lower)
        score += min(action_words * 0.1, 0.4)
        
        # Specific recommendations
        specific_words = sum(1 for word in self.suggestion_indicators['specific'] 
                            if word in text_lower)
        score += min(specific_words * 0.1, 0.3)
        
        # Examples provided
        example_words = sum(1 for word in self.suggestion_indicators['examples'] 
                           if word in text_lower)
        score += min(example_words * 0.1, 0.2)
        
        # Code examples (look for code-like patterns)
        if re.search(r'`[^`]+`|```[^`]+```|\b\w+\(\)', suggestion):
            score += 0.1
        
        return min(score, 1.0)
    
    def _determine_quality_level(self, score: float) -> ExplanationQuality:
        """Determine quality level based on score."""
        if score >= 0.8:
            return ExplanationQuality.EXCELLENT
        elif score >= 0.6:
            return ExplanationQuality.GOOD
        elif score >= 0.4:
            return ExplanationQuality.FAIR
        else:
            return ExplanationQuality.POOR
    
    def _identify_strengths(self, explanation: str, suggestion: str) -> List[str]:
        """Identify strengths in the explanation and suggestion."""
        strengths = []
        
        if explanation:
            text_lower = explanation.lower()
            
            # Check for various strength indicators
            if len(explanation.split()) >= 20:
                strengths.append("Detailed explanation")
            
            if any(word in text_lower for word in self.positive_indicators['clarity']):
                strengths.append("Clear reasoning")
            
            if any(word in text_lower for word in self.positive_indicators['context']):
                strengths.append("Good context")
            
            if any(word in text_lower for word in self.positive_indicators['impact']):
                strengths.append("Impact explained")
            
            if any(word in text_lower for word in self.positive_indicators['technical_accuracy']):
                strengths.append("Technical accuracy")
        
        if suggestion:
            sugg_lower = suggestion.lower()
            
            if any(word in sugg_lower for word in self.suggestion_indicators['actionable']):
                strengths.append("Actionable suggestions")
            
            if any(word in sugg_lower for word in self.suggestion_indicators['specific']):
                strengths.append("Specific recommendations")
            
            if any(word in sugg_lower for word in self.suggestion_indicators['examples']):
                strengths.append("Examples provided")
            
            if re.search(r'`[^`]+`|```[^`]+```|\b\w+\(\)', suggestion):
                strengths.append("Code examples")
        
        return strengths
    
    def _identify_weaknesses(self, explanation: str, suggestion: str) -> List[str]:
        """Identify weaknesses in the explanation and suggestion."""
        weaknesses = []
        
        if explanation:
            # Check for vague language
            for pattern in self.weakness_patterns['too_vague']:
                if re.search(pattern, explanation, re.IGNORECASE):
                    weaknesses.append("Vague language")
                    break
            
            # Check if too short
            if self.weakness_patterns['too_short'](explanation):
                weaknesses.append("Too brief")
            
            # Check for missing context
            if self.weakness_patterns['no_context'](explanation):
                weaknesses.append("Lacks context")
            
            # Check for missing impact
            if self.weakness_patterns['no_impact'](explanation):
                weaknesses.append("No impact explanation")
        else:
            weaknesses.append("No explanation provided")
        
        if not suggestion:
            weaknesses.append("No suggestions provided")
        elif len(suggestion.split()) < 5:
            weaknesses.append("Suggestion too brief")
        
        return weaknesses
    
    def _identify_missing_elements(self, explanation: str, suggestion: str, issue: Dict) -> List[str]:
        """Identify missing elements that would improve the explanation."""
        missing = []
        
        if not explanation:
            missing.extend(["Explanation", "Context", "Impact description", "Technical details"])
            return missing
        
        text_lower = explanation.lower()
        
        # Check for missing context
        if not any(word in text_lower for word in self.positive_indicators['context']):
            missing.append("Code context")
        
        # Check for missing impact
        if not any(word in text_lower for word in self.positive_indicators['impact']):
            missing.append("Impact description")
        
        # Check for missing technical details
        if not any(word in text_lower for word in self.positive_indicators['technical_accuracy']):
            missing.append("Technical details")
        
        # Check for missing suggestions
        if not suggestion:
            missing.append("Actionable suggestions")
        elif not any(word in suggestion.lower() for word in self.suggestion_indicators['actionable']):
            missing.append("Specific actions")
        
        # Category-specific missing elements
        category = issue.get('category', '').lower()
        if category == 'security':
            if 'risk' not in text_lower and 'vulnerability' not in text_lower:
                missing.append("Security risk explanation")
        elif category == 'performance':
            if 'performance' not in text_lower and 'efficiency' not in text_lower:
                missing.append("Performance impact")
        
        return missing
    
    def validate_explanations_batch(self, issues_with_explanations: List[Dict]) -> List[ExplanationAssessment]:
        """Validate explanations for a batch of issues."""
        assessments = []
        
        for item in issues_with_explanations:
            issue = item.get('issue', {})
            explanation = item.get('explanation', '')
            suggestion = item.get('suggestion', '')
            
            assessment = self.assess_explanation(issue, explanation, suggestion)
            assessments.append(assessment)
        
        return assessments
    
    def generate_explanation_report(self, assessments: List[ExplanationAssessment]) -> str:
        """Generate a report on explanation quality."""
        report = []
        report.append("=== EXPLANATION QUALITY REPORT ===")
        report.append("")
        
        if not assessments:
            report.append("No explanations to assess.")
            return "\n".join(report)
        
        # Overall statistics
        total_assessments = len(assessments)
        avg_quality_score = sum(a.quality_score for a in assessments) / total_assessments
        avg_readability = sum(a.readability_score for a in assessments) / total_assessments
        avg_completeness = sum(a.completeness_score for a in assessments) / total_assessments
        avg_actionability = sum(a.actionability_score for a in assessments) / total_assessments
        
        report.append("Overall Statistics:")
        report.append(f"  Total Explanations: {total_assessments}")
        report.append(f"  Average Quality Score: {avg_quality_score:.3f}")
        report.append(f"  Average Readability: {avg_readability:.3f}")
        report.append(f"  Average Completeness: {avg_completeness:.3f}")
        report.append(f"  Average Actionability: {avg_actionability:.3f}")
        report.append("")
        
        # Quality distribution
        quality_counts = {}
        for assessment in assessments:
            level = assessment.quality_level.value
            quality_counts[level] = quality_counts.get(level, 0) + 1
        
        report.append("Quality Distribution:")
        for level in ['excellent', 'good', 'fair', 'poor']:
            count = quality_counts.get(level, 0)
            percentage = (count / total_assessments) * 100
            report.append(f"  {level.title()}: {count} ({percentage:.1f}%)")
        report.append("")
        
        # Common strengths
        all_strengths = []
        for assessment in assessments:
            all_strengths.extend(assessment.strengths)
        
        if all_strengths:
            strength_counts = {}
            for strength in all_strengths:
                strength_counts[strength] = strength_counts.get(strength, 0) + 1
            
            report.append("Common Strengths:")
            for strength, count in sorted(strength_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
                report.append(f"  {strength}: {count} occurrences")
            report.append("")
        
        # Common weaknesses
        all_weaknesses = []
        for assessment in assessments:
            all_weaknesses.extend(assessment.weaknesses)
        
        if all_weaknesses:
            weakness_counts = {}
            for weakness in all_weaknesses:
                weakness_counts[weakness] = weakness_counts.get(weakness, 0) + 1
            
            report.append("Common Weaknesses:")
            for weakness, count in sorted(weakness_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
                report.append(f"  {weakness}: {count} occurrences")
            report.append("")
        
        # Recommendations for improvement
        report.append("Recommendations for Improvement:")
        if avg_readability < 0.6:
            report.append("  - Improve readability with clearer language and better structure")
        if avg_completeness < 0.6:
            report.append("  - Provide more complete explanations with context and impact")
        if avg_actionability < 0.6:
            report.append("  - Make suggestions more actionable with specific steps")
        
        # Show worst performing explanations
        poor_assessments = [a for a in assessments if a.quality_level == ExplanationQuality.POOR]
        if poor_assessments:
            report.append("")
            report.append("Issues Needing Attention:")
            for assessment in poor_assessments[:5]:  # Show first 5
                report.append(f"  {assessment.issue_id}: Score {assessment.quality_score:.2f}")
                report.append(f"    Weaknesses: {', '.join(assessment.weaknesses)}")
                report.append(f"    Missing: {', '.join(assessment.missing_elements)}")
        
        return "\n".join(report)