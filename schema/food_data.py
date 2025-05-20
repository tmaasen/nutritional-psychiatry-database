from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime

from constants.food_data_enums import (
    ImpactType, Direction, TimeToEffect, BrainNutrientSource, 
    ImpactsSource, SourcePriorityType, InteractionType, 
    EffectType, PatternName, PatternContribution, CalculationMethod
)
from constants.food_data_constants import (
    DEFAULT_CONFIDENCE_RATINGS, FOOD_CATEGORY_MAPPING
)
from utils.completeness_utils import calculate_completeness

@dataclass
class ServingInfo:
    serving_size: float = 100.0
    serving_unit: str = "g"
    household_serving: Optional[str] = None

@dataclass
class StandardNutrients:
    calories: Optional[float] = None
    protein_g: Optional[float] = None
    carbohydrates_g: Optional[float] = None
    fat_g: Optional[float] = None
    fiber_g: Optional[float] = None
    sugars_g: Optional[float] = None
    sugars_added_g: Optional[float] = None
    calcium_mg: Optional[float] = None
    iron_mg: Optional[float] = None
    magnesium_mg: Optional[float] = None
    phosphorus_mg: Optional[float] = None
    potassium_mg: Optional[float] = None
    sodium_mg: Optional[float] = None
    zinc_mg: Optional[float] = None
    copper_mg: Optional[float] = None
    manganese_mg: Optional[float] = None
    selenium_mcg: Optional[float] = None
    vitamin_c_mg: Optional[float] = None
    vitamin_a_iu: Optional[float] = None

@dataclass
class Omega3:
    total_g: Optional[float] = None
    epa_mg: Optional[float] = None
    dha_mg: Optional[float] = None
    ala_mg: Optional[float] = None
    confidence: Optional[int] = DEFAULT_CONFIDENCE_RATINGS.get("omega3", 5)

@dataclass
class BrainNutrients:
    tryptophan_mg: Optional[float] = None
    tyrosine_mg: Optional[float] = None
    vitamin_b6_mg: Optional[float] = None
    folate_mcg: Optional[float] = None
    vitamin_b12_mcg: Optional[float] = None
    vitamin_d_mcg: Optional[float] = None
    magnesium_mg: Optional[float] = None
    zinc_mg: Optional[float] = None
    iron_mg: Optional[float] = None
    selenium_mcg: Optional[float] = None
    choline_mg: Optional[float] = None
    omega3: Optional[Omega3] = None

@dataclass
class BioactiveCompounds:
    polyphenols_mg: Optional[float] = None
    flavonoids_mg: Optional[float] = None
    anthocyanins_mg: Optional[float] = None
    carotenoids_mg: Optional[float] = None
    probiotics_cfu: Optional[float] = None
    prebiotic_fiber_g: Optional[float] = None

@dataclass
class ResearchSupport:
    citation: str
    doi: Optional[str] = None
    url: Optional[str] = None
    study_type: Optional[str] = None
    year: Optional[int] = None

@dataclass
class MentalHealthImpact:
    impact_type: Union[ImpactType, str]
    direction: Union[Direction, str]
    mechanism: str
    strength: int
    confidence: int
    time_to_effect: Optional[Union[TimeToEffect, str]] = None
    research_context: Optional[str] = None
    research_support: List[ResearchSupport] = field(default_factory=list)
    notes: Optional[str] = None
    
    def __post_init__(self):
        # Convert string values to enum values if needed
        if isinstance(self.impact_type, str):
            try:
                self.impact_type = ImpactType(self.impact_type)
            except ValueError:
                pass  # Keep as string if not valid enum value
                
        if isinstance(self.direction, str):
            try:
                self.direction = Direction(self.direction)
            except ValueError:
                pass
                
        if isinstance(self.time_to_effect, str):
            try:
                self.time_to_effect = TimeToEffect(self.time_to_effect)
            except ValueError:
                pass

@dataclass
class NutrientInteraction:
    interaction_id: str
    nutrients_involved: List[str]
    interaction_type: Union[InteractionType, str]
    mechanism: str
    confidence: int
    pathway: Optional[str] = None
    mental_health_relevance: Optional[str] = None
    research_support: List[ResearchSupport] = field(default_factory=list)
    foods_demonstrating: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        # Convert string to enum if needed
        if isinstance(self.interaction_type, str):
            try:
                self.interaction_type = InteractionType(self.interaction_type)
            except ValueError:
                pass

@dataclass
class CircadianFactor:
    factor: str
    effects: List[str]
    relevant_to: List[str]
    confidence: int
    citations: List[str] = field(default_factory=list)

@dataclass
class CircadianEffects:
    description: Optional[str] = None
    factors: List[CircadianFactor] = field(default_factory=list)

@dataclass
class FoodCombination:
    combination: str
    effects: List[str]
    relevant_to: List[str]
    confidence: int

@dataclass
class PreparationEffect:
    method: str
    effects: List[str]
    relevant_to: List[str]
    confidence: int

