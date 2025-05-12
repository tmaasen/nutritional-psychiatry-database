# utils/json_utils.py
"""
Utilities for robust JSON parsing of AI responses.
"""

import json
import re
from typing import Dict, Any, Optional

from utils.logging_utils import setup_logging

logger = setup_logging(__name__)

class JSONParser:
    """Provides robust JSON parsing for AI responses."""
    
    @staticmethod
    def extract_json(text: str) -> Optional[str]:
        """
        Extract JSON string from text that might contain other content.
        
        Args:
            text: Text potentially containing JSON
            
        Returns:
            Extracted JSON string or None if not found
        """
        # Try to find JSON between curly braces
        json_match = re.search(r'(\{.*\})', text, re.DOTALL)
        if json_match:
            return json_match.group(1)
        
        # Try to find JSON between square brackets
        json_match = re.search(r'(\[.*\])', text, re.DOTALL)
        if json_match:
            return json_match.group(1)
        
        return None
    
    @staticmethod
    def parse_json(text: str, default: Any = None) -> Dict:
        """
        Safely parse JSON from text with fallback.
        
        Args:
            text: Text containing JSON
            default: Default value if parsing fails
            
        Returns:
            Parsed JSON or default value
        """
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to extract JSON from text
            json_str = JSONParser.extract_json(text)
            if json_str:
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    logger.warning(f"Could not parse JSON even after extraction: {json_str[:100]}...")
            
            logger.error(f"Failed to parse JSON: {text[:100]}...")
            return default if default is not None else {}
    
    @staticmethod
    def validate_json_schema(data: Dict, required_fields: list) -> bool:
        """
        Validate that JSON contains required fields.
        
        Args:
            data: JSON data to validate
            required_fields: List of required field names
            
        Returns:
            True if valid, False otherwise
        """
        return all(field in data for field in required_fields)