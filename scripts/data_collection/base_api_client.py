"""
Base API client for the Nutritional Psychiatry Dataset project.
"""

import logging
from typing import Dict, Any, Optional, List
from utils.api_utils import make_request
from data.postgres_client import PostgresClient

# Initialize logger
logger = logging.getLogger(__name__)

class BaseAPIClient:
    """
    Base class for API clients in the Nutritional Psychiatry Dataset project.
    
    This class provides common functionality for making API requests,
    handling responses, and storing data in the database.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        db_client: Optional[PostgresClient] = None
    ):
        """
        Initialize the API client.
        
        Args:
            api_key: API key for authentication
            base_url: Base URL for API requests
            db_client: Database client for storing results
        """
        self.api_key = api_key
        self.base_url = base_url
        self.db_client = db_client
        
        # Initialize logger
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def make_request(
        self,
        endpoint: str,
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
            endpoint: API endpoint
            params: Query parameters
            headers: Request headers
            method: HTTP method
            retry_count: Number of retry attempts
            retry_delay: Initial delay between retries
            timeout: Request timeout in seconds
        
        Returns:
            JSON response as dictionary
        """
        url = f"{self.base_url}/{endpoint}"
        
        # Add API key to headers if not present
        if headers is None:
            headers = {}
        if self.api_key and "Authorization" not in headers:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        return make_request(
            url=url,
            params=params,
            headers=headers,
            method=method,
            retry_count=retry_count,
            retry_delay=retry_delay,
            timeout=timeout
        )
    
    def search(
        self,
        query: str,
        page_size: int = 25,
        page_number: int = 1,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Search for items using the API.
        
        Args:
            query: Search query
            page_size: Number of results per page
            page_number: Page number
            **kwargs: Additional search parameters
        
        Returns:
            Search results
        """
        raise NotImplementedError("Subclasses must implement search()")
    
    def get_details(self, item_id: str, **kwargs) -> Dict[str, Any]:
        """
        Get detailed information for an item.
        
        Args:
            item_id: Item identifier
            **kwargs: Additional parameters
        
        Returns:
            Item details
        """
        raise NotImplementedError("Subclasses must implement get_details()")
    
    def save_to_database(self, data: Dict[str, Any]) -> str:
        """
        Save API response data to the database.
        
        Args:
            data: Data to save
        
        Returns:
            Database ID of saved item
        """
        if not self.db_client:
            raise ValueError("Database client not initialized")
        
        try:
            return self.db_client.import_food_from_json(data)
        except Exception as e:
            self.logger.error(f"Error saving to database: {e}")
            raise
    
    def process_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process API response data.
        
        Args:
            response: Raw API response
        
        Returns:
            Processed data
        """
        raise NotImplementedError("Subclasses must implement process_response()")
    
    def validate_response(self, response: Dict[str, Any]) -> bool:
        """
        Validate API response data.
        
        Args:
            response: API response
        
        Returns:
            Whether the response is valid
        """
        raise NotImplementedError("Subclasses must implement validate_response()") 