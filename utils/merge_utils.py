
from typing import Dict
from utils.logging_utils import setup_logging

logger = setup_logging(__name__)

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