from enum import Enum

class ImpactType(str, Enum):
    MOOD_ELEVATION = "mood_elevation"
    MOOD_DEPRESSION = "mood_depression"
    ANXIETY_REDUCTION = "anxiety_reduction"
    ANXIETY_INCREASE = "anxiety_increase"
    COGNITIVE_ENHANCEMENT = "cognitive_enhancement"
    COGNITIVE_DECLINE = "cognitive_decline"
    ENERGY_INCREASE = "energy_increase"
    ENERGY_DECREASE = "energy_decrease"
    STRESS_REDUCTION = "stress_reduction"
    SLEEP_IMPROVEMENT = "sleep_improvement"
    GUT_HEALTH_IMPROVEMENT = "gut_health_improvement"

class Direction(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    MIXED = "mixed"

class TimeToEffect(str, Enum):
    ACUTE = "acute"
    CUMULATIVE = "cumulative"
    BOTH = "both_acute_and_cumulative"

class BrainNutrientSource(str, Enum):
    USDA_PROVIDED = "usda_provided"
    OPENFOODFACTS = "openfoodfacts"
    LITERATURE_DERIVED = "literature_derived"
    AI_GENERATED = "ai_generated"
    EXPERT_ESTIMATED = "expert_estimated"

class ImpactsSource(str, Enum):
    DIRECT_STUDIES = "direct_studies"
    LITERATURE_REVIEW = "literature_review"
    MECHANISM_INFERENCE = "mechanism_inference"
    AI_GENERATED = "ai_generated"

class SourcePriorityType(str, Enum):
    USDA = "usda"
    OPENFOODFACTS = "openfoodfacts"
    LITERATURE = "literature"
    AI_GENERATED = "ai_generated"

class InteractionType(str, Enum):
    SYNERGISTIC = "synergistic"
    ANTAGONISTIC = "antagonistic"
    REQUIRED_COFACTOR = "required_cofactor"
    PROTECTIVE = "protective"
    INHIBITORY = "inhibitory"

class EffectType(str, Enum):
    UPREGULATION = "upregulation"
    DOWNREGULATION = "downregulation"
    MODULATION = "modulation"
    PROTECTION = "protection"

class PatternName(str, Enum):
    MEDITERRANEAN = "mediterranean"
    WESTERN = "western"
    DASH = "dash"
    MIND = "mind"
    VEGETARIAN = "vegetarian"
    VEGAN = "vegan"
    KETOGENIC = "ketogenic"
    LOW_FODMAP = "low_fodmap"

class PatternContribution(str, Enum):
    KEY_COMPONENT = "key_component"
    SUPPORTIVE = "supportive"
    OCCASIONAL = "occasional"
    LIMITED = "limited"
    AVOIDED = "avoided"

class CalculationMethod(str, Enum):
    DIETARY_INFLAMMATORY_INDEX = "dietary_inflammatory_index"
    EMPIRICAL_DIETARY_INDEX = "empirical_dietary_index"
    EXPERT_ESTIMATE = "expert_estimate"