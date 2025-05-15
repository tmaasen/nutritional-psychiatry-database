#!/usr/bin/env python3
"""
Database utilities for the Nutritional Psychiatry Database project.

This module provides utilities for database connection management, query execution,
and data import/export operations.
"""

import json
import logging
from typing import Dict, List, Optional, Union, Tuple
from contextlib import contextmanager
from psycopg2.extras import RealDictCursor, execute_values
from psycopg2 import pool

from config import get_env

from schema.food_data import FoodData

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
        """
        Perform a batch insert operation.
        
        Args:
            table: Table name
            columns: Column names
            values: List of value tuples
            page_size: Number of rows per insert
            
        Returns:
            Number of rows inserted
        """
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
    
    # Food retrieval methods
    
    def get_food_by_id(self, food_id: str) -> Optional[FoodData]:
        """
        Get a complete food profile by ID.
        
        Args:
            food_id: Food ID (e.g., "usda_173950")
            
        Returns:
            Complete food data dictionary or None if not found
        """
        try:
            food_data = self.execute_query(
                "SELECT get_complete_food_profile(%s) AS food_data",
                (food_id,)
            )[0]['food_data']

            return FoodData.from_dict(food_data)
        except Exception as e:
            logger.error(f"Error getting food {food_id}: {e}")
            raise

    # Data import/export methods for migration and backup only
    
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
            
            result = self.execute_query(
                "SELECT import_food_from_json(%s::jsonb) AS food_id",
                (json_str,)
            )[0]
            
            food_id = result['food_id']
            logger.info(f"Imported food with ID: {food_id}")
            return food_id
                
        except Exception as e:
            logger.error(f"Error importing food from JSON: {e}")
            raise
    
    def export_food_to_json(self, food_id: str) -> Dict:
        """
        Export a food to JSON format.
        
        Args:
            food_id: Food ID to export
            
        Returns:
            Food data dictionary
        """
        try:
            food_data = self.get_food_by_id(food_id)
            
            if not food_data:
                raise ValueError(f"Food with ID {food_id} not found")
            
            return food_data
            
        except Exception as e:
            logger.error(f"Error exporting food {food_id}: {e}")
            raise