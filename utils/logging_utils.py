#!/usr/bin/env python3
"""
Logging utilities for the Nutritional Psychiatry Dataset project.

This module provides cloud-ready logging configuration that outputs to stdout/stderr
in a format suitable for container environments.
"""

import logging
import sys
import json
import os
import time
from typing import Optional, Dict, Any, Union
from functools import wraps

def setup_logging(
    name: Optional[str] = None,
    level: int = logging.INFO,
    format_type: str = "text"
) -> logging.Logger:
    """
    Set up cloud-ready logging with consistent formatting.
    
    Args:
        name: Logger name (defaults to the module name)
        level: Logging level
        format_type: "text" or "json" for structured logging
    
    Returns:
        Configured logger instance
    """
    # Use the calling module's name if not specified
    if name is None:
        name = logging.getLogger().name
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Always output to stdout
    handler = logging.StreamHandler(sys.stdout)
    
    if format_type.lower() == "json":
        formatter = JsonLogFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger

class JsonLogFormatter(logging.Formatter):
    """
    Format logs as JSON for structured logging.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as JSON."""
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "process": record.process,
            "thread": record.thread,
        }
        
        # Add exception info if available
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key.startswith("_") or key in log_data:
                continue
            if isinstance(value, (str, int, float, bool, type(None))):
                log_data[key] = value
        
        return json.dumps(log_data)

def log_execution_time(logger: Optional[logging.Logger] = None):
    """
    Decorator to log function execution time.
    
    Args:
        logger: Logger to use (defaults to module-level logger)
    """
    if logger is None:
        logger = logging.getLogger()
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.debug(f"{func.__name__} executed in {execution_time:.4f} seconds")
            return result
        return wrapper
    
    return decorator