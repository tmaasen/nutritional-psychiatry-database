# utils/project_utils.py
"""
Project structure utilities for the Nutritional Psychiatry Dataset project.
"""

import os
from typing import Dict

def get_project_dirs(base_dir: str = "data") -> Dict[str, str]:
    """
    Get standard directory paths for the project.
    
    Args:
        base_dir: Base directory for data
    
    Returns:
        Dictionary of directory paths
    """
    directories = {
        # Raw data
        "usda_raw": os.path.join(base_dir, "raw", "usda_foods"),
        "off_raw": os.path.join(base_dir, "raw", "openfoodfacts"),
        "literature_raw": os.path.join(base_dir, "raw", "literature"),
        "manual_raw": os.path.join(base_dir, "raw", "manual_entries"),
        
        # Processed data
        "processed": os.path.join(base_dir, "processed", "base_foods"),
        
        # Enriched data
        "ai_generated": os.path.join(base_dir, "enriched", "ai_generated"),
        "calibrated": os.path.join(base_dir, "enriched", "calibrated"),
        "merged": os.path.join(base_dir, "enriched", "merged"),
        
        # Evaluation data
        "evaluation": os.path.join(base_dir, "evaluation"),
        "reference": os.path.join(base_dir, "reference"),
        
        # Final data
        "final": os.path.join(base_dir, "final")
    }
    
    return directories

def create_project_dirs(base_dir: str = "data") -> Dict[str, str]:
    """
    Create all standard project directories.
    
    Args:
        base_dir: Base directory for data
    
    Returns:
        Dictionary of created directory paths
    """
    directories = get_project_dirs(base_dir)
    
    for directory in directories.values():
        os.makedirs(directory, exist_ok=True)
    
    return directories