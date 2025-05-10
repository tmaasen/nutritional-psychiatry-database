"""
OpenFoodFacts API Integration with Python-native Schema
This script interfaces with the OpenFoodFacts API to retrieve food data.
"""

# Standard imports
import time
from typing import Dict, List, Optional, Any, Union

# Project utilities
from utils.db_utils import PostgresClient
from utils.nutrient_utils import extract_nutrient_by_mapping, calculate_nutrient_completeness
from utils.data_utils import generate_food_id, create_food_metadata
from utils.api_utils import make_api_request
from utils.logging_utils import setup_logging

# Constants
from constants.food_data_constants import (
    OFF_STANDARD_NUTRIENTS_MAPPING,
    OFF_BRAIN_NUTRIENTS_MAPPING,
    OFF_OMEGA3_MAPPING,
    FOOD_CATEGORY_MAPPING,
    COMPLETENESS_REQUIRED_FIELDS,
    OFF_DEFAULT_FIELDS
)

# Initialize logger
logger = setup_logging(__name__)

class OpenFoodFactsAPI:
    """Client for the OpenFoodFacts API."""
    
    def __init__(self, user_agent: str = None, base_url: str = None):
        """Initialize the API client with user agent information."""
        self.user_agent = user_agent or "NutritionalPsychiatryDataset/1.0"
        self.base_url = base_url or "https://world.openfoodfacts.org/api/v2"
        self.headers = {"User-Agent": self.user_agent}
    
    def search_products(self, 
                        query: str = None, 
                        brands: str = None,
                        categories: str = None,
                        page: int = 1, 
                        page_size: int = 20,
                        fields: str = None) -> Dict:
        """
        Search for products in the OpenFoodFacts database.
        """
        endpoint = f"{self.base_url}/search"
        
        if fields is None:
            fields = OFF_DEFAULT_FIELDS
        
        params = {
            "search_terms": query,
            "brands": brands,
            "categories": categories,
            "page": page,
            "page_size": page_size,
            "fields": fields,
            "sort_by": "popularity_score"
        }
        
        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}
        
        return make_api_request(
            url=endpoint,
            params=params,
            headers=self.headers,
            retry_count=3,
            timeout=30,
            rate_limit_delay=1.0
        )
    
    def get_product(self, barcode: str, fields: str = None) -> Dict:
        """
        Get detailed information about a specific product by barcode.
        """
        if not barcode:
            raise ValueError("Barcode is required")
            
        endpoint = f"{self.base_url}/product/{barcode}"
        
        params = {}
        if fields:
            params["fields"] = fields
        
        return make_api_request(
            url=endpoint,
            params=params,
            headers=self.headers,
            retry_count=3,
            timeout=30,
            rate_limit_delay=1.0
        )

def validate_response(data: Dict) -> bool:
    """
    Validate processed data.
    
    Args:
        data: Processed data
        
    Returns:
        True if valid, False otherwise
    """
    # Basic validation
    if not data or not isinstance(data, dict):
        return False
    
    required_fields = ["food_id", "name", "category", "standard_nutrients"]
    return all(field in data for field in required_fields)

def transform_to_schema(off_product: Dict) -> Dict:
    """
    Transform OpenFoodFacts product data to our schema format.
    
    Args:
        off_product: OpenFoodFacts product data
        
    Returns:
        Dictionary in our schema format
    """
    # Extract product data
    product = off_product.get("product", {})
    
    if not product:
        logger.warning("Empty product data")
        return {}
    
    # Get nutriment data
    nutriments = product.get("nutriments", {})
    
    # Extract category using mapping
    category = _map_category(product.get("categories_tags", []))
    
    # Create standard nutrients
    standard_nutrients = extract_nutrient_by_mapping(
        nutriments, 
        OFF_STANDARD_NUTRIENTS_MAPPING
    )
    
    # Create brain nutrients
    brain_nutrients = _extract_brain_nutrients(nutriments)
    
    # Generate food ID and metadata
    food_id = generate_food_id("off", product.get('code', ''))
    source_url = f"https://world.openfoodfacts.org/product/{product.get('code', '')}"
    
    metadata = create_food_metadata(
        source="off",
        original_id=product.get('code', ''),
        source_url=source_url,
        additional_tags=product.get("categories_tags", [])
    )
    
    if "image_url" in product:
        metadata["image_url"] = product.get("image_url", "")
    
    # Calculate completeness
    data = {
        "standard_nutrients": standard_nutrients,
        "brain_nutrients": brain_nutrients
    }
    completeness = calculate_nutrient_completeness(data, COMPLETENESS_REQUIRED_FIELDS)
    
    # Build the transformed data
    transformed = {
        "food_id": food_id,
        "name": product.get("product_name", ""),
        "description": product.get("generic_name", product.get("product_name", "")),
        "category": category,
        "serving_info": {
            "serving_size": 100.0,
            "serving_unit": "g",
            "household_serving": product.get("serving_size", "")
        },
        "standard_nutrients": standard_nutrients,
        "brain_nutrients": brain_nutrients,
        "bioactive_compounds": {},
        "mental_health_impacts": [],
        "data_quality": {
            "completeness": completeness,
            "overall_confidence": 7,
            "brain_nutrients_source": "openfoodfacts"
        },
        "metadata": metadata
    }
    
    return transformed

