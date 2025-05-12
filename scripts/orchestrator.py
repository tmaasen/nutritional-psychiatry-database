#!/usr/bin/env python3
"""
Nutritional Psychiatry Dataset Orchestrator

This script orchestrates the end-to-end process of building the Nutritional Psychiatry Dataset:
1. Data Collection (USDA, OpenFoodFacts, Literature)
2. Data Transformation
3. AI Enrichment
4. Validation
5. Confidence Calibration
6. Source Prioritization & Merging

Run this script to process foods through the entire pipeline or specific steps.
"""

import time
import sys
from typing import List, Dict, Optional, Callable, Any
from config import get_config

# Import utility modules
from schema.schema_validator import SchemaValidator
from scripts.data_processing.food_data_transformer import FoodDataTransformer
from utils import (
    setup_logging,
)
from utils.db_utils import PostgresClient

# Import processing modules
from scripts.data_collection.usda_api import USDAFoodDataCentralAPI
from scripts.data_collection.openfoodfacts_api import OpenFoodFactsAPI
from scripts.data_collection.literature_extract import LiteratureExtractor
from scripts.data_processing.ai_enrichment import AIEnrichmentEngine
from scripts.ai.confidence_calibration_system import ConfidenceCalibrationSystem
from scripts.data_processing.food_source_prioritization import SourcePrioritizer

# Initialize logger
logger = setup_logging(__name__, log_file="nutritional_psychiatry_dataset.log")

