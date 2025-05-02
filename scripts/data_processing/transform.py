#!/usr/bin/env python3
"""
USDA Data Transformation Script
Transforms raw USDA food data into our nutritional psychiatry schema.
"""

import os
import json
import glob
import logging
from data.postgres_client import PostgresClient
from typing import Dict, List, Any, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class USDADataTransformer:
    
    def instantiate_db_client(self) -> PostgresClient:
        """
        Instantiates and returns a PostgresClient instance.

        Returns:
            PostgresClient: An instance of the PostgresClient.
        """
        return PostgresClient()
    
    """Transforms USDA food data to our schema format."""
    
    # Mapping of USDA nutrient IDs to our schema fields
    # This is based on actual USDA nutrient IDs and will need to be expanded
    NUTRIENT_ID_MAPPING = {
        # Standard nutrients
        "1008": "standard_nutrients.calories",
        "1003": "standard_nutrients.protein_g",
        "1004": "standard_nutrients.fat_g",
        "1005": "standard_nutrients.carbohydrates_g",
        "1079": "standard_nutrients.fiber_g",
        "2000": "standard_nutrients.sugars_g",
        "1063": "standard_nutrients.sugars_added_g",
        "1087": "standard_nutrients.calcium_mg",
        "1089": "standard_nutrients.iron_mg",
        "1090": "standard_nutrients.magnesium_mg",
        "1091": "standard_nutrients.phosphorus_mg",
        "1092": "standard_nutrients.potassium_mg",
        "1093": "standard_nutrients.sodium_mg",
        "1095": "standard_nutrients.zinc_mg",
        "1098": "standard_nutrients.copper_mg",
        "1101": "standard_nutrients.manganese_mg",
        "1103": "standard_nutrients.selenium_mcg",
        
        # Brain-specific nutrients (those available in USDA)
        "1106": "brain_nutrients.vitamin_b6_mg",
        "1090": "brain_nutrients.magnesium_mg",  # Duplicate mapping for organizational purposes
        "1095": "brain_nutrients.zinc_mg",       # Duplicate mapping for organizational purposes
        "1089": "brain_nutrients.iron_mg",       # Duplicate mapping for organizational purposes
        "1103": "brain_nutrients.selenium_mcg",  # Duplicate mapping for organizational purposes
        "1178": "brain_nutrients.vitamin_b12_mcg",
        "1184": "brain_nutrients.vitamin_d_mcg",
        "1109": "brain_nutrients.vitamin_e_mg",
        "1177": "brain_nutrients.folate_mcg",
        "1180": "brain_nutrients.choline_mg",
        
        # Omega-3 fatty acids
        "1258": "brain_nutrients.omega3.total_g",
        "1404": "brain_nutrients.omega3.epa_mg",  # EPA
        "1271": "brain_nutrients.omega3.dha_mg",  # DHA
        "1403": "brain_nutrients.omega3.ala_mg",  # ALA
        
        # Amino acids
        "1210": "brain_nutrients.tryptophan_mg",
        "1218": "brain_nutrients.tyrosine_mg"
    }
    
    # Food category mapping (simplified for POC)
    FOOD_CATEGORY_MAPPING = {
        "Fruits and Fruit Juices": "Fruits",
        "Vegetables and Vegetable Products": "Vegetables",
        "Beef Products": "Protein Foods",
        "Poultry Products": "Protein Foods",
        "Pork Products": "Protein Foods",
        "Fish and Seafood Products": "Protein Foods",
        "Legumes and Legume Products": "Protein Foods",
        "Dairy and Egg Products": "Dairy",
        "Cereal Grains and Pasta": "Grains",
        "Baked Products": "Grains",
        "Nuts and Seeds": "Nuts and Seeds",
        "Beverages": "Beverages",
        "Sweets": "Sweets",
        "Fast Foods": "Processed Foods"
    }
    
    def __init__(self, schema_path: str, db_client: PostgresClient = None):
        """
        Initialize the transformer with a schema definition.
        
        Args:
            schema_path: Path to the JSON schema file
            db_client: Instance of PostgresClient for db access

        """
        try:
            with open(schema_path, 'r') as f:
                self.schema = json.load(f)
                logger.info(f"Loaded schema from {schema_path}")
        except Exception as e:
            logger.error(f"Error loading schema: {e}")
            raise
        
        self.db_client = db_client or self.instantiate_db_client()
    
    def _get_nested_value(self, data: Dict, path: str, default: Any = None) -> Any:
        """
        Get a value from a nested dictionary using a dot-separated path.
        
        Args:
            data: Dictionary to extract from
            path: Dot-separated path to the value
            default: Default value if not found
            
        Returns:
            The value at the path or default if not found
        """
        keys = path.split('.')
        result = data
        
        for key in keys:
            if isinstance(result, dict) and key in result:
                result = result[key]
            else:
                return default
                
        return result
    
    def _set_nested_value(self, data: Dict, path: str, value: Any) -> None:
        """
        Set a value in a nested dictionary using a dot-separated path.
        Creates intermediate dictionaries as needed.
        
        Args:
            data: Dictionary to modify
            path: Dot-separated path to set
            value: Value to set
        """
        keys = path.split('.')
        current = data
        
        # Navigate to the correct nested location, creating dictionaries as needed
        for i, key in enumerate(keys[:-1]):
            if key not in current or not isinstance(current[key], dict):
                current[key] = {}
            current = current[key]
        
        # Set the final value
        current[keys[-1]] = value
    
    def transform_usda_food(self, usda_data: Dict) -> Dict:
        """
        Transform USDA food data into our schema format.
        
        Args:
            usda_data: Raw USDA food data
            
        Returns:
            Transformed data in our schema format
        """
        # Create a new dictionary with our schema structure
        transformed = {}
        
        # Basic food information
        transformed["food_id"] = f"usda_{usda_data.get('fdcId', '')}"
        transformed["name"] = usda_data.get('description', '')
        transformed["description"] = usda_data.get('description', '')
        
        # Get food category
        usda_category = usda_data.get('foodCategory', {}).get('description', '')
        transformed["category"] = self.FOOD_CATEGORY_MAPPING.get(usda_category, usda_category)
        
        # Serving info
        if 'servingSize' in usda_data:
            serving_info = {
                "serving_size": usda_data.get('servingSize'),
                "serving_unit": usda_data.get('servingSizeUnit', 'g')
            }
            if 'householdServingFullText' in usda_data:
                serving_info["household_serving"] = usda_data.get('householdServingFullText')
            transformed["serving_info"] = serving_info
        
        # Initialize standard_nutrients and brain_nutrients
        transformed["standard_nutrients"] = {}
        transformed["brain_nutrients"] = {}
        transformed["brain_nutrients"]["omega3"] = {"confidence": 0}
        
        # Map nutrients
        if 'foodNutrients' in usda_data:
            for nutrient_data in usda_data['foodNutrients']:
                nutrient_id = str(nutrient_data.get('nutrient', {}).get('id'))
                
                if nutrient_id in self.NUTRIENT_ID_MAPPING:
                    # Get the target path in our schema
                    target_path = self.NUTRIENT_ID_MAPPING[nutrient_id]
                    
                    # Extract the value (accounting for different USDA formats)
                    if 'amount' in nutrient_data:
                        value = nutrient_data.get('amount')
                    elif 'value' in nutrient_data:
                        value = nutrient_data.get('value')
                    else:
                        continue
                    
                    # Set the value in our transformed data
                    self._set_nested_value(transformed, target_path, value)
        
        # Add confidence ratings for brain nutrients
        if 'brain_nutrients' in transformed and 'omega3' in transformed['brain_nutrients']:
            # Set confidence based on completeness of omega-3 data
            omega3_fields = ['total_g', 'epa_mg', 'dha_mg', 'ala_mg']
            available_fields = sum(1 for field in omega3_fields 
                                if field in transformed['brain_nutrients']['omega3'])
            
            if available_fields > 0:
                confidence = min(10, (available_fields / len(omega3_fields)) * 10)
                transformed['brain_nutrients']['omega3']['confidence'] = round(confidence, 1)
        
        # Add data quality metrics
        transformed["data_quality"] = {
            "completeness": self._calculate_completeness(transformed),
            "overall_confidence": 7,  # USDA data is generally reliable
            "brain_nutrients_source": "usda_provided",
            "impacts_source": None  # No impacts from USDA data
        }
        
        # Add empty placeholders for sections not in USDA data
        transformed["bioactive_compounds"] = {}
        transformed["mental_health_impacts"] = []
        
        # Add metadata
        transformed["metadata"] = {
            "version": "0.1.0",
            "created": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "source_urls": [
                f"https://fdc.nal.usda.gov/fdc-app.html#/food-details/{usda_data.get('fdcId')}/nutrients"
            ],
            "tags": []
        }
        
        return transformed
    
    def _calculate_completeness(self, transformed_data: Dict) -> float:
        """
        Calculate the completeness score for transformed data.
        
        Args:
            transformed_data: Transformed food data
        
        Returns:
            Completeness score between 0 and 1
        """
        # Count fields that have values
        fields_with_values = 0
        total_standard_fields = 0
        
        # Check standard nutrients
        if 'standard_nutrients' in transformed_data:
            std_nutrients = transformed_data['standard_nutrients']
            total_standard_fields += 7  # Count basic nutrients as expected
            fields_with_values += sum(1 for k in ['calories', 'protein_g', 'carbohydrates_g', 
                                               'fat_g', 'fiber_g', 'sugars_g', 'sugars_added_g'] 
                                   if k in std_nutrients and std_nutrients[k] is not None)
        
        # Check brain nutrients
        if 'brain_nutrients' in transformed_data:
            brain_nutrients = transformed_data['brain_nutrients']
            # Core brain nutrients we hope to have
            core_brain_fields = ['vitamin_b6_mg', 'folate_mcg', 'vitamin_b12_mcg', 
                               'vitamin_d_mcg', 'magnesium_mg', 'zinc_mg', 'iron_mg',
                               'selenium_mcg', 'tryptophan_mg', 'tyrosine_mg']
            
            total_standard_fields += len(core_brain_fields)
            fields_with_values += sum(1 for k in core_brain_fields 
                                   if k in brain_nutrients and brain_nutrients[k] is not None)
            
            # Check omega-3
            if 'omega3' in brain_nutrients:
                omega3 = brain_nutrients['omega3']
                omega3_fields = ['total_g', 'epa_mg', 'dha_mg', 'ala_mg']
                total_standard_fields += len(omega3_fields)
                fields_with_values += sum(1 for k in omega3_fields 
                                       if k in omega3 and omega3[k] is not None)
        
        # Calculate completeness
        if total_standard_fields > 0:
            return round(fields_with_values / total_standard_fields, 2)
        return 0.0
    
    def process_directory(self, input_dir: str, output_dir: str, db_client: PostgresClient = None) -> List[str]:
        """
        Process all USDA food data files in a directory.
        
        Args:
            db_client: Database client
            
        Returns:
            List of paths to transformed data files
        """
        db_client = db_client or self.db_client
        
        transformed_files = []
        
        input_files = db_client.get_all_foods()
        
        for input_file in input_files:
            try:
                usda_data = input_file
                transformed_data = self.transform_usda_food(usda_data)
                db_client.import_food_from_json(transformed_data)
            except Exception as e:
                logger.error(f"Error processing {input_file}: {e}")
        
        return transformed_files


def main():
    """Main function to execute the transformation."""
    schema_path = os.path.join("schema", "schema.json")
    db_client = PostgresClient()

    try:
        transformer = USDADataTransformer(schema_path, db_client)
        transformed_files = transformer.process_directory("", "", db_client)
        logger.info(f"Successfully transformed {len(transformed_files)} files")
    except Exception as e:
        logger.error(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
