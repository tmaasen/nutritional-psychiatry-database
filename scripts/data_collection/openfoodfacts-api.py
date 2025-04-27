#!/usr/bin/env python3
"""
OpenFoodFacts API Integration
This script interfaces with the OpenFoodFacts API to retrieve food data.

This script assumes:
- Direct access to the OpenFoodFacts public API (no authentication required)
- Internet connectivity to access the API
- Data is saved to `data/raw/openfoodfacts/` by default
- Foods can be searched by name, category, or other parameters
- Rate limiting to respect the OpenFoodFacts API (1 request per second)
"""

import os
import json
import time
import requests
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OpenFoodFactsAPI:
    """Client for the OpenFoodFacts API."""
    
    BASE_URL = "https://world.openfoodfacts.org/api/v2"
    
    def __init__(self, user_agent: str = None):
        """
        Initialize the API client with user agent information.
        
        Args:
            user_agent: Identification string for API requests (required by OFF)
        """
        self.user_agent = user_agent or "NutritionalPsychiatryDataset/1.0"
        self.headers = {
            "User-Agent": self.user_agent
        }
    
    def search_products(self, 
                        query: str = None, 
                        brands: str = None,
                        categories: str = None,
                        ingredients: str = None,
                        countries: str = None,
                        page: int = 1, 
                        page_size: int = 20,
                        fields: str = None,
                        sort_by: str = "popularity_score") -> Dict:
        """
        Search for products in the OpenFoodFacts database.
        
        Args:
            query: General search term
            brands: Filter by brand(s)
            categories: Filter by categories
            ingredients: Filter by ingredients
            countries: Filter by country of origin
            page: Page number for pagination
            page_size: Number of results per page
            fields: Comma-separated fields to include
            sort_by: Field to sort results by
        
        Returns:
            Dictionary containing search results
        """
        endpoint = f"{self.BASE_URL}/search"
        
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
            "ingredients": ingredients,
            "countries": countries,
            "page": page,
            "page_size": page_size,
            "fields": fields,
            "sort_by": sort_by
        }
        
        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}
        
        try:
            response = requests.get(endpoint, params=params, headers=self.headers)
            response.raise_for_status()
            
            # Rate limiting
            time.sleep(1)  # Be nice to the OFF API
            
            return response.json()
        except requests.exceptions.RequestException as e:
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
        endpoint = f"{self.BASE_URL}/product/{barcode}"
        
        params = {}
        if fields:
            params["fields"] = fields
        
        try:
            response = requests.get(endpoint, params=params, headers=self.headers)
            response.raise_for_status()
            
            # Rate limiting
            time.sleep(1)
            
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting product {barcode}: {e}")
            raise
    
    def transform_to_schema(self, off_product: Dict) -> Dict:
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
        
        # Create basis of transformed data
        transformed = {
            "food_id": f"off_{product.get('code', '')}",
            "name": product.get("product_name", ""),
            "description": product.get("generic_name", product.get("product_name", "")),
            "category": self._map_category(product.get("categories_tags", [])),
            "serving_info": {
                "serving_size": self._extract_serving_size(product.get("serving_size", "")),
                "serving_unit": "g",
                "household_serving": product.get("serving_size", "")
            },
            "standard_nutrients": self._extract_standard_nutrients(nutriments),
            "brain_nutrients": self._extract_brain_nutrients(nutriments),
            "bioactive_compounds": {},  # Mostly not available in OFF
            "data_quality": {
                "completeness": self._calculate_completeness(nutriments),
                "overall_confidence": 7,  # OpenFoodFacts data is generally reliable
                "brain_nutrients_source": "openfoodfacts"
            },
            "metadata": {
                "version": "0.1.0",
                "created": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "source_urls": [
                    f"https://world.openfoodfacts.org/product/{product.get('code', '')}"
                ],
                "source_ids": {
                    "openfoodfacts_id": product.get('code', '')
                },
                "image_url": product.get("image_url", ""),
                "tags": product.get("categories_tags", [])
            }
        }
        
        # Add inflammation index if possible
        transformed["inflammatory_index"] = self._calculate_inflammatory_index(product, nutriments)
        
        # Extract allergen info if available
        if "allergens_tags" in product:
            allergens = [allergen.replace("en:", "") for allergen in product.get("allergens_tags", [])]
            if allergens:
                transformed["allergens"] = allergens
        
        return transformed
    
    def _map_category(self, categories_tags: List[str]) -> str:
        """Map OpenFoodFacts category tags to our simplified categories."""
        category_mapping = {
            "fruits": "Fruits",
            "vegetables": "Vegetables",
            "meat": "Protein Foods",
            "fish": "Protein Foods",
            "seafood": "Protein Foods",
            "legumes": "Protein Foods",
            "dairy": "Dairy",
            "cereals": "Grains",
            "grains": "Grains",
            "breads": "Grains",
            "nuts": "Nuts and Seeds",
            "seeds": "Nuts and Seeds",
            "beverages": "Beverages",
            "sweets": "Sweets",
            "fast-food": "Processed Foods"
        }
        
        # Clean up category tags
        clean_tags = [tag.replace("en:", "").lower() for tag in categories_tags]
        
        # Find the first matching category
        for tag in clean_tags:
            for key, value in category_mapping.items():
                if key in tag:
                    return value
        
        # Default to the first category or "Miscellaneous"
        if clean_tags:
            return clean_tags[0].capitalize()
        return "Miscellaneous"
    
    def _extract_serving_size(self, serving_size_str: str) -> Optional[float]:
        """Extract numeric serving size from string."""
        if not serving_size_str:
            return 100.0  # Default to 100g if no serving size provided
        
        # Try to extract a number
        import re
        numbers = re.findall(r'(\d+(?:\.\d+)?)', serving_size_str)
        if numbers:
            try:
                return float(numbers[0])
            except ValueError:
                pass
        
        return 100.0  # Default
    
    def _extract_standard_nutrients(self, nutriments: Dict) -> Dict:
        """Extract standard nutrients from OFF nutriments data."""
        # Mapping from OFF field names to our schema
        nutrient_mapping = {
            "energy-kcal_100g": "calories",
            "proteins_100g": "protein_g",
            "carbohydrates_100g": "carbohydrates_g",
            "fat_100g": "fat_g",
            "fiber_100g": "fiber_g",
            "sugars_100g": "sugars_g",
            "calcium_100g": "calcium_mg",
            "iron_100g": "iron_mg",
            "magnesium_100g": "magnesium_mg",
            "phosphorus_100g": "phosphorus_mg",
            "potassium_100g": "potassium_mg",
            "sodium_100g": "sodium_mg",
            "zinc_100g": "zinc_mg",
            "copper_100g": "copper_mg",
            "manganese_100g": "manganese_mg",
            "selenium_100g": "selenium_mcg",
            "vitamin-c_100g": "vitamin_c_mg",
            "vitamin-a_100g": "vitamin_a_iu"
        }
        
        # Extract values and convert units where needed
        standard_nutrients = {}
        for off_name, schema_name in nutrient_mapping.items():
            if off_name in nutriments and nutriments[off_name] is not None:
                value = nutriments[off_name]
                
                # Unit conversions if needed
                if off_name in ["calcium_100g", "iron_100g", "magnesium_100g", 
                                "phosphorus_100g", "potassium_100g", "sodium_100g",
                                "zinc_100g", "copper_100g", "manganese_100g"]:
                    # Convert g to mg
                    value *= 1000
                
                if off_name == "selenium_100g":
                    # Convert g to mcg
                    value *= 1000000
                
                standard_nutrients[schema_name] = value
        
        return standard_nutrients
    
    def _extract_brain_nutrients(self, nutriments: Dict) -> Dict:
        """Extract brain-specific nutrients from OFF nutriments data."""
        # Mapping from OFF field names to our schema
        nutrient_mapping = {
            "tryptophan_100g": "tryptophan_mg",
            "tyrosine_100g": "tyrosine_mg",
            "vitamin-b6_100g": "vitamin_b6_mg",
            "folates_100g": "folate_mcg",
            "vitamin-b12_100g": "vitamin_b12_mcg",
            "vitamin-d_100g": "vitamin_d_mcg",
            "magnesium_100g": "magnesium_mg",
            "zinc_100g": "zinc_mg",
            "iron_100g": "iron_mg",
            "selenium_100g": "selenium_mcg",
            "choline_100g": "choline_mg"
        }
        
        # Extract omega-3 data
        omega3 = {}
        if "omega-3-fat_100g" in nutriments:
            omega3["total_g"] = nutriments["omega-3-fat_100g"]
        
        if "dha_100g" in nutriments:
            omega3["dha_mg"] = nutriments["dha_100g"] * 1000
        
        if "epa_100g" in nutriments:
            omega3["epa_mg"] = nutriments["epa_100g"] * 1000
        
        if "ala_100g" in nutriments:
            omega3["ala_mg"] = nutriments["ala_100g"] * 1000
        
        # Add confidence level if we have omega-3 data
        if omega3:
            omega3["confidence"] = 7
        
        # Extract other brain nutrients
        brain_nutrients = {}
        for off_name, schema_name in nutrient_mapping.items():
            if off_name in nutriments and nutriments[off_name] is not None:
                value = nutriments[off_name]
                
                # Unit conversions
                if off_name in ["tryptophan_100g", "tyrosine_100g"]:
                    # Convert g to mg
                    value *= 1000
                
                if off_name == "folates_100g":
                    # Convert g to mcg
                    value *= 1000000
                
                if off_name == "vitamin-b12_100g":
                    # Convert g to mcg
                    value *= 1000000
                
                if off_name == "vitamin-d_100g":
                    # Convert g to mcg
                    value *= 1000000
                
                if off_name in ["magnesium_100g", "zinc_100g", "iron_100g"]:
                    # Convert g to mg
                    value *= 1000
                
                if off_name == "selenium_100g":
                    # Convert g to mcg
                    value *= 1000000
                
                if off_name == "choline_100g":
                    # Convert g to mg
                    value *= 1000
                
                brain_nutrients[schema_name] = value
        
        # Add omega-3 data if available
        if omega3:
            brain_nutrients["omega3"] = omega3
        
        return brain_nutrients
    
    def _calculate_completeness(self, nutriments: Dict) -> float:
        """Calculate completeness score for nutriment data."""
        # Count key nutrients we'd expect to have
        key_nutrients = [
            "energy-kcal_100g", "proteins_100g", "carbohydrates_100g", 
            "fat_100g", "fiber_100g", "sugars_100g"
        ]
        
        # Brain nutrients we'd ideally have
        brain_nutrients = [
            "vitamin-b6_100g", "folates_100g", "vitamin-b12_100g", 
            "vitamin-d_100g", "magnesium_100g", "zinc_100g", 
            "iron_100g", "selenium_100g", "omega-3-fat_100g"
        ]
        
        # Count how many we have
        standard_count = sum(1 for n in key_nutrients if n in nutriments and nutriments[n] is not None)
        brain_count = sum(1 for n in brain_nutrients if n in nutriments and nutriments[n] is not None)
        
        # Calculate completeness score
        standard_completeness = standard_count / len(key_nutrients)
        brain_completeness = brain_count / len(brain_nutrients) if brain_count > 0 else 0
        
        # Weight standard nutrients more heavily
        overall_completeness = (standard_completeness * 0.7) + (brain_completeness * 0.3)
        
        return round(overall_completeness, 2)
    
    def _calculate_inflammatory_index(self, product: Dict, nutriments: Dict) -> Dict:
        """
        Calculate a simplified inflammatory index based on available data.
        
        This is a very simplified approximation of the Dietary Inflammatory Index.
        """
        # Start with neutral score
        score = 0.0
        confidence = 5
        
        # Anti-inflammatory nutrients
        anti_inflammatory = {
            "fiber_100g": 0.5,
            "vitamin-c_100g": 0.3,
            "magnesium_100g": 0.3,
            "omega-3-fat_100g": 0.7,
            "folates_100g": 0.3
        }
        
        # Pro-inflammatory markers
        pro_inflammatory = {
            "saturated-fat_100g": 0.5,
            "trans-fat_100g": 0.8,
            "salt_100g": 0.3,
            "sugars_100g": 0.4
        }
        
        # Calculate anti-inflammatory score
        for nutrient, weight in anti_inflammatory.items():
            if nutrient in nutriments and nutriments[nutrient] is not None:
                # Normalize to reasonable range and apply weight
                normalized = min(1.0, nutriments[nutrient] / 10.0)  # Cap at reasonable maximum
                score -= normalized * weight
        
        # Calculate pro-inflammatory score
        for nutrient, weight in pro_inflammatory.items():
            if nutrient in nutriments and nutriments[nutrient] is not None:
                # Normalize to reasonable range and apply weight
                normalized = min(1.0, nutriments[nutrient] / 10.0)
                score += normalized * weight
        
        # Adjust based on food processing level (if available)
        if "nova_group" in product:
            nova_group = product["nova_group"]
            # NOVA Group 4 (ultra-processed) is more inflammatory
            if nova_group == 4:
                score += 2
                confidence += 1
            elif nova_group == 1:
                score -= 1
                confidence += 1
        
        # Check if additives present that may affect inflammation
        if "additives_tags" in product:
            has_problematic_additives = any(
                additive in product["additives_tags"] 
                for additive in ["e102", "e104", "e110", "e122", "e124", "e129"]
            )
            if has_problematic_additives:
                score += 1
        
        # Scale to -10 to +10 range
        score = max(-10, min(10, score * 2))
        
        # Higher confidence if we have more inflammatory markers
        factors_present = sum(1 for n in list(anti_inflammatory) + list(pro_inflammatory) 
                             if n in nutriments and nutriments[n] is not None)
        if factors_present >= 5:
            confidence = min(8, confidence + 1)
        
        return {
            "value": round(score, 1),
            "confidence": confidence,
            "calculation_method": "simplified_estimate",
            "citations": ["PMID:24182172"]
        }
    
    def search_and_save(self, query: str, output_dir: str, limit: int = 10) -> List[str]:
        """
        Search for products and save them to files.
        
        Args:
            query: Search term
            output_dir: Directory to save results
            limit: Maximum number of products to save
        
        Returns:
            List of saved file paths
        """
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            # Search for products
            results = self.search_products(
                query=query, 
                page_size=min(limit, 100),  # API limit is 100
                sort_by="popularity_score"
            )
            
            saved_files = []
            count = 0
            
            for product in results.get("products", []):
                if count >= limit:
                    break
                
                # Get full product details
                try:
                    product_data = {"product": product}  # Wrap in same format as API response
                    transformed = self.transform_to_schema(product_data)
                    
                    if transformed:
                        # Save to file
                        filename = f"{transformed['food_id']}.json"
                        file_path = os.path.join(output_dir, filename)
                        
                        with open(file_path, 'w') as f:
                            json.dump(transformed, f, indent=2)
                        
                        saved_files.append(file_path)
                        logger.info(f"Saved {transformed['name']} to {file_path}")
                        
                        count += 1
                except Exception as e:
                    logger.error(f"Error processing product {product.get('code')}: {e}")
            
            return saved_files
            
        except Exception as e:
            logger.error(f"Error searching for {query}: {e}")
            raise

def main():
    """Main function to execute the script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Fetch and transform OpenFoodFacts data")
    parser.add_argument("--query", help="Search term", default="")
    parser.add_argument("--categories", help="Categories to search for", default="")
    parser.add_argument("--output-dir", default="data/raw/openfoodfacts", help="Output directory")
    parser.add_argument("--limit", type=int, default=10, help="Maximum number of products to fetch")
    
    args = parser.parse_args()
    
    api = OpenFoodFactsAPI(user_agent="NutritionalPsychiatryDataset/1.0")
    
    try:
        saved_files = api.search_and_save(
            query=args.query,
            output_dir=args.output_dir,
            limit=args.limit
        )
        
        logger.info(f"Successfully saved {len(saved_files)} products")
        
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    main()