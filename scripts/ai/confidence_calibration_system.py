#!/usr/bin/env python3
"""
Confidence Calibration System for Nutritional Psychiatry Database

This script applies confidence calibration to the entire database:
- Adjusts confidence ratings based on global accuracy metrics
- Ensures consistency across similar foods
- Applies food-category specific adjustments
- Produces a calibrated version of the database

This version uses the database directly instead of file I/O and leverages
the established data models for better type safety and validation.
"""

import os
import json
import glob
import argparse
from datetime import datetime
import sys
from typing import Dict, List, Optional, Tuple

# Import project utilities
from utils.logging_utils import setup_logging
from utils.db_utils import PostgresClient
from config import get_config

# Import data models
from schema.food_data import (
    FoodData, BrainNutrients, Metadata, Omega3, BioactiveCompounds,
    MentalHealthImpact, SourcePriority, DataQuality
)

# Initialize logger
logger = setup_logging(__name__)

class ConfidenceCalibrationSystem:
    """System for calibrating confidence ratings in the nutritional psychiatry database."""
    
    def __init__(
        self,
        db_client: Optional[PostgresClient] = None,
        batch_size: int = 100,
        dry_run: bool = False
    ):
        self.db_client = db_client or PostgresClient()
        self.batch_size = batch_size
        self.dry_run = dry_run
        
        # Load evaluation metrics to guide calibration
        self.calibration_model = self._load_calibration_model()
        
        logger.info(f"Initialized Confidence Calibration System")
        if dry_run:
            logger.info("DRY RUN MODE: No changes will be saved to database")
    
    def _load_calibration_model(self) -> Dict:
        """
        Load evaluation metrics from database to build calibration model.
        
        Returns:
            Dictionary with calibration parameters by nutrient and food category
        """
        model = {
            "global": {
                "nutrient_adjustments": {},
                "category_adjustments": {},
                "overall_confidence_adjustment": 0.0
            }
        }
        
        try:
            # Find the most recent evaluation metrics in the database
            query = """
            SELECT metrics_data 
            FROM evaluation_metrics 
            WHERE metrics_type = 'nutrients' 
            ORDER BY timestamp DESC 
            LIMIT 1
            """
            
            results = self.db_client.execute_query(query)
            
            if not results:
                logger.warning("No evaluation metrics found in database. Using default calibration model.")
                return model
            
            summary = results[0]["metrics_data"]
            
            logger.info(f"Loaded evaluation metrics from database")
            
            # Extract nutrient-specific calibration factors
            if "nutrient_types_by_accuracy" in summary:
                for nutrient, metrics in summary["nutrient_types_by_accuracy"].items():
                    accuracy = metrics.get("accuracy_within_25_percent", 0)
                    mean_error = metrics.get("mean_error_percent", 0)
                    
                    # Calculate adjustment factor based on accuracy and error
                    if accuracy < 50:
                        # Nutrient predictions are less reliable, reduce confidence
                        adjustment = -2.0
                    elif accuracy < 75:
                        # Moderately reliable, slight reduction
                        adjustment = -1.0
                    elif accuracy >= 90:
                        # Very reliable, boost confidence
                        adjustment = 0.5
                    else:
                        # Reasonably reliable, no adjustment
                        adjustment = 0.0
                    
                    model["global"]["nutrient_adjustments"][nutrient] = adjustment
            
            # Calculate overall confidence adjustment
            if "mean_absolute_percentage_error" in summary:
                mape = summary["mean_absolute_percentage_error"]
                confidence_error = summary.get("confidence_calibration_error", 0)
                
                # If AI is generally overconfident (common issue), reduce confidence
                if confidence_error > 2:
                    model["global"]["overall_confidence_adjustment"] = -confidence_error / 2
                
                # Adjust overall confidence based on MAPE
                if mape > 50:
                    model["global"]["overall_confidence_adjustment"] -= 1.0
            
            logger.info(f"Calibration model built with {len(model['global']['nutrient_adjustments'])} nutrient-specific adjustments")
            logger.info(f"Global confidence adjustment: {model['global']['overall_confidence_adjustment']}")
            
        except Exception as e:
            logger.error(f"Error loading evaluation metrics from database: {e}", exc_info=True)
            # Continue with default model
        
        return model
    
    def calibrate_confidence(self, food_data: Dict) -> Dict:
        """
        Calibrate confidence ratings in food data.
        
        Args:
            food_data: Food data dictionary
            
        Returns:
            Food data with calibrated confidence ratings
        """
        try:
            # Convert to FoodData object for type safety
            food = FoodData.from_dict(food_data)
            food_category = food.category
            
            # Apply calibrations to brain nutrients
            if food.brain_nutrients:
                self._calibrate_brain_nutrients(food)
                
            # Apply calibrations to bioactive compounds
            if food.bioactive_compounds:
                self._calibrate_bioactive_compounds(food)
                
            # Apply calibrations to mental health impacts
            if food.mental_health_impacts:
                self._calibrate_mental_health_impacts(food)
            
            # Add calibration metadata
            if not food.metadata:
                # This should rarely happen since metadata is required,
                # but handle it gracefully just in case
                from datetime import datetime
                food.metadata = Metadata(
                    version='0.1.0',
                    created=datetime.now().isoformat(),
                    last_updated=datetime.now().isoformat(),
                    tags=['calibration']
                )
            
            return food.to_dict()
                
        except Exception as e:
            logger.error(f"Error calibrating food {food_data.get('food_id', 'unknown')}: {e}")
            # Return original data if calibration fails
            return food_data
    
    def _calibrate_brain_nutrients(self, food: FoodData) -> None:
        """
        Calibrate confidence ratings for brain nutrients.
        
        Args:
            food: FoodData object to calibrate
        """
        if not food.brain_nutrients:
            return
        
        brain_nutrients = food.brain_nutrients
        
        # Process regular brain nutrients
        for nutrient_name in dir(brain_nutrients):
            # Skip special attributes and non-confidence fields
            if nutrient_name.startswith('_') or nutrient_name.startswith('confidence_'):
                continue
                
            # Skip methods and non-data attributes
            if callable(getattr(brain_nutrients, nutrient_name)) or isinstance(getattr(brain_nutrients, nutrient_name), (dict, list)):
                continue
            
            # Get current confidence rating if it exists
            confidence_key = f"confidence_{nutrient_name}"
            if hasattr(brain_nutrients, confidence_key):
                current_confidence = getattr(brain_nutrients, confidence_key)
                
                if current_confidence is not None:
                    # Apply nutrient-specific adjustment
                    adjustment = self.calibration_model["global"]["nutrient_adjustments"].get(nutrient_name, 0)
                    
                    # Apply category-specific adjustment if available
                    category_adjustment = self.calibration_model["global"]["category_adjustments"].get(food.category, {}).get(nutrient_name, 0)
                    
                    # Apply global adjustment
                    global_adjustment = self.calibration_model["global"]["overall_confidence_adjustment"]
                    
                    # Calculate new confidence
                    new_confidence = current_confidence + adjustment + category_adjustment + global_adjustment
                    
                    # Ensure confidence is in valid range (1-10)
                    new_confidence = max(1, min(10, new_confidence))
                    
                    # Update confidence
                    setattr(brain_nutrients, confidence_key, new_confidence)
        
        # Handle omega-3 separately if it exists
        if brain_nutrients.omega3:
            omega3 = brain_nutrients.omega3
            if hasattr(omega3, 'confidence') and omega3.confidence is not None:
                current_confidence = omega3.confidence
                
                # Apply global adjustment
                global_adjustment = self.calibration_model["global"]["overall_confidence_adjustment"]
                
                # Apply omega3-specific adjustments
                omega3_adjustment = self.calibration_model["global"]["nutrient_adjustments"].get("omega3", 0)
                
                # Calculate new confidence
                new_confidence = current_confidence + global_adjustment + omega3_adjustment
                
                # Ensure confidence is in valid range (1-10)
                new_confidence = max(1, min(10, new_confidence))
                
                # Update confidence
                omega3.confidence = new_confidence
    
    def _calibrate_bioactive_compounds(self, food: FoodData) -> None:
        """
        Calibrate confidence ratings for bioactive compounds.
        
        Args:
            food: FoodData object to calibrate
        """
        if not food.bioactive_compounds:
            return
        
        bioactive_compounds = food.bioactive_compounds
        
        # Bioactive compounds typically have higher uncertainty
        bioactive_adjustment = -1.0  # Conservative adjustment for bioactives
        global_adjustment = self.calibration_model["global"]["overall_confidence_adjustment"]
        
        # Process bioactive compounds
        for compound_name in dir(bioactive_compounds):
            # Skip special attributes and non-confidence fields
            if compound_name.startswith('_') or compound_name.startswith('confidence_'):
                continue
                
            # Skip methods and non-data attributes
            if callable(getattr(bioactive_compounds, compound_name)) or isinstance(getattr(bioactive_compounds, compound_name), (dict, list)):
                continue
            
            # Get current confidence rating if it exists
            confidence_key = f"confidence_{compound_name}"
            if hasattr(bioactive_compounds, confidence_key):
                current_confidence = getattr(bioactive_compounds, confidence_key)
                
                if current_confidence is not None:
                    # Apply adjustments
                    new_confidence = current_confidence + global_adjustment + bioactive_adjustment
                    
                    # Ensure confidence is in valid range (1-10)
                    new_confidence = max(1, min(10, new_confidence))
                    
                    # Update confidence
                    setattr(bioactive_compounds, confidence_key, new_confidence)
    
    def _calibrate_mental_health_impacts(self, food: FoodData) -> None:
        """
        Calibrate confidence ratings for mental health impacts.
        
        Args:
            food: FoodData object to calibrate
        """
        if not food.mental_health_impacts:
            return
        
        # Mental health impacts generally need conservative confidence
        impact_adjustment = -1.0  # Be conservative for mental health claims
        global_adjustment = self.calibration_model["global"]["overall_confidence_adjustment"]
        
        # Process each impact
        for impact in food.mental_health_impacts:
            if hasattr(impact, 'confidence') and impact.confidence is not None:
                current_confidence = impact.confidence
                
                # Apply adjustments
                new_confidence = current_confidence + global_adjustment + impact_adjustment
                
                # Ensure confidence is in valid range (1-10)
                new_confidence = max(1, min(10, new_confidence))
                
                # Update confidence
                impact.confidence = new_confidence
    
    def get_foods_to_calibrate(self, batch_size: int = None, offset: int = 0) -> List[Dict]:
        """
        Get foods that need confidence calibration from the database.
        
        Args:
            batch_size: Maximum number of foods to retrieve
            offset: Offset for pagination
            
        Returns:
            List of food data dictionaries
        """
        limit = batch_size or self.batch_size
        
        try:
            query = """
            SELECT food_id, name, food_data
            FROM foods
            WHERE food_data->'data_quality'->>'overall_confidence' IS NOT NULL
            ORDER BY food_id
            LIMIT %s OFFSET %s
            """
            
            results = self.db_client.execute_query(query, (limit, offset))
            return results
            
        except Exception as e:
            logger.error(f"Error fetching foods to calibrate: {e}")
            return []
    
    def save_calibrated_food(self, food_id: str, calibrated_data: Dict) -> bool:
        """
        Save calibrated food data to the database.
        
        Args:
            food_id: Food ID
            calibrated_data: Calibrated food data
            
        Returns:
            True if saved successfully, False otherwise
        """
        if self.dry_run:
            logger.info(f"DRY RUN: Would save calibrated data for {food_id}")
            return True
            
        try:
            query = """
            UPDATE foods
            SET food_data = %s, 
                last_updated = NOW()
            WHERE food_id = %s
            RETURNING food_id
            """
            
            result = self.db_client.execute_query(query, (json.dumps(calibrated_data), food_id))
            
            if result and result[0]['food_id'] == food_id:
                return True
            else:
                logger.warning(f"Food {food_id} not found in database")
                return False
                
        except Exception as e:
            logger.error(f"Error saving calibrated food {food_id}: {e}")
            return False
    
    def calibrate_batch(self, batch: List[Dict]) -> Tuple[int, int]:
        """
        Calibrate a batch of foods.
        
        Args:
            batch: List of food dictionaries from database
            
        Returns:
            Tuple of (successful_count, failed_count)
        """
        success_count = 0
        failure_count = 0
        
        for item in batch:
            food_id = item['food_id']
            food_data = item['food_data']
            
            try:
                logger.debug(f"Calibrating {food_id}: {item['name']}")
                calibrated = self.calibrate_confidence(food_data)
                
                if self.save_calibrated_food(food_id, calibrated):
                    success_count += 1
                    logger.debug(f"Successfully calibrated {food_id}")
                else:
                    failure_count += 1
                    logger.warning(f"Failed to save calibrated food {food_id}")
                    
            except Exception as e:
                failure_count += 1
                logger.error(f"Error processing food {food_id}: {e}")
        
        return success_count, failure_count
    
    def calibrate_database(self) -> Dict[str, int]:
        """
        Calibrate the entire database.
        
        Returns:
            Dictionary with statistics about calibration process
        """
        start_time = datetime.now()
        
        stats = {
            "total_processed": 0,
            "successfully_calibrated": 0,
            "failed": 0,
            "batches": 0
        }
        
        offset = 0
        while True:
            # Get batch of foods to calibrate
            batch = self.get_foods_to_calibrate(self.batch_size, offset)
            
            if not batch:
                logger.info(f"No more foods to calibrate")
                break
            
            stats["batches"] += 1
            stats["total_processed"] += len(batch)
            
            # Process batch
            logger.info(f"Processing batch {stats['batches']} ({len(batch)} foods)")
            success, failure = self.calibrate_batch(batch)
            
            stats["successfully_calibrated"] += success
            stats["failed"] += failure
            
            # Update offset for next batch
            offset += len(batch)
            
            # Log progress
            logger.info(f"Batch {stats['batches']} completed: {success} succeeded, {failure} failed")
            
            # Exit if batch is smaller than batch size (last batch)
            if len(batch) < self.batch_size:
                break
        
        # Calculate timing
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        stats["duration_seconds"] = duration
        stats["foods_per_second"] = stats["total_processed"] / duration if duration > 0 else 0
        
        logger.info(f"Calibration complete: {stats['successfully_calibrated']} succeeded, {stats['failed']} failed")
        logger.info(f"Total time: {duration:.2f} seconds ({stats['foods_per_second']:.2f} foods/sec)")
        
        return stats

def main():
    """Main function to execute calibration."""
    parser = argparse.ArgumentParser(description="Calibrate confidence ratings in database")
    parser.add_argument("--evaluation-dir", help="Directory with evaluation results")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size for processing")
    parser.add_argument("--dry-run", action="store_true", help="Run without saving changes")
    
    args = parser.parse_args()
    
    try:
        # Initialize database client
        db_client = PostgresClient()
        
        # Initialize calibrator
        calibrator = ConfidenceCalibrationSystem(
            db_client=db_client,
            evaluation_dir=args.evaluation_dir,
            batch_size=args.batch_size,
            dry_run=args.dry_run
        )
        
        # Run calibration
        stats = calibrator.calibrate_database()
        
        # Print summary
        print("\nCalibration Summary:")
        print(f"Total foods processed: {stats['total_processed']}")
        print(f"Successfully calibrated: {stats['successfully_calibrated']}")
        print(f"Failed: {stats['failed']}")
        print(f"Processing time: {stats['duration_seconds']:.2f} seconds")
        print(f"Processing rate: {stats['foods_per_second']:.2f} foods/second")
        
    except Exception as e:
        logger.error(f"Error during calibration: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()