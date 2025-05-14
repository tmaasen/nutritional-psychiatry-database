# utils/api_utils.py
"""
API request utilities for the Nutritional Psychiatry Dataset project.
"""

import time
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def make_api_request(
    url: str,
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    method: str = "GET",
    api_key: Optional[str] = None,
    api_key_param: str = "api_key",
    retry_count: int = 3,
    retry_delay: float = 1.0,
    timeout: int = 30,
    rate_limit_delay: float = 0.5
) -> Dict[str, Any]:
    """
    Make an API request.
    
    Args:
        url: API endpoint URL
        params: Query parameters
        headers: Request headers
        method: HTTP method
        api_key: Optional API key
        api_key_param: Parameter name for API key
        retry_count: Number of retry attempts
        retry_delay: Initial delay between retries
        timeout: Request timeout in seconds
        rate_limit_delay: Delay after request to respect rate limits
        
    Returns:
        JSON response as dictionary
    """
    if api_key:
        if params is None:
            params = {}
        params[api_key_param] = api_key
    
    response = make_request(
        url=url,
        params=params,
        headers=headers,
        method=method,
        retry_count=retry_count,
        retry_delay=retry_delay,
        timeout=timeout
    )
    
    # Respect rate limits
    time.sleep(rate_limit_delay)
    
    return response