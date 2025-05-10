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

def setup_logging(name=None, level=logging.INFO):
    """Simple cloud-ready logging setup."""
    logger = logging.getLogger(name or __name__)
    logger.setLevel(level)
    
    # Clear existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Add stdout handler
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger


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