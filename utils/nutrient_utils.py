import json
import os
from typing import Dict, List, Any, Optional
from schema.food_data import StandardNutrients
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
    def extract_nutrients_by_mapping(
        nutrient_data: List[Dict[str, Any]], 
        mapping: Dict[str, str],
        id_field: str = "id",
        value_field: str = "amount",
        unit_field: str = "unitName"
    ) -> StandardNutrients:

        extracted = StandardNutrients()
        
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
                    
                    extracted.nutrients[target_field] = value
        
        return extracted

    @staticmethod
    def parse_nutrient_predictions(response: Any) -> Dict[str, float]:
        """
        Parse nutrient predictions from AI response.
        
        Args:
            response: AI response (string or parsed dict)
            
        Returns:
            Dictionary of nutrient predictions
        """
        try:
            # If response is a string, parse it
            if isinstance(response, str):
                # Extract JSON from the response using JSONParser
                predictions = JSONParser.parse_json(response, {})
            else:
                predictions = response
            
            # Filter to just the numeric values and ignore confidence ratings
            numeric_predictions = {}
            for key, value in predictions.items():
                if isinstance(value, (int, float)) and not key.startswith("confidence_") and key != "reasoning":
                    numeric_predictions[key] = value
            
            return numeric_predictions
            
        except Exception as e:
            logger.error(f"Error parsing nutrient predictions: {e}")
            return {}

    @staticmethod
    def parse_bioactive_predictions(response: Any) -> Dict[str, float]:
        """
        Parse bioactive compound predictions from AI response.
        
        Args:
            response: AI response (string or parsed dict)
            
        Returns:
            Dictionary of bioactive compound predictions
        """
        try:
            # If response is a string, parse it
            if isinstance(response, str):
                # Extract JSON from the response
                predictions = JSONParser.parse_json(response, {})
            else:
                predictions = response
            
            # Filter to keep just the numeric fields and remove confidence fields
            return {k: v for k, v in predictions.items() 
                    if isinstance(v, (int, float)) and not k.startswith("confidence_") 
                    and k != "reasoning"}
                    
        except Exception as e:
            logger.error(f"Error parsing bioactive predictions: {e}")
            return {}

    @staticmethod
    def parse_mental_health_impacts(response: Any) -> List[Dict]:
        """
        Parse mental health impact predictions from AI response.
        
        Args:
            response: AI response (string or parsed list/dict)
            
        Returns:
            List of mental health impact dictionaries
        """
        try:
            # If response is a string, parse it
            if isinstance(response, str):
                # Extract JSON from the response
                impacts = JSONParser.parse_json(response, [])
            else:
                impacts = response
            
            # Handle case where the result isn't a list
            if not isinstance(impacts, list):
                if isinstance(impacts, dict) and "impacts" in impacts:
                    impacts = impacts["impacts"]
                else:
                    impacts = [impacts]  # Treat as single impact
            
            # Validate each impact
            valid_impacts = []
            required_fields = ["impact_type", "direction", "mechanism", "strength", "confidence"]
            
            for impact in impacts:
                if isinstance(impact, dict) and all(field in impact for field in required_fields):
                    valid_impacts.append(impact)
                else:
                    missing = [field for field in required_fields if field not in impact]
                    logger.warning(f"Impact missing required fields: {missing}")
            
            return valid_impacts
            
        except Exception as e:
            logger.error(f"Error parsing mental health impacts: {e}")
            return []

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