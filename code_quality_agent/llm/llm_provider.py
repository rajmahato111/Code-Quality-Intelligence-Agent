"""LLM provider integration using LangChain."""

import os
import logging
import time
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from dataclasses import dataclass
from abc import ABC, abstractmethod

try:
    from langchain_openai import ChatOpenAI
    from langchain_anthropic import ChatAnthropic
    from langchain_core.messages import HumanMessage, SystemMessage
    from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.runnables import RunnablePassthrough
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    # Create mock classes for when LangChain is not available
    class ChatOpenAI:
        def __init__(self, *args, **kwargs):
            pass
    
    class ChatAnthropic:
        def __init__(self, *args, **kwargs):
            pass
    
    class ChatPromptTemplate:
        @staticmethod
        def from_messages(*args, **kwargs):
            return None
    
    class StrOutputParser:
        def __init__(self):
            pass


logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    MOCK = "mock"  # For testing


@dataclass
class LLMConfig:
    """Configuration for LLM providers."""
    provider: LLMProvider
    model_name: str
    api_key: Optional[str] = None
    temperature: float = 0.1
    max_tokens: int = 1000
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0


@dataclass
class LLMResponse:
    """Response from LLM provider."""
    content: str
    provider: LLMProvider
    model: str
    tokens_used: Optional[int] = None
    response_time: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None


class BaseLLMProvider(ABC):
    """Base class for LLM providers."""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.client = None
        self._initialize_client()
    
    @abstractmethod
    def _initialize_client(self) -> None:
        """Initialize the LLM client."""
        pass
    
    @abstractmethod
    def _make_request(self, messages: List[Dict[str, str]]) -> str:
        """Make a request to the LLM provider."""
        pass
    
    def generate_response(
        self, 
        messages: List[Dict[str, str]], 
        **kwargs
    ) -> LLMResponse:
        """
        Generate a response from the LLM with retry logic.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            **kwargs: Additional parameters for the LLM
            
        Returns:
            LLMResponse object with the result
        """
        start_time = time.time()
        
        for attempt in range(self.config.max_retries):
            try:
                content = self._make_request(messages, **kwargs)
                response_time = time.time() - start_time
                
                return LLMResponse(
                    content=content,
                    provider=self.config.provider,
                    model=self.config.model_name,
                    response_time=response_time,
                    success=True
                )
                
            except Exception as e:
                logger.warning(f"LLM request attempt {attempt + 1} failed: {e}")
                
                if attempt < self.config.max_retries - 1:
                    time.sleep(self.config.retry_delay * (2 ** attempt))  # Exponential backoff
                else:
                    response_time = time.time() - start_time
                    return LLMResponse(
                        content="",
                        provider=self.config.provider,
                        model=self.config.model_name,
                        response_time=response_time,
                        success=False,
                        error_message=str(e)
                    )


