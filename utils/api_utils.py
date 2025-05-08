# utils/api_utils.py
"""
API request utilities for the Nutritional Psychiatry Dataset project.
"""

import time
import requests
import logging
from typing import Dict, Any, Optional

# Initialize logger
logger = logging.getLogger(__name__)

def make_request(
    url: str,
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    method: str = "GET",
    retry_count: int = 3,
    retry_delay: float = 1.0,
    timeout: int = 30
) -> Dict[str, Any]:
    """
    Make an API request with retry logic and proper error handling.
    
    Args:
        url: API endpoint URL
        params: Query parameters
        headers: Request headers
        method: HTTP method (GET, POST, etc.)
        retry_count: Number of retry attempts
        retry_delay: Initial delay between retries (exponential backoff)
        timeout: Request timeout in seconds
    
    Returns:
        JSON response as dictionary
    
    Raises:
        requests.exceptions.RequestException: For request failures after retries
    """
    params = params or {}
    headers = headers or {}
    
    attempt = 0
    while attempt < retry_count:
        try:
            if method.upper() == "GET":
                response = requests.get(
                    url, 
                    params=params, 
                    headers=headers,
                    timeout=timeout
                )
            elif method.upper() == "POST":
                response = requests.post(
                    url, 
                    json=params, 
                    headers=headers,
                    timeout=timeout
                )
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            # Raise for HTTP errors
            response.raise_for_status()
            
            # Return JSON response
            return response.json()
            
        except requests.exceptions.RequestException as e:
            attempt += 1
            
            # If it's a rate limit issue, wait longer
            if hasattr(e, 'response') and e.response and e.response.status_code == 429:
                retry_delay *= 3  # Wait much longer for rate limits
            
            if attempt < retry_count:
                logger.warning(f"Request failed: {e}. Retrying in {retry_delay:.1f}s ({attempt}/{retry_count})")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                logger.error(f"Request failed after {retry_count} attempts: {e}")
                raise