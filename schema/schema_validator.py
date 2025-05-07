from typing import Dict, List, Optional, Any, Union

class SchemaValidator:
    """Validates food data against the schema."""
    
    @staticmethod
    def validate_food_data(data: Dict) -> List[str]:
        """
        Validate food data against the schema.
        
        Args:
            data: Food data to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Required fields
        required_fields = ["food_id", "name", "category", "standard_nutrients", "data_quality", "metadata"]
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")
        
        # Validate specific section structures if they exist
        if "standard_nutrients" in data and not isinstance(data["standard_nutrients"], dict):
            errors.append("standard_nutrients must be a dictionary")
            
        if "brain_nutrients" in data and not isinstance(data["brain_nutrients"], dict):
            errors.append("brain_nutrients must be a dictionary")
            
        if "mental_health_impacts" in data and not isinstance(data["mental_health_impacts"], list):
            errors.append("mental_health_impacts must be a list")
            
        if "metadata" in data:
            metadata = data["metadata"]
            if "version" not in metadata:
                errors.append("metadata.version is required")
            if "source_urls" in metadata and not isinstance(metadata["source_urls"], list):
                errors.append("metadata.source_urls must be a list")
        
        # Validate data quality
        if "data_quality" in data:
            data_quality = data["data_quality"]
            if "completeness" in data_quality:
                completeness = data_quality["completeness"]
                if not isinstance(completeness, (int, float)) or completeness < 0 or completeness > 1:
                    errors.append("data_quality.completeness must be a number between 0 and 1")
            
            if "overall_confidence" in data_quality:
                confidence = data_quality["overall_confidence"]
                if not isinstance(confidence, (int, float)) or confidence < 1 or confidence > 10:
                    errors.append("data_quality.overall_confidence must be a number between 1 and 10")
        
        return errors