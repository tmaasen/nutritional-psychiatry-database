"""
OpenFoodFacts API Integration with Python-native Schema
This script interfaces with the OpenFoodFacts API to retrieve food data.

Features:
- Uses Python dataclasses for the schema definition 
- Clean separation of API client, data transformer, and repository
- Uses project utility modules for HTTP requests, logging, and configuration
"""

import time
from typing import Dict, List, Optional, Any, Union

# Import utility modules
from models.schema_validator import SchemaValidator
from scripts.data_processing.food_data_transformer import FoodDataTransformer
from utils.api_utils import make_request
from utils.logging_utils import setup_logging
from utils.config_utils import get_config
from scripts.data_collection.base_api_client import BaseAPIClient
from data.postgres_client import PostgresClient

# Initialize logger
logger = setup_logging(__name__)

# Load configuration
config = get_config()

class OpenFoodFactsClient:
    """Client for the OpenFoodFacts API, handles only API interactions."""
    
    def __init__(self, user_agent: str = None, base_url: str = None):
        """
        Initialize the API client with user agent information.
        
        Args:
            user_agent: Identification string for API requests
            base_url: Base URL for API requests
        """
        self.user_agent = user_agent or "NutritionalPsychiatryDataset/1.0"
        self.base_url = base_url or config.get_api_url("OPENFOODFACTS") or "https://world.openfoodfacts.org/api/v2"
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
        
        Args:
            query: General search term
            brands: Filter by brand(s)
            categories: Filter by categories
            page: Page number for pagination
            page_size: Number of results per page
            fields: Comma-separated fields to include
            
        Returns:
            Dictionary containing search results
        """
        endpoint = f"{self.base_url}/search"
        
        if fields is None:
            # Default fields to fetch - focus on nutrition data
            fields = (
                "code,product_name,brands,categories_tags,image_url,"
                "nutriments,nutrient_levels,nutrition_score_fr,"
                "ingredients_analysis_tags,ingredients_text_with_allergens,"
                "serving_size,nutrient_levels"
            )
        
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
        
        try:
            response = make_request(
                url=endpoint,
                params=params,
                headers=self.headers,
                retry_count=3,
                timeout=30
            )
            
            # Rate limiting
            time.sleep(1)  # Be nice to the OFF API
            
            return response
        except Exception as e:
            logger.error(f"Error searching products: {e}")
            raise
    
    def get_product(self, barcode: str, fields: str = None) -> Dict:
        """
        Get detailed information about a specific product by barcode.
        
        Args:
            barcode: Product barcode
            fields: Comma-separated fields to include
        
        Returns:
            Dictionary containing product information
        """
        if not barcode:
            raise ValueError("Barcode is required")
            
        endpoint = f"{self.base_url}/product/{barcode}"
        
        params = {}
        if fields:
            params["fields"] = fields
        
        try:
            response = make_request(
                url=endpoint,
                params=params,
                headers=self.headers,
                retry_count=3,
                timeout=30
            )
            
            # Rate limiting
            time.sleep(1)
            
            return response
        except Exception as e:
            logger.error(f"Error getting product {barcode}: {e}")
            raise

class OpenFoodFactsAPI(BaseAPIClient):
    """
    Main class for OpenFoodFacts API integration.
    Coordinates the client, transformer and data storage.
    """
    
    def __init__(self, db_client: PostgresClient = None):
        """
        Initialize the OpenFoodFacts API integration.
        
        Args:
            db_client: Database client for storing results
        """
        super().__init__(db_client=db_client)
        self.client = OpenFoodFactsClient()
        self.transformer = FoodDataTransformer()
        self.validator = SchemaValidator()
    
    def search(self, query: str) -> Dict:
        """
        Search for products based on query.
        
        Args:
            query: Search term
            
        Returns:
            Dictionary with search results
        """
        return self.client.search_products(query=query)
    
    def get_details(self, barcode: str) -> Dict:
        """
        Get detailed product information.
        
        Args:
            barcode: Product barcode
            
        Returns:
            Dictionary with product details
        """
        return self.client.get_product(barcode)
    
    def process_response(self, response: Dict) -> Dict:
        """
        Process response data.
        
        Args:
            response: API response data
            
        Returns:
            Processed data in schema format
        """
        return self.transformer.transform_to_schema(response)
    
    def validate_response(self, data: Dict) -> bool:
        """
        Validate processed data.
        
        Args:
            data: Processed data
            
        Returns:
            True if valid, False otherwise
        """
        errors = self.validator.validate_food_data(data)
        if errors:
            logger.warning(f"Validation errors: {errors}")
            return False
        return True
    
    def search_and_import(self, query: str, limit: int = 10) -> List[str]:
        """
        Search for products and import them to the database.
        
        Args:
            query: Search term
            limit: Maximum number of products to save
            
        Returns:
            List of imported food IDs
        """
        if not self.db_client:
            raise ValueError("Database client is required for import")
            
        imported_foods = []
        try:
            # Search for products based on query
            results = self.search(query)
            
            count = 0
            
            for product in results.get("products", []):
                if count >= limit:
                    break
                
                # Get full product details
                try:
                    product_data = {"product": product}  # Wrap in same format as API response
                    transformed = self.process_response(product_data)
                    
                    if transformed and self.validate_response(transformed):
                        # Import to DB
                        food_id = self.db_client.import_food_from_json(transformed)
                        imported_foods.append(food_id)
                        logger.info(f"Imported {transformed['name']} to database")
                        
                        count += 1
                except Exception as e:
                    logger.error(f"Error processing product {product.get('code')}: {e}")
                    
            return imported_foods
            
        except Exception as e:
            logger.error(f"Error searching for {query}: {e}")
            raise