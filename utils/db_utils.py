#!/usr/bin/env python3
"""
Database utilities for the Nutritional Psychiatry Database project.

This module provides utilities for database connection management, query execution,
and data import/export operations.
"""

import json
import logging
from typing import Dict, List, Optional, Union, Tuple, Any
from contextlib import contextmanager
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
from psycopg2 import pool

from config import get_env
from constants.sql_queries import *  # Import all SQL queries
from schema.food_data import FoodData, BrainNutrients, Omega3, BioactiveCompounds, StandardNutrients
from schema.food_data import MentalHealthImpact, NutrientInteraction, DataQuality, Metadata, ServingInfo

logger = logging.getLogger(__name__)

class PostgresClient:
    """
    Client for interacting with PostgreSQL databases.
    
    Features:
    - Connection pooling
    - Context managers for connections and cursors
    - Query execution with error handling
    - Data import/export methods
    """
    
    def __init__(
        self,
        connection_string: Optional[str] = None,
        min_connections: int = 1,
        max_connections: int = 10
    ):
        """
        Initialize the database client.
        
        Args:
            connection_string: PostgreSQL connection string (defaults to environment)
            min_connections: Minimum number of connections in the pool
            max_connections: Maximum number of connections in the pool
        """
        # Use provided connection string or build from environment variables
        if not connection_string:
            connection_string = self._build_connection_string_from_env()
        
        self.connection_string = connection_string
        
        # Initialize connection pool
        try:
            self.connection_pool = pool.ThreadedConnectionPool(
                min_connections,
                max_connections,
                connection_string
            )
            logger.info(f"Initialized connection pool with {min_connections}-{max_connections} connections")
        except Exception as e:
            logger.error(f"Failed to initialize connection pool: {e}")
            raise
    
    def _build_connection_string_from_env(self) -> str:
        """Build connection string from environment variables."""
        
        db_host = get_env("DB_HOST")
        db_port = get_env("DB_PORT", "5432")
        db_name = get_env("DB_NAME")
        db_user = get_env("DB_USER")
        db_password = get_env("DB_PASSWORD")
        
        if not all([db_host, db_name, db_user, db_password]):
            raise ValueError("Database connection details not found in environment variables")
        
        # Determine SSL mode
        sslmode = get_env("DB_SSLMODE", "require")
        
        return (f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
                f"?sslmode={sslmode}")
    
    @contextmanager
    def get_connection(self, cursor_factory=None):
        """
        Get a connection from the pool.
        
        Args:
            cursor_factory: Optional cursor factory
            
        Yields:
            Connection object
        """
        connection = None
        try:
            connection = self.connection_pool.getconn()
            if cursor_factory:
                connection.cursor_factory = cursor_factory
            yield connection
        finally:
            if connection:
                self.connection_pool.putconn(connection)
    
    @contextmanager
    def get_cursor(self, cursor_factory=RealDictCursor):
        """
        Get a database cursor.
        
        Args:
            cursor_factory: Cursor factory
            
        Yields:
            Cursor object
        """
        with self.get_connection() as connection:
            cursor = connection.cursor(cursor_factory=cursor_factory)
            try:
                yield cursor
                connection.commit()
            except Exception as e:
                connection.rollback()
                logger.error(f"Database error: {e}")
                raise
            finally:
                cursor.close()
    
    def close(self):
        """Close the connection pool."""
        if hasattr(self, 'connection_pool'):
            self.connection_pool.closeall()
            logger.info("Closed connection pool")
    
    def execute_query(
        self, 
        query: str, 
        params: Optional[Union[Tuple, Dict]] = None, 
        fetch: bool = True
    ) -> Union[List[Dict], int]:
        """
        Execute a database query with proper error handling.
        
        Args:
            query: SQL query
            params: Query parameters
            fetch: Whether to fetch results
            
        Returns:
            Query results or number of affected rows
        """
        try:
            with self.get_cursor() as cursor:
                cursor.execute(query, params or ())
                if fetch:
                    return cursor.fetchall()
                return cursor.rowcount
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
    
    def batch_insert(
        self, 
        table: str, 
        columns: List[str], 
        values: List[Tuple], 
        page_size: int = 100
    ) -> int:
        try:
            with self.get_cursor() as cursor:
                return execute_values(
                    cursor,
                    f"INSERT INTO {table} ({','.join(columns)}) VALUES %s",
                    values,
                    page_size=page_size
                )
        except Exception as e:
            logger.error(f"Batch insert failed: {e}")
            raise
    
    def import_food_from_json(self, food_json: Union[Dict, str, FoodData]) -> str:
        """
        Import a food from JSON data into the normalized database schema.
        
        Args:
            food_json: Food data as dictionary, JSON string, or FoodData object
            
        Returns:
            Food ID of the imported food
        """
        try:
            # Convert to FoodData object if needed
            if isinstance(food_json, str):
                food_data = json.loads(food_json)
                food = FoodData.from_dict(food_data)
            elif isinstance(food_json, dict):
                food = FoodData.from_dict(food_json)
            else:
                food = food_json  # Assume it's already a FoodData object
            
            # Start transaction
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # 1. Insert/update main food record
                    cursor.execute(FOOD_UPSERT, (
                        food.food_id, 
                        food.name, 
                        food.description, 
                        food.category
                    ))
                    
                    food_id = cursor.fetchone()[0]
                    
                    # 2. Insert/update standard nutrients if present
                    if food.standard_nutrients:
                        sn = food.standard_nutrients
                        cursor.execute(STANDARD_NUTRIENTS_UPSERT, (
                            food_id, 
                            sn.calories, 
                            sn.protein_g, 
                            sn.carbohydrates_g, 
                            sn.fat_g, 
                            sn.fiber_g,
                            sn.sugars_g, 
                            sn.sugars_added_g, 
                            sn.calcium_mg, 
                            sn.iron_mg, 
                            sn.magnesium_mg,
                            sn.phosphorus_mg, 
                            sn.potassium_mg, 
                            sn.sodium_mg, 
                            sn.zinc_mg, 
                            sn.copper_mg,
                            sn.manganese_mg, 
                            sn.selenium_mcg, 
                            sn.vitamin_c_mg, 
                            sn.vitamin_a_iu
                        ))
                    
                    # 3. Insert/update brain nutrients if present
                    if food.brain_nutrients:
                        bn = food.brain_nutrients
                        cursor.execute(BRAIN_NUTRIENTS_UPSERT, (
                            food_id, 
                            bn.tryptophan_mg, 
                            bn.tyrosine_mg, 
                            bn.vitamin_b6_mg, 
                            bn.folate_mcg,
                            bn.vitamin_b12_mcg, 
                            bn.vitamin_d_mcg, 
                            bn.magnesium_mg, 
                            bn.zinc_mg, 
                            bn.iron_mg,
                            bn.selenium_mcg, 
                            bn.choline_mg
                        ))
                        
                        # 3a. Insert/update omega3 fatty acids if present
                        if bn.omega3:
                            o3 = bn.omega3
                            cursor.execute(OMEGA3_UPSERT, (
                                food_id, 
                                o3.total_g, 
                                o3.epa_mg, 
                                o3.dha_mg, 
                                o3.ala_mg, 
                                o3.confidence
                            ))
                    
                    # 4. Insert/update bioactive compounds if present
                    if food.bioactive_compounds:
                        bc = food.bioactive_compounds
                        cursor.execute(BIOACTIVE_COMPOUNDS_UPSERT, (
                            food_id, 
                            bc.polyphenols_mg, 
                            bc.flavonoids_mg, 
                            bc.anthocyanins_mg,
                            bc.carotenoids_mg, 
                            bc.probiotics_cfu, 
                            bc.prebiotic_fiber_g
                        ))
                    
                    # 5. Insert/update serving info if present
                    if food.serving_info:
                        si = food.serving_info
                        cursor.execute(SERVING_INFO_UPSERT, (
                            food_id, 
                            si.serving_size, 
                            si.serving_unit, 
                            si.household_serving
                        ))
                    
                    # 6. Insert/update data quality if present
                    if food.data_quality:
                        dq = food.data_quality
                        # Convert source_priority to JSON if it's a dict
                        sp = json.dumps(dq.source_priority) if dq.source_priority else None
                        
                        cursor.execute(DATA_QUALITY_UPSERT, (
                            food_id, 
                            dq.completeness, 
                            dq.overall_confidence,
                            dq.brain_nutrients_source, 
                            dq.impacts_source, 
                            sp
                        ))
                    
                    # 7. Insert/update metadata if present
                    if food.metadata:
                        md = food.metadata
                        # Convert arrays to JSON
                        source_urls = json.dumps(md.source_urls) if md.source_urls else '[]'
                        source_ids = json.dumps(md.source_ids) if md.source_ids else '{}'
                        tags = json.dumps(md.tags) if md.tags else '[]'
                        
                        cursor.execute(METADATA_UPSERT, (
                            food_id, 
                            md.version, 
                            md.created, 
                            md.last_updated,
                            md.image_url, 
                            source_urls, 
                            source_ids, 
                            tags
                        ))
                    
                    # 8. Insert/update mental health impacts if present
                    if food.mental_health_impacts:
                        # First delete existing impacts
                        cursor.execute(MENTAL_HEALTH_IMPACTS_DELETE, (food_id,))
                        
                        # Then insert each impact
                        for impact in food.mental_health_impacts:
                            cursor.execute(MENTAL_HEALTH_IMPACT_INSERT, (
                                food_id, 
                                impact.impact_type, 
                                impact.direction, 
                                impact.mechanism,
                                impact.strength, 
                                impact.confidence, 
                                impact.time_to_effect, 
                                impact.research_context, 
                                impact.notes
                            ))
                            
                            impact_id = cursor.fetchone()[0]
                            
                            # Insert research support for this impact
                            if impact.research_support:
                                for support in impact.research_support:
                                    cursor.execute(RESEARCH_SUPPORT_INSERT, (
                                        impact_id, 
                                        support.citation, 
                                        support.doi, 
                                        support.url,
                                        support.study_type, 
                                        support.year
                                    ))
                    
                    # 9. Insert/update nutrient interactions if present
                    if food.nutrient_interactions:
                        # First delete existing interactions
                        cursor.execute(NUTRIENT_INTERACTIONS_DELETE, (food_id,))
                        
                        # Then insert each interaction
                        for interaction in food.nutrient_interactions:
                            # Convert lists/objects to JSON
                            nutrients_involved = json.dumps(interaction.nutrients_involved)
                            research_support = json.dumps([r.__dict__ for r in interaction.research_support])
                            foods_demonstrating = json.dumps(interaction.foods_demonstrating)
                            
                            cursor.execute(NUTRIENT_INTERACTION_INSERT, (
                                food_id, 
                                interaction.interaction_id, 
                                interaction.interaction_type, 
                                interaction.pathway,
                                interaction.mechanism, 
                                interaction.mental_health_relevance, 
                                interaction.confidence,
                                nutrients_involved, 
                                research_support, 
                                foods_demonstrating
                            ))
                    
                    # 10. Insert/update contextual factors if present
                    if food.contextual_factors:
                        cf = food.contextual_factors
                        # Convert to JSON
                        circadian_effects = json.dumps(cf.circadian_effects.__dict__ if cf.circadian_effects else {})
                        food_combinations = json.dumps([c.__dict__ for c in cf.food_combinations])
                        preparation_effects = json.dumps([p.__dict__ for p in cf.preparation_effects])
                        
                        cursor.execute(CONTEXTUAL_FACTORS_UPSERT, (
                            food_id, 
                            circadian_effects, 
                            food_combinations, 
                            preparation_effects
                        ))
                    
                    # 11. Insert/update inflammatory index if present
                    if food.inflammatory_index:
                        ii = food.inflammatory_index
                        # Convert to JSON
                        citations = json.dumps(ii.citations)
                        
                        cursor.execute(INFLAMMATORY_INDEX_UPSERT, (
                            food_id, 
                            ii.value, 
                            ii.confidence, 
                            ii.calculation_method, 
                            citations
                        ))
                    
                    # 12. Insert/update neural targets if present
                    if food.neural_targets:
                        # First delete existing neural targets
                        cursor.execute(NEURAL_TARGETS_DELETE, (food_id,))
                        
                        # Then insert each target
                        for target in food.neural_targets:
                            # Convert to JSON
                            mechanisms = json.dumps(target.mechanisms)
                            
                            cursor.execute(NEURAL_TARGET_INSERT, (
                                food_id, 
                                target.pathway, 
                                target.effect, 
                                target.confidence,
                                mechanisms, 
                                target.mental_health_relevance
                            ))
                    
                    # 13. Insert/update population variations if present
                    if food.population_variations:
                        # First delete existing variations
                        cursor.execute(POPULATION_VARIATIONS_DELETE, (food_id,))
                        
                        # Then insert each variation
                        for variation in food.population_variations:
                            # Convert to JSON
                            variations_json = json.dumps([v.__dict__ for v in variation.variations])
                            
                            cursor.execute(POPULATION_VARIATION_INSERT, (
                                food_id, 
                                variation.population, 
                                variation.description, 
                                variations_json
                            ))
                    
                    # 14. Insert/update dietary patterns if present
                    if food.dietary_patterns:
                        # First delete existing patterns
                        cursor.execute(DIETARY_PATTERNS_DELETE, (food_id,))
                        
                        # Then insert each pattern
                        for pattern in food.dietary_patterns:
                            cursor.execute(DIETARY_PATTERN_INSERT, (
                                food_id, 
                                pattern.pattern_name, 
                                pattern.pattern_contribution,
                                pattern.mental_health_relevance
                            ))
                    
                    logger.info(f"Imported food with ID: {food_id}")
                    return food_id
                
        except Exception as e:
            logger.error(f"Error importing food from JSON: {e}")
            raise
    
    def get_food_by_id(self, food_id: str) -> Optional[FoodData]:
        """
        Get a complete food profile by ID.
        
        Args:
            food_id: Food ID (e.g., "usda_173950")
            
        Returns:
            Complete food data object or None if not found
        """
        try:
            # Get basic food information
            food_results = self.execute_query(FOOD_GET_BY_ID, (food_id,))
            
            if not food_results:
                logger.warning(f"Food with ID {food_id} not found")
                return None
            
            # Initialize food data with basic information
            food_data = FoodData(
                food_id=food_id,
                name=food_results[0]["name"],
                description=food_results[0]["description"],
                category=food_results[0]["category"],
            )
            
            # Get standard nutrients
            sn_results = self.execute_query(STANDARD_NUTRIENTS_GET_BY_FOOD_ID, (food_id,))
            if sn_results:
                food_data.standard_nutrients = {k: v for k, v in sn_results[0].items() if k != "food_id"}
            
            # Get brain nutrients
            bn_results = self.execute_query(BRAIN_NUTRIENTS_GET_BY_FOOD_ID, (food_id,))
            if bn_results:
                brain_nutrients = {k: v for k, v in bn_results[0].items() if k != "food_id"}
                
                # Get omega-3 fatty acids
                o3_results = self.execute_query(OMEGA3_GET_BY_FOOD_ID, (food_id,))
                if o3_results:
                    brain_nutrients["omega3"] = {k: v for k, v in o3_results[0].items() if k != "food_id"}
                
                food_data.brain_nutrients = brain_nutrients
            
            # Get bioactive compounds
            bc_results = self.execute_query(BIOACTIVE_COMPOUNDS_GET_BY_FOOD_ID, (food_id,))
            if bc_results:
                food_data.bioactive_compounds = {k: v for k, v in bc_results[0].items() if k != "food_id"}
            
            # Get serving info
            si_results = self.execute_query(SERVING_INFO_GET_BY_FOOD_ID, (food_id,))
            if si_results:
                food_data.serving_info = {k: v for k, v in si_results[0].items() if k != "food_id"}
            
            # Get data quality
            dq_results = self.execute_query(DATA_QUALITY_GET_BY_FOOD_ID, (food_id,))
            if dq_results:
                food_data.data_quality = {k: v for k, v in dq_results[0].items() if k != "food_id"}
            
            # Get metadata
            md_results = self.execute_query(METADATA_GET_BY_FOOD_ID, (food_id,))
            if md_results:
                food_data.metadata = {k: v for k, v in md_results[0].items() if k != "food_id"}
            
            # Get mental health impacts
            mhi_results = self.execute_query(MENTAL_HEALTH_IMPACTS_GET_BY_FOOD_ID, (food_id,))
            if mhi_results:
                impacts = []
                for impact in mhi_results:
                    impact_id = impact["id"]
                    impact_data = {k: v for k, v in impact.items() if k not in ["id", "food_id"]}
                    
                    # Get research support for this impact
                    rs_results = self.execute_query(RESEARCH_SUPPORT_GET_BY_IMPACT_ID, (impact_id,))
                    if rs_results:
                        impact_data["research_support"] = [
                            {k: v for k, v in support.items() if k not in ["id", "impact_id"]} 
                            for support in rs_results
                        ]
                    
                    impacts.append(impact_data)
                
                food_data.mental_health_impacts = impacts
            
            # Get nutrient interactions
            ni_results = self.execute_query(NUTRIENT_INTERACTIONS_GET_BY_FOOD_ID, (food_id,))
            if ni_results:
                food_data.nutrient_interactions = [
                    {k: v for k, v in interaction.items() if k not in ["id", "food_id"]} 
                    for interaction in ni_results
                ]
            
            # Get contextual factors
            cf_results = self.execute_query(CONTEXTUAL_FACTORS_GET_BY_FOOD_ID, (food_id,))
            if cf_results:
                food_data.contextual_factors = {k: v for k, v in cf_results[0].items() if k != "food_id"}
            
            # Get inflammatory index
            ii_results = self.execute_query(INFLAMMATORY_INDEX_GET_BY_FOOD_ID, (food_id,))
            if ii_results:
                food_data.inflammatory_index = {k: v for k, v in ii_results[0].items() if k != "food_id"}
            
            # Get neural targets
            nt_results = self.execute_query(NEURAL_TARGETS_GET_BY_FOOD_ID, (food_id,))
            if nt_results:
                food_data.neural_targets = [
                    {k: v for k, v in target.items() if k not in ["id", "food_id"]} 
                    for target in nt_results
                ]
            
            # Get population variations
            pv_results = self.execute_query(POPULATION_VARIATIONS_GET_BY_FOOD_ID, (food_id,))
            if pv_results:
                food_data.population_variations = [
                    {k: v for k, v in variation.items() if k not in ["id", "food_id"]} 
                    for variation in pv_results
                ]
            
            # Get dietary patterns
            dp_results = self.execute_query(DIETARY_PATTERNS_GET_BY_FOOD_ID, (food_id,))
            if dp_results:
                food_data.dietary_patterns = [
                    {k: v for k, v in pattern.items() if k not in ["id", "food_id"]} 
                    for pattern in dp_results
                ]
            
            return food_data
        
        except Exception as e:
            logger.error(f"Error retrieving food {food_id}: {e}")
            raise
    
    def get_all_foods_without_mental_health_impacts(self, limit: Optional[int] = None) -> List[FoodData]:
        limit_val = limit if limit is not None else 100  # Default limit
        
        try:
            results = self.execute_query(FOOD_GET_WITHOUT_IMPACTS, (limit_val,))
            
            foods = []
            for result in results:
                food_id = result["food_id"]
                food = self.get_food_by_id(food_id)
                if food:
                    foods.append(food)
            
            return foods
            
        except Exception as e:
            logger.error(f"Error getting foods without mental health impacts: {e}")
            return []
    
    def save_evaluation(self, food_id: str, test_run_id: str, evaluation_type: str, evaluation_data: Dict) -> bool:
        try:
            timestamp = datetime.now().isoformat()
            
            result = self.execute_query(
                FOOD_EVALUATION_INSERT,
                (food_id, test_run_id, timestamp, evaluation_type, json.dumps(evaluation_data))
            )
            
            return bool(result)
            
        except Exception as e:
            logger.error(f"Error saving evaluation for {food_id}: {e}")
            return False
    
    def save_evaluation_metrics(self, test_run_id: str, metrics_type: str, metrics_data: Dict) -> bool:
        try:
            timestamp = datetime.now().isoformat()
            
            result = self.execute_query(
                EVALUATION_METRICS_INSERT,
                (test_run_id, timestamp, metrics_type, json.dumps(metrics_data))
            )
            
            return bool(result)
            
        except Exception as e:
            logger.error(f"Error saving evaluation metrics: {e}")
            return False
    
    def get_latest_evaluation_metrics(self, metrics_type: str) -> Optional[Dict]:
        try:
            results = self.execute_query(EVALUATION_METRICS_GET_LATEST, (metrics_type,))
            
            if results:
                return results[0]["metrics_data"]
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting latest evaluation metrics: {e}")
            return None