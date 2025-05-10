"""
OpenFoodFacts API Integration with Python-native Schema
This script interfaces with the OpenFoodFacts API to retrieve food data.
"""

# Standard imports
from typing import Dict, List

# Project utilities
from scripts.data_processing.food_data_transformer import FoodDataTransformer
from utils.db_utils import PostgresClient
from utils.api_utils import make_api_request
from utils.logging_utils import setup_logging

# Constants
from constants.food_data_constants import OFF_DEFAULT_FIELDS

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
    food_transformer = FoodDataTransformer()
    
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
            transformed = food_transformer.transform_off_data(product_data)
            
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