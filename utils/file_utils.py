# utils/file_utils.py
"""
File I/O utilities for the Nutritional Psychiatry Dataset project.
"""

import json
import os
import glob
from typing import Dict, List, Any, Optional, Union


def load_json(filepath: str) -> Dict[str, Any]:
    """
    Load JSON from file with proper error handling.
    
    Args:
        filepath: Path to JSON file
    
    Returns:
        JSON content as dictionary
    
    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file contains invalid JSON
    """
    with open(filepath, 'r') as f:
        return json.load(f)


def save_json(data: Union[Dict[str, Any], List[Any]], filepath: str, indent: int = 2) -> None:
    """
    Save data to JSON file with error handling.
    
    Args:
        data: Data to save
        filepath: Output file path
        indent: JSON indentation level
    """
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=indent)


def find_files(directory: str, pattern: str = "*.json") -> List[str]:
    """
    Find files matching a pattern in a directory.
    
    Args:
        directory: Directory to search
        pattern: File glob pattern
    
    Returns:
        List of matching file paths
    """
    return glob.glob(os.path.join(directory, pattern))


def ensure_directory(directory: str) -> None:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        directory: Directory path to create
    """
    os.makedirs(directory, exist_ok=True)