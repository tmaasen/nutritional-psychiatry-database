# Nutritional Psychiatry Dataset: Data Dictionary

This document provides detailed descriptions of all fields in the Nutritional Psychiatry Dataset schema. It serves as a reference for understanding the data structure, field meanings, units of measurement, and data types.

```mermaid
classDiagram
    class FoodData {
        +String food_id
        +String name
        +String description
        +String category
        +ServingInfo serving_info
        +StandardNutrients standard_nutrients
        +BrainNutrients brain_nutrients
        +BioactiveCompounds bioactive_compounds
        +List~MentalHealthImpact~ mental_health_impacts
        +NutrientInteractions nutrient_interactions
        +ContextualFactors contextual_factors
        +InflammatoryIndex inflammatory_index
        +DataQuality data_quality
        +Metadata metadata
    }
    
    class ServingInfo {
        +Number serving_size
        +String serving_unit
        +String household_serving
    }
    
    class StandardNutrients {
        +Number calories
        +Number protein_g
        +Number carbohydrates_g
        +Number fat_g
        +Number fiber_g
        +Number sugars_g
        ...
    }
    
    class BrainNutrients {
        +Number tryptophan_mg
        +Number tyrosine_mg
        +Number vitamin_b6_mg
        +Number folate_mcg
        +Number vitamin_b12_mcg
        +Omega3 omega3
        ...
    }
    
    class Omega3 {
        +Number total_g
        +Number epa_mg
        +Number dha_mg
        +Number ala_mg
        +Number confidence
    }
    
    class BioactiveCompounds {
        +Number polyphenols_mg
        +Number flavonoids_mg
        +Number anthocyanins_mg
        +Number carotenoids_mg
        +Number probiotics_cfu
        +Number prebiotic_fiber_g
    }
    
    class MentalHealthImpact {
        +String impact_type
        +String direction
        +String mechanism
        +Number strength
        +Number confidence
        +String time_to_effect
        +String research_context
        +List~ResearchCitation~ research_support
    }
    
    class DataQuality {
        +Number completeness
        +Number overall_confidence
        +String brain_nutrients_source
        +String impacts_source
        +SourcePriority source_priority
    }
    
    class Metadata {
        +String version
        +DateTime created
        +DateTime last_updated
        +List~String~ source_urls
        +List~String~ tags
    }
    
    FoodData *-- ServingInfo
    FoodData *-- StandardNutrients
    FoodData *-- BrainNutrients
    FoodData *-- BioactiveCompounds
    FoodData *-- MentalHealthImpact
    FoodData *-- DataQuality
    FoodData *-- Metadata
    BrainNutrients *-- Omega3
```

## Basic Food Information

| Field | Description | Type | Example | Notes |
|-------|-------------|------|---------|-------|
| `food_id` | Unique identifier | String | "usda_173950" | Prefixed with source type (e.g., "usda_") |
| `name` | Common food name | String | "Blueberries, raw" | Standardized naming convention |
| `description` | Detailed description | String | "Raw blueberries (Vaccinium spp.), edible fruit portions" | May include taxonomic information |
| `category` | Food group/category | String | "Fruits" | Simplified category system |

## Serving Information

| Field | Description | Type | Example | Notes |
|-------|-------------|------|---------|-------|
| `serving_info.serving_size` | Standard serving size | Number | 100 | Typically per 100g for comparison |
| `serving_info.serving_unit` | Unit of measurement | String | "g" | Usually grams |
| `serving_info.household_serving` | Common household measure | String | "1 cup (148g)" | For practical use |

## Standard Nutrients

All values per 100g of food unless otherwise specified.