def _map_category(categories_tags: List[str]) -> str:
    """Map OpenFoodFacts category tags to our simplified categories."""
    # Clean up category tags
    clean_tags = [tag.replace("en:", "").lower() for tag in categories_tags]
    
    # Find the first matching category
    for tag in clean_tags:
        for key, value in FOOD_CATEGORY_MAPPING.items():
            if key in tag:
                return value
    
    # Default to the first category or "Miscellaneous"
    if clean_tags:
        return clean_tags[0].capitalize()
    return "Miscellaneous"

def _extract_brain_nutrients(nutriments: Dict) -> Dict:
    """Extract brain-specific nutrients from OpenFoodFacts nutriments data."""
    brain_nutrients = {}
    omega3 = {}
    
    # Extract standard brain nutrients
    for off_name, schema_name in OFF_BRAIN_NUTRIENTS_MAPPING.items():
        if off_name in nutriments and nutriments[off_name] is not None:
            brain_nutrients[schema_name] = nutriments[off_name]
    
    # Extract omega-3 data
    for off_name, schema_name in OFF_OMEGA3_MAPPING.items():
        if off_name in nutriments and nutriments[off_name] is not None:
            omega3[schema_name] = nutriments[off_name]
    
    # Add omega-3 data if available
    if omega3:
        omega3["confidence"] = 7
        brain_nutrients["omega3"] = omega3
    
    return brain_nutrients

def search_and_import(api_client: OpenFoodFactsAPI, db_client: PostgresClient, query: str, limit: int = 10) -> List[str]:
    """
    Search for products and import them to the database.
    
    Args:
        api_client: Initialized API client
        db_client: Database client
        query: Search term
        limit: Maximum number of products to save
        
    Returns:
        List of imported food IDs
    """
    if not db_client:
        raise ValueError("Database client is required for import")
        
    imported_foods = []
    logger.info(f"Searching for '{query}'")
    
    # Search for products
    results = api_client.search_products(query)
    
    if not results.get("products"):
        logger.warning(f"No results found for {query}")
        return imported_foods
    
    # Process each product up to the limit
    count = 0
    for product in results.get("products", [])[:limit]:
        try:
            product_data = {"product": product}
            transformed = transform_to_schema(product_data)
            
            if transformed and validate_response(transformed):
                # Import to DB
                food_id = db_client.import_food_from_json(transformed)
                imported_foods.append(food_id)
                logger.info(f"Imported {transformed['name']} to database")
                count += 1
        except Exception as e:
            logger.error(f"Error processing product {product.get('code')}: {e}")
    
    return imported_foods

def main():
    """Main function to execute the script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Fetch and transform OpenFoodFacts data")
    parser.add_argument("--query", help="Search term", default="")
    parser.add_argument("--limit", type=int, help="Maximum number of products to import", default=10)
    
    args = parser.parse_args()
    
    try:
        # Instantiate database client
        db_client = PostgresClient()
        
        # Create API client
        api_client = OpenFoodFactsAPI()
        
        # Search and import
        imported_foods = search_and_import(
            api_client=api_client,
            db_client=db_client,
            query=args.query, 
            limit=args.limit
        )
        
        logger.info(f"Successfully imported {len(imported_foods)} products")
        
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    main()