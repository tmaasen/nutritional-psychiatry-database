// src/models/food-data.ts

/**
 * Nutritional Psychiatry Food Data Model
 * Core data model for the Nutritional Psychiatry Dataset
 */

// Base interfaces for reusable types
export interface MetadataObject {
  version: string;
  created: string;
  lastUpdated: string;
  sourceUrls: string[];
  sourceIds?: Record<string, string>;
  imageUrl?: string;
  tags: string[];
}

export interface DataQuality {
  completeness: number;
  overallConfidence: number;
  brainNutrientsSource?:
    | "usda_provided"
    | "openfoodfacts"
    | "literature_derived"
    | "ai_generated"
    | "expert_estimated";
  impactsSource?:
    | "direct_studies"
    | "literature_review"
    | "mechanism_inference"
    | "ai_generated";
  sourcePriority?: {
    standardNutrients?:
      | "usda"
      | "openfoodfacts"
      | "literature"
      | "ai_generated";
    brainNutrients?: "usda" | "openfoodfacts" | "literature" | "ai_generated";
    bioactiveCompounds?:
      | "usda"
      | "openfoodfacts"
      | "literature"
      | "ai_generated";
  };
}

export interface ServingInfo {
  servingSize: number;
  servingUnit: string;
  householdServing?: string;
}

export interface StandardNutrients {
  calories?: number;
  protein_g?: number;
  carbohydrates_g?: number;
  fat_g?: number;
  fiber_g?: number;
  sugars_g?: number;
  sugars_added_g?: number;
  calcium_mg?: number;
  iron_mg?: number;
  magnesium_mg?: number;
  phosphorus_mg?: number;
  potassium_mg?: number;
  sodium_mg?: number;
  zinc_mg?: number;
  copper_mg?: number;
  manganese_mg?: number;
  selenium_mcg?: number;
  vitamin_c_mg?: number;
  vitamin_a_iu?: number;
}

export interface Omega3 {
  total_g?: number;
  epa_mg?: number;
  dha_mg?: number;
  ala_mg?: number;
  confidence?: number;
}

export interface BrainNutrients {
  tryptophan_mg?: number;
  tyrosine_mg?: number;
  vitamin_b6_mg?: number;
  folate_mcg?: number;
  vitamin_b12_mcg?: number;
  vitamin_d_mcg?: number;
  magnesium_mg?: number;
  zinc_mg?: number;
  iron_mg?: number;
  selenium_mcg?: number;
  choline_mg?: number;
  omega3?: Omega3;
}

export interface BioactiveCompounds {
  polyphenols_mg?: number;
  flavonoids_mg?: number;
  anthocyanins_mg?: number;
  carotenoids_mg?: number;
  probiotics_cfu?: number;
  prebiotic_fiber_g?: number;
}

export interface ResearchSupport {
  citation: string;
  doi?: string;
  url?: string;
  study_type?: string;
  year?: number;
}

export interface MentalHealthImpact {
  impact_type:
    | "mood_elevation"
    | "mood_depression"
    | "anxiety_reduction"
    | "anxiety_increase"
    | "cognitive_enhancement"
    | "cognitive_decline"
    | "energy_increase"
    | "energy_decrease"
    | "stress_reduction"
    | "sleep_improvement"
    | "gut_health_improvement";
  direction: "positive" | "negative" | "neutral" | "mixed";
  mechanism: string;
  strength: number;
  confidence: number;
  time_to_effect?: "acute" | "cumulative" | "both_acute_and_cumulative";
  research_context?: string;
  research_support?: ResearchSupport[];
  notes?: string;
}

export interface NutrientInteraction {
  interaction_id: string;
  nutrients_involved: string[];
  interaction_type:
    | "synergistic"
    | "antagonistic"
    | "required_cofactor"
    | "protective"
    | "inhibitory";
  pathway?: string;
  mechanism: string;
  mental_health_relevance?: string;
  confidence: number;
  research_support?: ResearchSupport[];
  foods_demonstrating?: string[];
}

export interface CircadianFactor {
  factor: string;
  effects: string[];
  relevant_to: string[];
  confidence: number;
  citations?: string[];
}

export interface CircadianEffects {
  description?: string;
  factors: CircadianFactor[];
}

export interface FoodCombination {
  combination: string;
  effects: string[];
  relevant_to: string[];
  confidence: number;
}

export interface PreparationEffect {
  method: string;
  effects: string[];
  relevant_to: string[];
  confidence: number;
}

export interface ContextualFactors {
  circadian_effects?: CircadianEffects;
  food_combinations?: FoodCombination[];
  preparation_effects?: PreparationEffect[];
}

export interface PopulationVariation {
  population: string;
  description: string;
  variations: {
    nutrient: string;
    effect: string;
    mechanism?: string;
    impact_modifier?: number;
    recommendations?: string[];
    confidence: number;
    citations?: string[];
  }[];
}

export interface DietaryPattern {
  pattern_name:
    | "mediterranean"
    | "western"
    | "dash"
    | "mind"
    | "vegetarian"
    | "vegan"
    | "ketogenic"
    | "low_fodmap";
  pattern_contribution:
    | "key_component"
    | "supportive"
    | "occasional"
    | "limited"
    | "avoided";
  mental_health_relevance?: string;
}

export interface InflammatoryIndex {
  value: number;
  confidence: number;
  calculation_method:
    | "dietary_inflammatory_index"
    | "empirical_dietary_index"
    | "expert_estimate";
  citations: string[];
}

export interface NeuralTarget {
  pathway: string;
  effect: "upregulation" | "downregulation" | "modulation" | "protection";
  confidence: number;
  mechanisms?: string[];
  mental_health_relevance?: string;
}

/**
 * Main FoodData interface representing the complete schema
 */
export interface FoodData {
  food_id: string;
  name: string;
  description?: string;
  category: string;
  serving_info?: ServingInfo;
  standard_nutrients: StandardNutrients;
  brain_nutrients?: BrainNutrients;
  bioactive_compounds?: BioactiveCompounds;
  mental_health_impacts?: MentalHealthImpact[];
  nutrient_interactions?: NutrientInteraction[];
  contextual_factors?: ContextualFactors;
  population_variations?: PopulationVariation[];
  dietary_patterns?: DietaryPattern[];
  inflammatory_index?: InflammatoryIndex;
  neural_targets?: NeuralTarget[];
  data_quality: DataQuality;
  metadata: MetadataObject;
}

/**
 * Type guards for runtime type checking
 */
export function isFoodData(obj: any): obj is FoodData {
  return (
    obj &&
    typeof obj.food_id === "string" &&
    typeof obj.name === "string" &&
    typeof obj.category === "string" &&
    typeof obj.standard_nutrients === "object"
  );
}
