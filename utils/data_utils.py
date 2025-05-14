
import re
from typing import Optional, List

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
