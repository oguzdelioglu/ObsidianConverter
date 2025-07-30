"""
OpenAI LLM provider implementation
"""
import os
import logging
from typing import Dict, Any, Optional, List

try:
    import openai
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from obsidian_converter.llm_providers.base import BaseLLMProvider

logger = logging.getLogger("obsidian_converter")


class OpenAIProvider(BaseLLMProvider):
    """LLM provider using OpenAI API"""
    
    def __init__(self, model_name: str = "gpt-3.5-turbo", **kwargs):
        """
        Initialize the OpenAI provider
        
        Args:
            model_name: Name of the OpenAI model to use
            **kwargs: Additional arguments
        """
        super().__init__(model_name)
        self.api_key = kwargs.get("api_key") or os.environ.get("OPENAI_API_KEY")
        self.temperature = kwargs.get("temperature", 0.7)
        self.max_tokens = kwargs.get("max_tokens")
        
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI package is not installed. Install with 'pip install openai'.")
            
        if not self.api_key:
            raise ValueError("OpenAI API key not provided. Set OPENAI_API_KEY environment variable.")
            
        # Initialize client
        self.client = OpenAI(api_key=self.api_key)
    
    def invoke(self, prompt: str) -> str:
        """
        Invoke the OpenAI model with a prompt
        
        Args:
            prompt: The prompt to send to the model
            
        Returns:
            The model's response as text
            
        Raises:
            Exception: If the API call fails
        """
        try:
            # Prepare completion params
            params = {
                "model": self.model_name,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": self.temperature
            }
            
            if self.max_tokens:
                params["max_tokens"] = self.max_tokens
            
            # Call OpenAI API
            response = self.client.chat.completions.create(**params)
            
            # Extract text from response
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error invoking OpenAI LLM: {str(e)}")
            raise
    
    def get_provider_name(self) -> str:
        """Get the provider name"""
        return "openai"
    
    @property
    def supports_streaming(self) -> bool:
        """Check if streaming is supported"""
        return True
    
    @staticmethod
    def get_available_models() -> Dict[str, List[str]]:
        """
        Get available models from OpenAI
        
        Returns:
            Dictionary of available models by category
        """
        if not OPENAI_AVAILABLE:
            return {}
            
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return {}
            
        try:
            client = OpenAI(api_key=api_key)
            models = client.models.list()
            
            # Organize models by category
            model_dict = {
                "gpt": [],
                "embedding": [],
                "other": []
            }
            
            for model in models.data:
                model_id = model.id
                if "gpt" in model_id:
                    model_dict["gpt"].append(model_id)
                elif "embedding" in model_id or "text-embedding" in model_id:
                    model_dict["embedding"].append(model_id)
                else:
                    model_dict["other"].append(model_id)
                    
            return model_dict
            
        except Exception as e:
            logger.warning(f"Failed to get available OpenAI models: {e}")
            
        return {}
    
    def validate_env(self) -> bool:
        """
        Validate that OpenAI API is accessible with the provided key
        
        Returns:
            True if OpenAI API is available, False otherwise
        """
        if not OPENAI_AVAILABLE:
            logger.warning("OpenAI package is not installed")
            return False
            
        if not self.api_key:
            logger.warning("OpenAI API key not provided")
            return False
            
        try:
            # Try listing models as a simple API test
            self.client.models.list()
            return True
        except Exception as e:
            logger.warning(f"Failed to connect to OpenAI API: {e}")
            return False