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

import argparse
from datetime import datetime
from typing import Dict, List, Optional
import sys

# Import project models
from schema.food_data import (
    FoodData, Omega3, EvaluationMetrics, FoodEvaluation
)

# Import project utilities
from utils.logging_utils import setup_logging
from utils.db_utils import PostgresClient

# Import project constants
from constants.food_data_constants import (
    BRAIN_NUTRIENTS_TO_PREDICT,
    DEFAULT_CONFIDENCE_RATINGS
)

# Import AI client
from scripts.ai.openai_api import OpenAIAPI

# Initialize logger
logger = setup_logging(__name__)

# Evaluation constants
EVALUATION_THRESHOLDS = {
    "WITHIN_10_PERCENT": 10,
    "WITHIN_25_PERCENT": 25,
    "WITHIN_50_PERCENT": 50,
    "HIGH_CONFIDENCE_THRESHOLD": 7,
    "MEDIUM_CONFIDENCE_THRESHOLD": 5,
    "LOW_CONFIDENCE_THRESHOLD": 3
}

class KnownAnswerTester:
    """Tests AI predictions against known reference values."""
    
    def __init__(
        self, 
        openai_client: OpenAIAPI,
        db_client: Optional[PostgresClient] = None,
        confidence_calibration: bool = True,
        batch_size: int = 50
    ):
        """
        Initialize the tester.
        
        Args:
            openai_client: OpenAI client for making predictions
            db_client: Optional database client (created if not provided)
            confidence_calibration: Whether to calibrate confidence ratings
            batch_size: Number of foods to process in each batch
        """
        self.openai_client = openai_client
        self.db_client = db_client or PostgresClient()
        self.confidence_calibration = confidence_calibration
        self.batch_size = batch_size
        
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
    
    def _load_reference_data(self, food_ids: Optional[List[str]] = None) -> Dict[str, Dict]:
        """
        Load reference data for known-answer testing from database.
        
        Args:
            food_ids: Optional list of food IDs to fetch (fetches all reference data if None)
            
        Returns:
            Dictionary of reference data by food name
        """
        reference_data = {}
        
        try:
            if food_ids:
                # Fetch specific reference foods
                placeholders = ','.join(['%s'] * len(food_ids))
                query = f"""
                SELECT food_id, name, food_data 
                FROM foods
                WHERE food_id IN ({placeholders}) AND source = 'reference'
                """
                results = self.db_client.execute_query(query, food_ids)
            else:
                # Fetch all reference foods
                query = """
                SELECT food_id, name, food_data 
                FROM foods
                WHERE source = 'reference'
                """
                results = self.db_client.execute_query(query)
            
            # Process results
            for result in results:
                food_name = result['name']
                reference_data[food_name] = result['food_data']
            
            logger.info(f"Loaded reference data for {len(reference_data)} foods from database")
            
        except Exception as e:
            logger.error(f"Error loading reference data: {e}")
        
        return reference_data
    
    def _get_reference_values(self, food_name: str) -> Dict:
        """
        Get reference values for a specific food by name.
        
        Args:
            food_name: Food name to lookup
            
        Returns:
            Dictionary of reference data or empty dict if not found
        """
        try:
            query = """
            SELECT food_data 
            FROM foods
            WHERE name ILIKE %s AND source = 'reference'
            LIMIT 1
            """
            results = self.db_client.execute_query(query, (f"%{food_name}%",))
            
            if results:
                return results[0]['food_data']
            else:
                logger.warning(f"No reference data found for {food_name}")
                return {}
                
        except Exception as e:
            logger.error(f"Error fetching reference values for {food_name}: {e}")
            return {}
    
    def _evaluate_numeric_prediction(
        self, 
        predicted_value: float, 
        reference_value: float, 
        predicted_confidence: int
    ) -> Dict:
        """
        Evaluate a numeric prediction against a reference value.
        
        Args:
            predicted_value: Predicted numeric value
            reference_value: Reference (known) value
            predicted_confidence: Confidence rating (1-10)
            
        Returns:
            Dictionary with evaluation metrics
        """
        # Calculate error metrics
        absolute_error = abs(predicted_value - reference_value)
        percent_error = (absolute_error / reference_value) * 100 if reference_value > 0 else float('inf')
        
        # Determine expected confidence based on error
        expected_confidence = 10
        if percent_error > EVALUATION_THRESHOLDS["WITHIN_10_PERCENT"]:
            expected_confidence = EVALUATION_THRESHOLDS["HIGH_CONFIDENCE_THRESHOLD"]
        if percent_error > EVALUATION_THRESHOLDS["WITHIN_25_PERCENT"]:
            expected_confidence = EVALUATION_THRESHOLDS["MEDIUM_CONFIDENCE_THRESHOLD"]
        if percent_error > EVALUATION_THRESHOLDS["WITHIN_50_PERCENT"]:
            expected_confidence = EVALUATION_THRESHOLDS["LOW_CONFIDENCE_THRESHOLD"]
        if percent_error > 100:
            expected_confidence = 1
        
        confidence_error = abs(predicted_confidence - expected_confidence)
        
        # Create evaluation result
        result = {
            "predicted": predicted_value,
            "reference": reference_value,
            "absolute_error": absolute_error,
            "percentage_error": percent_error,
            "predicted_confidence": predicted_confidence,
            "expected_confidence": expected_confidence,
            "confidence_error": confidence_error,
            "within_10_percent": percent_error <= EVALUATION_THRESHOLDS["WITHIN_10_PERCENT"],
            "within_25_percent": percent_error <= EVALUATION_THRESHOLDS["WITHIN_25_PERCENT"],
            "within_50_percent": percent_error <= EVALUATION_THRESHOLDS["WITHIN_50_PERCENT"]
        }
        
        return result
    
    def _update_nutrient_metrics(self, nutrient: str, evaluation: Dict):
        """
        Update metrics for a specific nutrient.
        
        Args:
            nutrient: Nutrient name
            evaluation: Evaluation result from _evaluate_numeric_prediction
        """
        # Initialize nutrient in metrics if needed
        if nutrient not in self.metrics["nutrients"]["nutrients_by_accuracy"]:
            self.metrics["nutrients"]["nutrients_by_accuracy"][nutrient] = {
                "total": 0,
                "within_10_percent": 0,
                "within_25_percent": 0,
                "within_50_percent": 0,
                "sum_percent_error": 0.0,
                "sum_confidence_error": 0.0
            }
        
        nutrient_metrics = self.metrics["nutrients"]["nutrients_by_accuracy"][nutrient]
        
        # Update counters
        nutrient_metrics["total"] += 1
        if evaluation["within_10_percent"]:
            nutrient_metrics["within_10_percent"] += 1
        if evaluation["within_25_percent"]:
            nutrient_metrics["within_25_percent"] += 1
        if evaluation["within_50_percent"]:
            nutrient_metrics["within_50_percent"] += 1
        
        # Update sums for calculating means
        nutrient_metrics["sum_percent_error"] += evaluation["percentage_error"]
        nutrient_metrics["sum_confidence_error"] += evaluation["confidence_error"]
    
    def _update_global_metrics(self, evaluations: Dict, eval_type: str = "nutrients"):
        """
        Update global metrics based on a set of evaluations.
        
        Args:
            evaluations: Dictionary of evaluation results
            eval_type: Type of evaluation (nutrients, bioactives, mental_health_impacts)
        """
        metrics = self.metrics[eval_type]
        
        # Count total evaluations
        num_evaluations = sum(1 for eval_dict in evaluations.values() 
                              if isinstance(eval_dict, dict) and "percentage_error" in eval_dict)
        
        if num_evaluations == 0:
            return
        
        # Update counters
        metrics["total_predictions"] += num_evaluations
        
        # Calculate sums for within thresholds
        if eval_type == "nutrients" or eval_type == "bioactives":
            metrics["within_10_percent"] += sum(1 for eval_dict in evaluations.values()
                                              if isinstance(eval_dict, dict) and 
                                              eval_dict.get("within_10_percent", False))
            
            metrics["within_25_percent"] += sum(1 for eval_dict in evaluations.values()
                                              if isinstance(eval_dict, dict) and 
                                              eval_dict.get("within_25_percent", False))
            
            metrics["within_50_percent"] += sum(1 for eval_dict in evaluations.values()
                                              if isinstance(eval_dict, dict) and 
                                              eval_dict.get("within_50_percent", False))
        
        # Calculate error metrics
        sum_abs_error = sum(eval_dict.get("absolute_error", 0) for eval_dict in evaluations.values()
                            if isinstance(eval_dict, dict) and "absolute_error" in eval_dict)
        
        sum_percent_error = sum(eval_dict.get("percentage_error", 0) for eval_dict in evaluations.values()
                               if isinstance(eval_dict, dict) and "percentage_error" in eval_dict)
        
        sum_confidence_error = sum(eval_dict.get("confidence_error", 0) for eval_dict in evaluations.values()
                                  if isinstance(eval_dict, dict) and "confidence_error" in eval_dict)
        
        # Update means using weighted averaging with previous means
        prev_count = metrics["total_predictions"] - num_evaluations
        
        if prev_count > 0:
            metrics["mean_absolute_error"] = (
                (metrics["mean_absolute_error"] * prev_count) + (sum_abs_error / num_evaluations)
            ) / metrics["total_predictions"]
            
            metrics["mean_absolute_percentage_error"] = (
                (metrics["mean_absolute_percentage_error"] * prev_count) + (sum_percent_error / num_evaluations)
            ) / metrics["total_predictions"]
            
            metrics["confidence_calibration_error"] = (
                (metrics["confidence_calibration_error"] * prev_count) + (sum_confidence_error / num_evaluations)
            ) / metrics["total_predictions"]
        else:
            metrics["mean_absolute_error"] = sum_abs_error / num_evaluations
            metrics["mean_absolute_percentage_error"] = sum_percent_error / num_evaluations
            metrics["confidence_calibration_error"] = sum_confidence_error / num_evaluations
    
    def _calibrate_confidence(self, evaluations: Dict[str, Dict]) -> Dict[str, Dict]:
        calibrated = {}
        
        for key, eval_data in evaluations.items():
            if not isinstance(eval_data, dict) or "percentage_error" not in eval_data:
                continue
                
            percentage_error = eval_data.get("percentage_error", 0)
            predicted_confidence = eval_data.get("predicted_confidence", 5)
            
            # Calculate calibrated confidence based on error
            calibrated_confidence = predicted_confidence
            
            # Simple calibration logic - adjust based on error
            if percentage_error > 100 and predicted_confidence > 3:
                calibrated_confidence = 3
            elif percentage_error > EVALUATION_THRESHOLDS["WITHIN_50_PERCENT"] and predicted_confidence > 5:
                calibrated_confidence = 5
            elif percentage_error > EVALUATION_THRESHOLDS["WITHIN_25_PERCENT"] and predicted_confidence > 7:
                calibrated_confidence = 7
            elif percentage_error < EVALUATION_THRESHOLDS["WITHIN_10_PERCENT"] and predicted_confidence < 8:
                calibrated_confidence = 8
            
            # Copy evaluation data with calibrated confidence
            calibrated[key] = eval_data.copy()
            calibrated[key]["calibrated_confidence"] = calibrated_confidence
        
        return calibrated
    
    def _save_evaluation_to_db(
        self, 
        food_id: str, 
        evaluation_type: str, 
        evaluation_data: Dict, 
        test_run_id: str
    ) -> bool:
        """
        Save evaluation results to database.
        
        Args:
            food_id: Food ID
            evaluation_type: Type of evaluation
            evaluation_data: Evaluation data
            test_run_id: Test run identifier
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Create FoodEvaluation model instance
            evaluation = FoodEvaluation(
                food_id=food_id,
                test_run_id=test_run_id,
                timestamp=datetime.now().isoformat(),
                evaluation_type=evaluation_type,
                evaluation_data=evaluation_data
            )
            
            query = """
            INSERT INTO food_evaluations 
                (food_id, test_run_id, timestamp, evaluation_type, evaluation_data)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (food_id, test_run_id, evaluation_type) 
            DO UPDATE SET 
                timestamp = EXCLUDED.timestamp,
                evaluation_data = EXCLUDED.evaluation_data
            RETURNING id
            """
            
            params = (
                evaluation.food_id,
                evaluation.test_run_id,
                evaluation.timestamp,
                evaluation.evaluation_type,
                evaluation.evaluation_data
            )
            
            result = self.db_client.execute_query(query, params)
            return bool(result)
            
        except Exception as e:
            logger.error(f"Error saving evaluation for {food_id}: {e}")
            return False
    
    def _save_metrics_to_db(self, test_run_id: str) -> bool:
        """
        Save current metrics to database.
        
        Args:
            test_run_id: Test run identifier
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Save each metric type separately
            for metric_type, metric_data in self.metrics.items():
                # Create EvaluationMetrics model instance
                evaluation_metric = EvaluationMetrics(
                    test_run_id=test_run_id,
                    timestamp=datetime.now().isoformat(),
                    metrics_type=metric_type,
                    metrics_data=metric_data
                )
                
                query = """
                INSERT INTO evaluation_metrics 
                    (test_run_id, timestamp, metrics_type, metrics_data)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """
                
                params = (
                    evaluation_metric.test_run_id,
                    evaluation_metric.timestamp,
                    evaluation_metric.metrics_type,
                    evaluation_metric.metrics_data
                )
                
                self.db_client.execute_query(query, params)
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving metrics: {e}")
            return False
    
    def test_nutrient_predictions(
        self,
        food: FoodData,
        target_nutrients: List[str],
        reference_values: Dict,
        test_run_id: str,
        scientific_context: Optional[str] = None
    ) -> Dict:
        """
        Test nutrient predictions against known values.
        
        Args:
            food: FoodData object
            target_nutrients: List of nutrients to predict
            reference_values: Dictionary of known reference values
            test_run_id: Test run identifier
            scientific_context: Optional scientific context
            
        Returns:
            Dictionary with evaluation results
        """
        food_id = food.food_id
        food_name = food.name
        food_category = food.category
        
        logger.info(f"Testing nutrient predictions for {food_name}")
        
        # Convert model to dict for the OpenAI API
        standard_nutrients = {}
        if food.standard_nutrients:
            standard_nutrients = {k: v for k, v in food.standard_nutrients.__dict__.items() 
                                if not k.startswith('_') and v is not None}
        
        # Get predictions from the AI
        try:
            predicted = self.openai_client.predict_nutrients(
                food_name=food_name,
                food_category=food_category,
                standard_nutrients=standard_nutrients,
                existing_brain_nutrients={},  # Empty for testing
                target_nutrients=target_nutrients,
                food_id=None,  # Don't save to database during testing
                scientific_context=scientific_context
            )
            
            if isinstance(predicted, dict) and "error" in predicted:
                logger.error(f"Error making predictions: {predicted['error']}")
                return {"error": predicted["error"], "food_id": food_id, "food_name": food_name}
        except Exception as e:
            logger.error(f"Exception during prediction: {e}")
            return {"error": str(e), "food_id": food_id, "food_name": food_name}
        
        # Prepare result dictionary
        result = {
            "food_id": food_id,
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
        
        # Evaluate each nutrient prediction
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
                confidence = predicted.get(confidence_key, DEFAULT_CONFIDENCE_RATINGS.get("ai_generated", 5))
                
                # Evaluate prediction
                evaluation = self._evaluate_numeric_prediction(
                    predicted_value=predicted_value,
                    reference_value=reference_value,
                    predicted_confidence=confidence
                )
                
                # Store evaluation
                result["predictions"][nutrient] = evaluation
                
                # Update nutrient-specific metrics
                self._update_nutrient_metrics(nutrient, evaluation)
                
                # Update result metrics
                result["metrics"]["num_nutrients_evaluated"] += 1
                if evaluation["within_10_percent"]:
                    result["metrics"]["num_within_10_percent"] += 1
                if evaluation["within_25_percent"]:
                    result["metrics"]["num_within_25_percent"] += 1
                if evaluation["within_50_percent"]:
                    result["metrics"]["num_within_50_percent"] += 1
        
        # Calculate overall metrics for this food
        if result["metrics"]["num_nutrients_evaluated"] > 0:
            # Calculate means
            total_abs_error = sum(eval_dict.get("absolute_error", 0) 
                                 for eval_dict in result["predictions"].values())
            
            total_percent_error = sum(eval_dict.get("percentage_error", 0) 
                                     for eval_dict in result["predictions"].values())
            
            total_confidence_error = sum(eval_dict.get("confidence_error", 0) 
                                        for eval_dict in result["predictions"].values())
            
            count = result["metrics"]["num_nutrients_evaluated"]
            
            result["metrics"]["mean_absolute_error"] = total_abs_error / count
            result["metrics"]["mean_absolute_percentage_error"] = total_percent_error / count
            result["metrics"]["confidence_calibration_error"] = total_confidence_error / count
        
        # Update global metrics
        self._update_global_metrics(result["predictions"], "nutrients")
        
        # Apply confidence calibration if enabled
        if self.confidence_calibration and result["metrics"]["num_nutrients_evaluated"] > 0:
            result["calibrated_predictions"] = self._calibrate_confidence(result["predictions"])
        
        # Save result to database
        self._save_evaluation_to_db(
            food_id=food_id,
            evaluation_type="nutrient_predictions",
            evaluation_data=result,
            test_run_id=test_run_id
        )
        
        logger.info(f"Nutrient evaluation for {food_name} complete - MAPE: "
                    f"{result['metrics']['mean_absolute_percentage_error']:.2f}%")
        return result
    
    def test_mental_health_impacts(
        self,
        food: FoodData,
        reference_impacts: List[Dict],
        test_run_id: str,
        scientific_context: Optional[str] = None
    ) -> Dict:
        """
        Test mental health impact predictions against reference data.
        
        Args:
            food: FoodData object
            reference_impacts: List of reference mental health impacts
            test_run_id: Test run identifier
            scientific_context: Optional scientific context
            
        Returns:
            Dictionary with evaluation results
        """
        food_id = food.food_id
        food_name = food.name
        food_category = food.category
        
        logger.info(f"Testing mental health impact predictions for {food_name}")
        
        # Convert models to dicts for the OpenAI API
        standard_nutrients = {}
        if food.standard_nutrients:
            standard_nutrients = {k: v for k, v in food.standard_nutrients.__dict__.items() 
                                if not k.startswith('_') and v is not None}
        
        brain_nutrients = {}
        if food.brain_nutrients:
            # Handle nested Omega3 object
            brain_nutrients = {k: v for k, v in food.brain_nutrients.__dict__.items() 
                             if not k.startswith('_') and v is not None 
                             and not isinstance(v, Omega3)}
            
            # Add omega3 if present
            if food.brain_nutrients.omega3:
                omega3_dict = {k: v for k, v in food.brain_nutrients.omega3.__dict__.items() 
                              if not k.startswith('_') and v is not None}
                brain_nutrients['omega3'] = omega3_dict
        
        bioactive_compounds = {}
        if food.bioactive_compounds:
            bioactive_compounds = {k: v for k, v in food.bioactive_compounds.__dict__.items() 
                                 if not k.startswith('_') and v is not None}
        
        # Get predictions from the AI
        predicted_impacts = self.openai_client.predict_mental_health_impacts(
            food_name=food_name,
            food_category=food_category,
            standard_nutrients=standard_nutrients,
            brain_nutrients=brain_nutrients,
            bioactive_compounds=bioactive_compounds,
            food_id=None,  # Don't save to database during testing
            scientific_context=scientific_context
        )
        
        if isinstance(predicted_impacts, list) and predicted_impacts and "error" in predicted_impacts[0]:
            logger.error(f"Error making predictions: {predicted_impacts[0]['error']}")
            return {"error": predicted_impacts[0]['error'], "food_id": food_id, "food_name": food_name}

        # Prepare result dictionary
        result = {
            "food_id": food_id,
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
        predicted_impact_types = {impact.get("impact_type") for impact in predicted_impacts}
        reference_impact_types = {impact.get("impact_type") for impact in reference_impacts}
        
        # Count correctly identified impacts
        correctly_identified = len(predicted_impact_types.intersection(reference_impact_types))
        
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
                "predicted_confidence": pred_impact.get("confidence", DEFAULT_CONFIDENCE_RATINGS.get("ai_generated", 5)),
                "expected_confidence": DEFAULT_CONFIDENCE_RATINGS.get("ai_generated", 5),  # Default
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
                impact_eval["expected_confidence"] = matching_ref.get("confidence_threshold", DEFAULT_CONFIDENCE_RATINGS.get("literature", 7))
                
                # Calculate confidence error
                confidence_error = abs(impact_eval["predicted_confidence"] - impact_eval["expected_confidence"])
                confidence_errors.append(confidence_error)
                impact_eval["confidence_error"] = confidence_error
            
            result["detailed_evaluation"].append(impact_eval)
        
        # Calculate overall confidence calibration error
        if confidence_errors:
            result["metrics"]["confidence_calibration_error"] = sum(confidence_errors) / len(confidence_errors)
        
        # Update global mental health metrics
        self.metrics["mental_health_impacts"]["total_predictions"] += len(predicted_impacts)
        self.metrics["mental_health_impacts"]["correctly_identified"] += correctly_identified
        
        # Update moving averages for precision, recall, and confidence error
        prev_count = self.metrics["mental_health_impacts"]["total_predictions"] - len(predicted_impacts)
        
        if prev_count > 0:
            # Update precision
            prev_precision = self.metrics["mental_health_impacts"]["precision"]
            self.metrics["mental_health_impacts"]["precision"] = (
                (prev_precision * prev_count) + (precision * len(predicted_impacts))
            ) / self.metrics["mental_health_impacts"]["total_predictions"]
            
            # Update recall
            prev_recall = self.metrics["mental_health_impacts"]["recall"]
            self.metrics["mental_health_impacts"]["recall"] = (
                (prev_recall * prev_count) + (recall * len(predicted_impacts))
            ) / self.metrics["mental_health_impacts"]["total_predictions"]
            
            # Update confidence calibration error
            if confidence_errors:
                prev_cce = self.metrics["mental_health_impacts"]["confidence_calibration_error"]
                self.metrics["mental_health_impacts"]["confidence_calibration_error"] = (
                    (prev_cce * prev_count) + (result["metrics"]["confidence_calibration_error"] * len(confidence_errors))
                ) / (prev_count + len(confidence_errors))
        else:
            self.metrics["mental_health_impacts"]["precision"] = precision
            self.metrics["mental_health_impacts"]["recall"] = recall
            if confidence_errors:
                self.metrics["mental_health_impacts"]["confidence_calibration_error"] = result["metrics"]["confidence_calibration_error"]
        
        # Save result to database
        self._save_evaluation_to_db(
            food_id=food_id,
            evaluation_type="mental_health_impacts",
            evaluation_data=result,
            test_run_id=test_run_id
        )
        
        logger.info(f"Mental health impact evaluation for {food_name} complete - "
                   f"Precision: {precision:.2f}, Recall: {recall:.2f}")
        return result
    
    def get_metrics_summary(self) -> Dict:
        """
        Get summary of evaluation metrics.
        
        Returns:
            Dictionary with evaluation metrics summary
        """
        # Calculate summary metrics for nutrients
        nutrients_summary = self.metrics["nutrients"]
        if nutrients_summary["total_predictions"] > 0:
            nutrients_summary["percent_within_10"] = (
                nutrients_summary["within_10_percent"] / nutrients_summary["total_predictions"]) * 100
            nutrients_summary["percent_within_25"] = (
                nutrients_summary["within_25_percent"] / nutrients_summary["total_predictions"]) * 100
            nutrients_summary["percent_within_50"] = (
                nutrients_summary["within_50_percent"] / nutrients_summary["total_predictions"]) * 100
        
        # Calculate accuracy by nutrient type
        nutrient_accuracy = {}
        for nutrient, metrics in nutrients_summary["nutrients_by_accuracy"].items():
            if metrics["total"] > 0:
                within_25_percent = metrics.get("within_25_percent", 0)
                accuracy = (within_25_percent / metrics["total"]) * 100
                mean_error = metrics.get("sum_percent_error", 0) / metrics["total"]
                
                nutrient_accuracy[nutrient] = {
                    "accuracy_within_25_percent": accuracy,
                    "mean_error_percent": mean_error,
                    "sample_size": metrics["total"]
                }
        
        # Sort nutrients by accuracy
        sorted_nutrients = sorted(
            nutrient_accuracy.items(),
            key=lambda x: x[1]["accuracy_within_25_percent"],
            reverse=True
        )
        
        # Build summary dictionary
        summary = {
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
        
        return summary
    
    def _get_test_foods(self, batch_size: Optional[int] = None, offset: int = 0) -> List[Dict]:
        """
        Get a batch of foods to test from database.
        
        Args:
            batch_size: Optional batch size (defaults to self.batch_size)
            offset: Offset for pagination
            
        Returns:
            List of food data dictionaries
        """
        limit = batch_size or self.batch_size
        
        try:
            query = """
            SELECT food_id, name, food_data
            FROM foods
            WHERE source NOT IN ('reference', 'literature')
            ORDER BY food_id
            LIMIT %s OFFSET %s
            """
            
            results = self.db_client.execute_query(query, (limit, offset))
            return results
            
        except Exception as e:
            logger.error(f"Error fetching foods to test: {e}")
            return []
    
    def run_test_suite(self, food_ids: Optional[List[str]] = None) -> Dict:
        """
        Run test suite on a list of foods or all foods in database.
        
        Args:
            food_ids: Optional list of food IDs to test (tests all if None)
            
        Returns:
            Dictionary with test results summary
        """
        # Generate a unique test run ID
        test_run_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        logger.info(f"Starting test suite with ID: {test_run_id}")
        
        foods_tested = 0
        successful_tests = 0
        failed_tests = 0
        
        try:
            # Load reference data
            reference_data = self._load_reference_data()
            
            if not reference_data:
                logger.error("No reference data found. Cannot proceed with testing.")
                return {
                    "test_run_id": test_run_id,
                    "success": False,
                    "error": "No reference data found"
                }
            
            if food_ids:
                # Test specific foods
                for food_id in food_ids:
                    # Fetch food data
                    query = "SELECT food_data FROM foods WHERE food_id = %s"
                    results = self.db_client.execute_query(query, (food_id,))
                    
                    if not results:
                        logger.warning(f"Food {food_id} not found in database")
                        failed_tests += 1
                        continue
                    
                    food_data = results[0]["food_data"]
                    food = FoodData.from_dict(food_data)
                    
                    # Get reference values
                    reference_values = self._get_reference_values(food.name)
                    
                    # Test nutrient predictions
                    if reference_values:
                        target_nutrients = [key for key in reference_values.keys() 
                                          if key in BRAIN_NUTRIENTS_TO_PREDICT]
                        
                        if target_nutrients:
                            result = self.test_nutrient_predictions(
                                food=food,
                                target_nutrients=target_nutrients,
                                reference_values=reference_values,
                                test_run_id=test_run_id
                            )
                            
                            if "error" not in result:
                                successful_tests += 1
                            else:
                                failed_tests += 1
                    
                    # Test mental health impacts
                    reference_impacts = reference_values.get("mental_health_impacts", [])
                    if reference_impacts:
                        result = self.test_mental_health_impacts(
                            food=food,
                            reference_impacts=reference_impacts,
                            test_run_id=test_run_id
                        )
                        
                        if "error" not in result:
                            successful_tests += 1
                        else:
                            failed_tests += 1
                    
                    foods_tested += 1
            else:
                # Test all foods in batches
                offset = 0
                while True:
                    # Get batch of foods to test
                    batch = self._get_test_foods(self.batch_size, offset)
                    
                    if not batch:
                        logger.info("No more foods to test")
                        break
                    
                    for item in batch:
                        try:
                            food_data = item["food_data"]
                            food = FoodData.from_dict(food_data)
                            
                            # Get reference values
                            reference_values = self._get_reference_values(food.name)
                            
                            # Test nutrient predictions
                            if reference_values:
                                target_nutrients = [key for key in reference_values.keys() 
                                                  if key in BRAIN_NUTRIENTS_TO_PREDICT]
                                
                                if target_nutrients:
                                    result = self.test_nutrient_predictions(
                                        food=food,
                                        target_nutrients=target_nutrients,
                                        reference_values=reference_values,
                                        test_run_id=test_run_id
                                    )
                                    
                                    if "error" not in result:
                                        successful_tests += 1
                                    else:
                                        failed_tests += 1
                            
                            # Test mental health impacts
                            reference_impacts = reference_values.get("mental_health_impacts", [])
                            if reference_impacts:
                                result = self.test_mental_health_impacts(
                                    food=food,
                                    reference_impacts=reference_impacts,
                                    test_run_id=test_run_id
                                )
                                
                                if "error" not in result:
                                    successful_tests += 1
                                else:
                                    failed_tests += 1
                            
                            foods_tested += 1
                            
                        except Exception as e:
                            logger.error(f"Error testing food {item.get('food_id', 'unknown')}: {e}")
                            failed_tests += 1
                    
                    # Update offset for next batch
                    offset += len(batch)
                    
                    # Exit if batch is smaller than batch size (last batch)
                    if len(batch) < self.batch_size:
                        break
            
            # Save metrics to database
            metrics_summary = self.get_metrics_summary()
            self._save_metrics_to_db(test_run_id)
            
            result = {
                "test_run_id": test_run_id,
                "timestamp": datetime.now().isoformat(),
                "foods_tested": foods_tested,
                "successful_tests": successful_tests,
                "failed_tests": failed_tests,
                "metrics_summary": metrics_summary
            }
            
            logger.info(f"Test suite complete: {foods_tested} foods tested, "
                       f"{successful_tests} successful tests, {failed_tests} failed tests")
            
            return result
            
        except Exception as e:
            logger.error(f"Error running test suite: {e}", exc_info=True)
            return {
                "test_run_id": test_run_id,
                "success": False,
                "error": str(e)
            }


def main():
    """Main function to execute the evaluation."""
    parser = argparse.ArgumentParser(description="Evaluate AI-generated nutritional psychiatry data")
    parser.add_argument("--api-key", help="OpenAI API key")
    parser.add_argument("--food-ids", nargs="+", help="List of food IDs to test")
    parser.add_argument("--batch-size", type=int, default=50, help="Batch size for processing")
    parser.add_argument("--no-calibration", action="store_true", help="Disable confidence calibration")
    
    args = parser.parse_args()
    
    try:
        # Initialize database client
        db_client = PostgresClient()
        
        # Initialize OpenAI client
        openai_client = OpenAIAPI(api_key=args.api_key)
        
        # Initialize tester
        tester = KnownAnswerTester(
            openai_client=openai_client,
            db_client=db_client,
            confidence_calibration=not args.no_calibration,
            batch_size=args.batch_size
        )
        
        # Run test suite
        result = tester.run_test_suite(food_ids=args.food_ids)
        
        # Print summary
        print("\nTest Suite Summary:")
        print(f"Test Run ID: {result['test_run_id']}")
        print(f"Foods Tested: {result.get('foods_tested', 0)}")
        print(f"Successful Tests: {result.get('successful_tests', 0)}")
        print(f"Failed Tests: {result.get('failed_tests', 0)}")
        
        if 'metrics_summary' in result:
            metrics = result['metrics_summary']
            if 'nutrients' in metrics:
                nutrients = metrics['nutrients']
                print("\nNutrient Prediction Metrics:")
                print(f"  Total Predictions: {nutrients.get('total_predictions', 0)}")
                print(f"  Within 10% Accuracy: {nutrients.get('percent_within_10', 0):.2f}%")
                print(f"  Within 25% Accuracy: {nutrients.get('percent_within_25', 0):.2f}%")
                print(f"  Mean Absolute Percentage Error: {nutrients.get('mean_absolute_percentage_error', 0):.2f}%")
            
            if 'mental_health_impacts' in metrics:
                impacts = metrics['mental_health_impacts']
                print("\nMental Health Impact Metrics:")
                print(f"  Total Predictions: {impacts.get('total_predictions', 0)}")
                print(f"  Precision: {impacts.get('precision', 0):.2f}")
                print(f"  Recall: {impacts.get('recall', 0):.2f}")
        
    except Exception as e:
        logger.error(f"Error during evaluation: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()