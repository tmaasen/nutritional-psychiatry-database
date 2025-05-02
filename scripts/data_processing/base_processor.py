"""
Base processor for the Nutritional Psychiatry Dataset project.
"""

import logging
from typing import Dict, Any, Optional, List
from data.postgres_client import PostgresClient

# Initialize logger
logger = logging.getLogger(__name__)

class BaseProcessor:
    """
    Base class for data processors in the Nutritional Psychiatry Dataset project.
    
    This class provides common functionality for processing data,
    including validation, transformation, and database operations.
    """
    
    def __init__(
        self,
        db_client: Optional[PostgresClient] = None,
        schema_path: Optional[str] = None
    ):
        """
        Initialize the processor.
        
        Args:
            db_client: Database client for storing results
            schema_path: Path to JSON schema file
        """
        self.db_client = db_client
        self.schema_path = schema_path
        
        # Initialize logger
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process data according to the processor's logic.
        
        Args:
            data: Data to process
        
        Returns:
            Processed data
        """
        raise NotImplementedError("Subclasses must implement process()")
    
    def validate(self, data: Dict[str, Any]) -> List[str]:
        """
        Validate data against schema and business rules.
        
        Args:
            data: Data to validate
        
        Returns:
            List of validation errors
        """
        raise NotImplementedError("Subclasses must implement validate()")
    
    def transform(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform data to match the target schema.
        
        Args:
            data: Data to transform
        
        Returns:
            Transformed data
        """
        raise NotImplementedError("Subclasses must implement transform()")
    
    def save_to_database(self, data: Dict[str, Any]) -> str:
        """
        Save processed data to the database.
        
        Args:
            data: Data to save
        
        Returns:
            Database ID of saved item
        """
        if not self.db_client:
            raise ValueError("Database client not initialized")
        
        try:
            return self.db_client.import_food_from_json(data)
        except Exception as e:
            self.logger.error(f"Error saving to database: {e}")
            raise
    
    def load_from_database(self, item_id: str) -> Dict[str, Any]:
        """
        Load data from the database.
        
        Args:
            item_id: Database ID of item
        
        Returns:
            Item data
        """
        if not self.db_client:
            raise ValueError("Database client not initialized")
        
        try:
            return self.db_client.get_food_by_id(item_id)
        except Exception as e:
            self.logger.error(f"Error loading from database: {e}")
            raise
    
    def process_batch(
        self,
        items: List[Dict[str, Any]],
        batch_size: int = 100
    ) -> List[str]:
        """
        Process a batch of items.
        
        Args:
            items: List of items to process
            batch_size: Number of items to process at once
        
        Returns:
            List of database IDs for processed items
        """
        processed_ids = []
        
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            self.logger.info(f"Processing batch {i//batch_size + 1} of {(len(items) + batch_size - 1)//batch_size}")
            
            for item in batch:
                try:
                    # Process and validate
                    processed = self.process(item)
                    errors = self.validate(processed)
                    
                    if errors:
                        self.logger.warning(f"Validation errors for item: {errors}")
                        continue
                    
                    # Save to database
                    item_id = self.save_to_database(processed)
                    processed_ids.append(item_id)
                    
                except Exception as e:
                    self.logger.error(f"Error processing item: {e}")
                    continue
        
        return processed_ids 