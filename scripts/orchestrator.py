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

import os
import json
import time
import logging
from typing import List, Dict, Optional, Callable, Any
from config import get_config, Config

# Import utility modules
from utils import (
    setup_logging,
    load_json,
    save_json,
    ensure_directory,
    load_dotenv,
    get_env,
    load_config,
    create_project_dirs
)
from data.postgres_client import PostgresClient
import subprocess
import sys
# Import processing modules - direct imports from each script
from scripts.data_collection.usda_api import USDAFoodDataCentralAPI
from scripts.data_collection.openfoodfacts_api import OpenFoodFactsAPI
from scripts.data_collection.literature_extract import LiteratureExtractor
from scripts.data_processing.transform import USDADataTransformer
from scripts.data_processing.enrichment import AIEnrichmentEngine
from scripts.data_processing.validation import DataValidator
from scripts.ai.confidence_calibration_system import ConfidenceCalibrationSystem
from scripts.data_processing.food_source_prioritization import SourcePrioritizer

# Initialize logger
logger = setup_logging(__name__, log_file="nutritional_psychiatry_dataset.log")

class DatasetOrchestrator:
    """Orchestrates the end-to-end process of building the Nutritional Psychiatry Dataset."""
    
    def instantiate_db_client(self) -> PostgresClient:
        """
        Instantiates and returns a PostgresClient instance.

        Returns:
            PostgresClient: An instance of the PostgresClient.
        """
        return PostgresClient()
    

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
        
        # Set up directories
        self.directories = self.config.dirs
        
        # Validate required API keys
        self._validate_api_keys()
        
        # Initialize step tracking
        self.completed_steps = set()
        
        self.db_client = self.instantiate_db_client()
    
    def _validate_api_keys(self):
        """Validate required API keys are present."""
        required_keys = ["USDA_API_KEY", "OPENAI_API_KEY"]
        
        # First check the passed API keys
        if self.api_keys:
            for key in required_keys:
                if key not in self.api_keys or not self.api_keys[key]:
                    # Try to get from environment
                    self.api_keys[key] = get_env(key)
        else:
            # Initialize from environment
            self.api_keys = {key: get_env(key) for key in required_keys}
        
        # Check if any keys are still missing
        missing_keys = [key for key in required_keys if key not in self.api_keys or not self.api_keys[key]]
        
        if missing_keys:
            logger.warning(f"Missing required API keys: {', '.join(missing_keys)}")
            logger.warning("Some functionality may be limited")
    
    def _initialize_processors(self):
        """Initialize all data processors and API clients."""
        # Initialize API clients - remove db_client
        self.usda_client = USDAFoodDataCentralAPI(api_key=self.api_keys.get("USDA_API_KEY"))
        self.off_client = OpenFoodFactsAPI()
        
        # Initialize processors
        schema_path = os.path.join("schema", "schema.json")
        self.transformer = USDADataTransformer(schema_path)
        self.enricher = AIEnrichmentEngine(api_key=self.api_keys.get("OPENAI_API_KEY"))
        self.validator = DataValidator(schema_path)
        self.calibrator = ConfidenceCalibrationSystem(
            evaluation_dir=self.directories["evaluation"],
            dataset_dir=self.directories["ai_generated"],
            output_dir=self.directories["calibrated"]
        )
        self.prioritizer = SourcePrioritizer()
    
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
            saved_files = []
            
            if not self.food_list:
                logger.info("No food list provided. Using default foods.")
                default_foods = ["blueberries raw", "salmon raw", "spinach raw", "walnuts raw", "yogurt raw"]
                self.food_list = default_foods
            else:
                logger.info(f"Using food list provided: {self.food_list}")
            
            for food_query in self.food_list:
                logger.info(f"Collecting USDA data for {food_query}...")
                command = [
                    "python",
                    "scripts/data_collection/usda_api.py",
                    "--query",
                    food_query,
                    "--limit",
                    "1"
                ]
                
                result = subprocess.run(command, capture_output=True, text=True)
                
                if result.returncode == 0:
                    logger.info(f"USDA data collection for {food_query} completed successfully.")
                    # Process the captured output if necessary
                    logger.debug(f"STDOUT: {result.stdout}")
                    logger.debug(f"STDERR: {result.stderr}")
                else:
                    logger.error(f"USDA data collection for {food_query} failed.")
                    logger.error(f"STDERR: {result.stderr}")
                    logger.error(f"STDOUT: {result.stdout}")
            
            return saved_files
        
        return self.run_step(step_name, execute)

    
    def collect_openfoodfacts_data(self) -> List[str]:
        """Collect food data from OpenFoodFacts."""
        step_name = "openfoodfacts_data_collection"
        
        def execute():
            saved_files = []
            if not self.food_list:
                logger.info("No food list provided. Using default foods.")
                default_foods = ["blueberries", "salmon", "spinach", "walnuts", "yogurt"]
                self.food_list = default_foods
            else:
                logger.info(f"Using food list provided: {self.food_list}")
                
            for food_query in self.food_list:
                logger.info(f"Collecting OpenFoodFacts data for {food_query}...")
                command = [
                    "python",
                    "scripts/data_collection/openfoodfacts_api.py",
                    "--query",
                    food_query,
                    "--limit",
                    "1"
                ]
                
                result = subprocess.run(command, capture_output=True, text=True)
                
                if result.returncode == 0:
                    logger.info(f"OpenFoodFacts data collection for {food_query} completed successfully.")
                else:
                    logger.error(f"OpenFoodFacts data collection for {food_query} failed.")
                    logger.error(result.stderr)
            
            return saved_files
        return self.run_step(step_name, execute)    
    def collect_literature_data(self) -> List[str]:
        """Extract food-mood relationships from literature."""
        step_name = "literature_data_collection"
        
        def execute():
            import subprocess
            import os

            saved_files = []
            
            # Check if literature sources are defined
            literature_sources = self.config.get("literature_sources", [])
            if not literature_sources:
                logger.warning("No literature sources defined. Skipping literature data collection.")
                return []

            # Iterate through each literature source and run the literature_extract script
            for source in literature_sources:
                source_type = source.get("type")
                source_path = source.get("path")
                source_url = source.get("url")

                command = [
                    "python",
                    "scripts/data_collection/literature_extract.py"
                ]

                if source_type == "pdf" and source_path:
                    command.extend(["--pdfs", source_path])
                    logger.info(f"Extracting literature data from PDF: {source_path}...")
                elif source_type == "url" and source_url:
                    command.extend(["--urls", source_url])
                    logger.info(f"Extracting literature data from URL: {source_url}...")
                else:
                    logger.warning(f"Invalid literature source: {source}")
                    continue

                result = subprocess.run(command, capture_output=True, text=True)

                if result.returncode == 0:
                    logger.info(f"Literature extraction from {source_type}: {source_path or source_url} completed successfully.")
                    saved_files.append(source_path or source_url)
                else:
                    logger.error(f"Literature extraction from {source_type}: {source_path or source_url} failed.")
                    logger.error(f"STDERR: {result.stderr}")
            
            return saved_files
        
        return self.run_step(step_name, execute)
    
    def transform_data(self) -> List[str]:
        """Transform raw data to our schema format."""
        step_name = "data_transformation"
        dependencies = ["usda_data_collection"]
        
        def execute():
            # Process all USDA foods
            # we pass the db_client to the transformer, so that it can use it to interact with the db
            self.transformer.process_directory(
                db_client = self.db_client,
                input_dir="", output_dir=""
            )
        
        return self.run_step(step_name, execute, dependencies)
    
    def enrich_with_ai(self) -> List[str]:
        """Enrich food data with AI-generated predictions."""
        step_name = "ai_enrichment"
        dependencies = ["data_transformation"]
        
        def execute():
            # Apply AI enrichment to all foods in db
            self.enricher.enrich_directory(
                db_client=self.db_client,
                limit=self.batch_size if self.batch_size > 0 else None,
            )
        
        return self.run_step(step_name, execute, dependencies)
    
    def validate_with_known_answers(self) -> Dict:
        """Validate AI-generated predictions against known reference values."""
        step_name = "known_answer_testing"
        dependencies = ["ai_enrichment"]
        
        def execute():
            # Check if reference data exists
            reference_dir = self.directories["reference"]
            if not os.path.exists(reference_dir) or not os.listdir(reference_dir):
                logger.warning("No reference data found. Skipping validation.")
                return {}
            
            # Load test foods
            test_foods_path = os.path.join(self.output_dir, "test_foods.json")
            if not os.path.exists(test_foods_path):
                logger.warning(f"Test foods file {test_foods_path} not found.")
                return {}
            
            test_foods = load_json(test_foods_path)
            
            # Initialize tester
            from scripts.ai.known_answer_tester import KnownAnswerTester
            from scripts.ai.openai_client import OpenAIClient
            
            openai_client = OpenAIClient(api_key=self.api_keys.get("OPENAI_API_KEY"))
            
            tester = KnownAnswerTester(
                openai_client=openai_client,
                reference_data_dir=reference_dir,
                output_dir=self.directories["evaluation"]
            )
            
            # Run test suite
            return tester.run_test_suite(test_foods)
        
        return self.run_step(step_name, execute, dependencies)
    
    def calibrate_confidence(self) -> Dict:
        """Calibrate confidence ratings based on validation results."""
        step_name = "confidence_calibration"
        dependencies = ["ai_enrichment"]
        
        def execute():
            # Initialize calibrator from above
            # Calibrate dataset
            self.calibrator.calibrate_dataset()
            
            # Return summary
            return {"status": "completed"}
        
        return self.run_step(step_name, execute, dependencies)
    
    def merge_sources(self) -> List[str]:
        """Merge data from different sources with intelligent prioritization."""
        step_name = "source_prioritization"
        dependencies = ["data_transformation"]
        
        def execute():
            # Determine AI directory based on calibration
            ai_dir = self.directories["calibrated"] if "confidence_calibration" in self.completed_steps else self.directories["ai_generated"]
            
            # Check if literature directory contains files
            lit_dir = None
            if os.path.exists(self.directories["literature_raw"]) and os.listdir(self.directories["literature_raw"]):
                lit_dir = self.directories["literature_raw"]  
            
            # Merge directories
            return self.prioritizer.merge_directory(
                usda_dir=self.directories["processed"],
                openfoodfacts_dir=self.directories["off_raw"],
                literature_dir=lit_dir,
                ai_dir=ai_dir,
                output_dir=self.directories["merged"]
            )
        
        return self.run_step(step_name, execute, dependencies)
    
    def prepare_final_dataset(self) -> List[str]:
        """Prepare the final dataset for use."""
        step_name = "final_preparation"
        dependencies = ["source_prioritization"]
        
        def execute():
            # For the POC, simply copy merged files to final directory
            import shutil
            
            final_files = []
            
            for file in os.listdir(self.directories["merged"]):
                if file.endswith(".json"):
                    source_path = os.path.join(self.directories["merged"], file)
                    dest_path = os.path.join(self.directories["final"], file)
                    
                    shutil.copy(source_path, dest_path)
                    final_files.append(dest_path)
            
            return final_files
        
        return self.run_step(step_name, execute, dependencies)
    
    def run_all(self) -> bool:
        """Run the complete data processing pipeline."""
        logger.info("Starting Nutritional Psychiatry Dataset generation pipeline")
        start_time = time.time()
        
        steps = [
            ("Step 1: USDA Data Collection", self.collect_usda_data, []),
            ("Step 2: OpenFoodFacts Data Collection", self.collect_openfoodfacts_data, []),
            ("Step 3: Literature Data Collection", self.collect_literature_data, []),
            ("Step 4: Data Transformation", self.transform_data, ["usda_data_collection"]),
            ("Step 5: AI Enrichment", self.enrich_with_ai, ["data_transformation"]),
            ("Step 6: Known Answer Testing", self.validate_with_known_answers, ["ai_enrichment"]),
            ("Step 7: Confidence Calibration", self.calibrate_confidence, ["ai_enrichment"]),
            ("Step 8: Source Prioritization & Merging", self.merge_sources, ["data_transformation"]),
            ("Step 9: Final Dataset Preparation", self.prepare_final_dataset, ["source_prioritization"])
        ]
        
        failures = []
        for step_desc, step_func, dependencies in steps:
            logger.info(f"=== {step_desc} ===")
            
            # Extract step name from description
            step_name = step_desc.split(":", 1)[1].strip().lower().replace(" ", "_")        
            if step_name == 'data_transformation':
                step_func = lambda: step_func(db_client=self.db_client)
            if step_name == 'ai_enrichment':
                step_func = lambda: step_func(db_client=self.db_client)
            # Run step
            result = self.run_step(step_name, step_func, dependencies)
            
            if result is None:
                failures.append(step_desc)
                if not self.config.get("continue_on_failure", False):
                    logger.error(f"Pipeline stopped due to failure in {step_desc}")
                    break
        
        end_time = time.time()
        logger.info(f"Pipeline completed in {end_time - start_time:.2f} seconds")
        
        if failures:
            logger.error(f"The following steps failed: {', '.join(failures)}")
            return False
        else:
            logger.info("All steps completed successfully")
            return True
    
    def run_interactive(self):
        """Run the pipeline interactively, asking for confirmation at each step."""
        print("\n=== Nutritional Psychiatry Dataset Generator ===\n")
        print("This tool will guide you through generating the dataset step by step.")
        
        steps = [
            ("Collect USDA Food Data", self.collect_usda_data, []),
            ("Collect OpenFoodFacts Data", self.collect_openfoodfacts_data, []),
            ("Collect Literature Data", self.collect_literature_data, []),
            ("Transform Data to Schema", self.transform_data, ["collect_usda_food_data"]),
            ("Enrich with AI Predictions", self.enrich_with_ai, ["transform_data_to_schema"]),
            ("Validate with Known Answers", self.validate_with_known_answers, ["enrich_with_ai_predictions"]),
            ("Calibrate Confidence Ratings", self.calibrate_confidence, ["enrich_with_ai_predictions"]),
            ("Merge Data Sources", self.merge_sources, ["transform_data_to_schema"]),
            ("Prepare Final Dataset", self.prepare_final_dataset, ["merge_data_sources"])
        ]
        
        for i, (step_desc, step_func, dependencies) in enumerate(steps, 1):
            print(f"\nStep {i}/{len(steps)}: {step_desc}")
            
            # Convert to step name format
            step_name = step_desc.lower().replace(" ", "_")
            
            if not self._should_run_step(step_name):
                print("  Skipping this step based on configuration.")
                continue
            
            proceed = input("  Proceed with this step? (Y/n): ").strip().lower()
            if proceed in ("", "y", "yes"):
                print(f"  Running {step_desc}...")
                result = self.run_step(step_name, step_func, dependencies)
                
                if step_name == 'transform_data_to_schema':
                    result = self.transform_data(db_client=self.db_client)
                    
                if step_name == 'enrich_with_ai_predictions':
                    result = self.enrich_with_ai(db_client=self.db_client)
                
                if result is not None:
                    print(f"  ✓ {step_desc} completed successfully.")
                else:
                    print(f"  ✗ {step_desc} failed.")
                    retry = input("  Retry this step? (y/N): ").strip().lower()
                    if retry in ("y", "yes"):
                        print(f"  Retrying {step_desc}...")
                        result = self.run_step(step_name, step_func, dependencies)
                        if result is None:
                            print(f"  ✗ {step_desc} failed again.")
                    
                    if result is None and not self.config.get("continue_on_failure", False):
                        proceed = input("  Continue despite failure? (y/N): ").strip().lower()
                        if proceed not in ("y", "yes"):
                            print("\nExiting due to step failure.")
                            break
            else:
                print(f"  Skipping {step_desc}.")
        
        print("\nDataset generation process complete.")

