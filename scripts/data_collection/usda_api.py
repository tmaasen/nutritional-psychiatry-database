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
import argparse
import time
import requests
from typing import Dict, List, Any, Optional, Tuple
from data.postgres_client import PostgresClient
import logging
from config import get_config
from datetime import datetime

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
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make a request to the API with proper error handling and rate limiting."""
        if params is None:
            params = {}
        
        params['api_key'] = self.api_key
        
        url = f"{self.base_url}/{endpoint}"
        
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
        url = f"{self.base_url}/foods"
        params = {'api_key': self.api_key, 'format': format}
        
        try:
            response = requests.post(url, json=fdc_ids, params=params)
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
            food_id = db_client.import_food_from_json(food_details)
            imported_foods.append(food_id)
        except Exception as e:
            logger.error(f"Error fetching details for {food['name']}: {e}")
    
    return imported_foods
        
def transform_to_schema(usda_food: Dict) -> Dict:
        """
        Transform USDA FoodData Central product data to our schema format.
        
        Args:
            off_product: USDA FoodData Central product data
        
        Returns:
            Dictionary in our schema format
        """
        
        # Extract product data
        food = usda_food
        
        if not food:
            logger.warning("Empty food data")
            return {}

        # Extract nutriment data
        nutrients = food.get("foodNutrients", [])

        # Create basis of transformed data
        transformed = {
            "food_id": f"usda_{food.get('fdcId', '')}",
            "name": food.get("description", ""),
            "description": food.get("ingredients", food.get("description", "")),
            "category": food.get("foodCategory", {}).get("description", "Miscellaneous"),
            "serving_info": {
                "serving_size": 100.0,  # Default
                "serving_unit": "g",
                "household_serving": food.get("householdServingFullText", "")
            },
            "standard_nutrients": _extract_standard_nutrients(nutrients),
            "brain_nutrients": _extract_brain_nutrients(nutrients),
            "bioactive_compounds": {},  # Mostly not available in OFF
            "data_quality": {
                "completeness": _calculate_completeness(nutrients),
                "overall_confidence": 7,  # USDA data is generally reliable
                "brain_nutrients_source": "usda"
            },
            "metadata": {
                "version": "0.1.0",
                "created": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "source_urls": [
                    f"https://fdc.nal.usda.gov/fdc-app.html#/food-details/{food.get('fdcId', '')}/nutrients"
                ],
                "source_ids": {
                    "usda_fdc_id": food.get("fdcId", "")
                },
            }
        }
        return transformed

def _extract_standard_nutrients(food_nutrients: List[Dict]) -> Dict:
    """Extract standard nutrients from USDA nutriments data."""
    # Mapping from USDA field names to our schema
    nutrient_mapping = {
        "Energy": "calories",
        "Protein": "protein_g",
        "Carbohydrate, by difference": "carbohydrates_g",
        "Total lipid (fat)": "fat_g",
        "Fiber, total dietary": "fiber_g",
        "Sugars, total including NLEA": "sugars_g",
        "Calcium, Ca": "calcium_mg",
        "Iron, Fe": "iron_mg",
        "Magnesium, Mg": "magnesium_mg",
        "Phosphorus, P": "phosphorus_mg",
        "Potassium, K": "potassium_mg",
        "Sodium, Na": "sodium_mg",
        "Zinc, Zn": "zinc_mg",
        "Copper, Cu": "copper_mg",
        "Manganese, Mn": "manganese_mg",
        "Selenium, Se": "selenium_mcg",
        "Vitamin C, total ascorbic acid": "vitamin_c_mg",
        "Vitamin A, IU": "vitamin_a_iu"
    }

    standard_nutrients = {}
    for nutrient in food_nutrients:
        nutrient_name = nutrient.get("nutrient", {}).get("name")
        if nutrient_name in nutrient_mapping:
            schema_name = nutrient_mapping[nutrient_name]
            value = nutrient.get("amount")
            if value is not None:
                # Unit conversions if needed
                if nutrient.get("nutrient", {}).get("unitName") == "µg":
                    value /= 1000 #Convert ug to mg
                if nutrient_name in ["Selenium, Se"]:
                    value *= 1000 # Convert g to mcg
                standard_nutrients[schema_name] = value

    return standard_nutrients


def _extract_brain_nutrients(food_nutrients: List[Dict]) -> Dict:
    """Extract brain-specific nutrients from USDA nutriments data."""
    # Mapping from USDA field names to our schema
    nutrient_mapping = {
        "Tryptophan": "tryptophan_mg",
        "Tyrosine": "tyrosine_mg",
        "Vitamin B-6": "vitamin_b6_mg",
        "Folate, total": "folate_mcg",
        "Vitamin B-12": "vitamin_b12_mcg",
        "Vitamin D (D2 + D3)": "vitamin_d_mcg",
        "Magnesium, Mg": "magnesium_mg",
        "Zinc, Zn": "zinc_mg",
        "Iron, Fe": "iron_mg",
        "Selenium, Se": "selenium_mcg",
        "Choline, total": "choline_mg"
    }

    brain_nutrients = {}
    for nutrient in food_nutrients:
        nutrient_name = nutrient.get("nutrient", {}).get("name")
        if nutrient_name in nutrient_mapping:
            schema_name = nutrient_mapping[nutrient_name]
            value = nutrient.get("amount")
            if value is not None:
                # Unit conversions
                if nutrient.get("nutrient", {}).get("unitName") == "µg":
                    value *= 1000 #Convert ug to mg

                if nutrient_name in ["Folate, total"]:
                    value *= 1000000  # Convert g to mcg

                if nutrient_name in ["Vitamin B-12","Vitamin D (D2 + D3)"]:
                    value *= 1000000  # Convert g to mcg

                if nutrient_name == "Selenium, Se":
                    value *= 1000000 # Convert g to mcg
                brain_nutrients[schema_name] = value

    return brain_nutrients

def _calculate_completeness(food_nutrients: List[Dict]) -> float:
        """Calculate completeness score for nutriment data."""
        # Count key nutrients we'd expect to have
        key_nutrients = [
            "Energy", "Protein", "Carbohydrate, by difference",
            "Total lipid (fat)", "Fiber, total dietary", "Sugars, total including NLEA"
        ]

        # Brain nutrients we'd ideally have
        brain_nutrients = [
            "Vitamin B-6", "Folate, total", "Vitamin B-12",
            "Vitamin D (D2 + D3)", "Magnesium, Mg", "Zinc, Zn",
            "Iron, Fe", "Selenium, Se"
        ]

        # Count how many we have
        standard_count = sum(1 for n in key_nutrients if any(n in nutrient.get("nutrient", {}).get("name", "") for nutrient in food_nutrients))
        brain_count = sum(1 for n in brain_nutrients if any(n in nutrient.get("nutrient", {}).get("name", "") for nutrient in food_nutrients))

        # Calculate completeness score
        standard_completeness = standard_count / len(key_nutrients)
        brain_completeness = brain_count / len(brain_nutrients) if brain_count > 0 else 0

        # Weight standard nutrients more heavily
        overall_completeness = (standard_completeness * 0.7) + (brain_completeness * 0.3)

        return round(overall_completeness, 2)
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
