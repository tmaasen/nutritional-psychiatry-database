# food_data_transformer.py
import copy
from datetime import datetime
import re
from typing import Dict, List, Optional, Union

# Import utility modules
from schema.food_data import BrainNutrients, DataQuality, FoodData, InflammatoryIndex, Metadata, ServingInfo, StandardNutrients
from utils.logging_utils import setup_logging
from utils.data_utils import generate_food_id
from constants.food_data_constants import (
    # OpenFoodFacts mappings
    OFF_STANDARD_NUTRIENTS_MAPPING,
    OFF_BRAIN_NUTRIENTS_MAPPING,
    OFF_OMEGA3_MAPPING,
    # USDA mappings
    USDA_STANDARD_NUTRIENTS_MAPPING,
    USDA_BRAIN_NUTRIENTS_MAPPING,
    USDA_UNIT_CONVERSIONS,
    # General constants
    FOOD_CATEGORY_MAPPING,
    NUTRIENTS_G_TO_MG,
    NUTRIENTS_G_TO_MCG,
    ANTI_INFLAMMATORY_NUTRIENTS,
    PRO_INFLAMMATORY_NUTRIENTS,
    DEFAULT_CONFIDENCE_RATINGS,
    COMPLETENESS_REQUIRED_FIELDS
)
from utils.data_utils import calculate_completeness
from utils.nutrient_utils import NutrientUtils

# Initialize logger
logger = setup_logging(__name__)

