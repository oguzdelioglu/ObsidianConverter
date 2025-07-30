"""
Ollama LLM provider implementation
"""
import logging
import requests
from typing import Dict, Any, Optional, List

from obsidian_converter.llm_providers.base import BaseLLMProvider

logger = logging.getLogger("obsidian_converter")


class OllamaProvider(BaseLLMProvider):
    """LLM provider using Ollama"""
    
    def __init__(self, model_name: str, base_url: str = "http://localhost:11434", **kwargs):
        """
        Initialize the Ollama provider
        
        Args:
            model_name: Name of the Ollama model to use
            base_url: Base URL for the Ollama API
            **kwargs: Additional arguments
        """
        super().__init__(model_name)
        self.base_url = base_url.rstrip("/")
        self.timeout = kwargs.get("timeout", 300)  # Timeout in seconds (increased to 5 minutes)
    
    def invoke(self, prompt: str) -> str:
        """
        Invoke the Ollama model with a prompt
        
        Args:
            prompt: The prompt to send to the model
            
        Returns:
            The model's response as text
            
        Raises:
            Exception: If the API call fails
        """
        try:
            # Prepare request payload
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7
                }
            }
            
            # Call Ollama API
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                raise Exception(f"Ollama API error: {response.status_code} - {response.text}")
            
            # Parse response
            result = response.json()
            return result.get("response", "")
            
        except Exception as e:
            logger.error(f"Error invoking Ollama LLM: {str(e)}")
            raise
    
    def get_provider_name(self) -> str:
        """Get the provider name"""
        return "ollama"
    
    @property
    def supports_streaming(self) -> bool:
        """Check if streaming is supported"""
        return True
    
    @staticmethod
    def get_available_models() -> Dict[str, List[str]]:
        """
        Get available models from Ollama
        
        Returns:
            Dictionary of available models
        """
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                return {
                    "available": [model["name"] for model in models]
                }
        except Exception as e:
            logger.warning(f"Failed to get available Ollama models: {e}")
        
        return {"available": []}
    
    def validate_env(self) -> bool:
        """
        Validate that Ollama is running and the model is available
        
        Returns:
            True if Ollama is available, False otherwise
        """
        try:
            response = requests.get(f"{self.base_url}/api/version", timeout=5)
            if response.status_code != 200:
                logger.warning("Ollama service is not available")
                return False
                
            # Check if the specified model is available
            models = self.get_available_models().get("available", [])
            if not models or self.model_name not in models:
                # It might still work if the model will be pulled automatically
                logger.warning(f"Model '{self.model_name}' not found in Ollama, it will be pulled if needed")
            
            return True
        except Exception as e:
            logger.warning(f"Failed to connect to Ollama: {e}")
            return False