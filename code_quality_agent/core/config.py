"""Configuration management for the Code Quality Intelligence Agent."""

import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from pathlib import Path
import json
import yaml


@dataclass
class LLMConfig:
    """Configuration for LLM providers."""
    provider: str = "openai"  # openai, anthropic, etc.
    model: str = "gpt-4"
    api_key: Optional[str] = None
    temperature: float = 0.1
    max_tokens: int = 2000
    timeout: int = 30
    retry_attempts: int = 3


@dataclass
class AnalysisConfig:
    """Configuration for analysis behavior."""
    parallel_processing: bool = True
    max_workers: int = 4
    cache_enabled: bool = True
    cache_ttl_hours: int = 24
    confidence_threshold: float = 0.7
    max_issues_per_category: int = 50


@dataclass
class ParserConfig:
    """Configuration for code parsers."""
    include_patterns: List[str] = field(default_factory=lambda: ["*.py", "*.js", "*.ts", "*.jsx", "*.tsx"])
    exclude_patterns: List[str] = field(default_factory=lambda: [
        "node_modules/**", 
        ".git/**", 
        "__pycache__/**", 
        "*.pyc",
        ".venv/**",
        "venv/**",
        "build/**",
        "dist/**"
    ])
    max_file_size_mb: int = 10
    encoding: str = "utf-8"


@dataclass
class QAConfig:
    """Configuration for Q&A engine."""
    vector_store_path: str = ".code_quality_cache/vectors"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    max_context_length: int = 8000
    similarity_threshold: float = 0.7


@dataclass
class ReportConfig:
    """Configuration for report generation."""
    default_format: str = "text"  # text, json, html
    include_explanations: bool = True
    include_suggestions: bool = True
    max_explanation_length: int = 500
    color_output: bool = True


@dataclass
class Config:
    """Main configuration class."""
    llm: LLMConfig = field(default_factory=LLMConfig)
    analysis: AnalysisConfig = field(default_factory=AnalysisConfig)
    parser: ParserConfig = field(default_factory=ParserConfig)
    qa: QAConfig = field(default_factory=QAConfig)
    report: ReportConfig = field(default_factory=ReportConfig)
    
    @classmethod
    def from_file(cls, config_path: Path) -> 'Config':
        """Load configuration from a file."""
        if not config_path.exists():
            return cls()
        
        with open(config_path, 'r') as f:
            if config_path.suffix.lower() == '.yaml' or config_path.suffix.lower() == '.yml':
                data = yaml.safe_load(f)
            else:
                data = json.load(f)
        
        return cls.from_dict(data)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Config':
        """Create configuration from dictionary."""
        config = cls()
        
        if 'llm' in data:
            config.llm = LLMConfig(**data['llm'])
        if 'analysis' in data:
            config.analysis = AnalysisConfig(**data['analysis'])
        if 'parser' in data:
            config.parser = ParserConfig(**data['parser'])
        if 'qa' in data:
            config.qa = QAConfig(**data['qa'])
        if 'report' in data:
            config.report = ReportConfig(**data['report'])
        
        return config
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'llm': self.llm.__dict__,
            'analysis': self.analysis.__dict__,
            'parser': self.parser.__dict__,
            'qa': self.qa.__dict__,
            'report': self.report.__dict__,
        }
    
    def save_to_file(self, config_path: Path) -> None:
        """Save configuration to a file."""
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w') as f:
            if config_path.suffix.lower() == '.yaml' or config_path.suffix.lower() == '.yml':
                yaml.dump(self.to_dict(), f, default_flow_style=False)
            else:
                json.dump(self.to_dict(), f, indent=2)


class ConfigManager:
    """Manages configuration loading and environment variable integration."""
    
    def __init__(self):
        self._config: Optional[Config] = None
    
    def get_config(self) -> Config:
        """Get the current configuration, loading it if necessary."""
        if self._config is None:
            self._config = self._load_config()
        return self._config
    
    def _load_config(self) -> Config:
        """Load configuration from various sources."""
        # Try to load from config file
        config_paths = [
            Path.cwd() / "code_quality_config.yaml",
            Path.cwd() / "code_quality_config.json",
            Path.home() / ".code_quality" / "config.yaml",
            Path.home() / ".code_quality" / "config.json",
        ]
        
        config = None
        for config_path in config_paths:
            if config_path.exists():
                config = Config.from_file(config_path)
                break
        
        if config is None:
            config = Config()
        
        # Override with environment variables
        self._apply_env_overrides(config)
        
        return config
    
    def _apply_env_overrides(self, config: Config) -> None:
        """Apply environment variable overrides to configuration."""
        # LLM configuration
        if os.getenv("OPENAI_API_KEY"):
            config.llm.api_key = os.getenv("OPENAI_API_KEY")
        if os.getenv("ANTHROPIC_API_KEY") and config.llm.provider == "anthropic":
            config.llm.api_key = os.getenv("ANTHROPIC_API_KEY")
        
        # Analysis configuration
        if os.getenv("CQA_PARALLEL_PROCESSING"):
            config.analysis.parallel_processing = os.getenv("CQA_PARALLEL_PROCESSING").lower() == "true"
        if os.getenv("CQA_MAX_WORKERS"):
            config.analysis.max_workers = int(os.getenv("CQA_MAX_WORKERS"))
        
        # Report configuration
        if os.getenv("CQA_OUTPUT_FORMAT"):
            config.report.default_format = os.getenv("CQA_OUTPUT_FORMAT")


# Global configuration manager instance
config_manager = ConfigManager()