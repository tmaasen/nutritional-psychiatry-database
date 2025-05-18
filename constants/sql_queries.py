# constants/sql_queries.py

##############################################
# Food Table Operations
##############################################

# Insert or update a food record
FOOD_UPSERT = """
INSERT INTO foods (food_id, name, description, category, processed, validated)
VALUES (%s, %s, %s, %s, %s, %s)
ON CONFLICT (food_id) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    category = EXCLUDED.category,
    processed = EXCLUDED.processed,
    validated = EXCLUDED.validated
RETURNING food_id
"""

# Get a food record by ID
FOOD_GET_BY_ID = """
SELECT id, food_id, name, description, category, created_at, updated_at
FROM foods
WHERE food_id = %s
"""

# Get foods that need processing
FOOD_GET_UNPROCESSED = """
SELECT id, food_id, name, category, description
FROM foods 
WHERE processed = FALSE OR %s
LIMIT %s OFFSET %s
"""

# Get foods that need validation
FOOD_GET_UNVALIDATED = """
SELECT id, food_id, name, category, description
FROM foods 
WHERE validated = FALSE OR %s
LIMIT %s OFFSET %s
"""

# Update food processing status
FOOD_UPDATE_PROCESSED = """
UPDATE foods
SET processed = %s, updated_at = NOW()
WHERE food_id = %s
"""

# Update food validation status
FOOD_UPDATE_VALIDATED = """
UPDATE foods
SET validated = %s, validation_errors = %s, updated_at = NOW()
WHERE food_id = %s
"""

# Get all distinct food names
FOOD_GET_DISTINCT_NAMES = """
SELECT DISTINCT name FROM foods
WHERE source IN ('usda', 'openfoodfacts', 'literature', 'ai_generated')
"""

# Get similar foods by name
FOOD_GET_BY_NAME_AND_SOURCE = """
SELECT food_id, name, category
FROM foods
WHERE name ILIKE %s AND source = %s
"""

# Get all foods without mental health impacts (for enrichment)
FOOD_GET_WITHOUT_IMPACTS = """
SELECT f.food_id, f.name, f.category, f.description
FROM foods f
LEFT JOIN mental_health_impacts mhi ON f.food_id = mhi.food_id
WHERE mhi.id IS NULL
LIMIT %s
"""

##############################################
# Standard Nutrients Operations
##############################################

# Insert or update standard nutrients
STANDARD_NUTRIENTS_UPSERT = """
INSERT INTO standard_nutrients (
    food_id, calories, protein_g, carbohydrates_g, fat_g, fiber_g, 
    sugars_g, sugars_added_g, calcium_mg, iron_mg, magnesium_mg, 
    phosphorus_mg, potassium_mg, sodium_mg, zinc_mg, copper_mg, 
    manganese_mg, selenium_mcg, vitamin_c_mg, vitamin_a_iu
) VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
)
ON CONFLICT (food_id) DO UPDATE SET
    calories = EXCLUDED.calories,
    protein_g = EXCLUDED.protein_g,
    carbohydrates_g = EXCLUDED.carbohydrates_g,
    fat_g = EXCLUDED.fat_g,
    fiber_g = EXCLUDED.fiber_g,
    sugars_g = EXCLUDED.sugars_g,
    sugars_added_g = EXCLUDED.sugars_added_g,
    calcium_mg = EXCLUDED.calcium_mg,
    iron_mg = EXCLUDED.iron_mg,
    magnesium_mg = EXCLUDED.magnesium_mg,
    phosphorus_mg = EXCLUDED.phosphorus_mg,
    potassium_mg = EXCLUDED.potassium_mg,
    sodium_mg = EXCLUDED.sodium_mg,
    zinc_mg = EXCLUDED.zinc_mg,
    copper_mg = EXCLUDED.copper_mg,
    manganese_mg = EXCLUDED.manganese_mg,
    selenium_mcg = EXCLUDED.selenium_mcg,
    vitamin_c_mg = EXCLUDED.vitamin_c_mg,
    vitamin_a_iu = EXCLUDED.vitamin_a_iu
"""

# Get standard nutrients by food ID
STANDARD_NUTRIENTS_GET_BY_FOOD_ID = """
SELECT * FROM standard_nutrients
WHERE food_id = %s
"""

