#!/usr/bin/env python3
"""
AI-Assisted Data Enrichment Script
Enriches food data with brain-specific nutrients and mental health impacts using AI.
"""

import os
import json
import glob
import logging
import time
from typing import Dict, List, Any, Optional, Tuple
import importlib.util
import argparse
from datetime import datetime
import sys

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
from scripts.ai.openai_client import OpenAIClient

# Check if OpenAI is installed
if importlib.util.find_spec("openai") is None:
    print("This script requires the OpenAI Python package. Install with: pip install openai")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AIEnrichmentEngine:
    """Uses AI to enrich food data with brain-specific nutrients and mental health impacts."""
    
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
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        """
        Initialize the AI enrichment engine.
        
        Args:
            api_key: OpenAI API key
            model: Model to use for generation
        """
        if not api_key:
            raise ValueError("OpenAI API key is required. Set it as an argument or as OPENAI_API_KEY environment variable.")
        
        self.openai_client = OpenAIClient(api_key=api_key)
        logger.info(f"Initialized AI Enrichment Engine using {model} model")
    
    def enrich_brain_nutrients(self, food_data: Dict) -> Dict:
        """
        Enrich food data with missing brain-specific nutrients using AI.
        
        Args:
            food_data: Food data in our schema format
            
        Returns:
            Enriched food data
        """
        # Make a copy of the data to avoid modifying the original
        enriched_data = food_data.copy()
        
        # Get food name and basic information
        food_name = food_data.get('name', '')
        food_category = food_data.get('category', '')
        
        # Get standard nutrients for context
        standard_nutrients = food_data.get('standard_nutrients', {})
        
        # Get existing brain nutrients
        brain_nutrients = food_data.get('brain_nutrients', {})
        
        # Identify missing brain nutrients
        missing_nutrients = []
        for nutrient_path in self.BRAIN_NUTRIENTS_TO_PREDICT:
            if "." in nutrient_path:
                # Handle nested paths like omega3.total_g
                parts = nutrient_path.split('.')
                parent, child = parts[0], parts[1]
                
                if parent not in brain_nutrients or child not in brain_nutrients.get(parent, {}):
                    missing_nutrients.append(nutrient_path)
            else:
                if nutrient_path not in brain_nutrients:
                    missing_nutrients.append(nutrient_path)
        
        # If no missing nutrients, return original data
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
            
            # Update the enriched data with predictions
            for nutrient_path, value in predicted_nutrients.items():
                if "." in nutrient_path:
                    # Handle nested paths like omega3.total_g
                    parts = nutrient_path.split('.')
                    parent, child = parts[0], parts[1]
                    
                    if parent not in enriched_data.get('brain_nutrients', {}):
                        if 'brain_nutrients' not in enriched_data:
                            enriched_data['brain_nutrients'] = {}
                        enriched_data['brain_nutrients'][parent] = {}
                    
                    enriched_data['brain_nutrients'][parent][child] = value
                else:
                    if 'brain_nutrients' not in enriched_data:
                        enriched_data['brain_nutrients'] = {}
                    enriched_data['brain_nutrients'][nutrient_path] = value
            
            # Update metadata
            if 'data_quality' not in enriched_data:
                enriched_data['data_quality'] = {}
            
            # Mark brain nutrients as AI generated if we added predictions
            if predicted_nutrients:
                enriched_data['data_quality']['brain_nutrients_source'] = 'ai_generated'
            
            logger.info(f"Successfully enriched brain nutrients for {food_name}")
            
        except Exception as e:
            logger.error(f"Error predicting brain nutrients for {food_name}: {e}")
        
        return enriched_data
    
    def enrich_bioactive_compounds(self, food_data: Dict) -> Dict:
        """
        Enrich food data with bioactive compounds using AI.
        
        Args:
            food_data: Food data in our schema format
            
        Returns:
            Enriched food data
        """
        # Make a copy of the data to avoid modifying the original
        enriched_data = food_data.copy()
        
        # Get food name and basic information
        food_name = food_data.get('name', '')
        food_category = food_data.get('category', '')
        standard_nutrients = food_data.get('standard_nutrients', {})
        
        # Get existing bioactive compounds
        bioactive_compounds = food_data.get('bioactive_compounds', {})
        
        # If all bioactive compounds already exist, return original data
        if all(compound in bioactive_compounds for compound in self.BIOACTIVE_COMPOUNDS_TO_PREDICT):
            logger.info(f"Bioactive compounds already exist for {food_name}")
            return enriched_data
        
        logger.info(f"Predicting bioactive compounds for {food_name}")
        
        # Generate predictions using AI
        try:
            predicted_compounds = self.openai_client.predict_bioactive_compounds(
                food_name=food_name,
                food_category=food_category,
                standard_nutrients=standard_nutrients
            )
            
            # Parse the generated predictions
            predicted_compounds = self._parse_bioactive_predictions(predicted_compounds)
            
            # Update the enriched data with predictions
            if 'bioactive_compounds' not in enriched_data:
                enriched_data['bioactive_compounds'] = {}
            
            for compound, value in predicted_compounds.items():
                enriched_data['bioactive_compounds'][compound] = value
            
            logger.info(f"Successfully enriched bioactive compounds for {food_name}")
            
        except Exception as e:
            logger.error(f"Error predicting bioactive compounds for {food_name}: {e}")
        
        return enriched_data
    
    def enrich_mental_health_impacts(self, food_data: Dict) -> Dict:
        """
        Enrich food data with mental health impacts using AI.
        
        Args:
            food_data: Food data in our schema format
            
        Returns:
            Enriched food data
        """
        # Make a copy of the data to avoid modifying the original
        enriched_data = food_data.copy()
        
        # Get food name and basic information
        food_name = food_data.get('name', '')
        food_category = food_data.get('category', '')
        
        # Get nutrients for context
        standard_nutrients = food_data.get('standard_nutrients', {})
        brain_nutrients = food_data.get('brain_nutrients', {})
        bioactive_compounds = food_data.get('bioactive_compounds', {})
        
        # Get existing mental health impacts
        existing_impacts = food_data.get('mental_health_impacts', [])
        
        # If impacts already exist, return original data
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
            
            # Parse the generated predictions
            predicted_impacts = self._parse_mental_health_impacts(predicted_impacts)
            
            # Update the enriched data with predictions
            enriched_data['mental_health_impacts'] = predicted_impacts
            
            # Update data quality
            if 'data_quality' not in enriched_data:
                enriched_data['data_quality'] = {}
            
            # Mark impacts as AI generated
            enriched_data['data_quality']['impacts_source'] = 'ai_generated'
            
            logger.info(f"Successfully enriched mental health impacts for {food_name}")
            
        except Exception as e:
            logger.error(f"Error predicting mental health impacts for {food_name}: {e}")
        
        return enriched_data
    
    def _parse_nutrient_predictions(self, ai_response: str) -> Dict[str, float]:
        """
        Parse nutrient predictions from AI response.
        
        Args:
            ai_response: Response from AI
            
        Returns:
            Dictionary of nutrient predictions
        """
        try:
            # Extract JSON from the response
            json_start = ai_response.find('{')
            json_end = ai_response.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                logger.warning("No JSON found in AI response")
                return {}
            
            json_str = ai_response[json_start:json_end]
            predictions = json.loads(json_str)
            
            # Remove non-numeric fields like confidence notes
            numeric_predictions = {}
            for key, value in predictions.items():
                if isinstance(value, (int, float)) and key != "confidence":
                    numeric_predictions[key] = value
            
            return numeric_predictions
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing nutrient predictions: {e}")
            return {}
    
    def _parse_bioactive_predictions(self, ai_response: str) -> Dict[str, float]:
        """
        Parse bioactive compound predictions from AI response.
        
        Args:
            ai_response: Response from AI
            
        Returns:
            Dictionary of bioactive compound predictions
        """
        # Use the same parsing logic as for nutrients
        return self._parse_nutrient_predictions(ai_response)
    
    def _parse_mental_health_impacts(self, ai_response: str) -> List[Dict]:
        """
        Parse mental health impact predictions from AI response.
        
        Args:
            ai_response: Response from AI
            
        Returns:
            List of mental health impact dictionaries
        """
        try:
            # Extract JSON from the response
            json_start = ai_response.find('[')
            json_end = ai_response.rfind(']') + 1
            
            if json_start == -1 or json_end == 0:
                logger.warning("No JSON array found in AI response")
                return []
            
            json_str = ai_response[json_start:json_end]
            impacts = json.loads(json_str)
            
            # Validate required fields
            validated_impacts = []
            required_fields = ['impact_type', 'direction', 'mechanism', 'strength', 'confidence']
            
            for impact in impacts:
                if all(field in impact for field in required_fields):
                    # Convert any research citations to proper format
                    if 'research_citations' in impact and isinstance(impact['research_citations'], list):
                        impact['research_support'] = [
                            {'citation': citation} for citation in impact['research_citations']
                        ]
                    
                    validated_impacts.append(impact)
                else:
                    missing = [field for field in required_fields if field not in impact]
                    logger.warning(f"Impact missing required fields: {missing}")
            
            return validated_impacts
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing mental health impacts: {e}")
            return []
    
    def fully_enrich_food(self, food_data: Dict) -> Dict:
        """
        Apply all enrichment steps to a food item.
        
        Args:
            food_data: Food data in our schema format
            
        Returns:
            Fully enriched food data
        """
        food_name = food_data.get('name', 'Unknown food')
        logger.info(f"Beginning full enrichment for {food_name}")
        
        # Apply enrichment steps in sequence
        step1 = self.enrich_brain_nutrients(food_data)
        time.sleep(1)  # Avoid rate limiting
        
        step2 = self.enrich_bioactive_compounds(step1)
        time.sleep(1)  # Avoid rate limiting
        
        step3 = self.enrich_mental_health_impacts(step2)
        
        # Update data quality metrics
        result = step3
        
        # Calculate overall completeness
        if 'data_quality' not in result:
            result['data_quality'] = {}
        
        # Update metadata
        if 'metadata' not in result:
            result['metadata'] = {}
        
        result['metadata']['last_updated'] = datetime.now().isoformat()
        
        logger.info(f"Completed full enrichment for {food_name}")
        return result
    
    def enrich_directory(self, input_dir: str, output_dir: str, limit: Optional[int] = None) -> List[str]:
        """
        Enrich all food data files in a directory.
        
        Args:
            input_dir: Directory with base food data
            output_dir: Directory to save enriched data
            limit: Optional limit on number of files to process
            
        Returns:
            List of paths to enriched data files
        """
        os.makedirs(output_dir, exist_ok=True)
        
        enriched_files = []
        input_files = glob.glob(os.path.join(input_dir, "*.json"))
        
        # Apply limit if specified
        if limit:
            input_files = input_files[:limit]
        
        for input_file in input_files:
            try:
                with open(input_file, 'r') as f:
                    food_data = json.load(f)
                
                enriched_data = self.fully_enrich_food(food_data)
                
                # Save enriched data
                filename = os.path.basename(input_file)
                output_path = os.path.join(output_dir, filename)
                
                with open(output_path, 'w') as f:
                    json.dump(enriched_data, f, indent=2)
                
                enriched_files.append(output_path)
                logger.info(f"Enriched {input_file} -> {output_path}")
                
                # Sleep between files to avoid rate limiting
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error processing {input_file}: {e}")
        
        return enriched_files


def main():
    """Main function to execute the enrichment process."""
    parser = argparse.ArgumentParser(description="AI-Assisted Food Data Enrichment")
    parser.add_argument("--input-dir", default=os.path.join("data", "processed", "base_foods"),
                        help="Directory with base food data")
    parser.add_argument("--output-dir", default=os.path.join("data", "enriched", "ai_generated"),
                        help="Directory to save enriched data")
    parser.add_argument("--api-key", default=os.environ.get("OPENAI_API_KEY"),  help="OpenAI API key (or set OPENAI_API_KEY environment variable)")
    parser.add_argument("--model", default="gpt-4", help="OpenAI model to use")
    parser.add_argument("--limit", type=int, help="Limit number of files to process")
    
    args = parser.parse_args()
    
    try:
        enricher = AIEnrichmentEngine(api_key=args.api_key, model=args.model)
        logger.info(f"Processing files from {args.input_dir}")
        enriched_files = enricher.enrich_directory(args.input_dir, args.output_dir, limit=args.limit)
        logger.info(f"Successfully enriched {len(enriched_files)} files")
    except Exception as e:
        logger.error(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