class OpenAIProvider(BaseLLMProvider):
    """OpenAI LLM provider using LangChain."""
    
    def _initialize_client(self) -> None:
        """Initialize OpenAI client."""
        if not LANGCHAIN_AVAILABLE:
            raise ImportError("LangChain is required for OpenAI integration")
        
        api_key = self.config.api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key is required")
        
        self.client = ChatOpenAI(
            model=self.config.model_name,
            api_key=api_key,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            timeout=self.config.timeout
        )
        
        logger.info(f"Initialized OpenAI client with model: {self.config.model_name}")
    
    def _make_request(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Make request to OpenAI."""
        # Convert messages to LangChain format
        langchain_messages = []
        for msg in messages:
            if msg["role"] == "system":
                langchain_messages.append(SystemMessage(content=msg["content"]))
            elif msg["role"] == "user":
                langchain_messages.append(HumanMessage(content=msg["content"]))
        
        response = self.client.invoke(langchain_messages)
        return response.content


class AnthropicProvider(BaseLLMProvider):
    """Anthropic LLM provider using LangChain."""
    
    def _initialize_client(self) -> None:
        """Initialize Anthropic client."""
        if not LANGCHAIN_AVAILABLE:
            raise ImportError("LangChain is required for Anthropic integration")
        
        api_key = self.config.api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("Anthropic API key is required")
        
        self.client = ChatAnthropic(
            model=self.config.model_name,
            api_key=api_key,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            timeout=self.config.timeout
        )
        
        logger.info(f"Initialized Anthropic client with model: {self.config.model_name}")
    
    def _make_request(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Make request to Anthropic."""
        # Convert messages to LangChain format
        langchain_messages = []
        for msg in messages:
            if msg["role"] == "system":
                langchain_messages.append(SystemMessage(content=msg["content"]))
            elif msg["role"] == "user":
                langchain_messages.append(HumanMessage(content=msg["content"]))
        
        response = self.client.invoke(langchain_messages)
        return response.content


class MockLLMProvider(BaseLLMProvider):
    """Mock LLM provider for testing."""
    
    def __init__(self, config: LLMConfig, mock_responses: Optional[List[str]] = None):
        self.mock_responses = mock_responses or [
            "Based on your code analysis, I found several issues that need attention:\n\nHere are the key issues:\n- Missing documentation for critical functions\n- Potential security vulnerabilities in user input handling\n- Code duplication that affects maintainability\n\nI recommend addressing the high-priority issues first, particularly those related to documentation and security. Would you like me to provide specific fix suggestions for any of these issues?",
            "Your code has multiple areas that need improvement. Focus on adding proper documentation and fixing security issues first.",
            "The analysis shows documentation gaps and security concerns that should be prioritized."
        ]
        self.response_index = 0
        super().__init__(config)
    
    def _initialize_client(self) -> None:
        """Initialize mock client."""
        self.client = "mock_client"
        logger.info("Initialized mock LLM client")
    
    def _make_request(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Return mock response based on the content."""
        # Check if this is a question about issues
        user_message = ""
        for msg in messages:
            if msg.get("role") == "user":
                user_message = msg.get("content", "")
                break
        
        # If the message contains issue information, generate a specific response
        if "Total Issues:" in user_message and "Relevant Issues:" in user_message:
            # Extract issue count and details from the message
            lines = user_message.split('\n')
            total_issues = 0
            relevant_issues = []
            
            for line in lines:
                if "Total Issues:" in line:
                    try:
                        total_issues = int(line.split("Total Issues:")[1].strip())
                    except:
                        pass
                elif line.strip().startswith("- ") and "(" in line and ")" in line:
                    relevant_issues.append(line.strip())
            
            if total_issues > 0 or relevant_issues:
                response = f"Based on your code analysis, I found {total_issues} issues that need attention:\n\n"
                
                if relevant_issues:
                    response += "Here are the key issues:\n"
                    for issue in relevant_issues[:5]:  # Show top 5
                        response += f"{issue}\n"
                    response += "\n"
                
                response += "I recommend addressing the high-priority issues first, particularly those related to documentation and security. Would you like me to provide specific fix suggestions for any of these issues?"
                
                return response
        
        # Default mock response
        response = self.mock_responses[self.response_index % len(self.mock_responses)]
        self.response_index += 1
        
        # Simulate some processing time
        time.sleep(0.1)
        
        return response


class LLMManager:
    """Manager for LLM providers with fallback support."""
    
    def __init__(self, primary_config: LLMConfig, fallback_config: Optional[LLMConfig] = None):
        """
        Initialize LLM manager.
        
        Args:
            primary_config: Primary LLM provider configuration
            fallback_config: Optional fallback provider configuration
        """
        self.primary_provider = self._create_provider(primary_config)
        self.fallback_provider = self._create_provider(fallback_config) if fallback_config else None
        self.request_count = 0
        self.success_count = 0
        self.error_count = 0
    
    def _create_provider(self, config: LLMConfig) -> BaseLLMProvider:
        """Create LLM provider based on configuration."""
        if config.provider == LLMProvider.OPENAI:
            return OpenAIProvider(config)
        elif config.provider == LLMProvider.ANTHROPIC:
            return AnthropicProvider(config)
        elif config.provider == LLMProvider.MOCK:
            return MockLLMProvider(config)
        else:
            raise ValueError(f"Unsupported LLM provider: {config.provider}")
    
    def generate_response(
        self, 
        messages: List[Dict[str, str]], 
        use_fallback: bool = True,
        **kwargs
    ) -> LLMResponse:
        """
        Generate response with primary provider and fallback support.
        
        Args:
            messages: List of message dictionaries
            use_fallback: Whether to use fallback provider on failure
            **kwargs: Additional parameters
            
        Returns:
            LLMResponse object
        """
        self.request_count += 1
        
        # Try primary provider
        response = self.primary_provider.generate_response(messages, **kwargs)
        
        if response.success:
            self.success_count += 1
            return response
        
        # Try fallback provider if available and enabled
        if use_fallback and self.fallback_provider:
            logger.info("Primary provider failed, trying fallback provider")
            fallback_response = self.fallback_provider.generate_response(messages, **kwargs)
            
            if fallback_response.success:
                self.success_count += 1
                return fallback_response
        
        self.error_count += 1
        return response
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get usage statistics."""
        success_rate = (self.success_count / max(self.request_count, 1)) * 100
        
        return {
            "total_requests": self.request_count,
            "successful_requests": self.success_count,
            "failed_requests": self.error_count,
            "success_rate_percent": success_rate,
            "primary_provider": self.primary_provider.config.provider.value,
            "fallback_provider": self.fallback_provider.config.provider.value if self.fallback_provider else None,
            "langchain_available": LANGCHAIN_AVAILABLE
        }
    
    def reset_statistics(self) -> None:
        """Reset usage statistics."""
        self.request_count = 0
        self.success_count = 0
        self.error_count = 0


def create_default_llm_manager(
    provider: str = "openai",
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    enable_fallback: bool = True
) -> LLMManager:
    """
    Create a default LLM manager with common configurations.
    
    Args:
        provider: Primary provider name ("openai", "anthropic", or "mock")
        model: Model name to use
        api_key: API key (if not provided, will use environment variables)
        enable_fallback: Whether to enable mock fallback
        
    Returns:
        Configured LLMManager instance
    """
    # Get model from environment variable if not provided
    if model is None:
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    # Primary provider configuration
    if provider.lower() == "openai":
        primary_config = LLMConfig(
            provider=LLMProvider.OPENAI,
            model_name=model,
            api_key=api_key,
            temperature=0.1,
            max_tokens=1000
        )
    elif provider.lower() == "anthropic":
        primary_config = LLMConfig(
            provider=LLMProvider.ANTHROPIC,
            model_name=model,
            api_key=api_key,
            temperature=0.1,
            max_tokens=1000
        )
    elif provider.lower() == "mock":
        primary_config = LLMConfig(
            provider=LLMProvider.MOCK,
            model_name="mock-model",
            temperature=0.1,
            max_tokens=1000
        )
    else:
        raise ValueError(f"Unsupported provider: {provider}")
    
    # Fallback configuration (mock provider)
    fallback_config = None
    if enable_fallback and provider.lower() != "mock":
        fallback_config = LLMConfig(
            provider=LLMProvider.MOCK,
            model_name="mock-fallback",
            temperature=0.1,
            max_tokens=1000
        )
    
    return LLMManager(primary_config, fallback_config)