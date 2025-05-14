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
import argparse
import requests
from typing import Dict, List
from scripts.data_processing.food_data_transformer import FoodDataTransformer
from utils.db_utils import PostgresClient
from config import get_config

from utils.api_utils import make_api_request
from utils.logging_utils import setup_logging

logger = setup_logging(__name__)

class USDAFoodDataCentralAPI:
    """Client for the USDA FoodData Central API."""
        
    def __init__(self, api_key: str = None):
        config = get_config()
        self.api_key = api_key or config.get_api_key("USDA")
        self.base_url = config.get_api_url("USDA")
    
    def search_foods(self, query: str, page_size: int = 25, page_number: int = 1, data_type: str = "Foundation,SR Legacy,Survey (FNDDS),Branded") -> Dict:
        url = f"{self.base_url}/foods/search"
        params = {
            'query': query,
            'pageSize': page_size,
            'pageNumber': page_number,
            'dataType': data_type,
            'api_key': self.api_key
        }
        
        return make_api_request(
            url=url,
            params=params,
            timeout=30,
            rate_limit_delay=0.5
        )
    
    def get_food_details(self, fdc_id: str, format: str = "full") -> Dict:
        """
        Get detailed information for a specific food by its FDC ID.
        
        Args:
            fdc_id: The FDC ID of the food
            format: Level of detail to include ('full', 'abridged')
        
        Returns:
            Dictionary containing detailed food information
        """
        if not fdc_id:
            raise ValueError("FDC ID is required")
            
        url = f"{self.base_url}/food/{fdc_id}"
        params = {'format': format, 'api_key': self.api_key}
        
        return make_api_request(
            url=url,
            params=params,
            timeout=30,
            rate_limit_delay=0.5
        )
    
    def get_foods_list(self, fdc_ids: List[str], format: str = "full") -> List[Dict]:
        """
        Get detailed information for multiple foods by FDC ID.
        
        Args:
            fdc_ids: List of FDC IDs
            format: Level of detail to include ('full', 'abridged')
        
        Returns:
            List of dictionaries containing detailed food information
        """
        url = f"{self.base_url}/foods"
        params = {'api_key': self.api_key, 'format': format}
        headers = {"Content-Type": "application/json"}
        
        try:
            # For this special case, we use requests directly since we need to pass the
            # fdc_ids as JSON body, not as params
            response = requests.post(url, json=fdc_ids, params=params, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            raise
     
def search_and_import(api_client: USDAFoodDataCentralAPI, db_client: PostgresClient, search_term: str, limit: int = 10) -> List[str]:
    """
    Fetch a list of foods for the database based on the search term.
    
    Args:
        api_client: Initialized API client
        db_client: database client
        search_term: Search term to use to query the API
        limit: Maximum number of products to save
    
    Returns:
        List of imported food ids
    """
    logger.info(f"Searching for '{search_term}'")
    
    imported_foods = []
    food_transformer = FoodDataTransformer()
    
    search_results = api_client.search_foods(search_term)
    
    if not search_results.get('foods'):
        logger.warning(f"No results found for {search_term}")
        return imported_foods
    
    # Get the top results up to the limit
    top_results = search_results['foods'][:limit]
    
    for food in top_results:
        try:
            fdc_id = food.get('fdcId')
            if not fdc_id:
                continue
                
            logger.info(f"Processing {food.get('description', 'Unknown')} (FDC ID: {fdc_id})")
            
            # Get detailed food data
            food_details = api_client.get_food_details(fdc_id)
            
            # Transform and save using the transformer
            transformed_data = food_transformer.transform_usda_data(food_details)
            food_id = db_client.import_food_from_json(transformed_data)
            
            imported_foods.append(food_id)
            logger.info(f"Imported {food.get('description', 'Unknown')} with ID {food_id}")
            
        except Exception as e:
            logger.error(f"Error processing food: {e}", exc_info=True)
    
    return imported_foods

def main():
    """Main function to execute the script."""
    parser = argparse.ArgumentParser(description="Fetch and transform USDA FoodData Central data")
    parser.add_argument("--query", help="Search term", default="blueberries raw")
    parser.add_argument("--limit", type=int, help="Maximum number of products to import", default=10)
    args = parser.parse_args()
    
    try:
        api_key = os.environ.get("USDA_API_KEY")
        if not api_key:
            api_key = input("Enter your USDA FoodData Central API key: ")
        
        # instantiate database client
        db_client = PostgresClient()

        api_client = USDAFoodDataCentralAPI(api_key)
        
        imported_foods = search_and_import(api_client, db_client, search_term=args.query, limit=args.limit)
        logger.info(f"Successfully imported {len(imported_foods)} products: {imported_foods}")
    except Exception as e:
        logger.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