##############################################
# Brain Nutrients Operations
##############################################

# Insert or update brain nutrients
BRAIN_NUTRIENTS_UPSERT = """
INSERT INTO brain_nutrients (
    food_id, tryptophan_mg, tyrosine_mg, vitamin_b6_mg, folate_mcg,
    vitamin_b12_mcg, vitamin_d_mcg, magnesium_mg, zinc_mg, iron_mg,
    selenium_mcg, choline_mg
) VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
)
ON CONFLICT (food_id) DO UPDATE SET
    tryptophan_mg = EXCLUDED.tryptophan_mg,
    tyrosine_mg = EXCLUDED.tyrosine_mg,
    vitamin_b6_mg = EXCLUDED.vitamin_b6_mg,
    folate_mcg = EXCLUDED.folate_mcg,
    vitamin_b12_mcg = EXCLUDED.vitamin_b12_mcg,
    vitamin_d_mcg = EXCLUDED.vitamin_d_mcg,
    magnesium_mg = EXCLUDED.magnesium_mg,
    zinc_mg = EXCLUDED.zinc_mg,
    iron_mg = EXCLUDED.iron_mg,
    selenium_mcg = EXCLUDED.selenium_mcg,
    choline_mg = EXCLUDED.choline_mg
"""

# Get brain nutrients by food ID
BRAIN_NUTRIENTS_GET_BY_FOOD_ID = """
SELECT * FROM brain_nutrients
WHERE food_id = %s
"""

##############################################
# Omega-3 Fatty Acids Operations
##############################################

# Insert or update omega-3 fatty acids
OMEGA3_UPSERT = """
INSERT INTO omega3_fatty_acids (
    food_id, total_g, epa_mg, dha_mg, ala_mg, confidence
) VALUES (
    %s, %s, %s, %s, %s, %s
)
ON CONFLICT (food_id) DO UPDATE SET
    total_g = EXCLUDED.total_g,
    epa_mg = EXCLUDED.epa_mg,
    dha_mg = EXCLUDED.dha_mg,
    ala_mg = EXCLUDED.ala_mg,
    confidence = EXCLUDED.confidence
"""

# Get omega-3 by food ID
OMEGA3_GET_BY_FOOD_ID = """
SELECT * FROM omega3_fatty_acids
WHERE food_id = %s
"""

##############################################
# Bioactive Compounds Operations
##############################################

# Insert or update bioactive compounds
BIOACTIVE_COMPOUNDS_UPSERT = """
INSERT INTO bioactive_compounds (
    food_id, polyphenols_mg, flavonoids_mg, anthocyanins_mg,
    carotenoids_mg, probiotics_cfu, prebiotic_fiber_g
) VALUES (
    %s, %s, %s, %s, %s, %s, %s
)
ON CONFLICT (food_id) DO UPDATE SET
    polyphenols_mg = EXCLUDED.polyphenols_mg,
    flavonoids_mg = EXCLUDED.flavonoids_mg,
    anthocyanins_mg = EXCLUDED.anthocyanins_mg,
    carotenoids_mg = EXCLUDED.carotenoids_mg,
    probiotics_cfu = EXCLUDED.probiotics_cfu,
    prebiotic_fiber_g = EXCLUDED.prebiotic_fiber_g
"""

# Get bioactive compounds by food ID
BIOACTIVE_COMPOUNDS_GET_BY_FOOD_ID = """
SELECT * FROM bioactive_compounds
WHERE food_id = %s
"""

##############################################
# Data Quality Operations
##############################################

# Insert or update data quality
DATA_QUALITY_UPSERT = """
INSERT INTO data_quality (
    food_id, completeness, overall_confidence, 
    brain_nutrients_source, impacts_source, source_priority
) VALUES (
    %s, %s, %s, %s, %s, %s
)
ON CONFLICT (food_id) DO UPDATE SET
    completeness = EXCLUDED.completeness,
    overall_confidence = EXCLUDED.overall_confidence,
    brain_nutrients_source = EXCLUDED.brain_nutrients_source,
    impacts_source = EXCLUDED.impacts_source,
    source_priority = EXCLUDED.source_priority
"""