def main():
    """Main function to execute the orchestrator."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Nutritional Psychiatry Dataset Orchestrator")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--usda-key", help="USDA API key")
    parser.add_argument("--openai-key", help="OpenAI API key")
    parser.add_argument("--food", action="append", help="Food to process (can be used multiple times)")
    parser.add_argument("--food-list", help="Path to JSON file with list of foods", 
                       default=os.path.join("docs", "examples", "test_food.json"))
    parser.add_argument("--output-dir", default="data", help="Base directory for all data")
    parser.add_argument("--skip", action="append", help="Steps to skip (can be used multiple times)")
    parser.add_argument("--only", action="append", help="Only run these steps (can be used multiple times)")
    parser.add_argument("--batch-size", type=int, default=10, help="Number of foods to process in each batch")
    parser.add_argument("--force", action="store_true", help="Force reprocessing of existing files")
    parser.add_argument("--interactive", action="store_true", help="Run in interactive mode", default=True)
    
    args = parser.parse_args()
    
    # Load food list from file if provided
    food_list = []
    if args.food:
        food_list = args.food
    elif args.food_list and os.path.exists(args.food_list):
        try:
            food_list = load_json(args.food_list)
        except Exception as e:
            logger.error(f"Error loading food list: {e}")
    
    # Set up API keys
    api_keys = {
        "USDA_API_KEY": args.usda_key or get_env("USDA_API_KEY", ""),
        "OPENAI_API_KEY": args.openai_key or get_env("OPENAI_API_KEY", "")
    }
    
    # Create orchestrator
    orchestrator = DatasetOrchestrator(
        config_file=args.config,
        api_keys=api_keys,
        food_list=food_list,
        output_dir=args.output_dir,
        skip_steps=args.skip,
        only_steps=args.only,
        batch_size=args.batch_size,
        force_reprocess=args.force
    )
    
    # Run pipeline
    if args.interactive:
        orchestrator.run_interactive()
    else:
        orchestrator.run_all()


if __name__ == "__main__":
    main()