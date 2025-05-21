#!/usr/bin/env python3
"""
Database utilities for the Nutritional Psychiatry Database project.

This module provides utilities for database connection management, query execution,
and data import/export operations.
"""

import json
import logging
import time
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
    
    def __enter__(self):
        """Enable usage with context manager for automatic resource cleanup."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cleanup resources when exiting context manager."""
        self.close()
    
    def __del__(self):
        """Ensure connection pool is closed when object is garbage collected."""
        try:
            self.close()
        except Exception:
            pass
        
    def is_connected(self):
        """Check if the database connection is working."""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"Database connection check failed: {e}")
            return False
        
    def reconnect(self, max_attempts=3, delay=1.0):
        """Attempt to reconnect to the database."""
        attempt = 0
        while attempt < max_attempts:
            try:
                if hasattr(self, 'connection_pool'):
                    try:
                        self.connection_pool.closeall()
                    except Exception:
                        pass
                    
                self.connection_pool = pool.ThreadedConnectionPool(
                    1, 10,
                    self.connection_string
                )
                
                if self.is_connected():
                    return True
                    
            except Exception as e:
                logger.error(f"Database reconnection failed: {e}")
                
            attempt += 1
            time.sleep(delay * (2 ** attempt))
            
        logger.critical("Failed to reconnect to database after multiple attempts")
        return False

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
            if isinstance(food_json, str):
                food_data = json.loads(food_json)
                food = FoodData.from_dict(food_data)
            elif isinstance(food_json, dict):
                food = FoodData.from_dict(food_json)
            else:
                food = food_json
            
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(FOOD_UPSERT, (
                        food.food_id, 
                        food.name, 
                        food.description, 
                        food.category,
                        food.processed if hasattr(food, 'processed') else False,
                        food.validated if hasattr(food, 'validated') else False
                    ))
                    
                    food_id = cursor.fetchone()[0]
                    
                    if food.standard_nutrients:
                        sn = food.standard_nutrients
                        cursor.execute(STANDARD_NUTRIENTS_UPSERT, (
                            food_id, 
                            getattr(sn, 'calories', None), 
                            getattr(sn, 'protein_g', None), 
                            getattr(sn, 'carbohydrates_g', None), 
                            getattr(sn, 'fat_g', None), 
                            getattr(sn, 'fiber_g', None),
                            getattr(sn, 'sugars_g', None), 
                            getattr(sn, 'sugars_added_g', None), 
                            getattr(sn, 'calcium_mg', None), 
                            getattr(sn, 'iron_mg', None), 
                            getattr(sn, 'magnesium_mg', None),
                            getattr(sn, 'phosphorus_mg', None), 
                            getattr(sn, 'potassium_mg', None), 
                            getattr(sn, 'sodium_mg', None), 
                            getattr(sn, 'zinc_mg', None), 
                            getattr(sn, 'copper_mg', None),
                            getattr(sn, 'manganese_mg', None), 
                            getattr(sn, 'selenium_mcg', None), 
                            getattr(sn, 'vitamin_c_mg', None), 
                            getattr(sn, 'vitamin_a_iu', None)
                        ))
                    
                    if food.brain_nutrients:
                        bn = food.brain_nutrients
                        cursor.execute(BRAIN_NUTRIENTS_UPSERT, (
                            food_id, 
                            getattr(bn, 'tryptophan_mg', None), 
                            getattr(bn, 'tyrosine_mg', None), 
                            getattr(bn, 'vitamin_b6_mg', None), 
                            getattr(bn, 'folate_mcg', None),
                            getattr(bn, 'vitamin_b12_mcg', None), 
                            getattr(bn, 'vitamin_d_mcg', None), 
                            getattr(bn, 'magnesium_mg', None), 
                            getattr(bn, 'zinc_mg', None), 
                            getattr(bn, 'iron_mg', None),
                            getattr(bn, 'selenium_mcg', None), 
                            getattr(bn, 'choline_mg', None)
                        ))
                        
                        if hasattr(bn, 'omega3') and bn.omega3:
                            o3 = bn.omega3
                            cursor.execute(OMEGA3_UPSERT, (
                                food_id, 
                                getattr(o3, 'total_g', None), 
                                getattr(o3, 'epa_mg', None), 
                                getattr(o3, 'dha_mg', None), 
                                getattr(o3, 'ala_mg', None),
                                getattr(o3, 'confidence', None)
                            ))
                    
                    if hasattr(food, 'bioactive_compounds') and food.bioactive_compounds:
                        bc = food.bioactive_compounds
                        cursor.execute(BIOACTIVE_COMPOUNDS_UPSERT, (
                            food_id, 
                            getattr(bc, 'polyphenols_mg', None), 
                            getattr(bc, 'flavonoids_mg', None), 
                            getattr(bc, 'anthocyanins_mg', None),
                            getattr(bc, 'carotenoids_mg', None), 
                            getattr(bc, 'probiotics_cfu', None), 
                            getattr(bc, 'prebiotic_fiber_g', None)
                        ))
                    
                    if hasattr(food, 'serving_info') and food.serving_info:
                        si = food.serving_info
                        cursor.execute(SERVING_INFO_UPSERT, (
                            food_id, 
                            getattr(si, 'serving_size', None), 
                            getattr(si, 'serving_unit', None), 
                            getattr(si, 'household_serving', None)
                        ))
                    
                    if hasattr(food, 'data_quality') and food.data_quality:
                        dq = food.data_quality
                        sp = None
                        if hasattr(dq, 'source_priority') and dq.source_priority:
                            if hasattr(dq.source_priority, '__dict__'):
                                sp = json.dumps(dq.source_priority.__dict__)
                            else:
                                sp = json.dumps(dq.source_priority)
                        
                        cursor.execute(DATA_QUALITY_UPSERT, (
                            food_id, 
                            getattr(dq, 'completeness', None), 
                            getattr(dq, 'overall_confidence', None),
                            getattr(dq, 'brain_nutrients_source', None), 
                            getattr(dq, 'impacts_source', None), 
                            sp
                        ))
                    
                    if hasattr(food, 'metadata') and food.metadata:
                        md = food.metadata
                        source_urls = json.dumps(md.source_urls) if hasattr(md, 'source_urls') and md.source_urls else '[]'
                        source_ids = json.dumps(md.source_ids) if hasattr(md, 'source_ids') and md.source_ids else '{}'
                        tags = json.dumps(md.tags) if hasattr(md, 'tags') and md.tags else '[]'
                        
                        cursor.execute(METADATA_UPSERT, (
                            food_id, 
                            getattr(md, 'version', None), 
                            getattr(md, 'created', None), 
                            getattr(md, 'last_updated', None),
                            getattr(md, 'image_url', None), 
                            source_urls, 
                            source_ids, 
                            tags
                        ))
                    
                    if hasattr(food, 'mental_health_impacts') and food.mental_health_impacts:
                        cursor.execute(MENTAL_HEALTH_IMPACTS_DELETE, (food_id,))
                        
                        for impact in food.mental_health_impacts:
                            cursor.execute(MENTAL_HEALTH_IMPACT_INSERT, (
                                food_id, 
                                getattr(impact, 'impact_type', None), 
                                getattr(impact, 'direction', None), 
                                getattr(impact, 'mechanism', None),
                                getattr(impact, 'strength', None), 
                                getattr(impact, 'confidence', None), 
                                getattr(impact, 'time_to_effect', None), 
                                getattr(impact, 'research_context', None), 
                                getattr(impact, 'notes', None)
                            ))
                            
                            impact_id = cursor.fetchone()[0]
                            
                            if hasattr(impact, 'research_support') and impact.research_support:
                                for support in impact.research_support:
                                    cursor.execute(RESEARCH_SUPPORT_INSERT, (
                                        impact_id, 
                                        getattr(support, 'citation', None), 
                                        getattr(support, 'doi', None), 
                                        getattr(support, 'url', None),
                                        getattr(support, 'study_type', None), 
                                        getattr(support, 'year', None)
                                    ))
                    
                    conn.commit()
                    return food_id
                    
        except Exception as e:
            logger.error(f"Error importing food from JSON: {e}")
            raise

    def get_food_by_id_or_name(self, food_id: Optional[str], food_name: Optional[str]) -> Optional[FoodData]:
        """
        Get a complete food profile by ID.
        
        Args:
            food_id: Food ID (e.g., "usda_173950")
            
        Returns:
            Complete food data object or None if not found
        """
        try:
            if food_id:
                food_results = self.execute_query(FOOD_GET_BY_ID, (food_id,))
            elif food_name:
                food_results = self.execute_query(FOOD_GET_BY_NAME, (food_name,))
            
            if not food_results:
                logger.warning(f"Food with ID {food_id} not found")
                return None
            
            # Initialize required fields
            standard_nutrients = {}
            food_id = food_results[0]["food_id"]
            name = food_results[0]["name"]
            data_quality = {}
            metadata = {}

            food_data = FoodData(
                food_id=food_id,
                name=name, 
                description=food_results[0]["description"],
                category=food_results[0]["category"],
                standard_nutrients=standard_nutrients,
                data_quality=data_quality,
                metadata=metadata
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
                food = self.get_food_by_id_or_name(food_id)
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