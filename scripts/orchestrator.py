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
import sys
import json
import logging
import argparse
import subprocess
import time
from typing import List, Dict, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("nutritional_psychiatry_dataset.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DatasetOrchestrator:
    """Orchestrates the end-to-end process of building the Nutritional Psychiatry Dataset."""
    
    def __init__(
        self,
        config_file: Optional[str] = None,
        api_keys: Optional[Dict[str, str]] = None,
        food_list: Optional[List[str]] = None,
        output_dir: str = "data",
        skip_steps: Optional[List[str]] = None,
        only_steps: Optional[List[str]] = None,
        batch_size: int = 10,
        force_reprocess: bool = False
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
        self.config = self._load_config(config_file)
        self.api_keys = api_keys or {}
        self.food_list = food_list or []
        self.output_dir = output_dir
        self.skip_steps = skip_steps or []
        self.only_steps = only_steps
        self.batch_size = batch_size
        self.force_reprocess = force_reprocess
        
        # Set up directories
        self.directories = {
            "usda_raw": os.path.join(output_dir, "raw", "usda_foods"),
            "off_raw": os.path.join(output_dir, "raw", "openfoodfacts"),
            "literature_raw": os.path.join(output_dir, "raw", "literature"),
            "manual_entries": os.path.join(output_dir, "raw", "manual_entries"),
            "processed": os.path.join(output_dir, "processed", "base_foods"),
            "ai_generated": os.path.join(output_dir, "enriched", "ai_generated"),
            "evaluation": os.path.join(output_dir, "evaluation"),
            "calibrated": os.path.join(output_dir, "enriched", "calibrated"),
            "merged": os.path.join(output_dir, "enriched", "merged"),
            "final": os.path.join(output_dir, "final")
        }
        
        # Create directories
        for directory in self.directories.values():
            os.makedirs(directory, exist_ok=True)
        
        # Validate required API keys
        self._validate_api_keys()
    
    def _load_config(self, config_file: Optional[str]) -> Dict:
        """Load configuration file."""
        if not config_file or not os.path.exists(config_file):
            logger.info("No configuration file provided or file not found. Using defaults.")
            return {}
        
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            logger.info(f"Loaded configuration from {config_file}")
            return config
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return {}
    
    def _validate_api_keys(self):
        """Validate required API keys are present."""
        required_keys = ["USDA_API_KEY", "OPENAI_API_KEY"]
        missing_keys = [key for key in required_keys if key not in self.api_keys or not self.api_keys[key]]
        
        if missing_keys:
            logger.warning(f"Missing required API keys: {', '.join(missing_keys)}")
            logger.warning("Some functionality may be limited")
    
    def _should_run_step(self, step_name: str) -> bool:
        """Determine if a step should be run based on skip_steps and only_steps."""
        if self.only_steps:
            return step_name in self.only_steps
        else:
            return step_name not in self.skip_steps
    
    def run_step(self, step_name: str, command: List[str], env: Optional[Dict[str, str]] = None) -> bool:
        """
        Run a step by executing a command.
        
        Args:
            step_name: Name of the step
            command: Command to execute
            env: Environment variables for the command
            
        Returns:
            True if successful, False otherwise
        """
        if not self._should_run_step(step_name):
            logger.info(f"Skipping step: {step_name}")
            return True
        
        logger.info(f"Running step: {step_name}")
        logger.info(f"Command: {' '.join([str(item) for item in command])}")
        
        # Prepare environment
        cmd_env = os.environ.copy()
        if env:
            cmd_env.update(env)
        
        # Handle API keys
        for key, value in self.api_keys.items():
            cmd_env[key] = value
        
        try:
            start_time = time.time()
            logger.debug(f"Command structure: {[(type(item), item) for item in command]}")
            process = subprocess.run(
                command,
                env=cmd_env,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            end_time = time.time()
            
            # Log output
            logger.info(f"Step {step_name} completed in {end_time - start_time:.2f} seconds")
            if process.stdout:
                logger.debug(f"Output: {process.stdout}")
            
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Error running step {step_name}: {e}")
            logger.error(f"Command output: {e.stdout}")
            logger.error(f"Command error: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error running step {step_name}: {e}")
            return False
    
    def collect_usda_data(self) -> bool:
        """Collect food data from USDA FoodData Central."""
        step_name = "usda_data_collection"
        
        # Build command
        command = [
            sys.executable, 
            "scripts/data_collection/usda_api.py",
            "--output-dir", str(self.directories["usda_raw"])
        ]
        
        # Add food list if provided
        if self.food_list:
            # Make sure we're using a string, not a dict
            food_query = self.food_list[0]
            if isinstance(food_query, dict):
                # If it's a dictionary, extract the name field
                food_query = food_query.get("name", str(food_query))
            command.extend(["--query", str(food_query)])
        
        # Set environment
        env = {"USDA_API_KEY": self.api_keys.get("USDA_API_KEY", "")}
        
        return self.run_step(step_name, command, env)
    
    def collect_openfoodfacts_data(self) -> bool:
        """Collect food data from OpenFoodFacts."""
        step_name = "openfoodfacts_data_collection"
        
        # Build command
        command = [
            sys.executable, 
            "scripts/data_collection/openfoodfacts_api.py",
            "--output-dir", self.directories["off_raw"]
        ]
        
        # Add food list if provided
        if self.food_list:
            # Make sure we're using a string, not a dict
            food_query = self.food_list[0]
            if isinstance(food_query, dict):
                # If it's a dictionary, extract the name field
                food_query = food_query.get("name", str(food_query))
            command.extend(["--query", str(food_query)])
            command.extend(["--limit", "5"])  # Limit to 5 results per food
        
        return self.run_step(step_name, command)
    
    def collect_literature_data(self) -> bool:
        """Extract food-mood relationships from literature."""
        step_name = "literature_data_collection"
        
        # Check if literature sources are defined
        literature_sources = self.config.get("literature_sources", [])
        if not literature_sources:
            logger.warning("No literature sources defined. Skipping literature data collection.")
            return True
        
        # For each literature source
        success = True
        for source in literature_sources:
            if source.get("type") == "pdf":
                command = [
                    sys.executable, 
                    "scripts/data_collection/literature_extract.py",
                    "--input", source.get("path", ""),
                    "--output-dir", self.directories["literature_raw"]
                ]
                
                source_success = self.run_step(
                    f"{step_name}_{os.path.basename(source.get('path', 'unknown'))}",
                    command
                )
                success = success and source_success
        
        return success
    
    def transform_data(self) -> bool:
        """Transform raw data to our schema format."""
        step_name = "data_transformation"
        
        # Build command
        command = [
            sys.executable, 
            "scripts/data_processing/transform.py",
            "--input-dir", self.directories["usda_raw"],
            "--output-dir", self.directories["processed"]
        ]
        
        return self.run_step(step_name, command)
    
    def enrich_with_ai(self) -> bool:
        """Enrich food data with AI-generated predictions."""
        step_name = "ai_enrichment"
        
        # Build command
        command = [
            sys.executable, 
            "scripts/data_processing/enrichment.py",
            "--input-dir", self.directories["processed"],
            "--output-dir", self.directories["ai_generated"],
            "--model", self.config.get("ai", {}).get("model", "gpt-4o-mini")
        ]
        
        # Set environment
        env = {"OPENAI_API_KEY": self.api_keys.get("OPENAI_API_KEY", "")}
        
        # Add limit if batch size is defined
        if self.batch_size > 0:
            command.extend(["--limit", str(self.batch_size)])
        
        return self.run_step(step_name, command, env)
    
    def validate_with_known_answers(self) -> bool:
        """Validate AI-generated predictions against known reference values."""
        step_name = "known_answer_testing"
        
        # Check if reference data exists
        reference_dir = os.path.join(self.output_dir, "reference")
        if not os.path.exists(reference_dir) or not os.listdir(reference_dir):
            logger.warning("No reference data found. Skipping validation.")
            return True
        
        # Build command
        command = [
            sys.executable, 
            "scripts/ai/known_answer_tester.py",
            "--reference-dir", reference_dir,
            "--output-dir", self.directories["evaluation"],
            "--food-list", os.path.join(self.output_dir, "test_foods.json")
        ]
        
        # Set environment
        env = {"OPENAI_API_KEY": self.api_keys.get("OPENAI_API_KEY", "")}
        
        return self.run_step(step_name, command, env)
    
    def calibrate_confidence(self) -> bool:
        """Calibrate confidence ratings based on validation results."""
        step_name = "confidence_calibration"
        
        # Build command
        command = [
            sys.executable, 
            "scripts/ai/confidence_calibration_system.py",
            "--evaluation-dir", self.directories["evaluation"],
            "--dataset-dir", self.directories["ai_generated"],
            "--output-dir", self.directories["calibrated"]
        ]
        
        return self.run_step(step_name, command)
    
    def merge_sources(self) -> bool:
        """Merge data from different sources with intelligent prioritization."""
        step_name = "source_prioritization"
        
        # Build command
        command = [
            sys.executable, 
            "scripts/data_processing/food_source_prioritization.py",
            "--usda-dir", self.directories["processed"],
            "--openfoodfacts-dir", self.directories["off_raw"],
            "--output-dir", self.directories["merged"]
        ]
        
        # Add literature directory if it contains files
        if os.path.exists(self.directories["literature_raw"]) and os.listdir(self.directories["literature_raw"]):
            command.extend(["--literature-dir", self.directories["literature_raw"]])
        
        # Add AI directory if confidence calibration was not run
        if not self._should_run_step("confidence_calibration"):
            command.extend(["--ai-dir", self.directories["ai_generated"]])
        else:
            command.extend(["--ai-dir", self.directories["calibrated"]])
        
        return self.run_step(step_name, command)
    
    def prepare_final_dataset(self) -> bool:
        """Prepare the final dataset for use."""
        step_name = "final_preparation"
        
        # For the POC, we'll simply copy the merged files to the final directory
        command = ["cp", "-r", os.path.join(self.directories["merged"], "*.json"), self.directories["final"]]
        
        # Use platform-agnostic file copying
        if sys.platform == "win32":
            import shutil
            try:
                for file in os.listdir(self.directories["merged"]):
                    if file.endswith(".json"):
                        shutil.copy(
                            os.path.join(self.directories["merged"], file),
                            os.path.join(self.directories["final"], file)
                        )
                return True
            except Exception as e:
                logger.error(f"Error copying final dataset: {e}")
                return False
        else:
            return self.run_step(step_name, command)
    
    def run_all(self) -> bool:
        """Run the complete data processing pipeline."""
        logger.info("Starting Nutritional Psychiatry Dataset generation pipeline")
        start_time = time.time()
        
        steps = [
            ("Step 1: USDA Data Collection", self.collect_usda_data),
            ("Step 2: OpenFoodFacts Data Collection", self.collect_openfoodfacts_data),
            ("Step 3: Literature Data Extraction", self.collect_literature_data),
            ("Step 4: Data Transformation", self.transform_data),
            ("Step 5: AI Enrichment", self.enrich_with_ai),
            ("Step 6: Known Answer Testing", self.validate_with_known_answers),
            ("Step 7: Confidence Calibration", self.calibrate_confidence),
            ("Step 8: Source Prioritization & Merging", self.merge_sources),
            ("Step 9: Final Dataset Preparation", self.prepare_final_dataset)
        ]
        
        failures = []
        for step_desc, step_func in steps:
            logger.info(f"=== {step_desc} ===")
            success = step_func()
            if not success:
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
            ("Collect USDA Food Data", self.collect_usda_data),
            ("Collect OpenFoodFacts Data", self.collect_openfoodfacts_data),
            ("Extract Literature Data", self.collect_literature_data),
            ("Transform Data to Schema", self.transform_data),
            ("Enrich with AI Predictions", self.enrich_with_ai),
            ("Validate with Known Answers", self.validate_with_known_answers),
            ("Calibrate Confidence Ratings", self.calibrate_confidence),
            ("Merge Data Sources", self.merge_sources),
            ("Prepare Final Dataset", self.prepare_final_dataset)
        ]
        
        for i, (step_desc, step_func) in enumerate(steps, 1):
            print(f"\nStep {i}/{len(steps)}: {step_desc}")
            
            if not self._should_run_step(step_desc):
                print("  Skipping this step based on configuration.")
                continue
            
            proceed = input("  Proceed with this step? (Y/n): ").strip().lower()
            if proceed in ("", "y", "yes"):
                print(f"  Running {step_desc}...")
                success = step_func()
                if success:
                    print(f"  ✓ {step_desc} completed successfully.")
                else:
                    print(f"  ✗ {step_desc} failed.")
                    retry = input("  Retry this step? (y/N): ").strip().lower()
                    if retry in ("y", "yes"):
                        print(f"  Retrying {step_desc}...")
                        success = step_func()
                        if not success:
                            print(f"  ✗ {step_desc} failed again.")
                    
                    if not success and not self.config.get("continue_on_failure", False):
                        proceed = input("  Continue despite failure? (y/N): ").strip().lower()
                        if proceed not in ("y", "yes"):
                            print("\nExiting due to step failure.")
                            break
            else:
                print(f"  Skipping {step_desc}.")
        
        print("\nDataset generation process complete.")


def main():
    """Main function to execute the orchestrator."""
    parser = argparse.ArgumentParser(description="Nutritional Psychiatry Dataset Orchestrator")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--usda-key", help="USDA API key")
    parser.add_argument("--openai-key", help="OpenAI API key")
    parser.add_argument("--food", action="append", help="Food to process (can be used multiple times)")
    parser.add_argument("--food-list", help="Path to JSON file with list of foods", default=os.path.join("docs", "examples", "test_food.json"))
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
            with open(args.food_list, 'r') as f:
                food_data = json.load(f)
                if isinstance(food_data, list):
                    food_list = food_data
                elif isinstance(food_data, dict) and "foods" in food_data:
                    food_list = food_data["foods"]
        except Exception as e:
            logger.error(f"Error loading food list: {e}")
    
    # Set up API keys
    api_keys = {
        "USDA_API_KEY": args.usda_key or os.environ.get("USDA_API_KEY", ""),
        "OPENAI_API_KEY": args.openai_key or os.environ.get("OPENAI_API_KEY", "")
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
