from typing import Dict, List, Optional

from scripts.data_processing.food_data_transformer import FoodDataTransformer
from utils.db_utils import PostgresClient
from utils.api_utils import make_api_request
from utils.logging_utils import setup_logging
from constants.food_data_constants import OFF_DEFAULT_FIELDS

logger = setup_logging(__name__)

class OpenFoodFactsAPI:
    """Client for the OpenFoodFacts API."""
    
    def __init__(self, user_agent: str = None, base_url: str = None, search_url: str = None):
        self.user_agent = user_agent or "NutritionalPsychiatryDatabase/1.0"
        self.base_url = base_url or "https://world.openfoodfacts.org/api/v2"
        self.search_url = search_url or "https://search.openfoodfacts.org/search"
        self.headers = {"User-Agent": self.user_agent}
    
    def search_products(self, query: str, limit: int = 3) -> Dict:
        """
        Search products using the newer search-a-licious API with country filtering.
        """
        params = {
            "q": query,
            "page": 1, # Page to request, starts at 1.
            "page_size": 1, # Number of results to return per page.
            "langs": "['en']",
            "fields": OFF_DEFAULT_FIELDS
        }
        
        # if country:
        #     params["value_0"] = "en:united-states"
        
        return make_api_request(
            url=self.search_url,
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

def search_and_import(api_client: OpenFoodFactsAPI, 
                      db_client: PostgresClient, 
                      query: str, 
                      limit: int = 3) -> List[str]:
    if not db_client:
        raise ValueError("Database client is required for import")
        
    imported_foods = []
    food_transformer = FoodDataTransformer()
    
    search_results = api_client.search_products(
        query=query,
        limit=limit
    )
    
    if not search_results.get("hits"):
        logger.warning(f"No results found for query '{query}'")
        return imported_foods
    
    # Process each product up to the limit
    count = 0
    for product_brief in search_results.get("hits", [])[:limit]:
        try:
            product_code = product_brief.get("code")
            if not product_code:
                continue

            product_name = product_brief.get("product_name", "")
            # Skip if name doesn't contain the search term
            if query.lower() not in product_name.lower():
                continue
                
            logger.info(f"Retrieving complete data for {product_brief.get('product_name', 'Unknown')} (Code: {product_code})")
            
            product_data = api_client.get_product(product_code)
            
            if "product" not in product_data or "nutriments" not in product_data["product"]:
                continue
            
            transformed = food_transformer.transform_off_data(product_data)
            
            food_id = db_client.import_food_from_json(transformed)
            imported_foods.append(food_id)
            logger.info(f"Imported {transformed.name} to database")
            count += 1
            
            if count >= limit or len(imported_foods) >= 1:
                break
                
        except Exception as e:
            logger.error(f"Error processing product {product_brief.get('code')}: {e}")
    
    return imported_foods