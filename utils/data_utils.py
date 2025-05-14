
import re
from typing import Optional, List
from datetime import datetime

from schema.food_data import Metadata

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

def create_food_metadata(
    source: str, 
    original_id: str, 
    source_url: Optional[str] = None,
    additional_tags: Optional[List[str]] = None
) -> Metadata:
    """
    Create standardized metadata for food items.
    
    Args:
        source: Source identifier (e.g., 'usda', 'off')
        original_id: Original ID from the source
        source_url: URL to the original source data
        additional_tags: Additional tags to include
        
    Returns:
        Standardized metadata dictionary
    """
    now = datetime.now().isoformat()
    
    metadata = Metadata(
        version="0.1.0",
        created=now,
        last_updated=now,
        source_urls=[],
        source_ids={
            f"{source.lower()}_id": original_id
        },
        tags=additional_tags or []
    )
    
    if source_url:
        metadata["source_urls"].append(source_url)
        
    return metadata