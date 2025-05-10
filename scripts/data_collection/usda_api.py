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
from typing import Dict, List, Any
from utils.db_utils import PostgresClient
import logging
from config import get_config

# Add these imports
from utils.nutrient_utils import extract_nutrient_by_mapping, calculate_nutrient_completeness
from utils.data_utils import generate_food_id, create_food_metadata
from utils.api_utils import make_api_request
from constants.food_data_constants import (
    USDA_STANDARD_NUTRIENTS_MAPPING,
    USDA_BRAIN_NUTRIENTS_MAPPING,
    USDA_UNIT_CONVERSIONS,
    COMPLETENESS_REQUIRED_FIELDS
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class USDAFoodDataCentralAPI:
    """Client for the USDA FoodData Central API."""
        
    def __init__(self, api_key: str = None):
        """Initialize the API client with an API key."""
        config = get_config()
        self.api_key = api_key or config.get_api_key("USDA")
        self.base_url = config.get_api_url("USDA")
        
        if not self.api_key:
            raise ValueError("USDA API key is required. Set it in .env file or pass as argument.")
    
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
    
    # Search for food
    search_results = api_client.search_foods(search_term)
    
    if not search_results.get('foods'):
        logger.warning(f"No results found for {search_term}")
        return imported_foods
    
    # Get the top results up to the limit
    top_results = search_results['foods'][:limit]
    
    for food in top_results:
        try:
            # Get the food ID
            fdc_id = food.get('fdcId')
            if not fdc_id:
                continue
                
            logger.info(f"Processing {food.get('description', 'Unknown')} (FDC ID: {fdc_id})")
            
            # Get detailed food data
            food_details = api_client.get_food_details(fdc_id)
            
            # Transform and save
            transformed_data = transform_to_schema(food_details)
            food_id = db_client.import_food_from_json(transformed_data)
            
            imported_foods.append(food_id)
            logger.info(f"Imported {food.get('description', 'Unknown')} with ID {food_id}")
            
        except Exception as e:
            logger.error(f"Error processing food: {e}", exc_info=True)
    
    return imported_foods
        
def transform_to_schema(usda_food: Dict) -> Dict:
    """Transform USDA FoodData Central product data to our schema format."""
    food = usda_food
    
    if not food:
        logger.warning("Empty food data")
        return {}

    nutrients = food.get("foodNutrients", [])
    
    # Generate food ID using utility method
    food_id = generate_food_id("usda", food.get('fdcId', ''))
    
    # Create standard metadata using utility
    source_url = f"https://fdc.nal.usda.gov/fdc-app.html#/food-details/{food.get('fdcId', '')}/nutrients"
    metadata = create_food_metadata(
        source="usda",
        original_id=str(food.get('fdcId', '')),
        source_url=source_url,
        additional_tags=[food.get("foodCategory", {}).get("description", "")]
    )

    # Create basis of transformed data
    transformed = {
        "food_id": food_id,
        "name": food.get("description", ""),
        "description": food.get("ingredients", food.get("description", "")),
        "category": food.get("foodCategory", {}).get("description", "Miscellaneous"),
        "serving_info": {
            "serving_size": 100.0,
            "serving_unit": "g",
            "household_serving": food.get("householdServingFullText", "")
        },
        "standard_nutrients": _extract_standard_nutrients(nutrients),
        "brain_nutrients": _extract_brain_nutrients(nutrients),
        "bioactive_compounds": {},
        "data_quality": {
            "completeness": _calculate_completeness(nutrients),
            "overall_confidence": 7,
            "brain_nutrients_source": "usda"
        },
        "metadata": metadata
    }
    
    return transformed

def _extract_standard_nutrients(food_nutrients: List[Dict]) -> Dict:
    """Extract standard nutrients from USDA nutriments data."""
    return extract_nutrient_by_mapping(
        food_nutrients, 
        USDA_STANDARD_NUTRIENTS_MAPPING,
        id_field="nutrient.name",
        value_field="amount",
        unit_field="nutrient.unitName"
    )

def _extract_brain_nutrients(food_nutrients: List[Dict]) -> Dict:
    """Extract brain-specific nutrients from USDA nutriments data."""
    brain_nutrients = {}
    for nutrient in food_nutrients:
        nutrient_name = nutrient.get("nutrient", {}).get("name")
        if nutrient_name in USDA_BRAIN_NUTRIENTS_MAPPING:
            schema_name = USDA_BRAIN_NUTRIENTS_MAPPING[nutrient_name]
            value = nutrient.get("amount")
            if value is not None:
                # Unit conversions
                if nutrient.get("nutrient", {}).get("unitName") == "µg":
                    value /= 1000  # Convert µg to mg

                if nutrient_name in USDA_UNIT_CONVERSIONS["ug_to_mg"]:
                    value *= 1000  # Convert to µg

                if nutrient_name in USDA_UNIT_CONVERSIONS["g_to_mcg"]:
                    value *= 1000000  # Convert g to mcg
                brain_nutrients[schema_name] = value

    return brain_nutrients

def _calculate_completeness(food_nutrients: List[Dict[str, Any]]) -> float:
    """Calculate completeness score for nutriment data."""
    # Extract nutrients into the expected format
    data = {
        "standard_nutrients": _extract_standard_nutrients(food_nutrients),
        "brain_nutrients": _extract_brain_nutrients(food_nutrients)
    }
    
    return calculate_nutrient_completeness(data, COMPLETENESS_REQUIRED_FIELDS)

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
