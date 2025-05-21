#!/usr/bin/env python3
"""
AI-Assisted Data Enrichment Script
Enriches food data with brain-specific nutrients and mental health impacts using AI.
"""

import time
import argparse
from typing import Dict, List, Optional

# Import schema models
from schema.food_data import BioactiveCompounds, FoodData, BrainNutrients, Omega3, DataQuality, Metadata
from constants.food_data_constants import BRAIN_NUTRIENTS_TO_PREDICT

# Import utilities
from utils.db_utils import PostgresClient
from utils.nutrient_utils import NutrientUtils
from scripts.ai.openai_api import OpenAIAPI
from utils.logging_utils import setup_logging
from config import get_config
from datetime import datetime

logger = setup_logging(__name__)

class AIEnrichmentEngine:
    """Uses AI to enrich food data with brain-specific nutrients and mental health impacts using AI."""
    
    def __init__(self, model: str = None, db_client: Optional[PostgresClient] = None):
        config = get_config()
        
        # Use provided DB client or create a new one
        self.db_client = db_client or PostgresClient()
        
        self.api_key = config.get_api_key("OPENAI")
        self.model = model or config.get_value("ai_settings.model", "gpt-4o-mini")
        self.openai_client = OpenAIAPI(api_key=self.api_key, db_client=self.db_client)
    
        logger.info(f"Initialized AI Enrichment Engine using {self.model} model")
    
    def _get_attrs_dict(self, obj, exclude_nested=True):
        """Helper to convert object attributes to dictionary."""
        if not obj:
            return {}
        return {k: v for k, v in vars(obj).items() 
                if not k.startswith('_') and v is not None and 
                (not exclude_nested or not isinstance(v, (dict, list, Omega3)))}
    
    def enrich_brain_nutrients(self, food_data: FoodData) -> FoodData:
        """Predict missing brain nutrients using AI."""
        food = food_data
        enriched_data = FoodData.from_dict(food_data.to_dict())
        
        # Get missing nutrients
        existing_bn = self._get_attrs_dict(food.brain_nutrients)
        
        # Process omega3 specially
        omega3_dict = {}
        if food.brain_nutrients and food.brain_nutrients.omega3:
            omega3_dict = self._get_attrs_dict(food.brain_nutrients.omega3, exclude_nested=False)
            existing_bn['omega3'] = omega3_dict
            
        # Identify missing nutrients
        missing_nutrients = []
        for attr in BRAIN_NUTRIENTS_TO_PREDICT:
            if 'omega3' in attr:
                comp = attr.split('.')[-1]
                if 'omega3' not in existing_bn or comp not in existing_bn['omega3']:
                    missing_nutrients.append(attr)
            elif attr not in existing_bn:
                missing_nutrients.append(attr)
        
        if not missing_nutrients:
            logger.info(f"No missing brain nutrients for {food.name}")
            return enriched_data
        
        logger.info(f"Predicting missing brain nutrients for {food.name}: {missing_nutrients}")
        
        try:
            # Get predictions from AI
            predicted_nutrients = self.openai_client.predict_nutrients(
                food_name=food.name,
                food_category=food.category,
                standard_nutrients=self._get_attrs_dict(food.standard_nutrients),
                existing_brain_nutrients=existing_bn,
                target_nutrients=missing_nutrients
            )
            
            parsed_predictions = NutrientUtils.parse_nutrient_predictions(predicted_nutrients)
            
            # Initialize if needed
            if not enriched_data.brain_nutrients:
                enriched_data.brain_nutrients = BrainNutrients()
                
            # Update with predictions
            for nutrient_path, value in parsed_predictions.items():
                if "." in nutrient_path:
                    # Handle omega3
                    parts = nutrient_path.split('.')
                    if parts[0] == 'omega3':
                        if not enriched_data.brain_nutrients.omega3:
                            enriched_data.brain_nutrients.omega3 = Omega3()
                        setattr(enriched_data.brain_nutrients.omega3, parts[1], value)
                else:
                    setattr(enriched_data.brain_nutrients, nutrient_path, value)
            
            # Update data quality
            if not enriched_data.data_quality:
                enriched_data.data_quality = DataQuality()
            
            if parsed_predictions:
                enriched_data.data_quality.brain_nutrients_source = 'ai_generated'
                
            logger.info(f"Successfully enriched brain nutrients for {food.name}")
            
        except Exception as e:
            logger.error(f"Error predicting brain nutrients for {food.name}: {e}")
        
        return enriched_data
    
    def enrich_bioactive_compounds(self, food_data: FoodData) -> FoodData:
        """Predict bioactive compounds using AI."""
        food = food_data
        enriched_data = FoodData.from_dict(food_data.to_dict())
        
        # Check if we need to enrich bioactive compounds
        if food.bioactive_compounds and self._has_complete_bioactives(food.bioactive_compounds):
            logger.info(f"Bioactive compounds already complete for {food.name}")
            return enriched_data
        
        logger.info(f"Predicting bioactive compounds for {food.name}")
        
        try:
            # Get predictions from AI
            predicted_compounds = self.openai_client.predict_bioactive_compounds(
                food_name=food.name,
                food_category=food.category,
                standard_nutrients=self._get_attrs_dict(food.standard_nutrients)
            )
            
            parsed_compounds = NutrientUtils.parse_bioactive_predictions(predicted_compounds)
            
            # Initialize if needed
            if not enriched_data.bioactive_compounds:
                enriched_data.bioactive_compounds = BioactiveCompounds()
            
            # Update with predictions
            for compound, value in parsed_compounds.items():
                setattr(enriched_data.bioactive_compounds, compound, value)
            
            logger.info(f"Successfully enriched bioactive compounds for {food.name}")
            
        except Exception as e:
            logger.error(f"Error predicting bioactive compounds for {food.name}: {e}")
        
        return enriched_data
    
    def _has_complete_bioactives(self, bioactive_compounds):
        required = ["polyphenols_mg", "flavonoids_mg", "anthocyanins_mg", 
                   "carotenoids_mg", "probiotics_cfu", "prebiotic_fiber_g"]
        
        return all(hasattr(bioactive_compounds, attr) and 
                  getattr(bioactive_compounds, attr) is not None 
                  for attr in required)
    
    def enrich_mental_health_impacts(self, food_data: FoodData) -> FoodData:
        food = food_data
        enriched_data = FoodData.from_dict(food_data.to_dict())
        
        if food.mental_health_impacts and len(food.mental_health_impacts) > 0:
            logger.info(f"Mental health impacts already exist for {food.name}")
            return enriched_data
        
        logger.info(f"Predicting mental health impacts for {food.name}")
        
        try:
            # Get predictions from AI
            predicted_impacts = self.openai_client.predict_mental_health_impacts(
                food_name=food.name,
                food_category=food.category,
                standard_nutrients=self._get_attrs_dict(food.standard_nutrients),
                brain_nutrients=self._get_attrs_dict(food.brain_nutrients),
                bioactive_compounds=self._get_attrs_dict(food.bioactive_compounds)
            )
            
            parsed_impacts = NutrientUtils.parse_mental_health_impacts(predicted_impacts)
            
            # Update impacts
            enriched_data.mental_health_impacts = parsed_impacts
            
            # Update data quality
            if not enriched_data.data_quality:
                enriched_data.data_quality = DataQuality()
            
            enriched_data.data_quality.impacts_source = 'ai_generated'
            
            logger.info(f"Successfully enriched mental health impacts for {food.name}")
            
        except Exception as e:
            logger.error(f"Error predicting mental health impacts for {food.name}: {e}")
        
        return enriched_data
    
    def fully_enrich_food(self, food_data: FoodData) -> FoodData:
        """Apply all enrichment steps to a food item."""
        food_name = food_data.name
        logger.info(f"Beginning full enrichment for {food_name}")
        
        # Apply enrichment steps in sequence with rate limiting
        step1 = self.enrich_brain_nutrients(food_data)
        time.sleep(1)  # Avoid rate limiting
        
        step2 = self.enrich_bioactive_compounds(step1)
        time.sleep(1)  # Avoid rate limiting
        
        step3 = self.enrich_mental_health_impacts(step2)
        
        # Update metadata
        result = step3
        
        if not result.metadata:
            result.metadata = Metadata(
                version="0.1.0",
                created=datetime.now().isoformat(),
                last_updated=datetime.now().isoformat(),
                source_urls=[],
                tags=["enriched"]
            )
        else:
            result.metadata.last_updated = datetime.now().isoformat()
            if "enriched" not in result.metadata.tags:
                result.metadata.tags.append("enriched")

        # Save the fully enriched food
        self.db_client.import_food_from_json(result)
        
        logger.info(f"Completed full enrichment for {food_name}")
        return result
    
    def enrich_directory(self, limit: Optional[int] = None) -> List[str]:
        """Enrich all food data items that need enrichment."""
        enriched_ids = []
        
        # Retrieve foods without mental health impacts
        foods_to_enrich = self.db_client.get_all_foods_without_mental_health_impacts(limit)
        
        logger.info(f"Found {len(foods_to_enrich)} foods to enrich")
        
        for food in foods_to_enrich:
            try:
                enriched_data = self.fully_enrich_food(food)                
                enriched_ids.append(food.food_id)
                
                logger.info(f"Enriched {food.name} with ID {food.food_id}")
                
                # Sleep between foods to avoid rate limiting
                time.sleep(2)
            except Exception as e:
                logger.error(f"Error processing {food.food_id}: {e}")
        
        return enriched_ids

def main():
    parser = argparse.ArgumentParser(description="AI-Assisted Food Data Enrichment")
    parser.add_argument("--model", help="OpenAI model to use")
    parser.add_argument("--limit", type=int, help="Limit number of foods to process")
    parser.add_argument("--food-id", help="Specific food ID to enrich")
    
    args = parser.parse_args()    
    db_client = PostgresClient()
    
    try:
        # Initialize enricher
        config = get_config()
        model = args.model or config.get_value("ai_settings.model", "gpt-4o-mini")
        
        enricher = AIEnrichmentEngine(model=model, db_client=db_client)
        
        logger.info("Starting food data enrichment process")
        
        if args.food_id:
            # Enrich a specific food
            food = db_client.get_food_by_id_or_name(args.food_id)
            if food:
                enriched_food = enricher.fully_enrich_food(food)
                logger.info(f"Successfully enriched {food.name}")
            else:
                logger.error(f"Food with ID {args.food_id} not found")
        else:
            # Enrich multiple foods
            enriched_foods = enricher.enrich_directory(limit=args.limit)
            logger.info(f"Successfully enriched {len(enriched_foods)} foods")
        
    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)

if __name__ == "__main__":
    main()