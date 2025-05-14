# Keywords for identifying nutrients in text
NUTRIENT_KEYWORDS = [
    "omega-3", "omega 3", "epa", "dha", "folate", "vitamin b", "vitamin d",
    "magnesium", "zinc", "iron", "selenium", "tryptophan", "tyrosine",
    "polyphenol", "flavonoid", "probiotic", "prebiotic", "fiber", "fibre",
    "fatty acid", "antioxidant", "choline", "protein", "carbohydrate",
    "sugar", "amino acid", "mineral", "micronutrient", "macronutrient"
]

# Keywords for identifying mental health outcomes in text
MENTAL_HEALTH_KEYWORDS = [
    "depression", "anxiety", "mood", "stress", "cognition", "cognitive",
    "memory", "attention", "focus", "brain health", "mental health",
    "well-being", "wellbeing", "psychological", "neurodevelopment",
    "neuroplasticity", "bdnf", "serotonin", "dopamine", "neurotransmitter",
    "stress response", "hpa axis", "inflammation", "neuroinflammation"
]

# Common food sources to identify in text
FOOD_SOURCES = [
    "fish", "seafood", "salmon", "sardines", "tuna", "mackerel", "nuts",
    "seeds", "vegetables", "fruits", "whole grains", "beans", "legumes",
    "dairy", "yogurt", "cheese", "eggs", "meat", "poultry", "olive oil",
    "fermented foods", "chocolate", "green tea", "berries", "leafy greens"
]

# Keywords indicating direction of effect
DIRECTION_KEYWORDS = {
    "positive": ["improve", "increase", "enhance", "elevate", "promote", "benefit", "positive", "protective"],
    "negative": ["worsen", "decrease", "reduce", "lower", "diminish", "impair", "negative", "harmful"],
    "mixed": ["mixed", "variable", "inconsistent", "context-dependent", "unclear", "varied"],
    "neutral": ["no effect", "no association", "no relationship", "no impact", "no influence", "neutral"]
}

# Evidence hierarchy for rating research quality
EVIDENCE_HIERARCHY = {
    "meta_analysis": 10,
    "systematic_review": 9,
    "rct": 8,  # Randomized Controlled Trial
    "cohort_large": 7,  # Large cohort study (>1000 participants)
    "cohort_medium": 6,  # Medium cohort study (100-1000 participants)
    "case_control": 5,
    "cross_sectional_large": 4,
    "cross_sectional_small": 3,
    "case_series": 2,
    "animal_study": 2,
    "in_vitro": 1,
    "expert_opinion": 1
}

# Factors that adjust evidence confidence
EVIDENCE_ADJUSTMENT_FACTORS = {
    "sample_size_large": 1,  # >1000 participants
    "sample_size_medium": 0,  # 100-1000 participants
    "sample_size_small": -1,  # <100 participants
    "mechanistic_explanation": 1,  # Clear mechanism provided
    "replicated_findings": 1,  # Findings replicated in multiple studies
    "methodological_issues": -2,  # Significant methodological issues
    "conflict_of_interest": -1,  # Potential conflicts of interest
    "nutrient_focus": 0,  # Primary focus on nutrient vs. incidental
    "direct_measurement": 1,  # Direct measurement vs. self-report
}

# Keywords to identify study types in text
STUDY_TYPE_KEYWORDS = {
    "meta-analysis": "meta_analysis",
    "meta analysis": "meta_analysis",
    "systematic review": "systematic_review",
    "randomized controlled trial": "rct",
    "rct": "rct",
    "randomised controlled trial": "rct",
    "double-blind": "rct",
    "double blind": "rct",
    "placebo-controlled": "rct",
    "placebo controlled": "rct",
    "cohort study": "cohort_medium",
    "prospective cohort": "cohort_medium",
    "longitudinal study": "cohort_medium",
    "case-control": "case_control",
    "case control": "case_control",
    "cross-sectional": "cross_sectional_small",
    "cross sectional": "cross_sectional_small",
    "observational study": "cross_sectional_small",
    "case series": "case_series",
    "case report": "case_series",
    "animal study": "animal_study",
    "animal model": "animal_study",
    "in vitro": "in_vitro",
    "cell culture": "in_vitro",
    "expert opinion": "expert_opinion",
    "review": "expert_opinion"
}

# Indicators for mechanistic explanations in text
MECHANISM_INDICATORS = [
    "through", "via", "by", "mechanism", "pathway", "due to",
    "mediated by", "because of", "as a result of"
]

# Maximum characters to extract for mechanism descriptions
MECHANISM_EXTRACT_LENGTH = 100

# Literature data quality constants
LITERATURE_CONFIDENCE_DEFAULT = 7  # Default confidence for literature-derived data
LITERATURE_COMPLETENESS_DEFAULT = 0.5  # Default completeness score for literature data

# Source priority by section
SOURCE_PRIORITY_MAPPING = {
    "standard_nutrients": ["usda", "openfoodfacts", "literature", "ai_generated"],
    "brain_nutrients": ["literature", "usda", "openfoodfacts", "ai_generated"],
    "bioactive_compounds": ["literature", "openfoodfacts", "usda", "ai_generated"],
    "mental_health_impacts": ["literature", "ai_generated"],
    "nutrient_interactions": ["literature", "ai_generated"],
    "inflammatory_index": ["literature", "openfoodfacts", "ai_generated"]
}

# Confidence thresholds for considering a source
SOURCE_CONFIDENCE_THRESHOLDS = {
    "usda": 0,  # Always trust USDA
    "openfoodfacts": 6,  # Decent confidence
    "literature": 0,  # Always trust literature
    "ai_generated": 7  # High confidence for AI
}

# Field names for source tracking
SOURCE_PRIORITY_FIELD = "source_priority"