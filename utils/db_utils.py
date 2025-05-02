# utils/db_utils.py
"""
Database utilities for the Nutritional Psychiatry Dataset project.
"""

import logging
from typing import Dict, List, Any, Optional, Union
from contextlib import contextmanager
import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
from psycopg2 import pool

# Initialize logger
logger = logging.getLogger(__name__)

def create_connection_pool(
    connection_string: str,
    min_connections: int = 1,
    max_connections: int = 10
) -> pool.ThreadedConnectionPool:
    """
    Create a PostgreSQL connection pool.
    
    Args:
        connection_string: PostgreSQL connection string
        min_connections: Minimum number of connections
        max_connections: Maximum number of connections
    
    Returns:
        ThreadedConnectionPool instance
    
    Raises:
        psycopg2.OperationalError: If connection fails
    """
    try:
        connection_pool = pool.ThreadedConnectionPool(
            min_connections,
            max_connections,
            connection_string
        )
        logger.info(f"Created connection pool with {min_connections}-{max_connections} connections")
        return connection_pool
    except Exception as e:
        logger.error(f"Failed to create connection pool: {e}")
        raise

@contextmanager
def get_connection(connection_pool: pool.ThreadedConnectionPool, cursor_factory=None):
    """
    Get a connection from the pool.
    
    Args:
        connection_pool: ThreadedConnectionPool instance
        cursor_factory: Optional cursor factory
    
    Yields:
        Connection object
    """
    connection = None
    try:
        connection = connection_pool.getconn()
        if cursor_factory:
            connection.cursor_factory = cursor_factory
        yield connection
    finally:
        if connection:
            connection_pool.putconn(connection)

@contextmanager
def get_cursor(connection_pool: pool.ThreadedConnectionPool, cursor_factory=RealDictCursor):
    """
    Get a database cursor.
    
    Args:
        connection_pool: ThreadedConnectionPool instance
        cursor_factory: Cursor factory
    
    Yields:
        Cursor object
    """
    with get_connection(connection_pool) as connection:
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

def execute_query(
    cursor: RealDictCursor,
    query: str,
    params: Optional[tuple] = None,
    fetch: bool = True
) -> Union[List[Dict], int]:
    """
    Execute a database query with proper error handling.
    
    Args:
        cursor: Database cursor
        query: SQL query string
        params: Query parameters
        fetch: Whether to fetch results
    
    Returns:
        Query results or number of affected rows
    """
    try:
        cursor.execute(query, params)
        if fetch:
            return cursor.fetchall()
        return cursor.rowcount
    except Exception as e:
        logger.error(f"Query execution failed: {e}")
        raise

def batch_insert(
    cursor: RealDictCursor,
    table: str,
    columns: List[str],
    values: List[tuple],
    page_size: int = 100
) -> int:
    """
    Perform a batch insert operation.
    
    Args:
        cursor: Database cursor
        table: Table name
        columns: Column names
        values: List of value tuples
        page_size: Number of rows per insert
    
    Returns:
        Number of rows inserted
    """
    try:
        return execute_values(
            cursor,
            f"INSERT INTO {table} ({','.join(columns)}) VALUES %s",
            values,
            page_size=page_size,
            fetch=False
        )
    except Exception as e:
        logger.error(f"Batch insert failed: {e}")
        raise

def validate_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """
    Validate data against a schema.
    
    Args:
        data: Data to validate
        schema: Schema definition
    
    Returns:
        List of validation errors
    """
    errors = []
    # TODO: Implement schema validation
    return errors 