@dataclass
class ContextualFactors:
    circadian_effects: Optional[CircadianEffects] = None
    food_combinations: List[FoodCombination] = field(default_factory=list)
    preparation_effects: List[PreparationEffect] = field(default_factory=list)

@dataclass
class NutrientVariation:
    nutrient: str
    effect: str
    confidence: int
    mechanism: Optional[str] = None
    impact_modifier: Optional[float] = None
    recommendations: List[str] = field(default_factory=list)
    citations: List[str] = field(default_factory=list)

@dataclass
class PopulationVariation:
    population: str
    description: str
    variations: List[NutrientVariation] = field(default_factory=list)

@dataclass
class DietaryPattern:
    pattern_name: Union[PatternName, str]
    pattern_contribution: Union[PatternContribution, str]
    mental_health_relevance: Optional[str] = None
    
    def __post_init__(self):
        # Convert string to enum if needed
        if isinstance(self.pattern_name, str):
            try:
                self.pattern_name = PatternName(self.pattern_name)
            except ValueError:
                pass
                
        if isinstance(self.pattern_contribution, str):
            try:
                self.pattern_contribution = PatternContribution(self.pattern_contribution)
            except ValueError:
                pass

@dataclass
class InflammatoryIndex:
    value: float
    confidence: int = DEFAULT_CONFIDENCE_RATINGS.get("inflammatory_index", 5)
    calculation_method: Union[CalculationMethod, str] = CalculationMethod.EXPERT_ESTIMATE
    citations: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        # Convert string to enum if needed
        if isinstance(self.calculation_method, str):
            try:
                self.calculation_method = CalculationMethod(self.calculation_method)
            except ValueError:
                pass

@dataclass
class NeuralTarget:
    pathway: str
    effect: Union[EffectType, str]
    confidence: int
    mechanisms: List[str] = field(default_factory=list)
    mental_health_relevance: Optional[str] = None
    
    def __post_init__(self):
        # Convert string to enum if needed
        if isinstance(self.effect, str):
            try:
                self.effect = EffectType(self.effect)
            except ValueError:
                pass

@dataclass
class SourcePriority:
    standard_nutrients: Optional[SourcePriorityType] = None
    brain_nutrients: Optional[SourcePriorityType] = None
    bioactive_compounds: Optional[SourcePriorityType] = None
    
    def __post_init__(self):
        # Convert strings to enums if needed
        if isinstance(self.standard_nutrients, str):
            try:
                self.standard_nutrients = SourcePriorityType(self.standard_nutrients)
            except ValueError:
                pass
                
        if isinstance(self.brain_nutrients, str):
            try:
                self.brain_nutrients = SourcePriorityType(self.brain_nutrients)
            except ValueError:
                pass
                
        if isinstance(self.bioactive_compounds, str):
            try:
                self.bioactive_compounds = SourcePriorityType(self.bioactive_compounds)
            except ValueError:
                pass

@dataclass
class DataQuality:
    completeness: float
    overall_confidence: int
    brain_nutrients_source: Optional[Union[BrainNutrientSource, str]] = None
    impacts_source: Optional[Union[ImpactsSource, str]] = None
    source_priority: Optional[Union[SourcePriority, Dict]] = None
    
    def __post_init__(self):
        # Convert strings to enums if needed
        if isinstance(self.brain_nutrients_source, str):
            try:
                self.brain_nutrients_source = BrainNutrientSource(self.brain_nutrients_source)
            except ValueError:
                pass
                
        if isinstance(self.impacts_source, str):
            try:
                self.impacts_source = ImpactsSource(self.impacts_source)
            except ValueError:
                pass
                
        # Parse source_priority from dict if needed
        if isinstance(self.source_priority, dict):
            self.source_priority = SourcePriority(**self.source_priority)

@dataclass
class Metadata:
    version: str
    created: str
    last_updated: str
    source_urls: List[str] = field(default_factory=list)
    source_ids: Dict[str, str] = field(default_factory=dict)
    image_url: Optional[str] = None
    tags: List[str] = field(default_factory=list)

