"""
Code Quality Intelligence Agent

An AI-powered tool that analyzes code repositories and generates actionable,
developer-friendly reports with interactive Q&A capabilities.
"""

__version__ = "0.1.0"
__author__ = "Code Quality Intelligence Team"

from .core.orchestrator import AnalysisOrchestrator
from .core.models import AnalysisResult, Issue, QualityMetrics
from .analyzers.base import QualityAnalyzer
from .parsers.base import CodeParser

__all__ = [
    "AnalysisOrchestrator",
    "AnalysisResult", 
    "Issue",
    "QualityMetrics",
    "QualityAnalyzer",
    "CodeParser",
]