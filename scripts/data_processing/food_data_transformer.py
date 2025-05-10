import time
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

# Import utility modules
from utils.api_utils import make_request
from utils.logging_utils import setup_logging
from utils.db_utils import PostgresClient
from utils.nutrient_utils import NutrientUtils
from constants.food_data_constants import (
    OFF_STANDARD_NUTRIENTS_MAPPING,
    OFF_BRAIN_NUTRIENTS_MAPPING,
    OFF_OMEGA3_MAPPING,
    FOOD_CATEGORY_MAPPING,
    NUTRIENTS_G_TO_MG,
    NUTRIENTS_G_TO_MCG
)

# Initialize logger
logger = setup_logging(__name__)

class FoodDataTransformer:    
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
        
        # Extract category using FOOD_CATEGORY_MAPPING
        category = self._map_category(product.get("categories_tags", []))
        
        # Create standard nutrients using utility
        standard_nutrients_data = extract_nutrient_by_mapping(
            nutriments, 
            OFF_STANDARD_NUTRIENTS_MAPPING
        )
        
        # Create brain nutrients
        brain_nutrients_data = self._extract_brain_nutrients(nutriments)
        
        # Create serving info
        serving_info_data = self._extract_serving_info(product)
        
        # Generate food ID using utility
        food_id = generate_food_id("off", product.get('code', ''))
        
        # Create metadata using utility
        metadata_data = create_food_metadata(
            source="off",
            original_id=product.get('code', ''),
            source_url=f"https://world.openfoodfacts.org/product/{product.get('code', '')}",
            additional_tags=product.get("categories_tags", [])
        )
        
        # Add image URL if available
        if "image_url" in product:
            metadata_data["image_url"] = product.get("image_url", "")
        
        # Calculate completeness with utility
        data = {
            "standard_nutrients": standard_nutrients_data,
            "brain_nutrients": brain_nutrients_data
        }
        completeness = calculate_nutrient_completeness(data, COMPLETENESS_REQUIRED_FIELDS)
        
        # Create data quality
        data_quality_data = {
            "completeness": completeness,
            "overall_confidence": DEFAULT_CONFIDENCE_RATINGS["openfoodfacts"],
            "brain_nutrients_source": "openfoodfacts"
        }
        
        # Create inflammatory index if possible
        inflammatory_index_data = self._calculate_inflammatory_index(product, nutriments)
        
        # Build the full food data dictionary
        transformed_data = {
            "food_id": food_id,
            "name": product.get("product_name", ""),
            "description": product.get("generic_name", product.get("product_name", "")),
            "category": category,
            "serving_info": serving_info_data,
            "standard_nutrients": standard_nutrients_data,
            "brain_nutrients": brain_nutrients_data,
            "bioactive_compounds": {},
            "mental_health_impacts": [],
            "data_quality": data_quality_data,
            "metadata": metadata_data
        }
        
        # Add inflammatory index if available
        if inflammatory_index_data:
            transformed_data["inflammatory_index"] = inflammatory_index_data
        
        return transformed_data
    
    def _map_category(self, categories_tags: List[str]) -> str:
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
    
    def _extract_serving_info(self, product: Dict) -> Dict:
        """Extract serving information from product data."""
        serving_size_str = product.get("serving_size", "")
        serving_size = 100.0  # Default
        
        # Try to extract a number
        if serving_size_str:
            numbers = re.findall(r'(\d+(?:\.\d+)?)', serving_size_str)
            if numbers:
                try:
                    serving_size = float(numbers[0])
                except ValueError:
                    pass
        
        return {
            "serving_size": serving_size,
            "serving_unit": "g",
            "household_serving": serving_size_str
        }
    
    def _extract_standard_nutrients(self, nutriments: Dict) -> Dict:
        """Extract standard nutrients from OFF nutriments data."""
        standard_nutrients = {}
        
        for off_name, schema_name in self.standard_nutrients_mapping.items():
            if off_name in nutriments and nutriments[off_name] is not None:
                value = nutriments[off_name]
                
                # Unit conversions if needed
                if off_name in NUTRIENTS_G_TO_MG:
                    value = NutrientUtils.g_to_mg(value)
                
                elif off_name in NUTRIENTS_G_TO_MCG:
                    value = NutrientUtils.g_to_mcg(value)
                
                standard_nutrients[schema_name] = value
        
        return standard_nutrients
    
    def _extract_brain_nutrients(self, nutriments: Dict) -> Dict:
        """Extract brain-specific nutrients from OFF nutriments data."""
        brain_nutrients = {}
        
        # Extract standard brain nutrients
        for off_name, schema_name in self.nutrient_mappings["brain_nutrients"].items():
            if off_name in nutriments and nutriments[off_name] is not None:
                value = nutriments[off_name]
                
                # Unit conversions
                if off_name in ["tryptophan_100g", "tyrosine_100g", "choline_100g"]:
                    value = NutrientUtils.g_to_mg(value)
                
                elif off_name in ["folates_100g", "vitamin-b12_100g", "vitamin-d_100g"]:
                    value = NutrientUtils.g_to_mcg(value)
                
                elif off_name in ["magnesium_100g", "zinc_100g", "iron_100g"]:
                    value = NutrientUtils.g_to_mg(value)
                
                elif off_name == "selenium_100g":
                    value = NutrientUtils.g_to_mcg(value)
                
                brain_nutrients[schema_name] = value
        
        # Extract omega-3 data
        omega3 = {}
        
        for off_name, schema_name in self.nutrient_mappings["omega3"].items():
            if off_name in nutriments and nutriments[off_name] is not None:
                value = nutriments[off_name]
                
                # Unit conversion for DHA, EPA, ALA
                if off_name in ["dha_100g", "epa_100g", "ala_100g"]:
                    value = NutrientUtils.g_to_mg(value)
                
                omega3[schema_name] = value
        
        # Add confidence level if we have omega-3 data
        if omega3:
            omega3["confidence"] = 7
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
        standard_completeness = standard_count / len(key_nutrients) if key_nutrients else 0
        brain_completeness = brain_count / len(brain_nutrients) if brain_nutrients and brain_count > 0 else 0
        
        # Weight standard nutrients more heavily
        overall_completeness = (standard_completeness * 0.7) + (brain_completeness * 0.3)
        
        return round(overall_completeness, 2)
    
    def _calculate_inflammatory_index(self, product: Dict, nutriments: Dict) -> Optional[Dict]:
        """
        Calculate a simplified inflammatory index based on available data.
        
        This is a simplified approximation of the Dietary Inflammatory Index.
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
        
        # Scale to -10 to +10 range
        score = max(-10, min(10, score * 2))
        
        # Higher confidence if we have more inflammatory markers
        factors_present = sum(1 for n in list(anti_inflammatory) + list(pro_inflammatory) 
                             if n in nutriments and nutriments[n] is not None)
        if factors_present >= 5:
            confidence = min(8, confidence + 1)
        
        # Only return inflammatory index if we have some data to base it on
        if factors_present > 0:
            return {
                "value": round(score, 1),
                "confidence": confidence,
                "calculation_method": "simplified_estimate",
                "citations": ["PMID:24182172"]
            }
        return None