# utils/config_utils.py
"""
Configuration utilities for the Nutritional Psychiatry Dataset project.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, Union


# Initialize logger
logger = logging.getLogger(__name__)


def load_dotenv(env_file: str = ".env") -> None:
    """
    Load environment variables from .env file.
    
    Args:
        env_file: Path to .env file
    """
    if not os.path.exists(env_file):
        logger.warning(f"Environment file {env_file} not found")
        return
    
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            
            # Parse key-value pairs
            if '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip().strip('"\'')


def get_env(key: str, default: Any = None) -> Any:
    """
    Get environment variable with default fallback.
    
    Args:
        key: Environment variable name
        default: Default value if not found
    
    Returns:
        Value of environment variable or default
    """
    return os.environ.get(key, default)


def get_db_config() -> Dict[str, Any]:
    """
    Get database configuration from environment variables.
    
    Returns:
        Dictionary containing database configuration
    """
    return {
        "host": get_env("DB_HOST"),
        "port": get_env("DB_PORT", "5432"),
        "database": get_env("DB_NAME"),
        "user": get_env("DB_USER"),
        "password": get_env("DB_PASSWORD"),
        "sslmode": get_env("DB_SSLMODE", "require"),
        "min_connections": int(get_env("DB_MIN_CONNECTIONS", "1")),
        "max_connections": int(get_env("DB_MAX_CONNECTIONS", "10"))
    }


def get_api_config() -> Dict[str, Any]:
    """
    Get API configuration from environment variables.
    
    Returns:
        Dictionary containing API configuration
    """
    return {
        "usda_api_key": get_env("USDA_API_KEY"),
        "openfoodfacts_api_key": get_env("OPENFOODFACTS_API_KEY"),
        "openai_api_key": get_env("OPENAI_API_KEY")
    }


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from JSON file with error handling.
    
    Args:
        config_path: Path to config JSON file
    
    Returns:
        Configuration dictionary (empty if file not found)
    """
    if not config_path or not os.path.exists(config_path):
        logger.warning(f"Configuration file {config_path} not found. Using defaults.")
        return {}
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        logger.info(f"Loaded configuration from {config_path}")
        return config
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        return {}


def get_config() -> Dict[str, Any]:
    """
    Get complete configuration including environment variables and config file.
    
    Returns:
        Complete configuration dictionary
    """
    # Load environment variables
    load_dotenv()
    
    # Get database and API config
    config = {
        "database": get_db_config(),
        "api": get_api_config()
    }
    
    # Load additional config from file if exists
    config_file = get_env("CONFIG_FILE")
    if config_file:
        file_config = load_config(config_file)
        config.update(file_config)
    
    return config