
from typing import Dict, List, Any

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