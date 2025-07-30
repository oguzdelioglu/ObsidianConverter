"""
Base LLM provider interface
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseLLMProvider(ABC):
    """Base class for LLM providers"""
    
    @abstractmethod
    def __init__(self, model_name: str, **kwargs):
        """
        Initialize the LLM provider
        
        Args:
            model_name: Name of the model to use
            **kwargs: Additional provider-specific arguments
        """
        self.model_name = model_name
        
    @abstractmethod
    def invoke(self, prompt: str) -> str:
        """
        Invoke the LLM with a prompt
        
        Args:
            prompt: The prompt to send to the LLM
            
        Returns:
            The LLM's response as text
        """
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """
        Get the name of this LLM provider
        
        Returns:
            Provider name string
        """
        pass
    
    @property
    def supports_streaming(self) -> bool:
        """
        Whether this provider supports streaming responses
        
        Returns:
            True if streaming is supported, False otherwise
        """
        return False
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get information about the provider and model
        
        Returns:
            Dictionary with provider and model details
        """
        return {
            "provider": self.get_provider_name(),
            "model": self.model_name,
            "streaming_supported": self.supports_streaming
        }
    
    @staticmethod
    def get_available_models() -> Dict[str, Any]:
        """
        Get available models for this provider
        
        Returns:
            Dictionary of available models and their capabilities
        """
        return {}
    
    def validate_env(self) -> bool:
        """
        Validate that necessary environment variables or settings are available
        
        Returns:
            True if environment is valid, False otherwise
        """
        return True