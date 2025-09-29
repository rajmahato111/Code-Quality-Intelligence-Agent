"""LLM integration module for code quality intelligence."""

from .llm_provider import (
    LLMProvider,
    LLMConfig,
    LLMResponse,
    LLMManager,
    MockLLMProvider,
    create_default_llm_manager,
    LANGCHAIN_AVAILABLE
)

from .prompt_templates import (
    PromptType,
    PromptTemplate,
    PromptTemplateManager,
    prompt_manager
)

from .llm_service import (
    LLMService,
    create_llm_service
)

__all__ = [
    # Provider classes
    "LLMProvider",
    "LLMConfig", 
    "LLMResponse",
    "LLMManager",
    "MockLLMProvider",
    "create_default_llm_manager",
    "LANGCHAIN_AVAILABLE",
    
    # Template classes
    "PromptType",
    "PromptTemplate",
    "PromptTemplateManager",
    "prompt_manager",
    
    # Service classes
    "LLMService",
    "create_llm_service"
]