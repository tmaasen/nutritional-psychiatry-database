# config/__init__.py
"""
Centralized configuration management for the Nutritional Psychiatry Dataset project.
This module handles loading of environment variables, configuration files, and 
provides a unified interface for accessing configuration values throughout the application.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, Union, List

# Import utility functions
from utils import load_dotenv, load_json, get_env, get_project_dirs

# Initialize logger
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

class Config:
    """Centralized configuration management."""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration from environment variables and config file.
        
        Args:
            config_file: Optional path to JSON configuration file
        """
        # Load config file if provided
        self.config_data = {}
        if config_file:
            try:
                self.config_data = load_json(config_file)
                logger.info(f"Loaded configuration from {config_file}")
            except Exception as e:
                logger.error(f"Error loading configuration from {config_file}: {e}")
        
        # Initialize directory structure
        self.data_dir = get_env("DATA_DIR", "data")
        self.dirs = get_project_dirs(self.data_dir)
        
        # API keys with fallbacks
        self.api_keys = {
            "USDA_API_KEY": get_env("USDA_API_KEY"),
            "OPENAI_API_KEY": get_env("OPENAI_API_KEY")
        }
        
        # API configuration
        self.api_config = {
            "USDA_API_BASE_URL": get_env("USDA_API_BASE_URL", "https://api.nal.usda.gov/fdc/v1"),
            "OPENFOODFACTS_API_BASE_URL": get_env(
                "OPENFOODFACTS_API_BASE_URL", "https://world.openfoodfacts.org/api/v2"
            ),
            "RATE_LIMIT_DELAY": float(get_env("RATE_LIMIT_DELAY", "0.5"))
        }
        
        # AI settings
        self.ai_settings = {
            "model": get_env("AI_MODEL", "gpt-4o-mini"),
            "temperature": float(get_env("AI_TEMPERATURE", "0.2")),
            "max_tokens": int(get_env("AI_MAX_TOKENS", "2000"))
        }
        
        # Processing settings
        self.processing = {
            "batch_size": int(get_env("BATCH_SIZE", "10")),
            "force_reprocess": self._parse_bool(get_env("FORCE_REPROCESS", "False"))
        }
        
        # Literature sources (from config file)
        self.literature_sources = self.config_data.get("literature_sources", [])
        
        # Additional settings
        self.continue_on_failure = self._parse_bool(
            get_env("CONTINUE_ON_FAILURE", str(self.config_data.get("continue_on_failure", False)))
        )
    
    def _parse_bool(self, value: str) -> bool:
        """Convert string to boolean."""
        return value.lower() in ("yes", "true", "t", "1")
    
    def get_api_key(self, service: str) -> Optional[str]:
        """
        Get API key for a specific service.
        
        Args:
            service: Service name (e.g., "USDA", "OPENAI")
        
        Returns:
            API key if available, None otherwise
        """
        key_name = f"{service.upper()}_API_KEY"
        return self.api_keys.get(key_name)
    
    def get_api_url(self, service: str) -> str:
        """
        Get base URL for a specific API service.
        
        Args:
            service: Service name (e.g., "USDA", "OPENFOODFACTS")
        
        Returns:
            Base URL for the API
        """
        url_name = f"{service.upper()}_API_BASE_URL"
        return self.api_config.get(url_name, "")
    
    def get_value(self, path: str, default: Any = None) -> Any:
        """
        Get configuration value by dot-notation path.
        
        Args:
            path: Dot-notation path (e.g., "api_config.USDA_API_BASE_URL")
            default: Default value if path not found
            
        Returns:
            Configuration value or default
        """
        parts = path.split('.')
        value = self.__dict__
        
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                try:
                    value = getattr(value, part)
                except (AttributeError, TypeError):
                    return default
        
        return value
    
    def get_directory(self, name: str) -> str:
        """
        Get path to a specific project directory.
        
        Args:
            name: Directory name from the predefined project structure
            
        Returns:
            Full path to the directory
        """
        return self.dirs.get(name, "")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "api_keys": {k: "***" if v else None for k, v in self.api_keys.items()},  # Mask actual keys
            "api_config": self.api_config,
            "ai_settings": self.ai_settings,
            "processing": self.processing,
            "dirs": self.dirs,
            "literature_sources": self.literature_sources,
            "continue_on_failure": self.continue_on_failure
        }


# Create a default configuration instance
default_config = Config()

def get_config(config_file: Optional[str] = None) -> Config:
    """
    Get a configuration instance.
    
    Args:
        config_file: Optional path to configuration file
    
    Returns:
        Configuration instance
    """
    if config_file:
        return Config(config_file)
    return default_config