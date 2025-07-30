"""
Configuration handling for ObsidianConverter
"""
import os
import yaml
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

logger = logging.getLogger("obsidian_converter")

@dataclass
class ObsidianConverterConfig:
    """Configuration settings for ObsidianConverter"""
    # Core settings
    input_dir: str = "txt"
    output_dir: str = "vault"
    model: str = "mistral"
    
    # LLM provider settings
    provider: str = "ollama"  # "ollama", "openai", or "anthropic"
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    llm_temperature: float = 0.7
    
    # Processing settings
    similarity_threshold: float = 0.3
    max_links: int = 5
    use_cache: bool = True
    cache_file: str = ".llm_cache.json"
    
    # Performance settings
    parallel_processing: bool = True
    max_workers: int = 4
    chunk_size: int = 1000000  # 1MB chunks for large files
    
    # Obsidian specific settings
    obsidian_features: Dict[str, bool] = field(default_factory=lambda: {
        "callouts": True,
        "dataview": True,
        "toc": True,
        "graph_metadata": True
    })
    
    # Category mapping
    category_mapping: Dict[str, str] = field(default_factory=dict)
    
    # File patterns to include/exclude
    include_patterns: List[str] = field(default_factory=lambda: ["*.txt"])
    exclude_patterns: List[str] = field(default_factory=lambda: ["*.tmp", "~*"])
    
    @classmethod
    def from_file(cls, config_path: str) -> 'ObsidianConverterConfig':
        """
        Load configuration from a YAML file
        
        Args:
            config_path: Path to the config file
            
        Returns:
            ObsidianConverterConfig object
        """
        if not os.path.exists(config_path):
            logger.warning(f"Config file not found: {config_path}, using defaults")
            return cls()
        
        try:
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
                
            if not config_data:
                logger.warning("Empty config file, using defaults")
                return cls()
                
            # Create a new config object with defaults
            config = cls()
            
            # Core settings
            config.input_dir = config_data.get('input_dir', config.input_dir)
            config.output_dir = config_data.get('output_dir', config.output_dir)
            config.model = config_data.get('model', config.model)
            
            # Processing settings
            config.similarity_threshold = config_data.get('similarity_threshold', config.similarity_threshold)
            config.max_links = config_data.get('max_links', config.max_links)
            config.use_cache = config_data.get('use_cache', config.use_cache)
            config.cache_file = config_data.get('cache_file', config.cache_file)
            
            # Performance settings
            config.parallel_processing = config_data.get('parallel_processing', config.parallel_processing)
            config.max_workers = config_data.get('max_workers', config.max_workers)
            config.chunk_size = config_data.get('chunk_size', config.chunk_size)
            
            # Obsidian specific settings
            if 'obsidian_features' in config_data:
                for key, value in config_data['obsidian_features'].items():
                    if key in config.obsidian_features:
                        config.obsidian_features[key] = value
            
            # Category mapping
            if 'category_mapping' in config_data:
                config.category_mapping = config_data['category_mapping']
            
            # File patterns
            if 'include_patterns' in config_data:
                config.include_patterns = config_data['include_patterns']
            if 'exclude_patterns' in config_data:
                config.exclude_patterns = config_data['exclude_patterns']
                
            return config
                
        except Exception as e:
            logger.error(f"Error loading config file: {e}")
            return cls()
    
    def to_file(self, config_path: str) -> bool:
        """
        Save configuration to a YAML file
        
        Args:
            config_path: Path to save the config
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(config_path)), exist_ok=True)
            
            # Convert dataclass to dict
            config_dict = {
                'input_dir': self.input_dir,
                'output_dir': self.output_dir,
                'model': self.model,
                'similarity_threshold': self.similarity_threshold,
                'max_links': self.max_links,
                'use_cache': self.use_cache,
                'cache_file': self.cache_file,
                'parallel_processing': self.parallel_processing,
                'max_workers': self.max_workers,
                'chunk_size': self.chunk_size,
                'obsidian_features': self.obsidian_features,
                'category_mapping': self.category_mapping,
                'include_patterns': self.include_patterns,
                'exclude_patterns': self.exclude_patterns
            }
            
            with open(config_path, 'w') as f:
                yaml.dump(config_dict, f, default_flow_style=False)
                
            logger.info(f"Configuration saved to {config_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving config file: {e}")
            return False
            
    @classmethod
    def create_default_config(cls, config_path: str = "config.yaml") -> bool:
        """
        Create a default configuration file
        
        Args:
            config_path: Path to save the config
            
        Returns:
            True if successful, False otherwise
        """
        config = cls()
        return config.to_file(config_path)