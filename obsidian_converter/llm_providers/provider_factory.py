"""
LLM provider factory
"""
import os
import logging
from typing import Dict, Any, Optional, List

from obsidian_converter.llm_providers.base import BaseLLMProvider
from obsidian_converter.llm_providers.ollama_provider import OllamaProvider

# Import other providers conditionally to avoid hard dependencies
try:
    from obsidian_converter.llm_providers.openai_provider import OpenAIProvider
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from obsidian_converter.llm_providers.anthropic_provider import AnthropicProvider
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

logger = logging.getLogger("obsidian_converter")


class LLMProviderFactory:
    """Factory for creating LLM provider instances"""
    
    @staticmethod
    def create_provider(provider_name: str, model_name: str, **kwargs) -> BaseLLMProvider:
        """
        Create an LLM provider instance
        
        Args:
            provider_name: Name of the provider
            model_name: Name of the model to use
            **kwargs: Additional provider-specific arguments
            
        Returns:
            An instance of the specified LLM provider
            
        Raises:
            ValueError: If the provider is not supported or available
        """
        provider_name = provider_name.lower()
        
        # Create the appropriate provider
        if provider_name == "ollama":
            return OllamaProvider(model_name, **kwargs)
            
        elif provider_name == "openai":
            if not OPENAI_AVAILABLE:
                raise ValueError("OpenAI package is not installed. Install with 'pip install openai'.")
            return OpenAIProvider(model_name, **kwargs)
            
        elif provider_name == "anthropic":
            if not ANTHROPIC_AVAILABLE:
                raise ValueError("Anthropic package is not installed. Install with 'pip install anthropic'.")
            return AnthropicProvider(model_name, **kwargs)
            
        else:
            raise ValueError(f"Unsupported LLM provider: {provider_name}")
    
    @staticmethod
    def get_available_providers() -> Dict[str, Dict[str, Any]]:
        """
        Get information about available providers
        
        Returns:
            Dictionary of available providers and their capabilities
        """
        providers = {}
        
        # Ollama is always available as it's a core dependency
        providers["ollama"] = {
            "available": True,
            "models": OllamaProvider.get_available_models(),
            "default_model": "mistral"
        }
        
        # Check for OpenAI
        if OPENAI_AVAILABLE:
            providers["openai"] = {
                "available": True,
                "requires_api_key": True,
                "models": OpenAIProvider.get_available_models() if os.environ.get("OPENAI_API_KEY") else {},
                "default_model": "gpt-3.5-turbo"
            }
        else:
            providers["openai"] = {
                "available": False,
                "requires_api_key": True,
                "installation": "pip install openai"
            }
        
        # Check for Anthropic
        if ANTHROPIC_AVAILABLE:
            providers["anthropic"] = {
                "available": True,
                "requires_api_key": True,
                "models": AnthropicProvider.get_available_models() if os.environ.get("ANTHROPIC_API_KEY") else {},
                "default_model": "claude-3-sonnet-20240229"
            }
        else:
            providers["anthropic"] = {
                "available": False,
                "requires_api_key": True,
                "installation": "pip install anthropic"
            }
        
        return providers