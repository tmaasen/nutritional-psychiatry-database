
from typing import Dict, Any
from utils.logging_utils import setup_logging

logger = setup_logging(__name__)

def merge_nutrient_data(
    primary_data: Dict[str, Any], 
    secondary_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Merge nutrient data from two sources, prioritizing primary data.
    
    Args:
        primary_data: Primary nutrient data
        secondary_data: Secondary nutrient data
        
    Returns:
        Merged nutrient data
    """
    if not secondary_data:
        return primary_data.copy() if primary_data else {}
        
    if not primary_data:
        return secondary_data.copy()
    
    # Start with primary data
    merged = primary_data.copy()
    
    # Add fields from secondary data that don't exist in primary
    for key, value in secondary_data.items():
        if key not in merged or merged[key] is None:
            merged[key] = value
    
    return merged

def find_similar_food(food_name: str, foods: List[Dict]) -> Optional[Dict]:
    """
    Find a food with similar name using fuzzy matching.
    
    Args:
        food_name: Food name to match
        foods: List of food dictionaries
        
    Returns:
        Matching food or None if no match found
    """
    food_name_lower = food_name.lower()
    
    # First try for exact match
    for food in foods:
        if food.get("name", "").lower() == food_name_lower:
            return food
    
    # Try for partial match
    best_match = None
    best_similarity = 0.5  # Threshold
    
    for food in foods:
        food_name = food.get("name", "").lower()
        # Simple Jaccard similarity on words
        words1 = set(food_name_lower.split())
        words2 = set(food_name.split())
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        if union > 0:
            similarity = intersection / union
            if similarity > best_similarity:
                best_match = food
                best_similarity = similarity
    
    return best_match

def calculate_completeness(merged_data: Dict) -> float:
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
    if "standard_nutrients" in merged_data:
        std_nutrients = merged_data["standard_nutrients"]
        key_nutrients = ["calories", "protein_g", "carbohydrates_g", "fat_g", "fiber_g", "sugars_g"]
        
        total_fields += len(key_nutrients)
        filled_fields += sum(1 for n in key_nutrients if n in std_nutrients and std_nutrients[n] is not None)
    
    # Check brain nutrients
    if "brain_nutrients" in merged_data:
        brain_nutrients = merged_data["brain_nutrients"]
        key_brain_nutrients = ["tryptophan_mg", "vitamin_b6_mg", "folate_mcg", 
                             "vitamin_b12_mcg", "vitamin_d_mcg", "magnesium_mg"]
        
        total_fields += len(key_brain_nutrients)
        filled_fields += sum(1 for n in key_brain_nutrients if n in brain_nutrients and brain_nutrients[n] is not None)
    
    # Calculate score
    if total_fields > 0:
        return round(filled_fields / total_fields, 2)
    return 0.0