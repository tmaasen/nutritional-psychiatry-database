from typing import Dict, List, Any, Union
from dataclasses import is_dataclass, fields

from schema.food_data import (
    FoodData, StandardNutrients, BrainNutrients, Omega3,
    MentalHealthImpact, DataQuality, Metadata, ResearchSupport
)
from constants.food_data_constants import (
    BRAIN_NUTRIENTS_FIELDS, STD_NUTRIENT_FIELDS, OMEGA3_FIELDS,
    DEFAULT_CONFIDENCE_RATINGS
)
from constants.food_data_enums import ImpactType, Direction, TimeToEffect

class SchemaValidator:
    """Validates food data against the schema."""
    
    @staticmethod
    def validate_food_data(data: Union[Dict, FoodData]) -> List[str]:
        errors = []
        
        # Convert FoodData instance to dict if needed
        if is_dataclass(data):
            data = data.to_dict()
        
        # Required fields
        required_fields = ["food_id", "name", "category", "standard_nutrients", "data_quality", "metadata"]
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")
        
        # Validate specific section structures if they exist
        if "standard_nutrients" in data:
            if not isinstance(data["standard_nutrients"], dict):
                errors.append("standard_nutrients must be a dictionary")
            else:
                errors.extend(SchemaValidator._validate_standard_nutrients(data["standard_nutrients"]))
            
        if "brain_nutrients" in data:
            if not isinstance(data["brain_nutrients"], dict):
                errors.append("brain_nutrients must be a dictionary")
            else:
                errors.extend(SchemaValidator._validate_brain_nutrients(data["brain_nutrients"]))
            
        if "mental_health_impacts" in data:
            if not isinstance(data["mental_health_impacts"], list):
                errors.append("mental_health_impacts must be a list")
            else:
                errors.extend(SchemaValidator._validate_mental_health_impacts(data["mental_health_impacts"]))
            
        if "metadata" in data:
            errors.extend(SchemaValidator._validate_metadata(data["metadata"]))
        
        if "data_quality" in data:
            errors.extend(SchemaValidator._validate_data_quality(data["data_quality"]))
        
        # Add data quality checks
        quality_warnings = SchemaValidator.check_data_quality(data)
        errors.extend(quality_warnings)
        
        return errors
    
    @staticmethod
    def _validate_standard_nutrients(nutrients: Dict) -> List[str]:
        """Validate standard nutrients section."""
        errors = []
        
        # Check for required fields
        for field in STD_NUTRIENT_FIELDS:
            if field in nutrients and not isinstance(nutrients[field], (int, float, type(None))):
                errors.append(f"standard_nutrients.{field} must be a number or null")
        
        return errors
    
    @staticmethod
    def _validate_brain_nutrients(nutrients: Dict) -> List[str]:
        """Validate brain nutrients section."""
        errors = []
        
        # Check for required fields
        for field in BRAIN_NUTRIENTS_FIELDS:
            if field in nutrients and not isinstance(nutrients[field], (int, float, type(None))):
                errors.append(f"brain_nutrients.{field} must be a number or null")
        
        # Validate omega-3 if present
        if 'omega3' in nutrients:
            omega3 = nutrients['omega3']
            if not isinstance(omega3, dict):
                errors.append("brain_nutrients.omega3 must be a dictionary")
            else:
                for field in OMEGA3_FIELDS:
                    if field in omega3 and not isinstance(omega3[field], (int, float, type(None))):
                        errors.append(f"brain_nutrients.omega3.{field} must be a number or null")
        
        return errors
    
    @staticmethod
    def _validate_mental_health_impacts(impacts: List[Dict]) -> List[str]:
        """Validate mental health impacts section."""
        errors = []
        
        for i, impact in enumerate(impacts):
            # Check required fields
            required_fields = ["impact_type", "direction", "mechanism", "strength", "confidence"]
            for field in required_fields:
                if field not in impact:
                    errors.append(f"mental_health_impacts[{i}].{field} is required")
            
            # Validate field types
            if "strength" in impact and not isinstance(impact["strength"], int):
                errors.append(f"mental_health_impacts[{i}].strength must be an integer")
            if "confidence" in impact and not isinstance(impact["confidence"], int):
                errors.append(f"mental_health_impacts[{i}].confidence must be an integer")
            
            # Validate research support
            if "research_support" in impact:
                if not isinstance(impact["research_support"], list):
                    errors.append(f"mental_health_impacts[{i}].research_support must be a list")
                else:
                    for j, support in enumerate(impact["research_support"]):
                        if not isinstance(support, dict):
                            errors.append(f"mental_health_impacts[{i}].research_support[{j}] must be a dictionary")
                        elif "citation" not in support:
                            errors.append(f"mental_health_impacts[{i}].research_support[{j}].citation is required")
        
        return errors
    
    @staticmethod
    def _validate_metadata(metadata: Dict) -> List[str]:
        """Validate metadata section."""
        errors = []
        
        required_fields = ["version", "created", "last_updated"]
        for field in required_fields:
            if field not in metadata:
                errors.append(f"metadata.{field} is required")
        
        if "source_urls" in metadata and not isinstance(metadata["source_urls"], list):
            errors.append("metadata.source_urls must be a list")
        
        if "source_ids" in metadata and not isinstance(metadata["source_ids"], dict):
            errors.append("metadata.source_ids must be a dictionary")
        
        return errors
    
    @staticmethod
    def _validate_data_quality(data_quality: Dict) -> List[str]:
        """Validate data quality section."""
        errors = []
        
        # Check completeness
        if "completeness" in data_quality:
            completeness = data_quality["completeness"]
            if not isinstance(completeness, (int, float)) or completeness < 0 or completeness > 1:
                errors.append("data_quality.completeness must be a number between 0 and 1")
        
        # Check overall confidence
        if "overall_confidence" in data_quality:
            confidence = data_quality["overall_confidence"]
            if not isinstance(confidence, int) or confidence < 1 or confidence > 10:
                errors.append("data_quality.overall_confidence must be an integer between 1 and 10")
        
        # Check source information
        if "brain_nutrients_source" not in data_quality:
            errors.append("Missing brain_nutrients_source in data_quality")
        
        if "impacts_source" not in data_quality:
            errors.append("Missing impacts_source in data_quality")
        
        return errors
    
    @staticmethod
    def check_data_quality(food_data: Dict) -> List[str]:
        """Check for data quality issues beyond basic schema validation."""
        warnings = []
        
        # Check for missing brain nutrients
        if 'brain_nutrients' in food_data:
            brain_nutrients = food_data['brain_nutrients']
            
            # Check core brain nutrients
            missing = [n for n in BRAIN_NUTRIENTS_FIELDS if n not in brain_nutrients or brain_nutrients.get(n) is None]
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
                    for component in OMEGA3_FIELDS:
                        if component != 'total_g' and component in omega3 and omega3[component] is not None:
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