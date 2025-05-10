
from typing import Dict, List

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
                    
            # New validations from validation.py
            # Check for missing source information
            if "brain_nutrients_source" not in data_quality:
                errors.append("Missing brain_nutrients_source in data_quality")
            
            if "impacts_source" not in data_quality:
                errors.append("Missing impacts_source in data_quality")
        
        # Add data quality checks from validation.py
        quality_warnings = SchemaValidator.check_data_quality(data)
        errors.extend(quality_warnings)
        
        return errors
    
    @staticmethod
    def check_data_quality(food_data: Dict) -> List[str]:
        """
        Check for data quality issues beyond basic schema validation.
        
        Args:
            food_data: Food data dictionary
            
        Returns:
            List of warning messages
        """
        warnings = []
        
        # Check for missing brain nutrients
        if 'brain_nutrients' in food_data:
            brain_nutrients = food_data['brain_nutrients']
            
            # Core brain nutrients we expect to see (using constant)
            core_nutrients = ['tryptophan_mg', 'vitamin_b6_mg', 'folate_mcg', 
                             'vitamin_b12_mcg', 'vitamin_d_mcg', 'magnesium_mg', 
                             'zinc_mg', 'iron_mg']
            
            missing = [n for n in core_nutrients if n not in brain_nutrients or brain_nutrients.get(n) is None]
            if missing:
                warnings.append(f"Missing core brain nutrients: {', '.join(missing)}")
            
            # Check omega-3 completeness
            if 'omega3' in brain_nutrients:
                omega3 = brain_nutrients['omega3']
                if 'total_g' not in omega3 or omega3['total_g'] is None:
                    warnings.append("Missing total omega-3 value")
                
                # Check for implausible omega-3 values
                if 'total_g' in omega3 and omega3['total_g'] is not None:
                    total_g = omega3['total_g']
                    
                    # Check if individual components exceed total
                    components_sum = 0
                    for component in ['epa_mg', 'dha_mg', 'ala_mg']:
                        if component in omega3 and omega3[component] is not None:
                            components_sum += omega3[component]
                    
                    if components_sum > 0:
                        components_g = components_sum / 1000  # Convert mg to g
                        if components_g > total_g * 1.1:  # Allow 10% margin for rounding
                            warnings.append(f"Omega-3 components ({components_g:.2f}g) exceed total ({total_g:.2f}g)")
        
        # Check mental health impacts
        if 'mental_health_impacts' in food_data and food_data['mental_health_impacts']:
            impacts = food_data['mental_health_impacts']
            
            for i, impact in enumerate(impacts):
                # Check for impacts without research support
                if 'research_support' not in impact or not impact['research_support']:
                    warnings.append(f"Impact #{i+1} ({impact.get('impact_type', 'unknown')}) has no research support")
                
                # Check for high strength with low confidence
                if 'strength' in impact and 'confidence' in impact:
                    strength = impact['strength']
                    confidence = impact['confidence']
                    
                    if strength > 7 and confidence < 5:
                        warnings.append(f"Impact #{i+1} has high strength ({strength}) but low confidence ({confidence})")
        
        # Check for inconsistencies in values
        if 'standard_nutrients' in food_data and 'protein_g' in food_data['standard_nutrients']:
            protein = food_data['standard_nutrients'].get('protein_g')
            
            # Check tryptophan proportion (typically ~1-1.5% of protein)
            if ('brain_nutrients' in food_data and 
                'tryptophan_mg' in food_data['brain_nutrients']):
                tryptophan = food_data['brain_nutrients'].get('tryptophan_mg')
                
                if protein is not None and tryptophan is not None and protein > 0:
                    tryptophan_percent = (tryptophan / protein) / 10  # Convert mg/g to percentage
                    
                    if tryptophan_percent < 0.5 or tryptophan_percent > 2.0:
                        warnings.append(f"Unusual tryptophan proportion ({tryptophan_percent:.2f}% of protein)")
        
        return warnings