@dataclass
class FoodData:
    food_id: str
    name: str
    category: str
    standard_nutrients: StandardNutrients
    data_quality: DataQuality
    metadata: Metadata
    description: Optional[str] = None
    serving_info: Optional[ServingInfo] = None
    brain_nutrients: Optional[BrainNutrients] = None
    bioactive_compounds: Optional[BioactiveCompounds] = None
    mental_health_impacts: List[MentalHealthImpact] = field(default_factory=list)
    nutrient_interactions: List[NutrientInteraction] = field(default_factory=list)
    contextual_factors: Optional[ContextualFactors] = None
    population_variations: List[PopulationVariation] = field(default_factory=list)
    dietary_patterns: List[DietaryPattern] = field(default_factory=list)
    inflammatory_index: Optional[InflammatoryIndex] = None
    neural_targets: List[NeuralTarget] = field(default_factory=list)    
    processed: bool = False
    validated: bool = False
    validation_errors: Optional[List[str]] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Convert dataclass to dictionary."""
        return asdict(self)
    
    def update_timestamp(self) -> None:
        self.metadata.last_updated = datetime.now().isoformat()
    
    def normalize_category(self) -> None:
        """Normalize food category based on standard mappings."""
        if not self.category:
            return
            
        category_lower = self.category.lower()
        for key, value in FOOD_CATEGORY_MAPPING.items():
            if key in category_lower:
                self.category = value
                return

    @classmethod
    def _create_nested_dataclass(cls, data: Dict, dataclass_type: type, nested_fields: Dict[str, type] = None) -> Any:
        """
        Helper method to create nested dataclass instances.
        
        Args:
            data: Dictionary containing the data
            dataclass_type: The dataclass type to create
            nested_fields: Optional dict mapping field names to their nested dataclass types
            
        Returns:
            Instance of the specified dataclass type
        """
        if not data:
            return None
            
        # Handle nested fields if specified
        if nested_fields:
            data_copy = data.copy()
            for field_name, field_type in nested_fields.items():
                if field_name in data_copy:
                    if isinstance(data_copy[field_name], dict):
                        data_copy[field_name] = cls._create_nested_dataclass(
                            data_copy[field_name], 
                            field_type
                        )
            return dataclass_type(**data_copy)
            
        return dataclass_type(**data)
    
    @classmethod
    def _create_list_of_dataclasses(cls, data_list: List[Dict], dataclass_type: type, nested_fields: Dict[str, type] = None) -> List[Any]:
        """
        Helper method to create lists of dataclass instances.

        Returns:
            List of dataclass instances
        """
        if not data_list:
            return []
            
        return [
            cls._create_nested_dataclass(item, dataclass_type, nested_fields)
            for item in data_list
        ]
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'FoodData':
        """Create FoodData instance from dictionary."""
        nested_structure = {
            'standard_nutrients': (StandardNutrients, {}),
            'serving_info': (ServingInfo, {}),
            'brain_nutrients': (BrainNutrients, {'omega3': Omega3}),
            'bioactive_compounds': (BioactiveCompounds, {}),
            'data_quality': (DataQuality, {'source_priority': SourcePriority}),
            'metadata': (Metadata, {}),
            'inflammatory_index': (InflammatoryIndex, {}),
            'contextual_factors': (ContextualFactors, {
                'circadian_effects': CircadianEffects
            })
        }
        
        # Create a copy of the data to avoid modifying the original
        data_copy = data.copy()
        
        # Handle nested dataclasses
        for field_name, (dataclass_type, nested_fields) in nested_structure.items():
            if field_name in data_copy:
                data_copy[field_name] = cls._create_nested_dataclass(
                    data_copy[field_name],
                    dataclass_type,
                    nested_fields
                )
        
        # Handle lists of dataclasses
        list_fields = {
            'mental_health_impacts': (MentalHealthImpact, {'research_support': ResearchSupport}),
            'nutrient_interactions': (NutrientInteraction, {'research_support': ResearchSupport}),
            'population_variations': (PopulationVariation, {'variations': NutrientVariation}),
            'dietary_patterns': (DietaryPattern, {}),
            'neural_targets': (NeuralTarget, {})
        }
        
        for field_name, (dataclass_type, nested_fields) in list_fields.items():
            if field_name in data_copy:
                data_copy[field_name] = cls._create_list_of_dataclasses(
                    data_copy[field_name],
                    dataclass_type,
                    nested_fields
                )
        
        if 'metadata' not in data_copy:
            data_copy['metadata'] = Metadata(
                version='0.1.0',
                created=datetime.now().isoformat(),
                last_updated=datetime.now().isoformat(),
            )
        
        # Create the FoodData instance
        return cls(**data_copy)

@dataclass
class EvaluationMetrics:
    """Model for evaluation metrics records."""
    test_run_id: str
    timestamp: str
    metrics_type: str
    metrics_data: Dict[str, Any]
    id: Optional[int] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "test_run_id": self.test_run_id,
            "timestamp": self.timestamp,
            "metrics_type": self.metrics_type,
            "metrics_data": self.metrics_data
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'EvaluationMetrics':
        """Create instance from dictionary."""
        return cls(
            id=data.get("id"),
            test_run_id=data.get("test_run_id", ""),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            metrics_type=data.get("metrics_type", ""),
            metrics_data=data.get("metrics_data", {})
        )

@dataclass
class FoodEvaluation:
    """Model for food evaluation records."""
    food_id: str
    test_run_id: str
    timestamp: str
    evaluation_type: str
    evaluation_data: Dict[str, Any]
    id: Optional[int] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "food_id": self.food_id,
            "test_run_id": self.test_run_id,
            "timestamp": self.timestamp,
            "evaluation_type": self.evaluation_type,
            "evaluation_data": self.evaluation_data
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'FoodEvaluation':
        """Create instance from dictionary."""
        return cls(
            id=data.get("id"),
            food_id=data.get("food_id", ""),
            test_run_id=data.get("test_run_id", ""),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            evaluation_type=data.get("evaluation_type", ""),
            evaluation_data=data.get("evaluation_data", {})
        )