
import json
import os
from typing import Dict, List, Any, Optional
from utils.logging_utils import setup_logging
logger = setup_logging(__name__)
class NutrientUtils:
    """Utility class for nutrient conversion operations."""
    
    @staticmethod
    def g_to_mg(value: float) -> float:
        """Convert grams to milligrams."""
        return value * 1000
    
    @staticmethod
    def g_to_mcg(value: float) -> float:
        """Convert grams to micrograms."""
        return value * 1000000
    
    @staticmethod
    def extract_nutrient_by_mapping(
        nutrient_data: List[Dict[str, Any]], 
        mapping: Dict[str, str],
        id_field: str = "id",
        value_field: str = "amount",
        unit_field: str = "unitName"
    ) -> Dict[str, float]:
        """
        Extract nutrients from a list of nutrient objects using a mapping.
        
        Works with USDA, OpenFoodFacts, and other structured nutrient data.
        
        Args:
            nutrient_data: List of nutrient objects
            mapping: Dictionary mapping external nutrient IDs to schema field names
            id_field: Field name containing the nutrient identifier
            value_field: Field name containing the nutrient value
            unit_field: Field name containing the unit information
            
        Returns:
            Dictionary of extracted nutrients with schema field names as keys
        """
        extracted = {}
        
        for nutrient in nutrient_data:
            nutrient_id = str(nutrient.get(id_field, ""))
            
            if nutrient_id in mapping:
                # Get the target field name in our schema
                target_field = mapping[nutrient_id]
                
                # Extract the value
                value = nutrient.get(value_field)
                
                if value is not None:
                    # Handle unit conversions if needed
                    unit = nutrient.get(unit_field, "")
                    if unit == "µg":  # Convert micrograms to milligrams
                        value /= 1000
                    
                    extracted[target_field] = value
        
        return extracted

    @staticmethod
    def calculate_nutrient_completeness(
        data: Dict[str, Any], 
        required_fields: Dict[str, List[str]]
    ) -> float:
        """
        Calculate completeness score for nutritional data.
        
        Args:
            data: Food data dictionary
            required_fields: Dictionary mapping sections to lists of required fields
                Example: {"standard_nutrients": ["calories", "protein_g"], ...}
                
        Returns:
            Completeness score between 0 and 1
        """
        total_fields = 0
        filled_fields = 0
        
        for section, fields in required_fields.items():
            if section in data:
                section_data = data[section]
                total_fields += len(fields)
                
                for field in fields:
                    if field in section_data and section_data[field] is not None:
                        filled_fields += 1
        
        if total_fields == 0:
            return 0.0
            
        return round(filled_fields / total_fields, 2)

class NutrientNameNormalizer:
    """Normalizes nutrient names to match our schema."""
    
    def __init__(self, mapping_file: Optional[str] = None):
        """
        Initialize with optional mapping file.
        
        Args:
            mapping_file: Path to JSON file with nutrient name mappings
        """
        # Default mappings from food_data_constants could be used instead
        self.mapping = {
            # Default mappings
            "omega-3": "omega3.total_g",
            "omega-3 fatty acids": "omega3.total_g",
            "epa": "omega3.epa_mg",
            "dha": "omega3.dha_mg",
            "alpha-linolenic acid": "omega3.ala_mg",
            "vitamin b6": "vitamin_b6_mg",
            "pyridoxine": "vitamin_b6_mg",
            "folate": "folate_mcg",
            "folic acid": "folate_mcg",
            "vitamin b12": "vitamin_b12_mcg",
            "cobalamin": "vitamin_b12_mcg",
            "vitamin d": "vitamin_d_mcg",
            "cholecalciferol": "vitamin_d_mcg",
            "magnesium": "magnesium_mg",
            "zinc": "zinc_mg",
            "iron": "iron_mg",
            "selenium": "selenium_mcg",
            "tryptophan": "tryptophan_mg",
            "tyrosine": "tyrosine_mg",
            "choline": "choline_mg",
            "polyphenols": "bioactive_compounds.polyphenols_mg",
            "flavonoids": "bioactive_compounds.flavonoids_mg",
            "anthocyanins": "bioactive_compounds.anthocyanins_mg",
            "carotenoids": "bioactive_compounds.carotenoids_mg",
            "probiotics": "bioactive_compounds.probiotics_cfu",
            "prebiotic fiber": "bioactive_compounds.prebiotic_fiber_g"
        }
        
        # Load additional mappings if provided
        if mapping_file and os.path.exists(mapping_file):
            try:
                with open(mapping_file, 'r') as f:
                    additional_mappings = json.load(f)
                self.mapping.update(additional_mappings)
                logger.info(f"Loaded {len(additional_mappings)} additional nutrient mappings")
            except Exception as e:
                logger.error(f"Error loading nutrient mappings: {e}")
    
    def normalize(self, nutrient_name: str) -> str:
        """
        Normalize a nutrient name to match our schema.
        
        Args:
            nutrient_name: Raw nutrient name from literature
            
        Returns:
            Normalized nutrient name according to our schema
        """
        # Convert to lowercase for matching
        nutrient_lower = nutrient_name.lower()
        
        # Check for exact match
        if nutrient_lower in self.mapping:
            return self.mapping[nutrient_lower]
        
        # Check for partial matches
        for key, value in self.mapping.items():
            if key in nutrient_lower:
                return value
        
        # If no match, return as is
        return nutrient_name