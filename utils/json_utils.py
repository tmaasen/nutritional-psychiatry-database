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
        json_match = re.search(r'(\{.*\})', text, re.DOTALL)
        if json_match:
            return json_match.group(1)
        
        json_match = re.search(r'(\[.*\])', text, re.DOTALL)
        if json_match:
            return json_match.group(1)
        
        return None
    
    @staticmethod
    def parse_json(text: str, default: Any = None) -> Dict:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
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
        return all(field in data for field in required_fields)