# Get data quality by food ID
DATA_QUALITY_GET_BY_FOOD_ID = """
SELECT * FROM data_quality
WHERE food_id = %s
"""

##############################################
# Metadata Operations
##############################################

# Insert or update metadata
METADATA_UPSERT = """
INSERT INTO metadata (
    food_id, version, created, last_updated, 
    image_url, source_urls, source_ids, tags
) VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s
)
ON CONFLICT (food_id) DO UPDATE SET
    version = EXCLUDED.version,
    last_updated = EXCLUDED.last_updated,
    image_url = EXCLUDED.image_url,
    source_urls = EXCLUDED.source_urls,
    source_ids = EXCLUDED.source_ids,
    tags = EXCLUDED.tags
"""

# Get metadata by food ID
METADATA_GET_BY_FOOD_ID = """
SELECT * FROM metadata
WHERE food_id = %s
"""

##############################################
# Serving Info Operations
##############################################

# Insert or update serving info
SERVING_INFO_UPSERT = """
INSERT INTO serving_info (
    food_id, serving_size, serving_unit, household_serving
) VALUES (
    %s, %s, %s, %s
)
ON CONFLICT (food_id) DO UPDATE SET
    serving_size = EXCLUDED.serving_size,
    serving_unit = EXCLUDED.serving_unit,
    household_serving = EXCLUDED.household_serving
"""

# Get serving info by food ID
SERVING_INFO_GET_BY_FOOD_ID = """
SELECT * FROM serving_info
WHERE food_id = %s
"""

##############################################
# Mental Health Impact Operations
##############################################

# Delete existing mental health impacts
MENTAL_HEALTH_IMPACTS_DELETE = """
DELETE FROM mental_health_impacts
WHERE food_id = %s
"""

# Insert mental health impact
MENTAL_HEALTH_IMPACT_INSERT = """
INSERT INTO mental_health_impacts (
    food_id, impact_type, direction, mechanism, 
    strength, confidence, time_to_effect, research_context, notes
) VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s, %s
) RETURNING id
"""

# Get mental health impacts by food ID
MENTAL_HEALTH_IMPACTS_GET_BY_FOOD_ID = """
SELECT * FROM mental_health_impacts
WHERE food_id = %s
"""

##############################################
# Research Support Operations
##############################################

# Insert research support
RESEARCH_SUPPORT_INSERT = """
INSERT INTO research_support (
    impact_id, citation, doi, url, study_type, year
) VALUES (
    %s, %s, %s, %s, %s, %s
)
"""

# Get research support by impact ID
RESEARCH_SUPPORT_GET_BY_IMPACT_ID = """
SELECT * FROM research_support
WHERE impact_id = %s
"""

##############################################
# Nutrient Interaction Operations
##############################################

# Delete existing nutrient interactions
NUTRIENT_INTERACTIONS_DELETE = """
DELETE FROM nutrient_interactions
WHERE food_id = %s
"""

# Insert nutrient interaction
NUTRIENT_INTERACTION_INSERT = """
INSERT INTO nutrient_interactions (
    food_id, interaction_id, interaction_type, pathway,
    mechanism, mental_health_relevance, confidence,
    nutrients_involved, research_support, foods_demonstrating
) VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
)
"""

# Get nutrient interactions by food ID
NUTRIENT_INTERACTIONS_GET_BY_FOOD_ID = """
SELECT * FROM nutrient_interactions
WHERE food_id = %s
"""

##############################################
# Contextual Factors Operations
##############################################

# Insert or update contextual factors
CONTEXTUAL_FACTORS_UPSERT = """
INSERT INTO contextual_factors (
    food_id, circadian_effects, food_combinations, preparation_effects
) VALUES (
    %s, %s, %s, %s
)
ON CONFLICT (food_id) DO UPDATE SET
    circadian_effects = EXCLUDED.circadian_effects,
    food_combinations = EXCLUDED.food_combinations,
    preparation_effects = EXCLUDED.preparation_effects
"""

# Get contextual factors by food ID
CONTEXTUAL_FACTORS_GET_BY_FOOD_ID = """
SELECT * FROM contextual_factors
WHERE food_id = %s
"""

##############################################
# Inflammatory Index Operations
##############################################

