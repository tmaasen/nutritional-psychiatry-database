#!/usr/bin/env python3
"""
USDA FoodData Central API Integration
This script interfaces with the USDA FoodData Central API to retrieve food data.

This script assumes:
- You have registered for a USDA FoodData Central API key
- The API key is set as an environment variable or provided as an argument
- Internet connectivity to access the USDA API
- Data is saved to `data/raw/usda_foods/` by default
- A predefined list of foods is queried based on nutritional psychiatry relevance
"""

import os
import json
import time
import requests
from typing import Dict, List, Any, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class USDAFoodDataCentralAPI:
    """Client for the USDA FoodData Central API."""
    
    BASE_URL = "https://api.nal.usda.gov/fdc/v1"
    
    def __init__(self, api_key: str = None):
        """Initialize the API client with an API key."""
        self.api_key = api_key or os.environ.get("USDA_API_KEY")
        if not self.api_key:
            raise ValueError("USDA API key is required. Set it as an argument or as USDA_API_KEY environment variable.")
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make a request to the API with proper error handling and rate limiting."""
        if params is None:
            params = {}
        
        params['api_key'] = self.api_key
        
        url = f"{self.BASE_URL}/{endpoint}"
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            # Rate limiting: wait to avoid hitting API limits
            time.sleep(0.5)
            
            return response.json()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:
                logger.warning("Rate limit exceeded, waiting before retry...")
                time.sleep(5)  # Wait longer on rate limit
                return self._make_request(endpoint, params)
            else:
                logger.error(f"HTTP error: {e}")
                raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            raise
        except json.JSONDecodeError:
            logger.error("Error parsing JSON response")
            raise
    
    def search_foods(self, query: str, page_size: int = 25, page_number: int = 1, data_type: str = "Foundation,SR Legacy,Survey (FNDDS),Branded") -> Dict:
        """
        Search for foods by name or keyword.
        
        Args:
            query: Search terms
            page_size: Number of results per page
            page_number: Page number to return
            data_type: Comma-separated list of data types to include
        
        Returns:
            Dictionary containing search results
        """
        params = {
            'query': query,
            'pageSize': page_size,
            'pageNumber': page_number,
            'dataType': data_type
        }
        
        return self._make_request('foods/search', params)
    
    def get_food_details(self, fdc_id: str, format: str = "full") -> Dict:
        """
        Get detailed information for a specific food by its FDC ID.
        
        Args:
            fdc_id: The FDC ID of the food
            format: Level of detail to include ('full', 'abridged')
        
        Returns:
            Dictionary containing detailed food information
        """
        params = {'format': format}
        return self._make_request(f'food/{fdc_id}', params)
    
    def get_foods_list(self, fdc_ids: List[str], format: str = "full") -> List[Dict]:
        """
        Get detailed information for multiple foods by FDC ID.
        
        Args:
            fdc_ids: List of FDC IDs
            format: Level of detail to include ('full', 'abridged')
        
        Returns:
            List of dictionaries containing detailed food information
        """
        url = f"{self.BASE_URL}/foods"
        params = {'api_key': self.api_key, 'format': format}
        
        try:
            response = requests.post(url, json=fdc_ids, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            raise
    
    def save_food_data(self, food_data: Dict, output_dir: str, filename: Optional[str] = None) -> str:
        """
        Save food data to a JSON file.
        
        Args:
            food_data: Food data to save
            output_dir: Directory to save to
            filename: Optional filename (defaults to FDC ID)
        
        Returns:
            Path to saved file
        """
        os.makedirs(output_dir, exist_ok=True)
        
        if not filename:
            filename = f"{food_data.get('fdcId', 'unknown')}.json"
        
        file_path = os.path.join(output_dir, filename)
        
        with open(file_path, 'w') as f:
            json.dump(food_data, f, indent=2)
        
        logger.info(f"Saved food data to {file_path}")
        return file_path


def fetch_poc_foods(api_client: USDAFoodDataCentralAPI, output_dir: str) -> List[str]:
    """
    Fetch a predefined list of foods for the POC dataset.
    
    Args:
        api_client: Initialized API client
        output_dir: Directory to save raw food data
    
    Returns:
        List of paths to saved food data files
    """
    # Example foods representing diverse categories for POC
    poc_foods = [
        {"name": "Blueberries", "search_term": "blueberries raw"}
    ]
    
    saved_files = []
    for food in poc_foods:
        logger.info(f"Searching for {food['name']}...")
        search_results = api_client.search_foods(food['search_term'])
        
        if not search_results.get('foods'):
            logger.warning(f"No results found for {food['name']}")
            continue
        
        # Get the most relevant result (first one)
        fdc_id = search_results['foods'][0]['fdcId']
        logger.info(f"Found FDC ID {fdc_id} for {food['name']}")
        
        # Get detailed food data
        try:
            food_details = api_client.get_food_details(fdc_id)
            filename = f"{food['name'].lower().replace(' ', '_')}.json"
            saved_path = api_client.save_food_data(food_details, output_dir, filename)
            saved_files.append(saved_path)
        except Exception as e:
            logger.error(f"Error fetching details for {food['name']}: {e}")
    
    return saved_files


def main():
    """Main function to execute the script."""
    output_dir = os.path.join("data", "raw", "usda_foods")
    
    # Use API key from environment variable or input
    api_key = os.environ.get("USDA_API_KEY")
    if not api_key:
        api_key = input("Enter your USDA FoodData Central API key: ")
    
    try:
        api_client = USDAFoodDataCentralAPI(api_key)
        logger.info("Fetching POC foods...")
        saved_files = fetch_poc_foods(api_client, output_dir)
        logger.info(f"Successfully saved {len(saved_files)} food files")
    except Exception as e:
        logger.error(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
