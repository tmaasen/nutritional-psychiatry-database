# utils/logging_utils.py
"""
Logging utilities for the Nutritional Psychiatry Dataset project.
"""

import logging
import os
from typing import Optional


def setup_logging(
    name: Optional[str] = None,
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    format_str: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
) -> logging.Logger:
    """
    Set up logging with consistent formatting across all modules.
    
    Args:
        name: Logger name (defaults to the module name)
        level: Logging level
        log_file: Optional path to log file
        format_str: Log message format string
    
    Returns:
        Configured logger instance
    """
    # Use the calling module's name if not specified
    if name is None:
        name = logging.getLogger().name
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter(format_str)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Add file handler if specified
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger