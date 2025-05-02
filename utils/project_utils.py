# utils/project_utils.py
"""
Project structure utilities for the Nutritional Psychiatry Dataset project.
"""

import os
import warnings
from typing import Dict, Optional

def get_project_dirs(base_dir: str = "data") -> Dict[str, str]:
    """
    Get standard directory paths for the project.
    
    Args:
        base_dir: Base directory for data
    
    Returns:
        Dictionary of directory paths
    
    Note:
        This function is deprecated. Use get_project_paths() instead.
    """
    warnings.warn(
        "get_project_dirs() is deprecated. Use get_project_paths() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
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

def get_project_paths() -> Dict[str, str]:
    """
    Get standard paths for the project, including database schemas.
    
    Returns:
        Dictionary of paths and schemas
    """
    paths = {
        # Database schemas
        "db_schema": "nutritional_psychiatry",
        "db_tables": {
            "foods": "foods",
            "nutrients": "nutrients",
            "brain_nutrients": "brain_nutrients",
            "bioactive_compounds": "bioactive_compounds",
            "mental_health_impacts": "mental_health_impacts",
            "nutrient_interactions": "nutrient_interactions",
            "contextual_factors": "contextual_factors",
            "population_variations": "population_variations",
            "dietary_patterns": "dietary_patterns",
            "inflammatory_index": "inflammatory_index",
            "neural_targets": "neural_targets"
        },
        
        # Backup directories (for migration and exports)
        "backup_dir": os.path.join("data", "backup"),
        "export_dir": os.path.join("data", "export"),
        
        # Logging
        "log_dir": os.path.join("logs"),
        "migration_log": os.path.join("logs", "migration.log"),
        "api_log": os.path.join("logs", "api.log")
    }
    
    return paths

def create_project_dirs(base_dir: str = "data") -> Dict[str, str]:
    """
    Create all standard project directories.
    
    Args:
        base_dir: Base directory for data
    
    Returns:
        Dictionary of created directory paths
    
    Note:
        This function is deprecated. Use create_project_paths() instead.
    """
    warnings.warn(
        "create_project_dirs() is deprecated. Use create_project_paths() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    directories = get_project_dirs(base_dir)
    
    for directory in directories.values():
        os.makedirs(directory, exist_ok=True)
    
    return directories

def create_project_paths() -> Dict[str, str]:
    """
    Create all necessary project paths and directories.
    
    Returns:
        Dictionary of created paths
    """
    paths = get_project_paths()
    
    # Create backup and export directories
    os.makedirs(paths["backup_dir"], exist_ok=True)
    os.makedirs(paths["export_dir"], exist_ok=True)
    
    # Create logging directory
    os.makedirs(paths["log_dir"], exist_ok=True)
    
    return paths