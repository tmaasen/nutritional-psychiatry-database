#!/usr/bin/env python3
"""
AI-Assisted Data Enrichment Script
Enriches food data with brain-specific nutrients and mental health impacts using AI.
"""

import time
from typing import Dict, List, Optional
import argparse
from datetime import datetime

# Import schema models
from schema.food_data import BioactiveCompounds, BrainNutrients, DataQuality, FoodData, Metadata

# Import utilities
from utils.db_utils import PostgresClient
from utils.nutrient_utils import NutrientUtils
from scripts.ai.openai_api import OpenAIAPI
from utils.logging_utils import setup_logging
from config import get_config

logger = setup_logging(__name__)

class AIEnrichmentEngine:
    """Uses AI to enrich food data with brain-specific nutrients and mental health impacts."""
    
    def __init__(self, model: str = None, db_client: PostgresClient = None):
        config = get_config()
        
        self.db_client = db_client or PostgresClient()        
        self.api_key = config.get_api_key("OPENAI")
        self.model = model or config.get_value("ai_settings.model", "gpt-4o-mini")
        self.openai_client = OpenAIAPI(api_key=self.api_key)
        
        logger.info(f"Initialized AI Enrichment Engine using {self.model} model")
    
    def enrich_brain_nutrients(self, food_data: FoodData) -> FoodData:
        food = food_data
        
        # Make a copy of the data to avoid modifying the original
        enriched_data = food_data.copy()
        
        food_name = food.name
        food_category = food.category        
        standard_nutrients = food.standard_nutrients.__dict__ if food.standard_nutrients else {}
        
        brain_nutrients = food.brain_nutrients.__dict__ if food.brain_nutrients else {}
        
        missing_nutrients = food.get_missing_brain_nutrients()
        
        if not missing_nutrients:
            logger.info(f"No missing brain nutrients for {food_name}")
            return enriched_data
        
        logger.info(f"Predicting missing brain nutrients for {food_name}: {missing_nutrients}")
        
        # Generate predictions using AI
        try:
            predicted_nutrients = self.openai_client.predict_nutrients(
                food_name=food_name,
                food_category=food_category,
                standard_nutrients=standard_nutrients,
                existing_brain_nutrients=brain_nutrients,
                target_nutrients=missing_nutrients
            )
            
            parsed_predictions = NutrientUtils.parse_nutrient_predictions(predicted_nutrients)
            
            if 'brain_nutrients' not in enriched_data:
                enriched_data.brain_nutrients = BrainNutrients()
                
            for nutrient_path, value in parsed_predictions.items():
                if "." in nutrient_path:
                    # Handle nested paths like omega3.total_g
                    parts = nutrient_path.split('.')
                    parent, child = parts[0], parts[1]
                    
                    if parent not in enriched_data.brain_nutrients:
                        enriched_data.brain_nutrients[parent] = {}
                    
                    enriched_data.brain_nutrients[parent][child] = value
                else:
                    enriched_data.brain_nutrients[nutrient_path] = value
            
            # Update data quality
            if 'data_quality' not in enriched_data:
                enriched_data.data_quality = DataQuality()
            
            # Mark brain nutrients as AI generated if we added predictions
            if parsed_predictions:
                enriched_data.data_quality.brain_nutrients_source = 'ai_generated'
            
            logger.info(f"Successfully enriched brain nutrients for {food_name}")
            
        except Exception as e:
            logger.error(f"Error predicting brain nutrients for {food_name}: {e}")
        
        return enriched_data
    
    def enrich_bioactive_compounds(self, food_data: FoodData) -> FoodData:
        food = food_data
        
        enriched_data = food_data.copy()

        food_name = food.name
        food_category = food.category        
        standard_nutrients = food.standard_nutrients.__dict__ if food.standard_nutrients else {}
        
        bioactive_compounds = food.bioactive_compounds.__dict__ if food.bioactive_compounds else {}
        
        missing_compounds = food.get_missing_bioactive_compounds()
        
        if not missing_compounds:
            logger.info(f"No missing bioactive compounds for {food_name}")
            return enriched_data
        
        logger.info(f"Predicting bioactive compounds for {food_name}: {missing_compounds}")
        
        # Generate predictions using AI
        try:
            predicted_compounds = self.openai_client.predict_bioactive_compounds(
                food_name=food_name,
                food_category=food_category,
                standard_nutrients=standard_nutrients
            )
            
            parsed_compounds = NutrientUtils.parse_bioactive_predictions(predicted_compounds)
            
            if 'bioactive_compounds' not in enriched_data:
                enriched_data.bioactive_compounds = BioactiveCompounds()
            
            for compound, value in parsed_compounds.items():
                enriched_data.bioactive_compounds.compounds[compound] = value
            
            logger.info(f"Successfully enriched bioactive compounds for {food_name}")
            
        except Exception as e:
            logger.error(f"Error predicting bioactive compounds for {food_name}: {e}")
        
        return enriched_data
    
    def enrich_mental_health_impacts(self, food_data: FoodData) -> FoodData:
        food = food_data
        
        enriched_data = food_data.copy()
        
        food_name = food.name
        food_category = food.category        
        standard_nutrients = food.standard_nutrients
        brain_nutrients = food.brain_nutrients
        bioactive_compounds = food.bioactive_compounds
        
        existing_impacts = food.mental_health_impacts
        
        if existing_impacts:
            logger.info(f"Mental health impacts already exist for {food_name}")
            return enriched_data
        
        logger.info(f"Predicting mental health impacts for {food_name}")
        
        # Generate predictions using AI
        try:
            predicted_impacts = self.openai_client.predict_mental_health_impacts(
                food_name=food_name,
                food_category=food_category,
                standard_nutrients=standard_nutrients,
                brain_nutrients=brain_nutrients,
                bioactive_compounds=bioactive_compounds
            )
            
            parsed_impacts = NutrientUtils.parse_mental_health_impacts(predicted_impacts)
            
            enriched_data.mental_health_impacts = parsed_impacts
            
            if 'data_quality' not in enriched_data:
                enriched_data.data_quality = DataQuality()
            
            enriched_data.data_quality.impacts_source = 'ai_generated'
            
            logger.info(f"Successfully enriched mental health impacts for {food_name}")
            
        except Exception as e:
            logger.error(f"Error predicting mental health impacts for {food_name}: {e}")
        
        return enriched_data
    
    def fully_enrich_food(self, food_data: FoodData) -> FoodData:
        """
        Apply all enrichment steps to a food item.
        
        Args:
            food_data: Food data in our schema format
            
        Returns:
            Fully enriched food data
        """
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
        
        if 'metadata' not in result:
            result.metadata = Metadata(
                version="0.1.0",
                last_updated=datetime.now().isoformat(),
                source_urls=[],
                tags=["enriched"]
            )

        # Calculate completeness
        food_obj = result
        if 'data_quality' not in result:
            result.data_quality = DataQuality()
            
        result.data_quality.completeness = food_obj.calculate_completeness()
        
        logger.info(f"Completed full enrichment for {food_name}")
        return result
    
    def enrich_directory(self, db_client: PostgresClient = None, limit: Optional[int] = None) -> List[str]:
        """
        Enrich all food data items from database that need enrichment.
        
        Args:
            db_client: Database client
            limit: Optional limit on number of foods to process
            
        Returns:
            List of enriched food ids
        """
        db_client = db_client or self.db_client
        enriched_ids = []
        
        # Retrieve foods from database that need enrichment
        foods_to_enrich = db_client.get_all_foods_without_mental_health_impacts()
        if limit:
            foods_to_enrich = foods_to_enrich[:limit]
        
        logger.info(f"Found {len(foods_to_enrich)} foods to enrich")
        
        for food in foods_to_enrich:
            try:
                enriched_data = self.fully_enrich_food(food)                
                food_id = db_client.import_food_from_json(enriched_data)
                enriched_ids.append(food_id)
                
                logger.info(f"Enriched {food.get('name')} with ID {food_id}")
                
                # Sleep between foods to avoid rate limiting
                time.sleep(2)
            except Exception as e:
                logger.error(f"Error processing {food.get('food_id', 'unknown')}: {e}")
        
        return enriched_ids

def main():
    parser = argparse.ArgumentParser(description="AI-Assisted Food Data Enrichment")
    parser.add_argument("--model", help="OpenAI model to use")
    parser.add_argument("--limit", type=int, help="Limit number of foods to process")
    parser.add_argument("--batch-size", type=int, help="Batch size for processing")
    
    args = parser.parse_args()    
    db_client = PostgresClient()
    
    try:
        # Initialize enricher with configuration
        config = get_config()
        model = args.model or config.get_value("ai_settings.model", "gpt-4o-mini")
        
        enricher = AIEnrichmentEngine(
            model=model,
            db_client=db_client
        )
        
        logger.info("Starting food data enrichment process")
        
        enriched_foods = enricher.enrich_directory(
            db_client=db_client,
            limit=args.limit
        )
        
        logger.info(f"Successfully enriched {len(enriched_foods)} foods")
        
    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)

if __name__ == "__main__":
    main()