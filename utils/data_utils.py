import re

from constants.food_data_constants import BRAIN_NUTRIENTS_FIELDS, STD_NUTRIENT_FIELDS, OMEGA3_FIELDS
from schema.food_data import FoodData

def generate_food_id(source: str, original_id: str) -> str:
    clean_id = re.sub(r'[^\w\d]', '_', str(original_id))
    return f"{source.lower()}_{clean_id}"

def identify_source(food_data: FoodData) -> str:
    food_id = food_data.food_id
    metadata = food_data.metadata
    
    if "source_ids" in metadata:
        source_ids = metadata.source_ids
        if "usda_fdc_id" in source_ids:
            return "usda"
        elif "openfoodfacts_id" in source_ids:
            return "openfoodfacts"
    
    if food_id.startswith("usda_"):
        return "usda"
    elif food_id.startswith("off_"):
        return "openfoodfacts"
    elif food_id.startswith("lit_"):
        return "literature"
    elif food_id.startswith("ai_"):
        return "ai_generated"
    
    return "unknown"

def calculate_completeness(merged_data: FoodData, required_fields=None) -> float:
    total_fields = 0
    filled_fields = 0
    
    if required_fields is None:
        std_nutrient_fields = STD_NUTRIENT_FIELDS
        brain_nutrient_fields = BRAIN_NUTRIENTS_FIELDS
        omega3_fields = OMEGA3_FIELDS
    else:
        std_nutrient_fields = required_fields.get("standard_nutrients", [])
        brain_nutrient_fields = required_fields.get("brain_nutrients", [])
        omega3_fields = required_fields.get("omega3", [])
    
    # Check standard nutrients
    if merged_data.standard_nutrients:
        std_nutrients = merged_data.standard_nutrients
        total_fields += len(std_nutrient_fields)
        filled_fields += sum(1 for n in std_nutrient_fields if hasattr(std_nutrients, n) and getattr(std_nutrients, n) is not None)
    
    # Check brain nutrients
    if merged_data.brain_nutrients:
        brain_nutrients = merged_data.brain_nutrients
        
        # Check main brain nutrient fields
        total_fields += len(brain_nutrient_fields)
        filled_fields += sum(1 for n in brain_nutrient_fields if hasattr(brain_nutrients, n) and getattr(brain_nutrients, n) is not None)
        
        # Check omega-3 fields if present
        if brain_nutrients.omega3:
            total_fields += len(omega3_fields)
            filled_fields += sum(1 for n in omega3_fields if hasattr(brain_nutrients.omega3, n) and getattr(brain_nutrients.omega3, n) is not None)
    
    if total_fields > 0:
        return round(filled_fields / total_fields, 2)
    return 0.0

