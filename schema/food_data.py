from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime

from food_data_enums import (
    ImpactType, Direction, TimeToEffect, BrainNutrientSource, 
    ImpactsSource, SourcePriorityType, InteractionType, 
    EffectType, PatternName, PatternContribution, CalculationMethod
)
from food_data_constants import (
    BRAIN_NUTRIENTS_TO_PREDICT, BIOACTIVE_COMPOUNDS_TO_PREDICT,
    DEFAULT_CONFIDENCE_RATINGS, FOOD_CATEGORY_MAPPING
)

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
    
    def to_dict(self) -> Dict:
        """Convert dataclass to dictionary."""
        return asdict(self)
    
    def calculate_completeness(self) -> float:
        """Calculate the completeness score of the food data."""
        fields_with_values = 0
        total_fields = 0
        
        # Standard nutrients (core fields)
        std_nutrient_fields = [
            "calories", "protein_g", "carbohydrates_g", 
            "fat_g", "fiber_g", "sugars_g"
        ]
        
        total_fields += len(std_nutrient_fields)
        for field in std_nutrient_fields:
            if getattr(self.standard_nutrients, field) is not None:
                fields_with_values += 1
        
        # Brain nutrients (if present)
        if self.brain_nutrients:
            brain_nutrient_fields = [
                "tryptophan_mg", "vitamin_b6_mg", "folate_mcg", 
                "vitamin_b12_mcg", "vitamin_d_mcg", "magnesium_mg", 
                "zinc_mg", "iron_mg"
            ]
            
            total_fields += len(brain_nutrient_fields)
            for field in brain_nutrient_fields:
                if getattr(self.brain_nutrients, field) is not None:
                    fields_with_values += 1
            
            # Omega-3 fields
            if self.brain_nutrients.omega3:
                omega3_fields = ["total_g", "epa_mg", "dha_mg", "ala_mg"]
                total_fields += len(omega3_fields)
                for field in omega3_fields:
                    if getattr(self.brain_nutrients.omega3, field) is not None:
                        fields_with_values += 1
        
        completeness = fields_with_values / total_fields if total_fields > 0 else 0.0
        return round(completeness, 2)
    
    def update_completeness(self) -> None:
        """Update the completeness score in data_quality."""
        self.data_quality.completeness = self.calculate_completeness()
    
    def has_brain_nutrient(self, nutrient: str) -> bool:
        """Check if the food has a specific brain nutrient."""
        if not self.brain_nutrients:
            return False
            
        if "." in nutrient:
            # Handle nested paths like omega3.epa_mg
            section, field = nutrient.split(".")
            section_obj = getattr(self.brain_nutrients, section, None)
            return section_obj is not None and getattr(section_obj, field, None) is not None
            
        return getattr(self.brain_nutrients, nutrient, None) is not None
    
    def get_brain_nutrient(self, nutrient: str) -> Optional[float]:
        """Get the value of a specific brain nutrient."""
        if not self.brain_nutrients:
            return None
            
        if "." in nutrient:
            # Handle nested paths like omega3.epa_mg
            section, field = nutrient.split(".")
            section_obj = getattr(self.brain_nutrients, section, None)
            if section_obj is None:
                return None
            return getattr(section_obj, field, None)
            
        return getattr(self.brain_nutrients, nutrient, None)
    
    def has_mental_health_impacts(self) -> bool:
        """Check if the food has any mental health impacts."""
        return bool(self.mental_health_impacts)
    
    def get_impacts_by_type(self, impact_type: Union[ImpactType, str]) -> List[MentalHealthImpact]:
        """Get mental health impacts by type."""
        if not self.mental_health_impacts:
            return []
            
        # Convert string to enum if needed
        if isinstance(impact_type, str):
            try:
                impact_type_enum = ImpactType(impact_type)
            except ValueError:
                # If it's not a valid enum value, use the string as is
                return [impact for impact in self.mental_health_impacts 
                        if impact.impact_type == impact_type]
            
            return [impact for impact in self.mental_health_impacts 
                    if impact.impact_type == impact_type_enum]
        else:
            return [impact for impact in self.mental_health_impacts 
                    if impact.impact_type == impact_type]
    
    def update_timestamp(self) -> None:
        """Update the last_updated timestamp."""
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
    
    def get_missing_brain_nutrients(self) -> List[str]:
        """Get a list of missing brain nutrients that should be predicted."""
        missing = []
        for nutrient in BRAIN_NUTRIENTS_TO_PREDICT:
            if not self.has_brain_nutrient(nutrient):
                missing.append(nutrient)
        return missing
    
    def get_missing_bioactive_compounds(self) -> List[str]:
        """Get a list of missing bioactive compounds that should be predicted."""
        if not self.bioactive_compounds:
            return BIOACTIVE_COMPOUNDS_TO_PREDICT.copy()
            
        missing = []
        for compound in BIOACTIVE_COMPOUNDS_TO_PREDICT:
            if getattr(self.bioactive_compounds, compound, None) is None:
                missing.append(compound)
        return missing
    
    def validate(self) -> List[str]:
        """Validate the food data against schema requirements."""
        from schema_validator import SchemaValidator
        return SchemaValidator.validate_food_data(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'FoodData':
        """Create FoodData instance from dictionary."""
        # Handle nested dataclasses
        standard_nutrients_data = data.get('standard_nutrients', {})
        standard_nutrients = StandardNutrients(**standard_nutrients_data) if standard_nutrients_data else StandardNutrients()
        
        data_quality_data = data.get('data_quality', {})
        # Make a copy to avoid modifying the original
        data_quality_copy = data_quality_data.copy()
        
        # Handle source_priority separately
        source_priority = None
        if 'source_priority' in data_quality_copy:
            source_priority = SourcePriority(**data_quality_copy.pop('source_priority', {}))
        
        data_quality = DataQuality(**data_quality_copy, source_priority=source_priority)
        
        metadata_data = data.get('metadata', {})
        metadata = Metadata(**metadata_data) if metadata_data else Metadata(
            version='0.1.0',
            created=datetime.now().isoformat(),
            last_updated=datetime.now().isoformat(),
        )
        
        serving_info = None
        if 'serving_info' in data:
            serving_info = ServingInfo(**data['serving_info'])
        
        brain_nutrients = None
        if 'brain_nutrients' in data:
            brain_data = data['brain_nutrients'].copy()
            omega3 = None
            if 'omega3' in brain_data:
                omega3 = Omega3(**brain_data.pop('omega3', {}))
            brain_nutrients = BrainNutrients(**brain_data, omega3=omega3)
        
        bioactive_compounds = None
        if 'bioactive_compounds' in data:
            bioactive_compounds = BioactiveCompounds(**data['bioactive_compounds'])
        
        mental_health_impacts = []
        for impact in data.get('mental_health_impacts', []):
            impact_copy = impact.copy()
            research_support = []
            for support in impact_copy.pop('research_support', []):
                research_support.append(ResearchSupport(**support))
            impact_copy['research_support'] = research_support
            mental_health_impacts.append(MentalHealthImpact(**impact_copy))
        
        nutrient_interactions = []
        for interaction in data.get('nutrient_interactions', []):
            interaction_copy = interaction.copy()
            research_support = []
            for support in interaction_copy.pop('research_support', []):
                research_support.append(ResearchSupport(**support))
            interaction_copy['research_support'] = research_support
            nutrient_interactions.append(NutrientInteraction(**interaction_copy))
        
        contextual_factors = None
        if 'contextual_factors' in data:
            cf_data = data['contextual_factors'].copy()
            
            # Parse CircadianEffects
            circadian_effects = None
            if 'circadian_effects' in cf_data:
                ce_data = cf_data.pop('circadian_effects', {})
                factors = []
                for factor in ce_data.pop('factors', []):
                    factors.append(CircadianFactor(**factor))
                circadian_effects = CircadianEffects(
                    description=ce_data.get('description'),
                    factors=factors
                )
            
            # Parse FoodCombinations
            food_combinations = []
            for combo in cf_data.pop('food_combinations', []):
                food_combinations.append(FoodCombination(**combo))
            
            # Parse PreparationEffects
            preparation_effects = []
            for effect in cf_data.pop('preparation_effects', []):
                preparation_effects.append(PreparationEffect(**effect))
            
            contextual_factors = ContextualFactors(
                circadian_effects=circadian_effects,
                food_combinations=food_combinations,
                preparation_effects=preparation_effects
            )
        
        population_variations = []
        for pv in data.get('population_variations', []):
            pv_copy = pv.copy()
            variations = []
            for var in pv_copy.pop('variations', []):
                variations.append(NutrientVariation(**var))
            pv_copy['variations'] = variations
            population_variations.append(PopulationVariation(**pv_copy))
        
        dietary_patterns = []
        for pattern in data.get('dietary_patterns', []):
            dietary_patterns.append(DietaryPattern(**pattern))
        
        inflammatory_index = None
        if 'inflammatory_index' in data:
            inflammatory_index = InflammatoryIndex(**data['inflammatory_index'])
        
        neural_targets = []
        for target in data.get('neural_targets', []):
            neural_targets.append(NeuralTarget(**target))
        
        return cls(
            food_id=data.get('food_id', ''),
            name=data.get('name', ''),
            category=data.get('category', ''),
            description=data.get('description'),
            standard_nutrients=standard_nutrients,
            serving_info=serving_info,
            brain_nutrients=brain_nutrients,
            bioactive_compounds=bioactive_compounds,
            mental_health_impacts=mental_health_impacts,
            nutrient_interactions=nutrient_interactions,
            contextual_factors=contextual_factors,
            population_variations=population_variations,
            dietary_patterns=dietary_patterns,
            inflammatory_index=inflammatory_index,
            neural_targets=neural_targets,
            data_quality=data_quality,
            metadata=metadata
        )