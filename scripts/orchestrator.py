#!/usr/bin/env python3
"""
Nutritional Psychiatry Database Orchestrator

This script orchestrates the end-to-end process of building the Nutritional Psychiatry Database:
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

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

import time
from typing import List, Dict, Optional, Callable, Any, Set

# Import utility modules
from utils.logging_utils import setup_logging
from utils.db_utils import PostgresClient

# Import processing modules
from scripts.data_collection.usda_api import USDAFoodDataCentralAPI, search_and_import as usda_search_and_import
from scripts.data_collection.openfoodfacts_api import OpenFoodFactsAPI, search_and_import as off_search_and_import
from scripts.data_collection.literature_extract import LiteratureExtractor
from scripts.data_processing.food_data_transformer import FoodDataTransformer
from scripts.data_processing.ai_enrichment import AIEnrichmentEngine
from scripts.ai.confidence_calibration_system import ConfidenceCalibrationSystem
from scripts.data_processing.food_source_prioritization import SourcePrioritizer

# Import schema models
from schema.food_data import FoodData
from schema.schema_validator import SchemaValidator

# Import project configuration
from config import get_config

# Initialize logger
logger = setup_logging(__name__)

class DatabaseOrchestrator:
    """Orchestrates the end-to-end process of building the Nutritional Psychiatry Database."""
    
    def __init__(
        self,
        config_file: Optional[str] = None,
        food_list: Optional[List[str]] = None,
        output_dir: Optional[str] = None,
        skip_steps: Optional[List[str]] = None,
        only_steps: Optional[List[str]] = None,
        batch_size: Optional[int] = None,
        force_reprocess: Optional[bool] = None
    ):
        self.config = get_config(config_file)
        
        # Override config with arguments if provided
        self.api_keys = self.config.api_keys or {}
        self.food_list = food_list or []
        self.output_dir = output_dir or self.config.data_dir
        self.skip_steps = skip_steps or []
        self.only_steps = only_steps
        self.batch_size = batch_size or self.config.processing.get("batch_size", 10)
        self.force_reprocess = force_reprocess if force_reprocess is not None else self.config.processing.get("force_reprocess", False)
        
        self.db_client = PostgresClient()        
        self.completed_steps: Set[str] = set()
        self._initialize_processors()
    
    def _initialize_processors(self):
        """Initialize all data processors and API clients."""
        # Get API keys from config if not provided
        usda_api_key = self.api_keys.get("USDA_API_KEY") or self.config.get_api_key("USDA")
        openai_api_key = self.api_keys.get("OPENAI_API_KEY") or self.config.get_api_key("OPENAI")
        
        # Initialize API clients
        self.usda_client = USDAFoodDataCentralAPI(api_key=usda_api_key)
        self.off_client = OpenFoodFactsAPI()
        self.literature_client = LiteratureExtractor(db_client=self.db_client)
        
        # Initialize processors
        self.transformer = FoodDataTransformer()
        self.enricher = AIEnrichmentEngine(
            api_key=openai_api_key,
            db_client=self.db_client
        )
        self.validator = SchemaValidator()
        self.calibrator = ConfidenceCalibrationSystem(
            db_client=self.db_client
        )
        self.prioritizer = SourcePrioritizer(
            db_client=self.db_client
        )
        
        logger.info("All processors and clients initialized successfully")
    
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
            raise
    
    def collect_usda_data(self) -> List[str]:
        """Collect food data from USDA FoodData Central."""
        step_name = "usda_data_collection"
        
        def execute() -> List[str]:
            saved_ids = []
            
            if not self.food_list:
                logger.info("No food list provided.")
                return []
            
            # Process in batches
            for i in range(0, len(self.food_list), self.batch_size):
                batch = self.food_list[i:i+self.batch_size]
                logger.info(f"Processing USDA batch {i//self.batch_size + 1}/{(len(self.food_list)-1)//self.batch_size + 1} ({len(batch)} foods)")
                
                for food_query in batch:
                    try:
                        logger.info(f"Collecting USDA data for {food_query}...")
                        
                        # Use the existing search_and_import function
                        imported_foods = usda_search_and_import(
                            api_client=self.usda_client,
                            db_client=self.db_client,
                            search_term=food_query,
                            limit=1  # Just get the top match
                        )
                        
                        if imported_foods:
                            saved_ids.extend(imported_foods)
                            logger.info(f"Saved USDA data for {food_query} with ID(s): {imported_foods}")
                        else:
                            logger.warning(f"No results found for {food_query}")
                    
                    except Exception as e:
                        logger.error(f"Error processing {food_query}: {e}", exc_info=True)
                        raise
                
                # Slight delay between batches to avoid rate limiting
                if i + self.batch_size < len(self.food_list):
                    time.sleep(1)
            
            return saved_ids
        
        return self.run_step(step_name, execute)
    
    def collect_openfoodfacts_data(self) -> List[str]:
        """Collect food data from OpenFoodFacts."""
        step_name = "openfoodfacts_data_collection"
        
        def execute() -> List[str]:
            saved_ids = []
            
            if not self.food_list:
                logger.info("No food list provided. Skipping OpenFoodFacts data collection.")
                return []
            
            # Process in batches
            for i in range(0, len(self.food_list), self.batch_size):
                batch = self.food_list[i:i+self.batch_size]
                logger.info(f"Processing OpenFoodFacts batch {i//self.batch_size + 1}/{(len(self.food_list)-1)//self.batch_size + 1} ({len(batch)} foods)")
                
                for food_query in batch:
                    try:
                        logger.info(f"Collecting OpenFoodFacts data for {food_query}...")
                        
                        # Use the existing search_and_import function
                        imported_foods = off_search_and_import(
                            api_client=self.off_client,
                            db_client=self.db_client,
                            query=food_query,
                            limit=1  # Just get the top match
                        )
                        
                        if imported_foods:
                            saved_ids.extend(imported_foods)
                            logger.info(f"Saved OpenFoodFacts data for {food_query} with ID(s): {imported_foods}")
                        else:
                            logger.warning(f"No results found for {food_query}")
                    
                    except Exception as e:
                        logger.error(f"Error processing {food_query}: {e}", exc_info=True)
                        raise
                
                # Slight delay between batches to avoid rate limiting
                if i + self.batch_size < len(self.food_list):
                    time.sleep(1)
            
            return saved_ids
        
        return self.run_step(step_name, execute)
    
    def collect_literature_data(self) -> List[str]:
        """Collect food data from literature."""
        step_name = "literature_data_collection"
        
        def execute() -> List[str]:
            saved_ids = []
            
            # Use data from config if available
            literature_sources = self.config.literature_sources
            
            if not literature_sources:
                logger.warning("No literature sources specified. Skipping literature data collection.")
                return []
            
            logger.info(f"Processing {len(literature_sources)} literature sources")
            
            for source in literature_sources:
                try:
                    source_type = source.get("type", "").lower()
                    source_path = source.get("path", "")
                    source_food = source.get("food", "")
                    
                    if not source_path:
                        logger.warning(f"Missing path for literature source: {source}")
                        continue
                    
                    if source_type == "pdf":
                        logger.info(f"Processing PDF: {source_path} for {source_food}")
                        food_id = self.literature_client.process_pdf(source_path)
                        if food_id:
                            saved_ids.append(food_id)
                    elif source_type == "url":
                        logger.info(f"Processing URL: {source_path} for {source_food}")
                        food_id = self.literature_client.process_url(source_path)
                        if food_id:
                            saved_ids.append(food_id)
                    else:
                        logger.warning(f"Unknown literature source type: {source_type}")
                
                except Exception as e:
                    logger.error(f"Error processing literature source: {e}", exc_info=True)
                    raise
            
            return saved_ids
        
        return self.run_step(step_name, execute)
    
    def transform_data(self) -> List[str]:
        """Transform collected data to match our schema."""
        step_name = "data_transformation"
        
        def execute() -> List[str]:
            transformed_ids = []
            
            # Get all foods from database that need transformation
            query = """
            SELECT food_id, name, food_data 
            FROM foods 
            WHERE processed = FALSE OR %s
            LIMIT %s
            """
            
            batch_size = self.batch_size
            offset = 0
            
            while True:
                try:
                    # Get batch of foods
                    results = self.db_client.execute_query(
                        query, 
                        (self.force_reprocess, batch_size)
                    )
                    
                    if not results:
                        logger.info("No more foods to transform")
                        break
                    
                    logger.info(f"Transforming batch of {len(results)} foods")
                    
                    for item in results:
                        food_id = item['food_id']
                        food_name = item['name']
                        food_data = item['food_data']
                        
                        try:
                            # Convert to FoodData object
                            food_obj = FoodData.from_dict(food_data)
                            
                            # Transform the food data
                            transformed_data = self.transformer.transform(food_obj)
                            
                            # Validate the transformed data
                            validation_errors = self.validator.validate_food_data(transformed_data.to_dict())
                            
                            if validation_errors:
                                logger.warning(f"Validation errors for {food_name}: {validation_errors}")
                                continue
                            
                            # Save the transformed food data
                            with self.db_client.get_cursor() as cursor:
                                update_query = """
                                UPDATE foods
                                SET food_data = %s, processed = TRUE, last_updated = NOW()
                                WHERE food_id = %s
                                RETURNING food_id
                                """
                                
                                cursor.execute(update_query, (transformed_data.to_dict(), food_id))
                                result = cursor.fetchone()
                                
                                if result and result['food_id'] == food_id:
                                    transformed_ids.append(food_id)
                                    logger.info(f"Transformed {food_name} with ID {food_id}")
                                else:
                                    logger.warning(f"Failed to update {food_name} with ID {food_id}")
                        
                        except Exception as e:
                            logger.error(f"Error transforming {food_name}: {e}", exc_info=True)
                            raise
                    
                    # Move to next batch
                    offset += batch_size
                    
                    # Exit if batch is smaller than batch size (last batch)
                    if len(results) < batch_size:
                        break
                
                except Exception as e:
                    logger.error(f"Error processing transformation batch: {e}", exc_info=True)
                    raise
            
            return transformed_ids
        
        return self.run_step(step_name, execute)
    
    def enrich_with_ai(self) -> List[str]:
        """Enrich data with AI-generated information."""
        step_name = "ai_enrichment"
        
        def execute() -> List[str]:
            # Use the AIEnrichmentEngine's directory processing method
            try:
                enriched_ids = self.enricher.enrich_directory(
                    db_client=self.db_client,
                    limit=None if self.force_reprocess else self.batch_size
                )
                
                logger.info(f"Successfully enriched {len(enriched_ids)} foods with AI")
                return enriched_ids
                
            except Exception as e:
                logger.error(f"Error during AI enrichment: {e}", exc_info=True)
                raise
        
        return self.run_step(step_name, execute)
    
    def validate_with_known_answers(self) -> Dict:
        """Validate data against known answers."""
        step_name = "known_answer_validation"
        
        def execute() -> Dict:
            # Get foods from database that need validation
            query = """
            SELECT food_id, name, food_data 
            FROM foods 
            WHERE validated = FALSE OR %s
            LIMIT %s
            """
            
            batch_size = self.batch_size
            offset = 0
            
            validation_results = {
                "passed": [],
                "failed": [],
                "errors": []
            }
            
            while True:
                try:
                    # Get batch of foods
                    results = self.db_client.execute_query(
                        query, 
                        (self.force_reprocess, batch_size)
                    )
                    
                    if not results:
                        logger.info("No more foods to validate")
                        break
                    
                    logger.info(f"Validating batch of {len(results)} foods")
                    
                    for item in results:
                        food_id = item['food_id']
                        food_name = item['name']
                        food_data = item['food_data']
                        
                        try:
                            # Validate the food data
                            errors = self.validator.validate_food_data(food_data)
                            
                            # Update validation status in database
                            with self.db_client.get_cursor() as cursor:
                                update_query = """
                                UPDATE foods
                                SET validated = TRUE, validation_errors = %s, last_updated = NOW()
                                WHERE food_id = %s
                                RETURNING food_id
                                """
                                
                                cursor.execute(update_query, (errors, food_id))
                                
                            # Track validation results
                            if errors:
                                validation_results["failed"].append({
                                    "food_id": food_id,
                                    "name": food_name,
                                    "errors": errors
                                })
                            else:
                                validation_results["passed"].append({
                                    "food_id": food_id,
                                    "name": food_name
                                })
                                
                        except Exception as e:
                            logger.error(f"Error validating {food_name}: {e}", exc_info=True)
                            validation_results["errors"].append({
                                "food_id": food_id,
                                "name": food_name,
                                "error": str(e)
                            })
                            raise
                    
                    # Move to next batch
                    offset += batch_size
                    
                    # Exit if batch is smaller than batch size (last batch)
                    if len(results) < batch_size:
                        break
                
                except Exception as e:
                    logger.error(f"Error processing validation batch: {e}", exc_info=True)
                    raise
            
            return validation_results
        
        return self.run_step(step_name, execute)
    
    def calibrate_confidence(self) -> Dict:
        """Calibrate confidence scores."""
        step_name = "confidence_calibration"
        
        def execute() -> Dict:
            # Use the ConfidenceCalibrationSystem to calibrate the database
            try:
                stats = self.calibrator.calibrate_database()
                logger.info(f"Confidence calibration complete: {stats['successfully_calibrated']} succeeded, {stats['failed']} failed")
                return stats
                
            except Exception as e:
                logger.error(f"Error during confidence calibration: {e}", exc_info=True)
                raise
                
        return self.run_step(step_name, execute)
    
    def merge_sources(self) -> List[str]:
        """Merge data from different sources."""
        step_name = "source_merging"
        
        def execute() -> List[str]:
            # Use the SourcePrioritizer to merge all foods by name
            try:
                merged_ids = self.prioritizer.merge_all_foods(batch_size=self.batch_size)
                logger.info(f"Successfully merged {len(merged_ids)} foods")
                return merged_ids
                
            except Exception as e:
                logger.error(f"Error during source merging: {e}", exc_info=True)
                raise
        
        return self.run_step(step_name, execute)
    
    def run_all(self) -> bool:
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
                break
        
        return success
    
    def run_interactive(self):
        """Run the pipeline interactively."""
        print("\nNutritional Psychiatry Database Pipeline")
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
    
    parser = argparse.ArgumentParser(description="Nutritional Psychiatry Database Pipeline")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--foods", nargs="+", help="List of foods to process")
    parser.add_argument("--skip", nargs="+", help="Steps to skip")
    parser.add_argument("--only", nargs="+", help="Steps to run (ignores skip)")
    parser.add_argument("--batch-size", type=int, help="Batch size for processing")
    parser.add_argument("--force", action="store_true", help="Force reprocessing")
    parser.add_argument("--interactive", action="store_true", help="Run interactively")
    parser.add_argument("--continue-on-failure", action="store_true", 
                        help="Continue processing even if steps fail")
    
    args = parser.parse_args()
    
    try:
        orchestrator = DatabaseOrchestrator(
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
        logger.error(f"Error running orchestrator: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()