| Field | Description | Type | Unit | Notes |
|-------|-------------|------|------|-------|
| `standard_nutrients.calories` | Energy content | Number | kcal | Total caloric content |
| `standard_nutrients.protein_g` | Protein content | Number | g | Total protein |
| `standard_nutrients.carbohydrates_g` | Carbohydrate content | Number | g | Total carbohydrates |
| `standard_nutrients.fat_g` | Fat content | Number | g | Total fat |
| `standard_nutrients.fiber_g` | Dietary fiber | Number | g | Total fiber |
| `standard_nutrients.sugars_g` | Total sugars | Number | g | All sugars (natural + added) |
| `standard_nutrients.sugars_added_g` | Added sugars | Number | g | Sugars added during processing |
| `standard_nutrients.calcium_mg` | Calcium | Number | mg | |
| `standard_nutrients.iron_mg` | Iron | Number | mg | |
| `standard_nutrients.magnesium_mg` | Magnesium | Number | mg | |
| `standard_nutrients.phosphorus_mg` | Phosphorus | Number | mg | |
| `standard_nutrients.potassium_mg` | Potassium | Number | mg | |
| `standard_nutrients.sodium_mg` | Sodium | Number | mg | |
| `standard_nutrients.zinc_mg` | Zinc | Number | mg | |
| `standard_nutrients.vitamin_c_mg` | Vitamin C | Number | mg | |
| `standard_nutrients.vitamin_a_iu` | Vitamin A | Number | IU | International Units |

## Nutrient Interactions

Interactions between nutrients affecting mental health outcomes.

| Field | Description | Type | Notes |
|-------|-------------|------|-------|
| `interaction_id` | Unique identifier | String | e.g., "int_001" |
| `nutrients_involved` | List of interacting nutrients | Array | References to nutrient fields |
| `interaction_type` | Type of interaction | String | synergistic, antagonistic, required_cofactor, protective, inhibitory |
| `pathway` | Biochemical pathway affected | String | e.g., "serotonin_synthesis" |
| `mechanism` | Mechanism of action | String | Detailed explanation of interaction |
| `mental_health_relevance` | Relevance to mental health | String | How this interaction affects mental function |
| `confidence` | Confidence rating | Number | 1-10 scale |
| `research_support` | Supporting research | Array | Citations for interaction |
| `foods_demonstrating` | Foods showing this interaction | Array | Food IDs demonstrating interaction |

## Contextual Factors

Factors that affect how nutrients impact mental health based on context.

### Circadian Effects

| Field | Description | Type | Notes |
|-------|-------------|------|-------|
| `circadian_effects.description` | General description | String | Overview of time effects |
| `circadian_effects.factors[].factor` | Specific timing factor | String | e.g., "morning_consumption" |
| `circadian_effects.factors[].effects` | Effects of this timing | Array | List of effects |
| `circadian_effects.factors[].relevant_to` | Affected nutrients | Array | Nutrients affected by timing |
| `circadian_effects.factors[].confidence` | Confidence rating | Number | 1-10 scale |
| `circadian_effects.factors[].citations` | Supporting research | Array | Citations |

### Food Combinations

| Field | Description | Type | Notes |
|-------|-------------|------|-------|
| `food_combinations[].combination` | Combination type | String | e.g., "with_fat" |
| `food_combinations[].effects` | Effects of combination | Array | List of effects |
| `food_combinations[].relevant_to` | Affected nutrients | Array | Nutrients affected |
| `food_combinations[].confidence` | Confidence rating | Number | 1-10 scale |

### Preparation Effects

| Field | Description | Type | Notes |
|-------|-------------|------|-------|
| `preparation_effects[].method` | Preparation method | String | e.g., "fermentation" |
| `preparation_effects[].effects` | Effects of method | Array | List of effects |
| `preparation_effects[].relevant_to` | Affected nutrients | Array | Nutrients affected |
| `preparation_effects[].confidence` | Confidence rating | Number | 1-10 scale |

## Population Variations

Differences in response across different populations.

| Field | Description | Type | Notes |
|-------|-------------|------|-------|
| `population` | Target population | String | e.g., "older_adults" |
| `description` | Population description | String | Details about the population |
| `variations[].nutrient` | Affected nutrient | String | Nutrient field name |
| `variations[].effect` | Effect type | String | e.g., "reduced_absorption" |
| `variations[].mechanism` | Mechanism of variation | String | How the variation occurs |
| `variations[].impact_modifier` | Effect modifier | Number | Multiplier for effect strength |
| `variations[].recommendations` | Recommendations | Array | Advice for this population |
| `variations[].confidence` | Confidence rating | Number | 1-10 scale |
| `variations[].citations` | Supporting research | Array | Citations |

## Dietary Patterns

Information on whole dietary patterns this food contributes to.