# Insert or update inflammatory index
INFLAMMATORY_INDEX_UPSERT = """
INSERT INTO inflammatory_index (
    food_id, value, confidence, calculation_method, citations
) VALUES (
    %s, %s, %s, %s, %s
)
ON CONFLICT (food_id) DO UPDATE SET
    value = EXCLUDED.value,
    confidence = EXCLUDED.confidence,
    calculation_method = EXCLUDED.calculation_method,
    citations = EXCLUDED.citations
"""

# Get inflammatory index by food ID
INFLAMMATORY_INDEX_GET_BY_FOOD_ID = """
SELECT * FROM inflammatory_index
WHERE food_id = %s
"""

##############################################
# Neural Targets Operations
##############################################

# Delete existing neural targets
NEURAL_TARGETS_DELETE = """
DELETE FROM neural_targets
WHERE food_id = %s
"""

# Insert neural target
NEURAL_TARGET_INSERT = """
INSERT INTO neural_targets (
    food_id, pathway, effect, confidence, mechanisms, mental_health_relevance
) VALUES (
    %s, %s, %s, %s, %s, %s
)
"""

# Get neural targets by food ID
NEURAL_TARGETS_GET_BY_FOOD_ID = """
SELECT * FROM neural_targets
WHERE food_id = %s
"""

##############################################
# Population Variations Operations
##############################################

# Delete existing population variations
POPULATION_VARIATIONS_DELETE = """
DELETE FROM population_variations
WHERE food_id = %s
"""

# Insert population variation
POPULATION_VARIATION_INSERT = """
INSERT INTO population_variations (
    food_id, population, description, variations
) VALUES (
    %s, %s, %s, %s
)
"""

# Get population variations by food ID
POPULATION_VARIATIONS_GET_BY_FOOD_ID = """
SELECT * FROM population_variations
WHERE food_id = %s
"""

##############################################
# Dietary Patterns Operations
##############################################

# Delete existing dietary patterns
DIETARY_PATTERNS_DELETE = """
DELETE FROM dietary_patterns
WHERE food_id = %s
"""

# Insert dietary pattern
DIETARY_PATTERN_INSERT = """
INSERT INTO dietary_patterns (
    food_id, pattern_name, pattern_contribution, mental_health_relevance
) VALUES (
    %s, %s, %s, %s
)
"""

# Get dietary patterns by food ID
DIETARY_PATTERNS_GET_BY_FOOD_ID = """
SELECT * FROM dietary_patterns
WHERE food_id = %s
"""

##############################################
# Complete Food Profile Query
##############################################

# Get complete food profile - main query that consolidates all tables
GET_COMPLETE_FOOD_PROFILE = """
SELECT 
    f.food_id,
    f.name,
    f.description,
    f.category,
    f.created_at,
    f.updated_at,
    f.processed,
    f.validated,
    f.validation_errors
FROM foods f
WHERE f.food_id = %s
"""

# Additional queries to get all related data for a food
# These would be executed separately to build a complete food profile

##############################################
# Evaluation Queries
##############################################

# Insert food evaluation
FOOD_EVALUATION_INSERT = """
INSERT INTO food_evaluations 
    (food_id, test_run_id, timestamp, evaluation_type, evaluation_data)
VALUES (%s, %s, %s, %s, %s)
ON CONFLICT (food_id, test_run_id, evaluation_type) 
DO UPDATE SET 
    timestamp = EXCLUDED.timestamp,
    evaluation_data = EXCLUDED.evaluation_data
RETURNING id
"""

# Get food evaluations
FOOD_EVALUATIONS_GET_BY_FOOD_ID = """
SELECT * FROM food_evaluations
WHERE food_id = %s
"""

# Insert evaluation metrics
EVALUATION_METRICS_INSERT = """
INSERT INTO evaluation_metrics 
    (test_run_id, timestamp, metrics_type, metrics_data)
VALUES (%s, %s, %s, %s)
RETURNING id
"""

# Get latest evaluation metrics
EVALUATION_METRICS_GET_LATEST = """
SELECT metrics_data 
FROM evaluation_metrics 
WHERE metrics_type = %s 
ORDER BY timestamp DESC 
LIMIT 1
"""