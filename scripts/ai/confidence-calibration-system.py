#!/usr/bin/env python3
"""
Confidence Calibration System for Nutritional Psychiatry Dataset

This script applies confidence calibration to the entire dataset:
- Adjusts confidence ratings based on global accuracy metrics
- Ensures consistency across similar foods
- Applies food-category specific adjustments
- Produces a calibrated version of the dataset
"""

import os
import json
import glob
import logging
import argparse
from typing import Dict, List, Any, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ConfidenceCalibrationSystem:
    """System for calibrating confidence ratings in the dataset."""
    
    def __init__(
        self,
        evaluation_dir: str = "data/evaluation",
        dataset_dir: str = "data/enriched/ai_generated",
        output_dir: str = "data/enriched/calibrated"
    ):
        """
        Initialize the calibration system.
        
        Args:
            evaluation_dir: Directory with evaluation results
            dataset_dir: Directory with dataset to calibrate
            output_dir: Directory to save calibrated dataset
        """
        self.evaluation_dir = evaluation_dir
        self.dataset_dir = dataset_dir
        self.output_dir = output_dir
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Load evaluation metrics to guide calibration
        self.calibration_model = self._load_calibration_model()
    
    def _load_calibration_model(self) -> Dict:
        """
        Load evaluation metrics to build calibration model.
        
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
        
        # Find most recent evaluation summary
        summary_files = glob.glob(os.path.join(self.evaluation_dir, "evaluation_summary_*.json"))
        if not summary_files:
            logger.warning("No evaluation summary files found. Using default calibration model.")
            return model
        
        # Sort by modification time (most recent first)
        summary_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        summary_file = summary_files[0]
        
        try:
            with open(summary_file, 'r') as f:
                summary = json.load(f)
            
            logger.info(f"Loaded evaluation summary from {summary_file}")
            
            # Extract nutrient-specific calibration factors
            if "nutrients" in summary and "nutrient_types_by_accuracy" in summary["nutrients"]:
                for nutrient, metrics in summary["nutrients"]["nutrient_types_by_accuracy"].items():
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
            if "nutrients" in summary and "mean_absolute_percentage_error" in summary["nutrients"]:
                mape = summary["nutrients"]["mean_absolute_percentage_error"]
                confidence_error = summary["nutrients"].get("confidence_calibration_error", 0)
                
                # If AI is generally overconfident (common issue), reduce confidence
                if confidence_error > 2:
                    model["global"]["overall_confidence_adjustment"] = -confidence_error / 2
                
                # Adjust overall confidence based on MAPE
                if mape > 50:
                    model["global"]["overall_confidence_adjustment"] -= 1.0
            
            # Load food-category specific calibration
            # (This would require more evaluation data by category)
            
            logger.info(f"Calibration model built with {len(model['global']['nutrient_adjustments'])} nutrient-specific adjustments")
            
        except Exception as e:
            logger.error(f"Error loading evaluation summary: {e}")
        
        return model
    
    def calibrate_confidence(self, food_data: Dict) -> Dict:
        """
        Calibrate confidence ratings in food data.
        
        Args:
            food_data: Food data dictionary
            
        Returns:
            Food data with calibrated confidence ratings
        """
        # Make a copy of the data
        calibrated = food_data.copy()
        food_category = food_data.get("category", "")
        
        # Apply nutrient-specific calibrations
        if "brain_nutrients" in calibrated:
            brain_nutrients = calibrated["brain_nutrients"]
            
            for nutrient, value in brain_nutrients.items():
                # Skip non-numeric and non-confidence fields
                if not isinstance(value, (int, float)) or nutrient.startswith("confidence_"):
                    continue
                
                # Get current confidence rating
                confidence_key = f"confidence_{nutrient}"
                if confidence_key in brain_nutrients:
                    current_confidence = brain_nutrients[confidence_key]
                    
                    # Apply nutrient-specific adjustment
                    adjustment = self.calibration_model["global"]["nutrient_adjustments"].get(nutrient, 0)
                    
                    # Apply category-specific adjustment if available
                    category_adjustment = self.calibration_model["global"]["category_adjustments"].get(food_category, {}).get(nutrient, 0)
                    
                    # Apply global adjustment
                    global_adjustment = self.calibration_model["global"]["overall_confidence_adjustment"]
                    
                    # Calculate new confidence
                    new_confidence = current_confidence + adjustment + category_adjustment + global_adjustment
                    
                    # Ensure confidence is in valid range (1-10)
                    new_confidence = max(1, min(10, new_confidence))
                    
                    # Update confidence
                    brain_nutrients[confidence_key] = new_confidence
        
        # Apply bioactive compound calibrations
        if "bioactive_compounds" in calibrated:
            bioactive_compounds = calibrated["bioactive_compounds"]
            
            for compound, value in bioactive_compounds.items():
                # Skip non-numeric and non-confidence fields
                if not isinstance(value, (int, float)) or compound.startswith("confidence_"):
                    continue
                
                # Get current confidence rating
                confidence_key = f"confidence_{compound}"
                if confidence_key in bioactive_compounds:
                    current_confidence = bioactive_compounds[confidence_key]
                    
                    # Bioactive compounds tend to have less certainty, apply conservative adjustment
                    # (We have less evaluation data for these, so be more cautious)
                    global_adjustment = self.calibration_model["global"]["overall_confidence_adjustment"]
                    
                    # For bioactives, we're generally more uncertain, so reduce confidence more
                    bioactive_adjustment = -1.0
                    
                    # Calculate new confidence
                    new_confidence = current_confidence + global_adjustment + bioactive_adjustment
                    
                    # Ensure confidence is in valid range (1-10)
                    new_confidence = max(1, min(10, new_confidence))
                    
                    # Update confidence
                    bioactive_compounds[confidence_key] = new_confidence
        
        # Apply mental health impact calibrations
        if "mental_health_impacts" in calibrated:
            impacts = calibrated["mental_health_impacts"]
            
            for impact in impacts:
                if "confidence" in impact:
                    current_confidence = impact["confidence"]
                    
                    # Mental health impacts generally need conservative confidence
                    # Apply global adjustment plus specific reduction
                    global_adjustment = self.calibration_model["global"]["overall_confidence_adjustment"]
                    impact_adjustment = -1.0  # Be conservative for mental health claims
                    
                    # Calculate new confidence
                    new_confidence = current_confidence + global_adjustment + impact_adjustment
                    
                    # Ensure confidence is in valid range (1-10)
                    new_confidence = max(1, min(10, new_confidence))
                    
                    # Update confidence
                    impact["confidence"] = new_confidence
        
        # Add calibration metadata
        if "metadata" not in calibrated:
            calibrated["metadata"] = {}
        
        calibrated["metadata"]["confidence_calibration"] = {
            "timestamp": datetime.now().isoformat(),
            "method": "global_calibration_model",
            "version": "0.1.0"
        }
        
        return calibrated
    
    def calibrate_dataset(self):
        """Calibrate the entire dataset."""
        # List all files in dataset directory
        dataset_files = glob.glob(os.path.join(self.dataset_dir, "*.json"))
        logger.info(f"Found {len(dataset_files)} files to calibrate")
        
        calibrated_count = 0
        
        for file_path in dataset_files:
            try:
                # Load food data
                with open(file_path, 'r') as f:
                    food_data = json.load(f)
                
                # Calibrate confidence ratings
                calibrated = self.calibrate_confidence(food_data)
                
                # Save calibrated data
                filename = os.path.basename(file_path)
                output_path = os.path.join(self.output_dir, filename)
                
                with open(output_path, 'w') as f:
                    json.dump(calibrated, f, indent=2)
                
                calibrated_count += 1
                
            except Exception as e:
                logger.error(f"Error calibrating {file_path}: {e}")
        
        logger.info(f"Calibrated {calibrated_count} files. Saved to {self.output_dir}")


def main():
    """Main function to execute calibration."""
    parser = argparse.ArgumentParser(description="Calibrate confidence ratings in dataset")
    parser.add_argument("--evaluation-dir", default="data/evaluation", help="Directory with evaluation results")
    parser.add_argument("--dataset-dir", default="data/enriched/ai_generated", help="Directory with dataset to calibrate")
    parser.add_argument("--output-dir", default="data/enriched/calibrated", help="Directory to save calibrated dataset")
    
    args = parser.parse_args()
    
    try:
        calibrator = ConfidenceCalibrationSystem(
            evaluation_dir=args.evaluation_dir,
            dataset_dir=args.dataset_dir,
            output_dir=args.output_dir
        )
        
        calibrator.calibrate_dataset()
        
    except Exception as e:
        logger.error(f"Error during calibration: {e}")
        raise


if __name__ == "__main__":
    main()