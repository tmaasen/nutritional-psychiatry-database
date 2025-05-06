from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime

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
    confidence: Optional[float] = None

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
    impact_type: str  # One of mood_elevation, mood_depression, etc.
    direction: str  # positive, negative, neutral, mixed
    mechanism: str
    strength: float
    confidence: float
    time_to_effect: Optional[str] = None  # acute, cumulative, both_acute_and_cumulative
    research_context: Optional[str] = None
    research_support: List[ResearchSupport] = field(default_factory=list)
    notes: Optional[str] = None

@dataclass
class DataQuality:
    completeness: float
    overall_confidence: float
    brain_nutrients_source: Optional[str] = None
    impacts_source: Optional[str] = None
    source_priority: Dict[str, str] = field(default_factory=dict)

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
class InflammatoryIndex:
    value: float
    confidence: float
    calculation_method: str
    citations: List[str] = field(default_factory=list)

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
    inflammatory_index: Optional[InflammatoryIndex] = None
    
    def to_dict(self) -> Dict:
        """Convert dataclass to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'FoodData':
        """Create FoodData instance from dictionary."""
        # Handle nested dataclasses
        standard_nutrients = StandardNutrients(**data.get('standard_nutrients', {}))
        
        data_quality = DataQuality(**data.get('data_quality', {
            'completeness': 0.0,
            'overall_confidence': 5.0
        }))
        
        metadata = Metadata(**data.get('metadata', {
            'version': '0.1.0',
            'created': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat(),
        }))
        
        serving_info = None
        if 'serving_info' in data:
            serving_info = ServingInfo(**data['serving_info'])
        
        brain_nutrients = None
        if 'brain_nutrients' in data:
            brain_data = data['brain_nutrients'].copy()
            if 'omega3' in brain_data:
                brain_data['omega3'] = Omega3(**brain_data['omega3'])
            brain_nutrients = BrainNutrients(**brain_data)
        
        bioactive_compounds = None
        if 'bioactive_compounds' in data:
            bioactive_compounds = BioactiveCompounds(**data['bioactive_compounds'])
        
        mental_health_impacts = []
        for impact in data.get('mental_health_impacts', []):
            research_support = []
            for support in impact.get('research_support', []):
                research_support.append(ResearchSupport(**support))
            
            impact_copy = impact.copy()
            impact_copy['research_support'] = research_support
            mental_health_impacts.append(MentalHealthImpact(**impact_copy))
        
        inflammatory_index = None
        if 'inflammatory_index' in data:
            inflammatory_index = InflammatoryIndex(**data['inflammatory_index'])
        
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
            inflammatory_index=inflammatory_index,
            data_quality=data_quality,
            metadata=metadata
        )