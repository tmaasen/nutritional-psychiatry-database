#!/usr/bin/env python3
"""
PostgreSQL Database Client for Nutritional Psychiatry Dataset

This module provides a client for interacting with the Nutritional Psychiatry Dataset
PostgreSQL database. It handles connection management and provides methods for
querying, inserting, updating, and deleting food data.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Union, Tuple
from contextlib import contextmanager
import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
from psycopg2 import pool
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class PostgresClient:
    """
    Client for interacting with the Nutritional Psychiatry Dataset PostgreSQL database.
    
    This client handles connection management and provides methods for common
    database operations related to food data.
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
            connection_string: PostgreSQL connection string (defaults to environment variable)
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
        db_host = os.getenv("DB_HOST")
        # db_port = os.getenv("DB_PORT", "5432")
        db_name = os.getenv("DB_NAME")
        db_user = os.getenv("DB_USER")
        db_password = os.getenv("DB_PASSWORD")
        
        if not all([db_host, db_name, db_user, db_password]):
            raise ValueError("Database connection details not found in environment variables")
        
        # Neon.tech typically uses SSL connections
        sslmode = os.getenv("DB_SSLMODE", "require")
        
        return (f"postgresql://{db_user}:{db_password}@{db_host}/{db_name}"
                f"?sslmode={sslmode}")
    
    @contextmanager
    def get_connection(self, cursor_factory=None):
        """
        Get a connection from the pool.
        
        Args:
            cursor_factory: Optional cursor factory (e.g., RealDictCursor)
            
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
            cursor_factory: Cursor factory (defaults to RealDictCursor)
            
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
    
    # Food retrieval methods
    
    def get_food_by_id(self, food_id: str) -> Optional[Dict]:
        """
        Get a complete food profile by ID.
        
        Args:
            food_id: Food ID (e.g., "usda_173950")
            
        Returns:
            Complete food data dictionary or None if not found
        """
        try:
            with self.get_cursor() as cursor:
                cursor.execute(
                    "SELECT get_complete_food_profile(%s) AS food_data",
                    (food_id,)
                )
                result = cursor.fetchone()
                return result['food_data'] if result else None
        except Exception as e:
            logger.error(f"Error getting food {food_id}: {e}")
            raise
    
    def get_foods_by_name(self, name_pattern: str, limit: int = 10) -> List[Dict]:
        """
        Search for foods by name pattern.
        
        Args:
            name_pattern: Name pattern to search (case-insensitive, partial match)
            limit: Maximum number of results
            
        Returns:
            List of matching food dictionaries
        """
        try:
            with self.get_cursor() as cursor:
                cursor.execute(
                    """
                    SELECT f.food_id, f.name, f.category 
                    FROM foods f
                    WHERE f.name ILIKE %s
                    ORDER BY f.name
                    LIMIT %s
                    """,
                    (f"%{name_pattern}%", limit)
                )
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error searching foods by name '{name_pattern}': {e}")
            raise
    
    def get_foods_by_category(self, category: str, limit: int = 50) -> List[Dict]:
        """
        Get foods by category.
        
        Args:
            category: Food category
            limit: Maximum number of results
            
        Returns:
            List of food dictionaries
        """
        try:
            with self.get_cursor() as cursor:
                cursor.execute(
                    """
                    SELECT f.food_id, f.name, f.category 
                    FROM foods f
                    WHERE f.category = %s
                    ORDER BY f.name
                    LIMIT %s
                    """,
                    (category, limit)
                )
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error getting foods by category '{category}': {e}")
            raise
    
    def get_all_food_categories(self) -> List[str]:
        """
        Get all available food categories.
        
        Returns:
            List of category strings
        """
        try:
            with self.get_cursor() as cursor:
                cursor.execute(
                    """
                    SELECT DISTINCT category 
                    FROM foods 
                    ORDER BY category
                    """
                )
                results = cursor.fetchall()
                return [result['category'] for result in results if result['category']]
        except Exception as e:
            logger.error(f"Error getting food categories: {e}")
            raise
    
    # Nutrient-specific methods
    
    def get_foods_by_nutrient(
        self, 
        nutrient_name: str, 
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        limit: int = 20
    ) -> List[Dict]:
        """
        Get foods by nutrient content range.
        
        Args:
            nutrient_name: Name of the nutrient 
            min_value: Minimum nutrient value (optional)
            max_value: Maximum nutrient value (optional)
            limit: Maximum number of results
            
        Returns:
            List of food dictionaries with nutrient values
        """
        try:
            with self.get_cursor() as cursor:
                cursor.execute(
                    """
                    SELECT * FROM search_foods_by_nutrient(%s, %s, %s) LIMIT %s
                    """,
                    (nutrient_name, min_value, max_value, limit)
                )
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error searching foods by nutrient '{nutrient_name}': {e}")
            raise
    
    def get_foods_for_mental_health(
        self,
        impact_type: str,
        direction: Optional[str] = None,
        min_strength: Optional[int] = None,
        min_confidence: Optional[int] = None,
        limit: int = 20
    ) -> List[Dict]:
        """
        Get foods for a specific mental health goal.
        
        Args:
            impact_type: Type of mental health impact
            direction: Direction of effect (positive, negative, neutral, mixed)
            min_strength: Minimum strength (1-10)
            min_confidence: Minimum confidence (1-10)
            limit: Maximum number of results
            
        Returns:
            List of food dictionaries with impact details
        """
        try:
            with self.get_cursor() as cursor:
                cursor.execute(
                    """
                    SELECT * FROM find_foods_for_mental_health(%s, %s, %s, %s) LIMIT %s
                    """,
                    (impact_type, direction, min_strength, min_confidence, limit)
                )
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error finding foods for mental health impact '{impact_type}': {e}")
            raise
    
    # Data import methods
    
    def import_food_from_json(self, food_json: Union[Dict, str]) -> str:
        """
        Import a food from JSON data.
        
        Args:
            food_json: Food data as dictionary or JSON string
            
        Returns:
            Food ID of the imported food
        """
        try:
            # Convert string to dict if needed
            if isinstance(food_json, str):
                food_data = json.loads(food_json)
            else:
                food_data = food_json
            
            # Convert dict to JSON string for Postgres function
            json_str = json.dumps(food_data)
            
            with self.get_cursor() as cursor:
                cursor.execute(
                    "SELECT import_food_from_json(%s::jsonb) AS food_id",
                    (json_str,)
                )
                result = cursor.fetchone()
                food_id = result['food_id']
                logger.info(f"Imported food with ID: {food_id}")
                return food_id
                
        except Exception as e:
            logger.error(f"Error importing food from JSON: {e}")
            raise
    
    def import_foods_from_file(self, file_path: str) -> List[str]:
        """
        Import multiple foods from a JSON file.
        
        Args:
            file_path: Path to JSON file (can contain a list or a single object)
            
        Returns:
            List of imported food IDs
        """
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            food_ids = []
            
            # Handle both list and single object formats
            if isinstance(data, list):
                for food_data in data:
                    food_id = self.import_food_from_json(food_data)
                    food_ids.append(food_id)
            else:
                food_id = self.import_food_from_json(data)
                food_ids.append(food_id)
            
            logger.info(f"Imported {len(food_ids)} foods from {file_path}")
            return food_ids
            
        except Exception as e:
            logger.error(f"Error importing foods from file {file_path}: {e}")
            raise
    
    def import_directory(self, directory: str) -> Dict[str, List[str]]:
        """
        Import all JSON files from a directory.
        
        Args:
            directory: Directory path containing JSON food files
            
        Returns:
            Dictionary with successful and failed imports
        """
        import glob
        
        try:
            json_files = glob.glob(os.path.join(directory, "*.json"))
            logger.info(f"Found {len(json_files)} JSON files in {directory}")
            
            results = {
                "successful": [],
                "failed": []
            }
            
            for file_path in json_files:
                try:
                    food_ids = self.import_foods_from_file(file_path)
                    results["successful"].extend(food_ids)
                    logger.info(f"Imported {len(food_ids)} foods from {file_path}")
                except Exception as e:
                    logger.error(f"Failed to import {file_path}: {e}")
                    results["failed"].append(file_path)
            
            logger.info(f"Import complete: {len(results['successful'])} successful, "
                       f"{len(results['failed'])} failed")
            return results
            
        except Exception as e:
            logger.error(f"Error importing directory {directory}: {e}")
            raise
    
    # Data export methods
    
    def export_food_to_json(self, food_id: str, file_path: Optional[str] = None) -> Dict:
        """
        Export a food to JSON format.
        
        Args:
            food_id: Food ID to export
            file_path: Optional file path to save JSON
            
        Returns:
            Food data dictionary
        """
        try:
            # Get complete food data
            food_data = self.get_food_by_id(food_id)
            
            if not food_data:
                raise ValueError(f"Food with ID {food_id} not found")
            
            # Save to file if path provided
            if file_path:
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, 'w') as f:
                    json.dump(food_data, f, indent=2)
                logger.info(f"Exported food {food_id} to {file_path}")
            
            return food_data
            
        except Exception as e:
            logger.error(f"Error exporting food {food_id}: {e}")
            raise
    
    def export_foods_by_category(self, category: str, output_dir: str) -> List[str]:
        """
        Export all foods in a category to JSON files.
        
        Args:
            category: Category to export
            output_dir: Directory to save JSON files
            
        Returns:
            List of exported file paths
        """
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            # Get foods in category
            foods = self.get_foods_by_category(category)
            
            exported_files = []
            for food in foods:
                food_id = food['food_id']
                file_name = f"{food_id}.json"
                file_path = os.path.join(output_dir, file_name)
                
                self.export_food_to_json(food_id, file_path)
                exported_files.append(file_path)
            
            logger.info(f"Exported {len(exported_files)} foods in category '{category}'")
            return exported_files
            
        except Exception as e:
            logger.error(f"Error exporting foods in category '{category}': {e}")
            raise

    # Advanced query methods
    
    def get_food_nutrient_profiles(self, limit: int = 100) -> List[Dict]:
        """
        Get food nutrient profiles using the food_nutrient_profiles view.
        
        Args:
            limit: Maximum number of profiles to return
            
        Returns:
            List of food nutrient profiles
        """
        try:
            with self.get_cursor() as cursor:
                cursor.execute(
                    """
                    SELECT * FROM food_nutrient_profiles
                    LIMIT %s
                    """,
                    (limit,)
                )
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error getting food nutrient profiles: {e}")
            raise
    
    def get_foods_by_dietary_pattern(self, pattern: str) -> List[Dict]:
        """
        Get foods by dietary pattern.
        
        Args:
            pattern: Dietary pattern name
            
        Returns:
            List of foods in the specified dietary pattern
        """
        try:
            with self.get_cursor() as cursor:
                cursor.execute(
                    """
                    SELECT * FROM foods_by_dietary_pattern
                    WHERE pattern_name = %s
                    """,
                    (pattern,)
                )
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error getting foods by dietary pattern '{pattern}': {e}")
            raise
    
    # Management methods
    
    def _execute_query(self, query: str, params: Optional[Tuple] = None) -> int:
        """
        Execute a raw query, returning the number of affected rows.
        
        Args:
            query: SQL query
            params: Query parameters
            
        Returns:
            Number of affected rows
        """
        try:
            with self.get_cursor() as cursor:
                cursor.execute(query, params or ())
                return cursor.rowcount
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            raise
    
    def delete_food(self, food_id: str) -> bool:
        """
        Delete a food by ID.
        
        Args:
            food_id: Food ID to delete
            
        Returns:
            True if deletion was successful
        """
        try:
            # Using cascading foreign keys to handle related tables
            rows_affected = self._execute_query(
                "DELETE FROM foods WHERE food_id = %s",
                (food_id,)
            )
            return rows_affected > 0
        except Exception as e:
            logger.error(f"Error deleting food {food_id}: {e}")
            raise