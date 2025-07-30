"""
Anthropic LLM provider implementation
"""
import os
import logging
from typing import Dict, Any, Optional, List

try:
    import anthropic
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from obsidian_converter.llm_providers.base import BaseLLMProvider

logger = logging.getLogger("obsidian_converter")


class AnthropicProvider(BaseLLMProvider):
    """LLM provider using Anthropic API"""
    
    def __init__(self, model_name: str = "claude-3-opus-20240229", **kwargs):
        """
        Initialize the Anthropic provider
        
        Args:
            model_name: Name of the Anthropic model to use
            **kwargs: Additional arguments
        """
        super().__init__(model_name)
        self.api_key = kwargs.get("api_key") or os.environ.get("ANTHROPIC_API_KEY")
        self.temperature = kwargs.get("temperature", 0.7)
        self.max_tokens = kwargs.get("max_tokens", 4000)
        
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("Anthropic package is not installed. Install with 'pip install anthropic'.")
            
        if not self.api_key:
            raise ValueError("Anthropic API key not provided. Set ANTHROPIC_API_KEY environment variable.")
            
        # Initialize client
        self.client = Anthropic(api_key=self.api_key)
    
    def invoke(self, prompt: str) -> str:
        """
        Invoke the Anthropic model with a prompt
        
        Args:
            prompt: The prompt to send to the model
            
        Returns:
            The model's response as text
            
        Raises:
            Exception: If the API call fails
        """
        try:
            # Call Anthropic API
            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Extract text from response
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"Error invoking Anthropic LLM: {str(e)}")
            raise
    
    def get_provider_name(self) -> str:
        """Get the provider name"""
        return "anthropic"
    
    @property
    def supports_streaming(self) -> bool:
        """Check if streaming is supported"""
        return True
    
    @staticmethod
    def get_available_models() -> Dict[str, List[str]]:
        """
        Get available models from Anthropic
        
        Returns:
            Dictionary of available models
        """
        # Anthropic doesn't have a public API to list models
        # Return the known models
        return {
            "claude": [
                "claude-3-opus-20240229",
                "claude-3-sonnet-20240229",
                "claude-3-haiku-20240307",
                "claude-2.1",
                "claude-2.0",
                "claude-instant-1.2"
            ]
        }
    
    def validate_env(self) -> bool:
        """
        Validate that Anthropic API is accessible with the provided key
        
        Returns:
            True if Anthropic API is available, False otherwise
        """
        if not ANTHROPIC_AVAILABLE:
            logger.warning("Anthropic package is not installed")
            return False
            
        if not self.api_key:
            logger.warning("Anthropic API key not provided")
            return False
            
        try:
            # Try a simple API call to validate the key
            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=10,
                temperature=self.temperature,
                messages=[{"role": "user", "content": "Hello"}]
            )
            return True
        except Exception as e:
            logger.warning(f"Failed to connect to Anthropic API: {e}")
            return False