| Field | Description | Type | Notes |
|-------|-------------|------|-------|
| `pattern_name` | Name of dietary pattern | String | mediterranean, western, dash, mind, etc. |
| `pattern_contribution` | Food's role in pattern | String | key_component, supportive, occasional, limited, avoided |
| `mental_health_relevance` | Mental health relevance | String | How this role affects mental health |

## Inflammatory Index

Food's inflammatory potential.

| Field | Description | Type | Notes |
|-------|-------------|------|-------|
| `value` | Inflammatory index value | Number | -10 (anti-inflammatory) to +10 (pro-inflammatory) |
| `confidence` | Confidence rating | Number | 1-10 scale |
| `calculation_method` | Method used | String | dietary_inflammatory_index, empirical_dietary_index, expert_estimate |
| `citations` | Supporting research | Array | Research citations |

## Neural Targets

Neural pathways affected by food components.

| Field | Description | Type | Notes |
|-------|-------------|------|-------|
| `pathway` | Neural pathway affected | String | e.g., "bdnf_signaling" |
| `effect` | Type of effect | String | upregulation, downregulation, modulation, protection |
| `confidence` | Confidence rating | Number | 1-10 scale |
| `mechanisms` | Mechanism descriptions | Array | How the effect occurs |
| `mental_health_relevance` | Relevance to mental health | String | Clinical significance |

## Data Quality Metrics (Extended)

| Field | Description | Type | Notes |
|-------|-------------|------|-------|
| `source_priority.standard_nutrients` | Source used for standard nutrients | String | usda, openfoodfacts, literature, ai_generated |
| `source_priority.brain_nutrients` | Source used for brain nutrients | String | usda, openfoodfacts, literature, ai_generated |
| `source_priority.bioactive_compounds` | Source used for bioactive compounds | String | usda, openfoodfacts, literature, ai_generated |

## Metadata (Extended)

| Field | Description | Type | Notes |
|-------|-------------|------|-------|
| `source_ids.usda_fdc_id` | USDA FDC ID | String | Original USDA identifier |
| `source_ids.openfoodfacts_id` | OpenFoodFacts ID | String | Original OpenFoodFacts barcode |

## Brain-Specific Nutrients

All values per 100g of food unless otherwise specified.

| Field | Description | Type | Unit | Notes |
|-------|-------------|------|------|-------|
| `brain_nutrients.tryptophan_mg` | Tryptophan | Number | mg | Precursor to serotonin |
| `brain_nutrients.tyrosine_mg` | Tyrosine | Number | mg | Precursor to dopamine |
| `brain_nutrients.vitamin_b6_mg` | Vitamin B6 | Number | mg | Involved in neurotransmitter synthesis |
| `brain_nutrients.folate_mcg` | Folate (B9) | Number | mcg | Essential for brain development |
| `brain_nutrients.vitamin_b12_mcg` | Vitamin B12 | Number | mcg | Essential for nerve function |
| `brain_nutrients.vitamin_d_mcg` | Vitamin D | Number | mcg | Neuroprotective properties |
| `brain_nutrients.magnesium_mg` | Magnesium | Number | mg | Nervous system regulation |
| `brain_nutrients.zinc_mg` | Zinc | Number | mg | Neurotransmitter function |
| `brain_nutrients.iron_mg` | Iron | Number | mg | Oxygen transport to brain |
| `brain_nutrients.selenium_mcg` | Selenium | Number | mcg | Antioxidant protection |
| `brain_nutrients.choline_mg` | Choline | Number | mg | Precursor to acetylcholine |

### Omega-3 Fatty Acids

| Field | Description | Type | Unit | Notes |
|-------|-------------|------|------|-------|
| `brain_nutrients.omega3.total_g` | Total omega-3 | Number | g | Sum of ALA, EPA, DHA, etc. |
| `brain_nutrients.omega3.epa_mg` | Eicosapentaenoic acid | Number | mg | Marine-derived omega-3 |
| `brain_nutrients.omega3.dha_mg` | Docosahexaenoic acid | Number | mg | Primary omega-3 in brain |
| `brain_nutrients.omega3.ala_mg` | Alpha-linolenic acid | Number | mg | Plant-derived omega-3 |
| `brain_nutrients.omega3.confidence` | Confidence rating | Number | 1-10 | Quality of omega-3 data |

## Bioactive Compounds

All values per 100g of food unless otherwise specified.

