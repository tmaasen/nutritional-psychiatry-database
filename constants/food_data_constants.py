# OpenFoodFacts field mappings to our schema
OFF_STANDARD_NUTRIENTS_MAPPING = {
    "energy-kcal_100g": "calories",
    "proteins_100g": "protein_g",
    "carbohydrates_100g": "carbohydrates_g",
    "fat_100g": "fat_g",
    "fiber_100g": "fiber_g",
    "sugars_100g": "sugars_g",
    "calcium_100g": "calcium_mg",
    "iron_100g": "iron_mg",
    "magnesium_100g": "magnesium_mg",
    "phosphorus_100g": "phosphorus_mg",
    "potassium_100g": "potassium_mg",
    "sodium_100g": "sodium_mg",
    "zinc_100g": "zinc_mg",
    "copper_100g": "copper_mg",
    "manganese_100g": "manganese_mg",
    "selenium_100g": "selenium_mcg",
    "vitamin-c_100g": "vitamin_c_mg",
    "vitamin-a_100g": "vitamin_a_iu"
}

OFF_BRAIN_NUTRIENTS_MAPPING = {
    "tryptophan_100g": "tryptophan_mg",
    "tyrosine_100g": "tyrosine_mg",
    "vitamin-b6_100g": "vitamin_b6_mg",
    "folates_100g": "folate_mcg",
    "vitamin-b12_100g": "vitamin_b12_mcg",
    "vitamin-d_100g": "vitamin_d_mcg",
    "magnesium_100g": "magnesium_mg",
    "zinc_100g": "zinc_mg",
    "iron_100g": "iron_mg",
    "selenium_100g": "selenium_mcg",
    "choline_100g": "choline_mg"
}

OFF_OMEGA3_MAPPING = {
    "omega-3-fat_100g": "total_g",
    "dha_100g": "dha_mg",
    "epa_100g": "epa_mg",
    "ala_100g": "ala_mg"
}

# USDA Constants

# USDA nutrient ID mappings to our schema fields
USDA_STANDARD_NUTRIENTS_MAPPING = {
    "Energy": "calories",
    "Protein": "protein_g",
    "Carbohydrate, by difference": "carbohydrates_g",
    "Total lipid (fat)": "fat_g",
    "Fiber, total dietary": "fiber_g",
    "Sugars, total including NLEA": "sugars_g",
    "Calcium, Ca": "calcium_mg",
    "Iron, Fe": "iron_mg",
    "Magnesium, Mg": "magnesium_mg",
    "Phosphorus, P": "phosphorus_mg",
    "Potassium, K": "potassium_mg",
    "Sodium, Na": "sodium_mg",
    "Zinc, Zn": "zinc_mg",
    "Copper, Cu": "copper_mg",
    "Manganese, Mn": "manganese_mg",
    "Selenium, Se": "selenium_mcg",
    "Vitamin C, total ascorbic acid": "vitamin_c_mg",
    "Vitamin A, IU": "vitamin_a_iu"
}

# USDA brain-specific nutrient mappings
USDA_BRAIN_NUTRIENTS_MAPPING = {
    "Tryptophan": "tryptophan_mg",
    "Tyrosine": "tyrosine_mg",
    "Vitamin B-6": "vitamin_b6_mg",
    "Folate, total": "folate_mcg",
    "Vitamin B-12": "vitamin_b12_mcg",
    "Vitamin D (D2 + D3)": "vitamin_d_mcg",
    "Magnesium, Mg": "magnesium_mg",
    "Zinc, Zn": "zinc_mg",
    "Iron, Fe": "iron_mg",
    "Selenium, Se": "selenium_mcg",
    "Choline, total": "choline_mg"
}

# USDA unit conversion requirements
USDA_UNIT_CONVERSIONS = {
    "ug_to_mg": ["Folate, total", "Vitamin B-12", "Vitamin D (D2 + D3)"],
    "g_to_mcg": ["Selenium, Se"]
}

# Add this to the required fields constants for completeness calculation
COMPLETENESS_REQUIRED_FIELDS = {
    "standard_nutrients": [
        "calories", "protein_g", "carbohydrates_g", 
        "fat_g", "fiber_g", "sugars_g"
    ],
    "brain_nutrients": [
        "vitamin_b6_mg", "folate_mcg", "vitamin_b12_mcg",
        "vitamin_d_mcg", "magnesium_mg", "zinc_mg",
        "iron_mg", "selenium_mcg"
    ]
}

FOOD_CATEGORY_MAPPING = {
    "fruits": "Fruits",
    "vegetables": "Vegetables",
    "meat": "Protein Foods",
    "fish": "Protein Foods",
    "seafood": "Protein Foods",
    "legumes": "Protein Foods",
    "dairy": "Dairy",
    "cereals": "Grains",
    "grains": "Grains",
    "breads": "Grains",
    "nuts": "Nuts and Seeds",
    "seeds": "Nuts and Seeds",
    "beverages": "Beverages",
    "sweets": "Sweets",
    "fast-food": "Processed Foods"
}

# Nutrient that need unit conversion from g to mg
NUTRIENTS_G_TO_MG = [
    "calcium_100g", 
    "iron_100g", 
    "magnesium_100g", 
    "phosphorus_100g", 
    "potassium_100g", 
    "sodium_100g",
    "zinc_100g", 
    "copper_100g", 
    "manganese_100g",
    "tryptophan_100g", 
    "tyrosine_100g", 
    "choline_100g"
]

# Nutrients that need unit conversion from g to mcg
NUTRIENTS_G_TO_MCG = [
    "selenium_100g",
    "folates_100g", 
    "vitamin-b12_100g", 
    "vitamin-d_100g"
]

# Anti-inflammatory nutrients with their weights
ANTI_INFLAMMATORY_NUTRIENTS = {
    "fiber_100g": 0.5,
    "vitamin-c_100g": 0.3,
    "magnesium_100g": 0.3,
    "omega-3-fat_100g": 0.7,
    "folates_100g": 0.3
}

# Pro-inflammatory nutrients with their weights
PRO_INFLAMMATORY_NUTRIENTS = {
    "saturated-fat_100g": 0.5,
    "trans-fat_100g": 0.8,
    "salt_100g": 0.3,
    "sugars_100g": 0.4
}

# Default confidence ratings
DEFAULT_CONFIDENCE_RATINGS = {
    "openfoodfacts": 7,
    "omega3": 7,
    "inflammatory_index": 5
}

# API configuration constants
OFF_DEFAULT_FIELDS = (
    "code,product_name,brands,categories_tags,image_url,"
    "nutriments,nutrient_levels,nutrition_score_fr,"
    "ingredients_analysis_tags,ingredients_text_with_allergens,"
    "serving_size,nutrient_levels"
)

# Default brain nutrients to predict if not in USDA data
BRAIN_NUTRIENTS_TO_PREDICT = [
    "tryptophan_mg",
    "tyrosine_mg",
    "vitamin_b6_mg",
    "folate_mcg",
    "vitamin_b12_mcg",
    "vitamin_d_mcg",
    "magnesium_mg",
    "zinc_mg",
    "iron_mg",
    "selenium_mcg",
    "choline_mg",
    "omega3.total_g",
    "omega3.epa_mg",
    "omega3.dha_mg",
    "omega3.ala_mg"
]

# Default bioactive compounds to predict
BIOACTIVE_COMPOUNDS_TO_PREDICT = [
    "polyphenols_mg",
    "flavonoids_mg",
    "anthocyanins_mg",
    "carotenoids_mg",
    "probiotics_cfu",
    "prebiotic_fiber_g"
]
