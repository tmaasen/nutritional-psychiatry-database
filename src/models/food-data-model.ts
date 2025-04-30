// src/models/food-data-model.ts

import {
  FoodData,
  isFoodData,
  StandardNutrients,
  BrainNutrients,
  ServingInfo,
  DataQuality,
  MetadataObject,
  MentalHealthImpact,
  BioactiveCompounds,
  NutrientInteraction,
  ContextualFactors,
  PopulationVariation,
  DietaryPattern,
  InflammatoryIndex,
  NeuralTarget,
} from "./food-data";

/**
 * FoodDataModel class with methods for working with food data
 */
export class FoodDataModel implements FoodData {
  // Required properties
  food_id: string;
  name: string;
  category: string;
  standard_nutrients: StandardNutrients;
  data_quality: DataQuality;
  metadata: MetadataObject;

  // Optional properties
  description?: string;
  serving_info?: ServingInfo;
  brain_nutrients?: BrainNutrients;
  bioactive_compounds?: BioactiveCompounds;
  mental_health_impacts?: MentalHealthImpact[];
  nutrient_interactions?: NutrientInteraction[];
  contextual_factors?: ContextualFactors;
  population_variations?: PopulationVariation[];
  dietary_patterns?: DietaryPattern[];
  inflammatory_index?: InflammatoryIndex;
  neural_targets?: NeuralTarget[];

  /**
   * Create a new FoodDataModel
   */
  constructor(data: Partial<FoodData>) {
    // Initialize required properties
    this.food_id = data.food_id || "";
    this.name = data.name || "";
    this.category = data.category || "";
    this.standard_nutrients = data.standard_nutrients || {};

    // Initialize data quality with defaults
    this.data_quality = data.data_quality || {
      completeness: 0,
      overallConfidence: 0,
    };

    // Initialize metadata with defaults
    this.metadata = data.metadata || {
      version: "0.1.0",
      created: new Date().toISOString(),
      lastUpdated: new Date().toISOString(),
      sourceUrls: [],
      tags: [],
    };

    // Copy all other properties
    Object.assign(this, data);
  }

  /**
   * Validate the food data model
   * @returns Array of validation errors, empty if valid
   */
  validate(): string[] {
    const errors: string[] = [];

    // Check required fields
    if (!this.food_id) errors.push("Missing food_id");
    if (!this.name) errors.push("Missing name");
    if (!this.category) errors.push("Missing category");
    if (!this.standard_nutrients) errors.push("Missing standard_nutrients");

    // Check data quality
    if (!this.data_quality) {
      errors.push("Missing data_quality");
    } else {
      if (
        this.data_quality.completeness < 0 ||
        this.data_quality.completeness > 1
      ) {
        errors.push("Completeness must be between 0 and 1");
      }
      if (
        this.data_quality.overallConfidence < 1 ||
        this.data_quality.overallConfidence > 10
      ) {
        errors.push("Overall confidence must be between 1 and 10");
      }
    }

    // Validate mental health impacts if present
    if (this.mental_health_impacts && this.mental_health_impacts.length > 0) {
      this.mental_health_impacts.forEach((impact, index) => {
        if (impact.strength < 1 || impact.strength > 10) {
          errors.push(
            `Impact #${index + 1}: Strength must be between 1 and 10`
          );
        }
        if (impact.confidence < 1 || impact.confidence > 10) {
          errors.push(
            `Impact #${index + 1}: Confidence must be between 1 and 10`
          );
        }
      });
    }

    return errors;
  }

  /**
   * Calculate the completeness score
   * @returns Completeness score (0-1)
   */
  calculateCompleteness(): number {
    let fieldsWithValues = 0;
    let totalFields = 0;

    // Standard nutrients (core fields)
    const stdNutrientFields = [
      "calories",
      "protein_g",
      "carbohydrates_g",
      "fat_g",
      "fiber_g",
      "sugars_g",
    ];

    totalFields += stdNutrientFields.length;
    stdNutrientFields.forEach((field) => {
      if (this.standard_nutrients[field] != null) fieldsWithValues++;
    });

    // Brain nutrients (if present)
    if (this.brain_nutrients) {
      const brainNutrientFields = [
        "tryptophan_mg",
        "vitamin_b6_mg",
        "folate_mcg",
        "vitamin_b12_mcg",
        "vitamin_d_mcg",
        "magnesium_mg",
        "zinc_mg",
        "iron_mg",
      ];

      totalFields += brainNutrientFields.length;
      brainNutrientFields.forEach((field) => {
        if (this.brain_nutrients && this.brain_nutrients[field] != null)
          fieldsWithValues++;
      });

      // Check omega-3
      if (this.brain_nutrients.omega3) {
        const omega3Fields = ["total_g", "epa_mg", "dha_mg", "ala_mg"];
        totalFields += omega3Fields.length;
        omega3Fields.forEach((field) => {
          if (
            this.brain_nutrients &&
            this.brain_nutrients.omega3 &&
            this.brain_nutrients.omega3[field] != null
          )
            fieldsWithValues++;
        });
      }
    }

    // Calculate completeness
    return totalFields > 0 ? fieldsWithValues / totalFields : 0;
  }

  /**
   * Check if the food contains a specific brain nutrient
   */
  hasBrainNutrient(nutrient: string): boolean {
    if (!this.brain_nutrients) return false;

    if (nutrient.includes(".")) {
      // Handle nested paths like omega3.epa_mg
      const [section, field] = nutrient.split(".");
      return !!this.brain_nutrients[section]?.[field];
    }

    return !!this.brain_nutrients[nutrient];
  }

  /**
   * Get a specific brain nutrient value
   */
  getBrainNutrient(nutrient: string): number | null {
    if (!this.brain_nutrients) return null;

    if (nutrient.includes(".")) {
      // Handle nested paths like omega3.epa_mg
      const [section, field] = nutrient.split(".");
      return this.brain_nutrients[section]?.[field] || null;
    }

    return this.brain_nutrients[nutrient] || null;
  }

  /**
   * Check if food has mental health impacts
   */
  hasMentalHealthImpacts(): boolean {
    return (
      !!this.mental_health_impacts && this.mental_health_impacts.length > 0
    );
  }

  /**
   * Get mental health impacts by type
   */
  getImpactsByType(type: string): MentalHealthImpact[] {
    if (!this.mental_health_impacts) return [];
    return this.mental_health_impacts.filter(
      (impact) => impact.impact_type === type
    );
  }

  /**
   * Update the 'last_updated' timestamp in metadata
   */
  updateTimestamp(): void {
    this.metadata.lastUpdated = new Date().toISOString();
  }

  /**
   * Convert to plain object (for saving to JSON)
   */
  toJSON(): FoodData {
    return {
      food_id: this.food_id,
      name: this.name,
      description: this.description,
      category: this.category,
      serving_info: this.serving_info,
      standard_nutrients: this.standard_nutrients,
      brain_nutrients: this.brain_nutrients,
      bioactive_compounds: this.bioactive_compounds,
      mental_health_impacts: this.mental_health_impacts,
      nutrient_interactions: this.nutrient_interactions,
      contextual_factors: this.contextual_factors,
      population_variations: this.population_variations,
      dietary_patterns: this.dietary_patterns,
      inflammatory_index: this.inflammatory_index,
      neural_targets: this.neural_targets,
      data_quality: this.data_quality,
      metadata: this.metadata,
    };
  }

  /**
   * Create a FoodDataModel from a JSON object
   */
  static fromJSON(json: any): FoodDataModel {
    if (!isFoodData(json)) {
      throw new Error("Invalid food data format");
    }
    return new FoodDataModel(json);
  }
}