class FoodDataTransformer:
    """Transforms food data from various sources to our nutritional psychiatry schema."""
    
    def __init__(self):
        """Initialize the transformer with nutrient mappings."""
        # Store mapping dictionaries for each source
        self.mappings = {
            "usda": {
                "standard_nutrients": USDA_STANDARD_NUTRIENTS_MAPPING,
                "brain_nutrients": USDA_BRAIN_NUTRIENTS_MAPPING,
                "unit_conversions": USDA_UNIT_CONVERSIONS
            },
            "off": {
                "standard_nutrients": OFF_STANDARD_NUTRIENTS_MAPPING,
                "brain_nutrients": OFF_BRAIN_NUTRIENTS_MAPPING,
                "omega3": OFF_OMEGA3_MAPPING
            }
        }
        self.category_mapping = FOOD_CATEGORY_MAPPING
    
    def transform(self, food: FoodData) -> FoodData:
        """
        Transform a FoodData object by applying standardization and normalization.
        
        Args:
            food: FoodData object to transform
            
        Returns:
            Transformed FoodData object
        """
        # Make a copy to avoid modifying the original
        transformed = copy.deepcopy(food)
        
        # Apply category normalization
        transformed.normalize_category()
        
        # Update timestamps
        transformed.update_timestamp()
        
        # Calculate completeness
        transformed.update_completeness()
        
        # Mark as processed
        transformed.processed = True
        
        return transformed

    def transform_usda_data(self, usda_food: Dict) -> Dict:
        """
        Transform USDA FoodData Central data to our schema format.
        
        Args:
            usda_food: USDA product data
            
        Returns:
            Dictionary in our schema format
        """
        food = usda_food
        
        if not food:
            logger.warning("Empty USDA food data")
            return {}

        nutrients = food.get("foodNutrients", [])
        
        # Generate food ID
        food_id = generate_food_id("usda", food.get('fdcId', ''))
        
        # Create metadata
        source_url = f"https://fdc.nal.usda.gov/fdc-app.html#/food-details/{food.get('fdcId', '')}/nutrients"
        metadata = Metadata(
            version="0.1.0",
            created=datetime.now().isoformat(),
            last_updated=datetime.now().isoformat(),
            source_urls=[source_url],
            source_ids={
                "usda_id": str(food.get('fdcId', ''))
            }
        )
        
        # Map category
        category = food.get("foodCategory", {}).get("description", "Miscellaneous")
        mapped_category = self._map_category(category, is_tag=False)

        # Extract nutrients
        standard_nutrients = self._extract_usda_standard_nutrients(nutrients)
        brain_nutrients = self._extract_usda_brain_nutrients(nutrients)

        transformed = FoodData(
            food_id=food_id,
            name=food.get("description", ""),
            description=food.get("ingredients", food.get("description", "")),
            category=mapped_category,
            serving_info=ServingInfo(
                serving_size=100.0,
                serving_unit="g",
                household_serving=food.get("householdServingFullText", "")
            ),
            standard_nutrients=standard_nutrients,
            brain_nutrients=brain_nutrients,
            bioactive_compounds={},
            mental_health_impacts=[],
            data_quality=DataQuality(
                completeness=0.0,
                overall_confidence=DEFAULT_CONFIDENCE_RATINGS.get("usda", 7),
                brain_nutrients_source="usda_provided"
            ),
            metadata=metadata
        )

        # Calculate completeness
        completeness = calculate_completeness(transformed, COMPLETENESS_REQUIRED_FIELDS)
        transformed.data_quality.completeness = completeness
        
        return transformed
    
    def transform_off_data(self, off_product: Dict) -> Dict:
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
            logger.warning("Empty OpenFoodFacts product data")
            return {}
        
        # Get nutriment data
        nutriments = product.get("nutriments", {})
        
        # Extract category
        category = self._map_category(product.get("categories_tags", []))
        
        # Generate food ID
        food_id = generate_food_id("off", product.get('code', ''))
        
        # Create metadata
        source_url = f"https://world.openfoodfacts.org/product/{product.get('code', '')}"
        metadata = Metadata(
            version="0.1.0",
            created=datetime.now().isoformat(),
            last_updated=datetime.now().isoformat(),
            source_urls=[source_url],
            source_ids={
                "off_id": str(product.get('code', ''))
            }
        )
        
        if "image_url" in product:
            metadata.image_url = product.get("image_url", "")
        
        # Extract nutrients
        standard_nutrients = self._extract_off_standard_nutrients(nutriments)
        brain_nutrients = self._extract_off_brain_nutrients(nutriments)
        
        # Extract serving info
        serving_info = self._extract_serving_info(product)
        
        # Calculate completeness
        data = {
            "standard_nutrients": standard_nutrients,
            "brain_nutrients": brain_nutrients
        }
        completeness = calculate_completeness(data, COMPLETENESS_REQUIRED_FIELDS)
        
        # Calculate inflammatory index
        inflammatory_index = self._calculate_inflammatory_index(product, nutriments)

        transformed = FoodData(
            food_id=food_id,
            name=product.get("product_name", ""),
            description=product.get("generic_name", product.get("product_name", "")),
            category=category,
            serving_info=serving_info,
            standard_nutrients=standard_nutrients,
            brain_nutrients=brain_nutrients,
            bioactive_compounds={},
            mental_health_impacts=[],
            data_quality=DataQuality(
                completeness=completeness,
                overall_confidence=DEFAULT_CONFIDENCE_RATINGS.get("openfoodfacts", 7),  
                brain_nutrients_source="openfoodfacts"
            ),
            metadata=metadata
        )
        
        # Add inflammatory index if available
        if inflammatory_index:
            transformed.inflammatory_index = inflammatory_index
        
        return transformed
    
    def _map_category(self, category_data: Union[str, List[str]], is_tag: bool = True) -> str:
        """
        Map source category to our simplified categories.
        
        Args:
            category_data: Category string or list of category tags
            is_tag: Whether the data is a list of tags (True) or a single string (False)
            
        Returns:
            Mapped category string
        """
        if is_tag:
            # Handle OpenFoodFacts style tags
            clean_tags = [tag.replace("en:", "").lower() for tag in category_data]
            
            # Find the first matching category
            for tag in clean_tags:
                for key, value in self.category_mapping.items():
                    if key in tag:
                        return value
            
            # Default to the first category or "Miscellaneous"
            if clean_tags:
                return clean_tags[0].capitalize()
        else:
            # Handle USDA style category string
            category_lower = category_data.lower()
            for key, value in self.category_mapping.items():
                if key in category_lower:
                    return value
        
        return "Miscellaneous"
    
    def _extract_serving_info(self, product: Dict) -> ServingInfo:
        """
        Extract serving information from product data.
        
        Args:
            product: Product data
            
        Returns:
            Serving information dictionary
        """
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
        
        return ServingInfo(
            serving_size=serving_size,
            serving_unit="g",
            household_serving=serving_size_str
        )
    
    def _extract_usda_standard_nutrients(self, food_nutrients: List[Dict]) -> StandardNutrients:
        return NutrientUtils.extract_nutrients_by_mapping(
            food_nutrients, 
            self.mappings["usda"]["standard_nutrients"],
            id_field="nutrient.name",
            value_field="amount",
            unit_field="nutrient.unitName"
        )
    
    def _extract_usda_brain_nutrients(self, food_nutrients: List[Dict]) -> BrainNutrients:
        brain_nutrients = BrainNutrients()
        omega3 = {}
        has_omega3 = False
        
        for nutrient in food_nutrients:
            nutrient_name = nutrient.get("nutrient", {}).get("name")
            if nutrient_name in self.mappings["usda"]["brain_nutrients"]:
                schema_name = self.mappings["usda"]["brain_nutrients"][nutrient_name]
                value = nutrient.get("amount")
                
                if value is not None:
                    # Unit conversions
                    unit = nutrient.get("nutrient", {}).get("unitName", "")
                    
                    if unit == "µg":
                        value /= 1000  # Convert µg to mg
                    
                    if nutrient_name in self.mappings["usda"]["unit_conversions"]["ug_to_mg"]:
                        value *= 1000  # Convert to µg
                    
                    if nutrient_name in self.mappings["usda"]["unit_conversions"]["g_to_mcg"]:
                        value *= 1000000  # Convert g to mcg
                    
                    # Check if this is an omega-3 related nutrient
                    if "omega" in schema_name.lower():
                        has_omega3 = True
                        if schema_name == "omega3.total_g":
                            omega3["total_g"] = value
                        elif schema_name == "omega3.epa_mg":
                            omega3["epa_mg"] = value
                        elif schema_name == "omega3.dha_mg":
                            omega3["dha_mg"] = value
                        elif schema_name == "omega3.ala_mg":
                            omega3["ala_mg"] = value
                    else:
                        setattr(brain_nutrients, schema_name, value)
        
        # Add omega-3 data if available
        if has_omega3:
            brain_nutrients.omega3 = omega3
            brain_nutrients.confidence = DEFAULT_CONFIDENCE_RATINGS.get("omega3", 7)
            brain_nutrients.source = "usda_provided"
        return brain_nutrients
    
    def _extract_off_standard_nutrients(self, nutriments: Dict) -> StandardNutrients:
        standard_nutrients = StandardNutrients()
        
        for off_name, schema_name in self.mappings["off"]["standard_nutrients"].items():
            if off_name in nutriments and nutriments[off_name] is not None:
                value = nutriments[off_name]
                
                # Unit conversions if needed
                if off_name in NUTRIENTS_G_TO_MG:
                    value = NutrientUtils.g_to_mg(value)
                
                elif off_name in NUTRIENTS_G_TO_MCG:
                    value = NutrientUtils.g_to_mcg(value)
                
                standard_nutrients.nutrients[schema_name] = value
        
        return standard_nutrients
    
    def _extract_off_brain_nutrients(self, nutriments: Dict) -> BrainNutrients:
        brain_nutrients = BrainNutrients()
        
        # Extract standard brain nutrients
        for off_name, schema_name in self.mappings["off"]["brain_nutrients"].items():
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
                
                setattr(brain_nutrients, schema_name, value)
        
        # Extract omega-3 data
        omega3 = {}
        
        for off_name, schema_name in self.mappings["off"]["omega3"].items():
            if off_name in nutriments and nutriments[off_name] is not None:
                value = nutriments[off_name]
                
                # Unit conversion for DHA, EPA, ALA
                if off_name in ["dha_100g", "epa_100g", "ala_100g"]:
                    value = NutrientUtils.g_to_mg(value)
                
                omega3[schema_name] = value
        
        # Add confidence level if we have omega-3 data
        if omega3:
            brain_nutrients.omega3 = omega3
            brain_nutrients.confidence = DEFAULT_CONFIDENCE_RATINGS.get("omega3", 7)
            brain_nutrients.source = "openfoodfacts"
        
        return brain_nutrients
    
    def _calculate_inflammatory_index(self, product: Dict, nutriments: Dict) -> Optional[InflammatoryIndex]:
        # Start with neutral score
        score = 0.0
        confidence = DEFAULT_CONFIDENCE_RATINGS.get("inflammatory_index", 5)
        
        # Calculate anti-inflammatory score
        for nutrient, weight in ANTI_INFLAMMATORY_NUTRIENTS.items():
            if nutrient in nutriments and nutriments[nutrient] is not None:
                # Normalize to reasonable range and apply weight
                normalized = min(1.0, nutriments[nutrient] / 10.0)  # Cap at reasonable maximum
                score -= normalized * weight
        
        # Calculate pro-inflammatory score
        for nutrient, weight in PRO_INFLAMMATORY_NUTRIENTS.items():
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
        factors_present = sum(1 for n in list(ANTI_INFLAMMATORY_NUTRIENTS) + list(PRO_INFLAMMATORY_NUTRIENTS) 
                             if n in nutriments and nutriments[n] is not None)
        if factors_present >= 5:
            confidence = min(8, confidence + 1)
        
        # Only return inflammatory index if we have some data to base it on
        if factors_present > 0:
            return InflammatoryIndex(
                value=round(score, 1),
                confidence=confidence,
                calculation_method="simplified_estimate",
                citations=["PMID:24182172"]
            )
        
        return None
