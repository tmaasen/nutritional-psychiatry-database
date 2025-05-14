
import re

from schema.food_data import FoodData

def generate_food_id(source: str, original_id: str) -> str:
    """
    Generate standardized food ID from source and original ID.
    
    Args:
        source: Source identifier (e.g., 'usda', 'off')
        original_id: Original ID from the source
        
    Returns:
        Standardized food ID (e.g., 'usda_12345')
    """
    # Remove any special characters from IDs
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

def calculate_completeness(merged_data: FoodData) -> float:
    """
    Calculate completeness score for a food entry.
    
    Args:
        merged_data: Food data dictionary
        
    Returns:
        Completeness score (0-1)
    """
    total_fields = 0
    filled_fields = 0
    
    # Check standard nutrients
    if merged_data.standard_nutrients:
        std_nutrients = merged_data.standard_nutrients
        key_nutrients = ["calories", "protein_g", "carbohydrates_g", "fat_g", "fiber_g", "sugars_g"]
        
        total_fields += len(key_nutrients)
        filled_fields += sum(1 for n in key_nutrients if n in std_nutrients and std_nutrients[n] is not None)
    
    # Check brain nutrients
    if merged_data.brain_nutrients:
        brain_nutrients = merged_data.brain_nutrients
        key_brain_nutrients = ["tryptophan_mg", "vitamin_b6_mg", "folate_mcg", 
                             "vitamin_b12_mcg", "vitamin_d_mcg", "magnesium_mg"]
        
        total_fields += len(key_brain_nutrients)
        filled_fields += sum(1 for n in key_brain_nutrients if n in brain_nutrients and brain_nutrients[n] is not None)
    
    # Calculate score
    if total_fields > 0:
        return round(filled_fields / total_fields, 2)
    return 0.0