| Field | Description | Type | Unit | Notes |
|-------|-------------|------|------|-------|
| `bioactive_compounds.polyphenols_mg` | Total polyphenols | Number | mg | All phenolic compounds |
| `bioactive_compounds.flavonoids_mg` | Total flavonoids | Number | mg | Subclass of polyphenols |
| `bioactive_compounds.anthocyanins_mg` | Anthocyanins | Number | mg | Color pigments in berries |
| `bioactive_compounds.carotenoids_mg` | Carotenoids | Number | mg | Including lutein, zeaxanthin |
| `bioactive_compounds.probiotics_cfu` | Probiotic content | Number | CFU | Colony-forming units |
| `bioactive_compounds.prebiotic_fiber_g` | Prebiotic fiber | Number | g | Feeds beneficial bacteria |

## Mental Health Impacts

Each impact is represented as an object in an array.

| Field | Description | Type | Notes |
|-------|-------------|------|-------|
| `impact_type` | Category of impact | String | One of: mood_elevation, mood_depression, anxiety_reduction, anxiety_increase, cognitive_enhancement, cognitive_decline, energy_increase, energy_decrease, stress_reduction, sleep_improvement, gut_health_improvement |
| `direction` | Direction of effect | String | One of: positive, negative, neutral, mixed |
| `mechanism` | How it works | String | Biological pathway explanation |
| `strength` | Effect strength | Number | Scale 1-10, with 10 being strongest |
| `confidence` | Research confidence | Number | Scale 1-10, with 10 being highest confidence |
| `time_to_effect` | Timing of effects | String | acute, cumulative, both_acute_and_cumulative |
| `research_context` | Study context | String | Brief description of research background |

### Research Support

Citations for each mental health impact, nested as an array.

| Field | Description | Type | Notes |
|-------|-------------|------|-------|
| `citation` | Full citation text | String | APA, MLA, or similar format |
| `doi` | Digital Object Identifier | String | When available |
| `url` | Link to resource | String | When available |
| `study_type` | Type of study | String | e.g., RCT, cohort, meta-analysis |
| `year` | Publication year | Number | Year of publication |

## Data Quality Metrics

| Field | Description | Type | Notes |
|-------|-------------|------|-------|
| `data_quality.completeness` | Data completeness | Number | 0-1 scale, fraction of fields with data |
| `data_quality.overall_confidence` | Overall confidence | Number | 1-10 scale |
| `data_quality.brain_nutrients_source` | Source of brain nutrient data | String | usda_provided, literature_derived, ai_generated, expert_estimated |
| `data_quality.impacts_source` | Source of impact data | String | direct_studies, literature_review, mechanism_inference, ai_generated |

## Metadata

| Field | Description | Type | Notes |
|-------|-------------|------|-------|
| `metadata.version` | Dataset version | String | Semantic versioning |
| `metadata.created` | Creation timestamp | String | ISO format |
| `metadata.last_updated` | Update timestamp | String | ISO format |
| `metadata.source_urls` | Data source URLs | Array | Links to original sources |
| `metadata.image_url` | Image of food | String | URL to representative image |
| `metadata.tags` | Descriptive tags | Array | For categorization and search |

## Units of Measurement

| Unit | Description | Used For |
|------|-------------|----------|
| g | Gram | Macronutrients, total weights |
| mg | Milligram (1/1000 g) | Minerals, some vitamins |
| mcg | Microgram (1/1,000,000 g) | Trace nutrients, some vitamins |
| kcal | Kilocalorie | Energy content |
| IU | International Unit | Some vitamins (being phased out) |
| CFU | Colony Forming Unit | Probiotic bacteria count |

## Confidence Ratings

The confidence scale (1-10) has the following general interpretation:

| Rating | Interpretation |
|--------|----------------|
| 9-10 | Multiple direct measurements with standardized methods |
| 7-8 | Direct measurement or strong literature support |
| 5-6 | Derived from related nutrients or good AI prediction |
| 3-4 | Educated estimate based on similar foods |
| 1-2 | Best guess with limited supporting evidence |

## Notes on Missing Data

- `null` values indicate missing data
- Zero values (0) represent actual measured zero content
- Confidence ratings help distinguish between high-confidence zeros and low-confidence estimates

## Version History

This data dictionary reflects schema version 0.1.0 (initial POC). Fields may be added or modified in future versions.
