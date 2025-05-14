# utils/prompt_template_utils.py
import re
import os
import json
import glob
from typing import Dict, Any, Optional

from utils.logging_utils import setup_logging

logger = setup_logging(__name__)

class TemplateManager:
    """Manages loading and processing of templates."""
    
    @staticmethod
    def load_template(template_id: str, template_dir: Optional[str] = None) -> Dict:
        if not template_dir:
            from constants.ai_constants import TEMPLATE_DIR
            template_dir = TEMPLATE_DIR
            
        template_pattern = os.path.join(template_dir, "*.json")
        template_files = glob.glob(template_pattern)
        
        for file_path in template_files:
            try:
                with open(file_path, 'r') as f:
                    template_data = json.load(f)
                    if template_data.get("template_id") == template_id:
                        return template_data
            except Exception as e:
                logger.error(f"Error loading template from {file_path}: {e}")
        
        raise ValueError(f"Template with ID '{template_id}' not found")

    @staticmethod
    def sanitize_variables(variables: Dict[str, Any]) -> Dict[str, Any]:
        sanitized = {}
        for key, value in variables.items():
            if isinstance(value, str):
                # Remove potential template control sequences
                sanitized[key] = re.sub(r'\{%.*?%\}', '', value)
            elif isinstance(value, (dict, list)):
                # For dicts/lists, preserve structure
                sanitized[key] = value
            else:
                sanitized[key] = value
        return sanitized

    @staticmethod
    def substitute_template_variables(template_str: str, variables: Dict[str, Any]) -> str:
        # First sanitize the variables
        variables = TemplateManager.sanitize_variables(variables)
        
        # Handle conditional blocks with {% if condition %}...{% endif %} syntax
        pattern = r'{%\s*if\s+(\w+)\s*%}(.*?){%\s*endif\s*%}'
    
        def replace_conditional(match):
            condition_var = match.group(1)
            content = match.group(2)
            
            if condition_var in variables and variables[condition_var]:
                return content
            return ""
    
        # Replace conditionals
        template_str = re.sub(pattern, replace_conditional, template_str, flags=re.DOTALL)
        
        # Replace variables {{var}} with their values
        pattern = r'{{(\w+(?:_\w+)*)}}'
        
        def replace_var(match):
            var_name = match.group(1)
            if var_name in variables:
                value = variables[var_name]
                # Handle JSON serialization for dict values
                if isinstance(value, (dict, list)):
                    return json.dumps(value, indent=2)
                return str(value)
            return match.group(0)  # Keep original if not found
    
        return re.sub(pattern, replace_var, template_str)

    @staticmethod
    def create_messages_from_template(template_id: str, variables: Dict[str, Any]) -> list:
        """
        Create messages for API request from a template.
        
        Args:
            template_id: Template identifier
            variables: Dictionary of variable values
            
        Returns:
            List of message dictionaries
        """
        template = TemplateManager.load_template(template_id)
        
        system_prompt = template.get("system_prompt", "")
        user_prompt_template = template.get("user_prompt_template", "")
        
        # Substitute variables
        user_prompt = TemplateManager.substitute_template_variables(user_prompt_template, variables)
        
        # Create messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return messages