"""Initialize and register all quality analyzers."""

import logging
from .analyzer_registry import analyzer_registry, AnalyzerPriority

logger = logging.getLogger(__name__)


def initialize_analyzers():
    """Initialize and register all available analyzers."""
    try:
        # Import all analyzer classes
        from .security_analyzer import SecurityAnalyzer
        from .performance_analyzer import PerformanceAnalyzer
        from .complexity_analyzer import ComplexityAnalyzer
        from .duplication_analyzer import DuplicationAnalyzer
        from .testing_analyzer import TestingAnalyzer
        from .documentation_analyzer import DocumentationAnalyzer
        from .hotspot_analyzer import HotspotAnalyzer
        
        # Register analyzers with appropriate priorities
        analyzers_to_register = [
            (SecurityAnalyzer(), AnalyzerPriority.CRITICAL),
            (PerformanceAnalyzer(), AnalyzerPriority.HIGH),
            (ComplexityAnalyzer(), AnalyzerPriority.MEDIUM),
            (DuplicationAnalyzer(), AnalyzerPriority.MEDIUM),
            (TestingAnalyzer(), AnalyzerPriority.MEDIUM),
            (DocumentationAnalyzer(), AnalyzerPriority.LOW),
            (HotspotAnalyzer(), AnalyzerPriority.LOW),
        ]
        
        registered_count = 0
        for analyzer, priority in analyzers_to_register:
            try:
                analyzer_registry.register_analyzer(analyzer, priority)
                registered_count += 1
            except Exception as e:
                logger.error(f"Failed to register {analyzer.__class__.__name__}: {e}")
        
        logger.info(f"Successfully registered {registered_count} analyzers")
        
        # Validate all registered analyzers
        validation_results = analyzer_registry.validate_analyzers()
        if validation_results['invalid']:
            logger.warning(f"Invalid analyzers: {validation_results['invalid']}")
        if validation_results['warnings']:
            logger.warning(f"Analyzer warnings: {validation_results['warnings']}")
        
        return registered_count
        
    except ImportError as e:
        logger.error(f"Failed to import analyzer classes: {e}")
        return 0
    except Exception as e:
        logger.error(f"Failed to initialize analyzers: {e}")
        return 0


def get_analyzer_stats():
    """Get statistics about registered analyzers."""
    return analyzer_registry.get_registry_statistics()


# Initialize analyzers when this module is imported
_initialized = False

def ensure_analyzers_initialized():
    """Ensure analyzers are initialized (call this before using the registry)."""
    global _initialized
    if not _initialized:
        initialize_analyzers()
        _initialized = True