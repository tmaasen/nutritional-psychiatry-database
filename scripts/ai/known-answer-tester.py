#!/usr/bin/env python3
"""
Evaluation System for AI-Generated Nutritional Psychiatry Data

This script evaluates AI-generated predictions against known values and reference data:
- Compares nutrient predictions to reference values
- Assesses accuracy and calibrates confidence ratings
- Provides metrics for model performance tracking
- Validates mental health impacts against literature
- Implements known-answer testing for key nutrients and foods
"""

import os
import json
import logging
import argparse
from typing import Dict, List, Any, Tuple, Optional
import pandas as pd
import numpy as np
from datetime import datetime

# Import our OpenAI client
from openai_client import OpenAIClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class KnownAnswerTester:
    """Tests AI predictions against known reference values."""
    
    def __init__(
        self, 
        openai_client: OpenAIClient,
        reference_data_dir: str = "data/reference",
        output_dir: str = "data/evaluation",
        confidence_calibration: bool = True
    ):
        """
        Initialize the tester.
        
        Args:
            openai_client: OpenAI client for making predictions
            reference_data_dir: Directory with reference data
            output_dir: Directory to save evaluation results
            confidence_calibration: Whether to calibrate confidence ratings
        """
        self.openai_client = openai_client
        self.reference_data_dir = reference_data_dir
        self.output_dir = output_dir
        self.confidence_calibration = confidence_calibration
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Load reference data if exists
        self.reference_data = self._load_reference_data()
        
        # Performance metrics
        self.metrics = {
            "nutrients": {
                "total_predictions": 0,
                "within_10_percent": 0,
                "within_25_percent": 0,
                "within_50_percent": 0,
                "mean_absolute_error": 0.0,
                "mean_absolute_percentage_error": 0.0,
                "confidence_calibration_error": 0.0,
                "nutrients_by_accuracy": {}
            },
            "bioactives": {
                "total_predictions": 0,
                "within_25_percent": 0,
                "within_50_percent": 0,
                "mean_absolute_percentage_error": 0.0,
                "confidence_calibration_error": 0.0
            },
            "mental_health_impacts": {
                "total_predictions": 0,
                "correctly_identified": 0,
                "precision": 0.0,
                "recall": 0.0,
                "confidence_calibration_error": 0.0
            }
        }
    
    def _load_reference_data(self) -> Dict:
        """
        Load reference data for known-answer testing.
        
        Returns:
            Dictionary of reference data by food and nutrient
        """
        reference_data = {}
        
        # Check if reference data directory exists
        if not os.path.isdir(self.reference_data_dir):
            logger.warning(f"Reference data directory {self.reference_data_dir} not found")
            return reference_data
        
        # Load reference data files
        for filename in os.listdir(self.reference_data_dir):
            if filename.endswith(".json"):
                try:
                    file_path = os.path.join(self.reference_data_dir, filename)
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    
                    # Extract food name from filename
                    food_name = filename.replace(".json", "").replace("_", " ")
                    reference_data[food_name] = data
                    
                except Exception as e:
                    logger.error(f"Error loading reference data from {filename}: {e}")
        
        logger.info(f"Loaded reference data for {len(reference_data)} foods")
        return reference_data
    
    def test_nutrient_predictions(
        self,
        food_name: str,
        food_category: str,
        standard_nutrients: Dict,
        target_nutrients: List[str],
        reference_values: Dict,
        scientific_context: Optional[str] = None
    ) -> Dict:
        """
        Test nutrient predictions against known values.
        
        Args:
            food_name: Name of the food
            food_category: Food category
            standard_nutrients: Dictionary of standard nutrients
            target_nutrients: List of nutrients to predict
            reference_values: Dictionary of known reference values
            scientific_context: Optional scientific context
            
        Returns:
            Dictionary with evaluation results
        """
        logger.info(f"Testing nutrient predictions for {food_name}")
        
        # Get predictions from the AI
        predicted = self.openai_client.predict_nutrients(
            food_name=food_name,
            food_category=food_category,
            standard_nutrients=standard_nutrients,
            existing_brain_nutrients={},  # Empty for testing
            target_nutrients=target_nutrients,
            scientific_context=scientific_context
        )
        
        if "error" in predicted:
            logger.error(f"Error making predictions: {predicted['error']}")
            return {"error": predicted["error"], "food_name": food_name}
        
        # Prepare result dictionary
        result = {
            "food_name": food_name,
            "food_category": food_category,
            "timestamp": datetime.now().isoformat(),
            "predictions": {},
            "metrics": {
                "num_nutrients_evaluated": 0,
                "num_within_10_percent": 0,
                "num_within_25_percent": 0,
                "num_within_50_percent": 0,
                "mean_absolute_error": 0.0,
                "mean_absolute_percentage_error": 0.0,
                "confidence_calibration_error": 0.0
            }
        }
        
        # Evaluate nutrient predictions
        nutrient_errors = []
        percentage_errors = []
        confidence_errors = []
        
        for nutrient in target_nutrients:
            # Skip if nutrient not in reference values
            if nutrient not in reference_values:
                continue
            
            # Get predicted and reference values
            if nutrient in predicted:
                predicted_value = predicted[nutrient]
                reference_value = reference_values[nutrient]
                
                # Get confidence rating if available
                confidence_key = f"confidence_{nutrient}"
                confidence = predicted.get(confidence_key, 5)  # Default to 5 if not provided
                
                # Calculate error metrics
                absolute_error = abs(predicted_value - reference_value)
                percentage_error = (absolute_error / reference_value) * 100 if reference_value > 0 else float('inf')
                
                # Determine expected confidence based on error
                expected_confidence = 10
                if percentage_error > 10:
                    expected_confidence = 7
                if percentage_error > 25:
                    expected_confidence = 5
                if percentage_error > 50:
                    expected_confidence = 3
                if percentage_error > 100:
                    expected_confidence = 1
                
                confidence_error = abs(confidence - expected_confidence)
                
                # Track nutrient-specific results
                result["predictions"][nutrient] = {
                    "predicted": predicted_value,
                    "reference": reference_value,
                    "absolute_error": absolute_error,
                    "percentage_error": percentage_error,
                    "predicted_confidence": confidence,
                    "expected_confidence": expected_confidence,
                    "confidence_error": confidence_error
                }
                
                # Update overall metrics
                result["metrics"]["num_nutrients_evaluated"] += 1
                if percentage_error <= 10:
                    result["metrics"]["num_within_10_percent"] += 1
                if percentage_error <= 25:
                    result["metrics"]["num_within_25_percent"] += 1
                if percentage_error <= 50:
                    result["metrics"]["num_within_50_percent"] += 1
                
                nutrient_errors.append(absolute_error)
                percentage_errors.append(percentage_error)
                confidence_errors.append(confidence_error)
                
                # Update global metrics for this nutrient
                if nutrient not in self.metrics["nutrients"]["nutrients_by_accuracy"]:
                    self.metrics["nutrients"]["nutrients_by_accuracy"][nutrient] = {
                        "total": 0,
                        "within_25_percent": 0,
                        "mean_error": 0.0
                    }
                
                nutrient_metrics = self.metrics["nutrients"]["nutrients_by_accuracy"][nutrient]
                nutrient_metrics["total"] += 1
                if percentage_error <= 25:
                    nutrient_metrics["within_25_percent"] += 1
                
                # Update moving average of error
                prev_mean = nutrient_metrics["mean_error"]
                nutrient_metrics["mean_error"] = (prev_mean * (nutrient_metrics["total"] - 1) + percentage_error) / nutrient_metrics["total"]
        
        # Calculate overall metrics
        if nutrient_errors:
            result["metrics"]["mean_absolute_error"] = sum(nutrient_errors) / len(nutrient_errors)
            result["metrics"]["mean_absolute_percentage_error"] = sum(percentage_errors) / len(percentage_errors)
            result["metrics"]["confidence_calibration_error"] = sum(confidence_errors) / len(confidence_errors)
        
        # Update global metrics
        self.metrics["nutrients"]["total_predictions"] += result["metrics"]["num_nutrients_evaluated"]
        self.metrics["nutrients"]["within_10_percent"] += result["metrics"]["num_within_10_percent"]
        self.metrics["nutrients"]["within_25_percent"] += result["metrics"]["num_within_25_percent"]
        self.metrics["nutrients"]["within_50_percent"] += result["metrics"]["num_within_50_percent"]
        
        # Update global moving averages
        if nutrient_errors:
            prev_mae = self.metrics["nutrients"]["mean_absolute_error"]
            prev_mape = self.metrics["nutrients"]["mean_absolute_percentage_error"]
            prev_cce = self.metrics["nutrients"]["confidence_calibration_error"]
            
            total_prev = self.metrics["nutrients"]["total_predictions"] - result["metrics"]["num_nutrients_evaluated"]
            
            if total_prev > 0:
                self.metrics["nutrients"]["mean_absolute_error"] = (
                    (prev_mae * total_prev) + (result["metrics"]["mean_absolute_error"] * result["metrics"]["num_nutrients_evaluated"])
                ) / self.metrics["nutrients"]["total_predictions"]
                
                self.metrics["nutrients"]["mean_absolute_percentage_error"] = (
                    (prev_mape * total_prev) + (result["metrics"]["mean_absolute_percentage_error"] * result["metrics"]["num_nutrients_evaluated"])
                ) / self.metrics["nutrients"]["total_predictions"]
                
                self.metrics["nutrients"]["confidence_calibration_error"] = (
                    (prev_cce * total_prev) + (result["metrics"]["confidence_calibration_error"] * result["metrics"]["num_nutrients_evaluated"])
                ) / self.metrics["nutrients"]["total_predictions"]
            else:
                self.metrics["nutrients"]["mean_absolute_error"] = result["metrics"]["mean_absolute_error"]
                self.metrics["nutrients"]["mean_absolute_percentage_error"] = result["metrics"]["mean_absolute_percentage_error"]
                self.metrics["nutrients"]["confidence_calibration_error"] = result["metrics"]["confidence_calibration_error"]
        
        # Apply confidence calibration if enabled
        if self.confidence_calibration and nutrient_errors:
            result["calibrated_predictions"] = self._calibrate_confidence(result["predictions"])
        
        # Save result to file
        output_file = os.path.join(self.output_dir, f"{food_name.replace(' ', '_')}_nutrient_evaluation.json")
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        logger.info(f"Nutrient evaluation for {food_name} complete - MAPE: {result['metrics']['mean_absolute_percentage_error']:.2f}%")
        return result
    
    def test_mental_health_impacts(
        self,
        food_name: str,
        food_category: str,
        standard_nutrients: Dict,
        brain_nutrients: Dict,
        bioactive_compounds: Dict,
        reference_impacts: List[Dict],
        scientific_context: Optional[str] = None
    ) -> Dict:
        """
        Test mental health impact predictions against reference data.
        
        Args:
            food_name: Name of the food
            food_category: Food category
            standard_nutrients: Dictionary of standard nutrients
            brain_nutrients: Dictionary of brain nutrients
            bioactive_compounds: Dictionary of bioactive compounds
            reference_impacts: List of reference mental health impacts
            scientific_context: Optional scientific context
            
        Returns:
            Dictionary with evaluation results
        """
        logger.info(f"Testing mental health impact predictions for {food_name}")
        
        # Get predictions from the AI
        predicted_impacts = self.openai_client.generate_mental_health_impacts(
            food_name=food_name,
            food_category=food_category,
            standard_nutrients=standard_nutrients,
            brain_nutrients=brain_nutrients,
            bioactive_compounds=bioactive_compounds,
            scientific_context=scientific_context
        )
        
        if isinstance(predicted_impacts, list) and predicted_impacts and "error" in predicted_impacts[0]:
            logger.error(f"Error making predictions: {predicted_impacts[0]['error']}")
            return {"error": predicted_impacts[0]["error"], "food_name": food_name}
        
        # Prepare result dictionary
        result = {
            "food_name": food_name,
            "food_category": food_category,
            "timestamp": datetime.now().isoformat(),
            "predicted_impacts": predicted_impacts,
            "reference_impacts": reference_impacts,
            "metrics": {
                "num_predictions": len(predicted_impacts),
                "num_references": len(reference_impacts),
                "correctly_identified": 0,
                "precision": 0.0,
                "recall": 0.0,
                "confidence_calibration_error": 0.0
            },
            "detailed_evaluation": []
        }
        
        # Extract impact types from predictions and references
        predicted_types = [impact.get("impact_type") for impact in predicted_impacts]
        reference_types = [impact.get("impact_type") for impact in reference_impacts]
        
        # Count correctly identified impacts
        correctly_identified = 0
        for ref_type in reference_types:
            if ref_type in predicted_types:
                correctly_identified += 1
        
        # Calculate precision and recall
        precision = correctly_identified / len(predicted_impacts) if predicted_impacts else 0
        recall = correctly_identified / len(reference_impacts) if reference_impacts else 0
        
        # Update metrics
        result["metrics"]["correctly_identified"] = correctly_identified
        result["metrics"]["precision"] = precision
        result["metrics"]["recall"] = recall
        
        # Evaluate individual impacts
        confidence_errors = []
        
        for pred_impact in predicted_impacts:
            impact_type = pred_impact.get("impact_type")
            impact_eval = {
                "impact_type": impact_type,
                "predicted_confidence": pred_impact.get("confidence", 5),
                "expected_confidence": 5,  # Default
                "correctly_identified": False,
                "mechanism_plausibility": "not_evaluated",
                "citation_quality": "not_evaluated"
            }
            
            # Find matching reference impact
            matching_ref = None
            for ref_impact in reference_impacts:
                if ref_impact.get("impact_type") == impact_type:
                    matching_ref = ref_impact
                    break
            
            if matching_ref:
                impact_eval["correctly_identified"] = True
                impact_eval["expected_confidence"] = matching_ref.get("confidence_threshold", 5)
                
                # Calculate confidence error
                confidence_error = abs(impact_eval["predicted_confidence"] - impact_eval["expected_confidence"])
                confidence_errors.append(confidence_error)
                impact_eval["confidence_error"] = confidence_error
            
            result["detailed_evaluation"].append(impact_eval)
        
        # Calculate overall confidence calibration error
        if confidence_errors:
            result["metrics"]["confidence_calibration_error"] = sum(confidence_errors) / len(confidence_errors)
        
        # Update global metrics
        self.metrics["mental_health_impacts"]["total_predictions"] += len(predicted_impacts)
        self.metrics["mental_health_impacts"]["correctly_identified"] += correctly_identified
        
        # Update moving averages
        prev_precision = self.metrics["mental_health_impacts"]["precision"]
        prev_recall = self.metrics["mental_health_impacts"]["recall"]
        prev_cce = self.metrics["mental_health_impacts"]["confidence_calibration_error"]
        
        total_prev_foods = len(self.metrics["mental_health_impacts"]) - 1 if "precision" in self.metrics["mental_health_impacts"] else 0
        
        if total_prev_foods > 0:
            self.metrics["mental_health_impacts"]["precision"] = (prev_precision * total_prev_foods + precision) / (total_prev_foods + 1)
            self.metrics["mental_health_impacts"]["recall"] = (prev_recall * total_prev_foods + recall) / (total_prev_foods + 1)
            
            if confidence_errors:
                total_prev_impacts = self.metrics["mental_health_impacts"]["total_predictions"] - len(predicted_impacts)
                if total_prev_impacts > 0:
                    self.metrics["mental_health_impacts"]["confidence_calibration_error"] = (
                        (prev_cce * total_prev_impacts) + (result["metrics"]["confidence_calibration_error"] * len(confidence_errors))
                    ) / (total_prev_impacts + len(confidence_errors))
                else:
                    self.metrics["mental_health_impacts"]["confidence_calibration_error"] = result["metrics"]["confidence_calibration_error"]
        else:
            self.metrics["mental_health_impacts"]["precision"] = precision
            self.metrics["mental_health_impacts"]["recall"] = recall
            if confidence_errors:
                self.metrics["mental_health_impacts"]["confidence_calibration_error"] = result["metrics"]["confidence_calibration_error"]
        
        # Save result to file
        output_file = os.path.join(self.output_dir, f"{food_name.replace(' ', '_')}_impact_evaluation.json")
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        logger.info(f"Mental health impact evaluation for {food_name} complete - Precision: {precision:.2f}, Recall: {recall:.2f}")
        return result
    
    def _calibrate_confidence(self, predictions: Dict) -> Dict:
        """
        Calibrate confidence ratings based on prediction accuracy.
        
        Args:
            predictions: Dictionary of predictions with errors
            
        Returns:
            Dictionary with calibrated confidence ratings
        """
        calibrated = {}
        
        for nutrient, pred_data in predictions.items():
            percentage_error = pred_data.get("percentage_error", 0)
            predicted_confidence = pred_data.get("predicted_confidence", 5)
            
            # Calculate calibrated confidence based on error
            calibrated_confidence = predicted_confidence
            
            # Simple calibration logic - adjust based on error
            if percentage_error > 100 and predicted_confidence > 3:
                calibrated_confidence = 3
            elif percentage_error > 50 and predicted_confidence > 5:
                calibrated_confidence = 5
            elif percentage_error > 25 and predicted_confidence > 7:
                calibrated_confidence = 7
            elif percentage_error < 10 and predicted_confidence < 8:
                calibrated_confidence = 8
            
            # Copy prediction data with calibrated confidence
            calibrated[nutrient] = pred_data.copy()
            calibrated[nutrient]["calibrated_confidence"] = calibrated_confidence
        
        return calibrated
    
    def get_metrics_summary(self) -> Dict:
        """
        Get summary of evaluation metrics.
        
        Returns:
            Dictionary with evaluation metrics summary
        """
        # Calculate summary metrics
        nutrients_summary = self.metrics["nutrients"]
        if nutrients_summary["total_predictions"] > 0:
            nutrients_summary["percent_within_10"] = (nutrients_summary["within_10_percent"] / nutrients_summary["total_predictions"]) * 100
            nutrients_summary["percent_within_25"] = (nutrients_summary["within_25_percent"] / nutrients_summary["total_predictions"]) * 100
            nutrients_summary["percent_within_50"] = (nutrients_summary["within_50_percent"] / nutrients_summary["total_predictions"]) * 100
        
        # Calculate accuracy by nutrient type
        nutrient_accuracy = {}
        for nutrient, metrics in nutrients_summary["nutrients_by_accuracy"].items():
            if metrics["total"] > 0:
                accuracy = (metrics["within_25_percent"] / metrics["total"]) * 100
                nutrient_accuracy[nutrient] = {
                    "accuracy_within_25_percent": accuracy,
                    "mean_error_percent": metrics["mean_error"],
                    "sample_size": metrics["total"]
                }
        
        # Sort nutrients by accuracy
        sorted_nutrients = sorted(
            nutrient_accuracy.items(),
            key=lambda x: x[1]["accuracy_within_25_percent"],
            reverse=True
        )
        
        return {
            "timestamp": datetime.now().isoformat(),
            "nutrients": {
                "total_predictions": nutrients_summary["total_predictions"],
                "percent_within_10": nutrients_summary.get("percent_within_10", 0),
                "percent_within_25": nutrients_summary.get("percent_within_25", 0),
                "percent_within_50": nutrients_summary.get("percent_within_50", 0),
                "mean_absolute_percentage_error": nutrients_summary["mean_absolute_percentage_error"],
                "confidence_calibration_error": nutrients_summary["confidence_calibration_error"],
                "nutrient_types_by_accuracy": {k: v for k, v in sorted_nutrients}
            },
            "mental_health_impacts": {
                "total_predictions": self.metrics["mental_health_impacts"]["total_predictions"],
                "correctly_identified": self.metrics["mental_health_impacts"]["correctly_identified"],
                "precision": self.metrics["mental_health_impacts"]["precision"],
                "recall": self.metrics["mental_health_impacts"]["recall"],
                "confidence_calibration_error": self.metrics["mental_health_impacts"]["confidence_calibration_error"]
            }
        }
    
    def run_test_suite(self, foods: List[Dict]) -> Dict:
        """
        Run test suite on a list of foods.
        
        Args:
            foods: List of food dictionaries with reference data
            
        Returns:
            Dictionary with test results summary
        """
        logger.info(f"Running test suite on {len(foods)} foods")
        
        for food in foods:
            food_name = food["name"]
            food_category = food["category"]
            standard_nutrients = food.get("standard_nutrients", {})
            brain_nutrients = food.get("brain_nutrients", {})
            bioactive_compounds = food.get("bioactive_compounds", {})
            
            # Get reference values if available
            reference_values = {}
            if food_name in self.reference_data:
                reference_data = self.reference_data[food_name]
                
                # Extract nutrient reference values
                if "brain_nutrients" in reference_data:
                    reference_values.update(reference_data["brain_nutrients"])
                
                # Extract bioactive compound reference values
                if "bioactive_compounds" in reference_data:
                    bioactive_refs = reference_data["bioactive_compounds"]
                
                # Extract mental health impact reference values
                reference_impacts = reference_data.get("mental_health_impacts", [])
            else:
                # Use values from the food data as reference
                if "brain_nutrients" in food:
                    reference_values.update(food["brain_nutrients"])
                reference_impacts = food.get("mental_health_impacts", [])
            
            # Determine which nutrients to predict
            # For testing, we'll "predict" nutrients that are already in the reference data
            target_nutrients = list(reference_values.keys())
            
            if target_nutrients:
                # Test nutrient predictions
                self.test_nutrient_predictions(
                    food_name=food_name,
                    food_category=food_category,
                    standard_nutrients=standard_nutrients,
                    target_nutrients=target_nutrients,
                    reference_values=reference_values
                )
            
            if reference_impacts:
                # Test mental health impact predictions
                self.test_mental_health_impacts(
                    food_name=food_name,
                    food_category=food_category,
                    standard_nutrients=standard_nutrients,
                    brain_nutrients=brain_nutrients,
                    bioactive_compounds=bioactive_compounds,
                    reference_impacts=reference_impacts
                )
        
        # Get metrics summary
        summary = self.get_metrics_summary()
        
        # Save summary to file
        output_file = os.path.join(self.output_dir, f"evaluation_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(output_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Test suite complete - Summary saved to {output_file}")
        return summary