class DatasetOrchestrator:
    """Orchestrates the end-to-end process of building the Nutritional Psychiatry Dataset."""
    
    def __init__(
        self,
        config_file: Optional[str] = None,
        api_keys: Optional[Dict[str, str]] = None,
        food_list: Optional[List[str]] = None,
        output_dir: str = None,
        skip_steps: Optional[List[str]] = None,
        only_steps: Optional[List[str]] = None,
        batch_size: int = None,
        force_reprocess: bool = None
    ):
        """
        Initialize the orchestrator.

        Args:
            config_file: Path to configuration file
            api_keys: Dictionary of API keys
            food_list: List of foods to process
            output_dir: Base directory for all data
            skip_steps: List of steps to skip
            only_steps: List of steps to run (ignores skip_steps if provided)
            batch_size: Number of foods to process in each batch
            force_reprocess: Whether to reprocess existing files
        """
        # Load configuration
        self.config = get_config(config_file)
        
        # Override config with arguments if provided
        self.api_keys = api_keys or self.config.api_keys
        self.food_list = food_list or []
        self.output_dir = output_dir or self.config.data_dir
        self.skip_steps = skip_steps or []
        self.only_steps = only_steps
        self.batch_size = batch_size or self.config.processing["batch_size"]
        self.force_reprocess = force_reprocess if force_reprocess is not None else self.config.processing["force_reprocess"]
        
        # Initialize database client
        self.db_client = PostgresClient()
        
        # Initialize step tracking
        self.completed_steps = set()
        
        # Validate API keys
        self._validate_api_keys()
        
        # Initialize processors
        self._initialize_processors()
    
    def _validate_api_keys(self):
        """Validate required API keys."""
        required_keys = {
            "USDA_API_KEY": "USDA FoodData Central API key",
            "OPENAI_API_KEY": "OpenAI API key"
        }
        
        missing_keys = []
        for key, description in required_keys.items():
            if not self.api_keys.get(key):
                missing_keys.append(f"{key} ({description})")
        
        if missing_keys:
            error_msg = f"Missing required API keys: {', '.join(missing_keys)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Test API keys
        try:
            # Test USDA API key
            test_client = USDAFoodDataCentralAPI(
                api_key=self.api_keys["USDA_API_KEY"],
                db_client=self.db_client
            )
            test_client.search("test")
            logger.info("USDA API key validated successfully")
            
            # Test OpenAI API key
            test_client = AIEnrichmentEngine(
                api_key=self.api_keys["OPENAI_API_KEY"],
                db_client=self.db_client
            )
            test_client.process({"name": "test"})
            logger.info("OpenAI API key validated successfully")
            
        except Exception as e:
            logger.error(f"API key validation failed: {e}")
            raise
    
    def _initialize_processors(self):
        """Initialize all data processors and API clients."""
        # Initialize API clients
        self.usda_client = USDAFoodDataCentralAPI(
            api_key=self.api_keys.get("USDA_API_KEY"),
            db_client=self.db_client
        )
        self.off_client = OpenFoodFactsAPI(
            db_client=self.db_client
        )
        self.literature_client = LiteratureExtractor(
            db_client=self.db_client
        )
        
        # Initialize processors
        self.transformer = FoodDataTransformer(
            db_client=self.db_client
        )
        self.enricher = AIEnrichmentEngine(
            api_key=self.api_keys.get("OPENAI_API_KEY"),
            db_client=self.db_client
        )
        self.validator = SchemaValidator()
        self.calibrator = ConfidenceCalibrationSystem(
            evaluation_dir=self.config.dirs["evaluation"],
            dataset_dir=self.config.dirs["ai_generated"],
            output_dir=self.config.dirs["calibrated"],
            db_client=self.db_client
        )
        self.prioritizer = SourcePrioritizer(
            db_client=self.db_client
        )
    
    def _should_run_step(self, step_name: str) -> bool:
        """Determine if a step should be run based on skip_steps and only_steps."""
        if self.only_steps:
            return step_name in self.only_steps
        else:
            return step_name not in self.skip_steps
    
    def run_step(
        self, 
        step_name: str, 
        step_func: Callable[[], Any], 
        dependencies: Optional[List[str]] = None
    ) -> Any:
        """
        Run a step by calling a function directly.
        
        Args:
            step_name: Name of the step
            step_func: Function to call
            dependencies: List of step names that must complete before this step
            
        Returns:
            Return value from the step function
        """
        # Check if step should be run
        if not self._should_run_step(step_name):
            logger.info(f"Skipping step: {step_name}")
            return None
        
        # Check dependencies
        if dependencies:
            missing_deps = [dep for dep in dependencies if dep not in self.completed_steps]
            if missing_deps:
                logger.error(f"Cannot run {step_name}: missing dependencies {missing_deps}")
                return None
        
        logger.info(f"Running step: {step_name}")
        
        try:
            start_time = time.time()
            result = step_func()
            end_time = time.time()
            
            # Log completion
            logger.info(f"Step {step_name} completed in {end_time - start_time:.2f} seconds")
            
            # Mark as completed
            self.completed_steps.add(step_name)
            
            return result
            
        except Exception as e:
            logger.error(f"Error running step {step_name}: {e}", exc_info=True)
            return None
    
    def collect_usda_data(self) -> List[str]:
        """Collect food data from USDA FoodData Central."""
        step_name = "usda_data_collection"
        
        def execute():
            saved_ids = []
            
            if not self.food_list:
                logger.info("No food list provided. Using default foods.")
                default_foods = ["blueberries raw", "salmon raw", "spinach raw", "walnuts raw", "yogurt raw"]
                self.food_list = default_foods
            
            for food_query in self.food_list:
                logger.info(f"Collecting USDA data for {food_query}...")
                
                try:
                    # Search for food
                    search_results = self.usda_client.search(food_query)
                    
                    if not search_results.get("foods"):
                        logger.warning(f"No results found for {food_query}")
                        continue
                    
                    # Get details for first result
                    food_id = search_results["foods"][0]["fdcId"]
                    food_details = self.usda_client.get_details(food_id)
                    
                    # Process and save
                    processed = self.usda_client.process_response(food_details)
                    if self.usda_client.validate_response(processed):
                        item_id = self.usda_client.save_to_database(processed)
                        saved_ids.append(item_id)
                        logger.info(f"Saved USDA data for {food_query} with ID {item_id}")
                    else:
                        logger.warning(f"Invalid data for {food_query}")
                
                except Exception as e:
                    logger.error(f"Error processing {food_query}: {e}")
                    continue
            
            return saved_ids
        
        return self.run_step(step_name, execute)
    
    def collect_openfoodfacts_data(self) -> List[str]:
        """Collect food data from OpenFoodFacts."""
        step_name = "openfoodfacts_data_collection"
        
        def execute():
            saved_ids = []
            
            if not self.food_list:
                logger.info("No food list provided. Using default foods.")
                default_foods = ["blueberries raw", "salmon raw", "spinach raw", "walnuts raw", "yogurt raw"]
                self.food_list = default_foods
            
            for food_query in self.food_list:
                logger.info(f"Collecting OpenFoodFacts data for {food_query}...")
                
                try:
                    # Search for food
                    search_results = self.off_client.search(food_query)
                    
                    if not search_results.get("products"):
                        logger.warning(f"No results found for {food_query}")
                        continue
                    
                    # Get details for first result
                    product_id = search_results["products"][0]["id"]
                    product_details = self.off_client.get_details(product_id)
                    
                    # Process and save
                    processed = self.off_client.process_response(product_details)
                    if self.off_client.validate_response(processed):
                        item_id = self.off_client.save_to_database(processed)
                        saved_ids.append(item_id)
                        logger.info(f"Saved OpenFoodFacts data for {food_query} with ID {item_id}")
                    else:
                        logger.warning(f"Invalid data for {food_query}")
                
                except Exception as e:
                    logger.error(f"Error processing {food_query}: {e}")
                    continue
            
            return saved_ids
        
        return self.run_step(step_name, execute)
    
    def collect_literature_data(self) -> List[str]:
        """Collect food data from literature."""
        step_name = "literature_data_collection"
        
        def execute():
            saved_ids = []
            
            if not self.food_list:
                logger.info("No food list provided. Using default foods.")
                default_foods = ["blueberries raw", "salmon raw", "spinach raw", "walnuts raw", "yogurt raw"]
                self.food_list = default_foods
            
            for food_query in self.food_list:
                logger.info(f"Collecting literature data for {food_query}...")
                
                try:
                    # Search for literature
                    search_results = self.literature_client.search(food_query)
                    
                    if not search_results:
                        logger.warning(f"No results found for {food_query}")
                        continue
                    
                    # Process and save each result
                    for result in search_results:
                        processed = self.literature_client.process_response(result)
                        if self.literature_client.validate_response(processed):
                            item_id = self.literature_client.save_to_database(processed)
                            saved_ids.append(item_id)
                            logger.info(f"Saved literature data for {food_query} with ID {item_id}")
                        else:
                            logger.warning(f"Invalid data for {food_query}")
                
                except Exception as e:
                    logger.error(f"Error processing {food_query}: {e}")
                    continue
            
            return saved_ids
        
        return self.run_step(step_name, execute)
    
    def transform_data(self) -> List[str]:
        """Transform collected data to match our schema."""
        step_name = "data_transformation"
        
        def execute():
            # Get all foods from database
            foods = self.db_client.get_foods_by_name("")
            
            # Transform each food
            transformed_ids = []
            for food in foods:
                try:
                    # Transform and validate
                    transformed = self.transformer.transform(food)
                    errors = self.transformer.validate(transformed)
                    
                    if errors:
                        logger.warning(f"Validation errors for {food['name']}: {errors}")
                        continue
                    
                    # Save to database
                    item_id = self.transformer.save_to_database(transformed)
                    transformed_ids.append(item_id)
                    logger.info(f"Transformed {food['name']} with ID {item_id}")
                
                except Exception as e:
                    logger.error(f"Error transforming {food['name']}: {e}")
                    continue
            
            return transformed_ids
        
        return self.run_step(step_name, execute)
    
    def enrich_with_ai(self) -> List[str]:
        """Enrich data with AI-generated information."""
        step_name = "ai_enrichment"
        
        def execute():
            # Get all foods from database
            foods = self.db_client.get_foods_by_name("")
            
            # Enrich each food
            enriched_ids = []
            for food in foods:
                try:
                    # Enrich and validate
                    enriched = self.enricher.process(food)
                    errors = self.enricher.validate(enriched)
                    
                    if errors:
                        logger.warning(f"Validation errors for {food['name']}: {errors}")
                        continue
                    
                    # Save to database
                    item_id = self.enricher.save_to_database(enriched)
                    enriched_ids.append(item_id)
                    logger.info(f"Enriched {food['name']} with ID {item_id}")
                
                except Exception as e:
                    logger.error(f"Error enriching {food['name']}: {e}")
                    continue
            
            return enriched_ids
        
        return self.run_step(step_name, execute)
    
    def validate_with_known_answers(self) -> Dict:
        """Validate data against known answers."""
        step_name = "known_answer_validation"
        
        def execute():
            # Get all foods from database
            foods = self.db_client.get_foods_by_name("")
            
            # Validate each food
            validation_results = {
                "passed": [],
                "failed": [],
                "errors": []
            }
            
            for food in foods:
                try:
                    # Validate
                    errors = self.validator.validate(food)
                    
                    if errors:
                        validation_results["failed"].append({
                            "food_id": food["food_id"],
                            "name": food["name"],
                            "errors": errors
                        })
                    else:
                        validation_results["passed"].append({
                            "food_id": food["food_id"],
                            "name": food["name"]
                        })
                
                except Exception as e:
                    validation_results["errors"].append({
                        "food_id": food["food_id"],
                        "name": food["name"],
                        "error": str(e)
                    })
            
            return validation_results
        
        return self.run_step(step_name, execute)
    
    def calibrate_confidence(self) -> Dict:
        """Calibrate confidence scores."""
        step_name = "confidence_calibration"
        
        def execute():
            # Get all foods from database
            foods = self.db_client.get_foods_by_name("")
            
            # Calibrate each food
            calibration_results = {
                "calibrated": [],
                "failed": [],
                "errors": []
            }
            
            for food in foods:
                try:
                    # Calibrate
                    calibrated = self.calibrator.process(food)
                    
                    if calibrated:
                        calibration_results["calibrated"].append({
                            "food_id": food["food_id"],
                            "name": food["name"]
                        })
                    else:
                        calibration_results["failed"].append({
                            "food_id": food["food_id"],
                            "name": food["name"]
                        })
                
                except Exception as e:
                    calibration_results["errors"].append({
                        "food_id": food["food_id"],
                        "name": food["name"],
                        "error": str(e)
                    })
            
            return calibration_results
        
        return self.run_step(step_name, execute)
    
    def merge_sources(self) -> List[str]:
        """Merge data from different sources."""
        step_name = "source_merging"
        
        def execute():
            # Get all foods from database
            foods = self.db_client.get_foods_by_name("")
            
            # Merge each food
            merged_ids = []
            for food in foods:
                try:
                    # Merge sources
                    merged = self.prioritizer.process(food)
                    errors = self.prioritizer.validate(merged)
                    
                    if errors:
                        logger.warning(f"Validation errors for {food['name']}: {errors}")
                        continue
                    
                    # Save to database
                    item_id = self.prioritizer.save_to_database(merged)
                    merged_ids.append(item_id)
                    logger.info(f"Merged {food['name']} with ID {item_id}")
                
                except Exception as e:
                    logger.error(f"Error merging {food['name']}: {e}")
                    continue
            
            return merged_ids
        
        return self.run_step(step_name, execute)
    
    def run_all(self) -> bool:
        """
        Run all steps in the pipeline.
        
        Returns:
            Whether all steps completed successfully
        """
        steps = [
            ("usda_data_collection", self.collect_usda_data, []),
            ("openfoodfacts_data_collection", self.collect_openfoodfacts_data, []),
            ("literature_data_collection", self.collect_literature_data, []),
            ("data_transformation", self.transform_data, ["usda_data_collection", "openfoodfacts_data_collection", "literature_data_collection"]),
            ("ai_enrichment", self.enrich_with_ai, ["data_transformation"]),
            ("known_answer_validation", self.validate_with_known_answers, ["ai_enrichment"]),
            ("confidence_calibration", self.calibrate_confidence, ["known_answer_validation"]),
            ("source_merging", self.merge_sources, ["confidence_calibration"])
        ]
        
        success = True
        for step_name, step_func, dependencies in steps:
            result = self.run_step(step_name, step_func, dependencies)
            if result is None:
                success = False
                logger.error(f"Step {step_name} failed")
        
        return success
    
    def run_interactive(self):
        """Run the pipeline interactively."""
        print("Nutritional Psychiatry Dataset Pipeline")
        print("=====================================")
        
        while True:
            print("\nAvailable steps:")
            print("1. Collect USDA data")
            print("2. Collect OpenFoodFacts data")
            print("3. Collect literature data")
            print("4. Transform data")
            print("5. Enrich with AI")
            print("6. Validate with known answers")
            print("7. Calibrate confidence")
            print("8. Merge sources")
            print("9. Run all steps")
            print("0. Exit")
            
            choice = input("\nEnter your choice (0-9): ")
            
            if choice == "0":
                break
            elif choice == "1":
                self.collect_usda_data()
            elif choice == "2":
                self.collect_openfoodfacts_data()
            elif choice == "3":
                self.collect_literature_data()
            elif choice == "4":
                self.transform_data()
            elif choice == "5":
                self.enrich_with_ai()
            elif choice == "6":
                self.validate_with_known_answers()
            elif choice == "7":
                self.calibrate_confidence()
            elif choice == "8":
                self.merge_sources()
            elif choice == "9":
                self.run_all()
            else:
                print("Invalid choice. Please try again.")

def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Nutritional Psychiatry Dataset Pipeline")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--foods", nargs="+", help="List of foods to process")
    parser.add_argument("--skip", nargs="+", help="Steps to skip")
    parser.add_argument("--only", nargs="+", help="Steps to run (ignores skip)")
    parser.add_argument("--batch-size", type=int, help="Batch size for processing")
    parser.add_argument("--force", action="store_true", help="Force reprocessing")
    parser.add_argument("--interactive", action="store_true", help="Run interactively")
    
    args = parser.parse_args()
    
    try:
        orchestrator = DatasetOrchestrator(
            config_file=args.config,
            food_list=args.foods,
            skip_steps=args.skip,
            only_steps=args.only,
            batch_size=args.batch_size,
            force_reprocess=args.force
        )
        
        if args.interactive:
            orchestrator.run_interactive()
        else:
            success = orchestrator.run_all()
            if not success:
                sys.exit(1)
    
    except Exception as e:
        logger.error(f"Error running orchestrator: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()