def main():
    """Main function to execute the evaluation."""
    parser = argparse.ArgumentParser(description="Evaluate AI-generated nutritional psychiatry data")
    parser.add_argument("--api-key", help="OpenAI API key")
    parser.add_argument("--reference-dir", default="data/reference", help="Directory with reference data")
    parser.add_argument("--output-dir", default="data/evaluation", help="Directory to save evaluation results")
    parser.add_argument("--food-list", default="data/test_foods.json", help="JSON file with test foods")
    parser.add_argument("--no-calibration", action="store_true", help="Disable confidence calibration")
    
    args = parser.parse_args()
    
    try:
        # Initialize OpenAI client
        openai_client = OpenAIClient(api_key=args.api_key)
        
        # Initialize tester
        tester = KnownAnswerTester(
            openai_client=openai_client,
            reference_data_dir=args.reference_dir,
            output_dir=args.output_dir,
            confidence_calibration=not args.no_calibration
        )
        
        # Load test foods
        if os.path.exists(args.food_list):
            with open(args.food_list, 'r') as f:
                test_foods = json.load(f)
        else:
            logger.error(f"Food list file {args.food_list} not found")
            test_foods = []
        
        # Run test suite
        if test_foods:
            tester.run_test_suite(test_foods)
        else:
            logger.error("No test foods available")
        
    except Exception as e:
        logger.error(f"Error during evaluation: {e}")
        raise


if __name__ == "__main__":
    main()