#!/usr/bin/env python3
"""
OpenAI API Client for Nutritional Psychiatry Dataset

This client handles all interactions with the OpenAI API for data enrichment:
- Brain-specific nutrient prediction
- Bioactive compound estimation
- Mental health impact relationship generation
- Mechanism of action identification
- Confidence scoring calibration

Features:
- Configurable model selection
- Tiered fallback strategy for API errors
- Request rate limiting
- Response validation
- Cost tracking
- Comprehensive logging
"""

import os
import json
import time
import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple, Union
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import openai
from openai import AsyncOpenAI, OpenAI
import re
import glob
from string import Template

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OpenAIClient:
    """Client for interacting with OpenAI API for nutritional psychiatry data enrichment."""
    
    # Default models to use for different tasks
    DEFAULT_MODELS = {
        "nutrient_prediction": "gpt-4o-mini",
        "bioactive_prediction": "gpt-4o-mini",
        "impact_generation": "gpt-4o-mini",
        "mechanism_identification": "gpt-4o-mini",
        "confidence_calibration": "gpt-4o-mini",
        "fallback": "gpt-3.5-turbo"
    }
    
    # Token limits by model
    TOKEN_LIMITS = {
        "gpt-4o-mini": 8192,
        "gpt-4-turbo": 128000,
        "gpt-3.5-turbo": 4096
    }
    
    # Temperature settings by task
    TEMPERATURE_SETTINGS = {
        "nutrient_prediction": 0.2,  # Low temperature for factual accuracy
        "bioactive_prediction": 0.2,
        "impact_generation": 0.3,  # Slightly higher for creative mechanism reasoning
        "mechanism_identification": 0.3,
        "confidence_calibration": 0.1  # Very low for consistency
    }
    
    def __init__(
        self, 
        api_key: Optional[str] = None,
        models: Optional[Dict[str, str]] = None,
        max_retries: int = 3,
        backoff_factor: float = 2.0,
        request_timeout: int = 120,
        async_mode: bool = False,
        log_dir: Optional[str] = None
    ):
        """
        Initialize the OpenAI client.
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            models: Dictionary mapping task types to model names
            max_retries: Maximum number of retries for failed requests
            backoff_factor: Backoff factor for exponential retry
            request_timeout: Request timeout in seconds
            async_mode: Whether to use async client
            log_dir: Directory to save request/response logs
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set it as an argument or as OPENAI_API_KEY environment variable.")
        
        self.models = models or self.DEFAULT_MODELS.copy()
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.request_timeout = request_timeout
        self.async_mode = async_mode
        
        # Initialize client
        if async_mode:
            self.client = AsyncOpenAI(api_key=self.api_key, timeout=request_timeout)
        else:
            self.client = OpenAI(api_key=self.api_key, timeout=request_timeout)
        
        # Set up logging
        self.log_dir = log_dir
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
            self.request_log_path = os.path.join(log_dir, "openai_requests.jsonl")
            self.response_log_path = os.path.join(log_dir, "openai_responses.jsonl")
            self.error_log_path = os.path.join(log_dir, "openai_errors.jsonl")
        
        # Cost tracking
        self.cost_tracker = {
            "total_tokens": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_cost": 0.0,
            "requests": 0
        }
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.5  # 500ms minimum between requests

    def load_template(self, template_id: str) -> Dict:
        """
        Load a prompt template by ID.
        
        Args:
            template_id: Template identifier
            
        Returns:
            Template dictionary
        """
        template_path = None
        template_pattern = os.path.join("scripts", "ai", "prompt_templates", "*.json")
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

    def _substitute_template_variables(self, template_str: str, variables: Dict) -> str:
        """
        Substitute variables in a template string.
        
        Args:
            template_str: Template string with variables in {{var}} format
            variables: Dictionary of variable values
            
        Returns:
            String with variables substituted
        """
        # Handle conditional blocks with {% if condition %}...{% endif %} syntax
        # This is a simplified implementation that supports basic conditionals
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

    def create_messages_from_template(self, template_id: str, variables: Dict) -> List[Dict[str, str]]:
        """
        Create messages for API request from a template.
        
        Args:
            template_id: Template identifier
            variables: Dictionary of variable values
            
        Returns:
            List of message dictionaries
        """
        template = self.load_template(template_id)
        
        system_prompt = template.get("system_prompt", "")
        user_prompt_template = template.get("user_prompt_template", "")
        
        # Substitute variables
        user_prompt = self._substitute_template_variables(user_prompt_template, variables)
        
        # Create messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return messages

    def _log_request(self, task_type: str, model: str, messages: List[Dict], temperature: float):
        """Log API request details."""
        if not self.log_dir:
            return
        
        log_entry = {
            "timestamp": time.time(),
            "task_type": task_type,
            "model": model,
            "messages": messages,
            "temperature": temperature
        }
        
        with open(self.request_log_path, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    
    def _log_response(self, task_type: str, response: Dict):
        """Log API response details."""
        if not self.log_dir:
            return
        
        log_entry = {
            "timestamp": time.time(),
            "task_type": task_type,
            "response": response
        }
        
        with open(self.response_log_path, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    
    def _log_error(self, task_type: str, error: Exception, context: Dict):
        """Log API errors."""
        if not self.log_dir:
            return
        
        log_entry = {
            "timestamp": time.time(),
            "task_type": task_type,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context
        }
        
        with open(self.error_log_path, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    
    def _apply_rate_limiting(self):
        """Apply rate limiting to avoid hitting API rate limits."""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last_request
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _validate_json_response(self, text: str) -> Dict:
        """
        Parse JSON from AI response text.
        
        Args:
            text: Response text containing JSON
            
        Returns:
            Parsed JSON dictionary
        
        Raises:
            ValueError: If valid JSON cannot be parsed
        """
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Could not parse JSON from response: {e}")
    
    @retry(
        retry=retry_if_exception_type((openai.RateLimitError, openai.APITimeoutError, openai.APIConnectionError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30)
    )
    async def _async_complete(
        self, 
        task_type: str, 
        messages: List[Dict[str, str]], 
        temperature: Optional[float] = None,
        model: Optional[str] = None
    ) -> Dict:
        """
        Async method to generate a completion from the OpenAI API.
        
        Args:
            task_type: Type of task (for logging and model selection)
            messages: List of message dictionaries for the conversation
            temperature: Temperature setting (0-1)
            model: Model to use (overrides default for task type)
            
        Returns:
            Response dictionary
        """
        if not self.async_mode:
            raise ValueError("Client not initialized for async mode")
        
        # Select model and temperature based on task type
        if model is None:
            model = self.models.get(task_type, self.models["fallback"])
        
        if temperature is None:
            temperature = self.TEMPERATURE_SETTINGS.get(task_type, 0.3)

        we_did_not_specify_stop_tokens = True
        
        # Log request
        self._log_request(task_type, model, messages, temperature)
        
        try:
            # Apply rate limiting
            await asyncio.sleep(self.min_request_interval)
            
            user_message = None
            for message in messages:
                if message.get("role") == "system":
                    instructions = message.get("content")
                elif message.get("role") == "user":
                    user_message = message.get("content")
        
            # Make request using Responses API with JSON mode
            response = self.client.responses.create(
                model=model,
                instructions=instructions,
                input=user_message,
                temperature=temperature,
                text={"format": {"type": "json_object"}}
            )

            # Check if the conversation was too long for the context window, resulting in incomplete JSON 
            if response.status == "incomplete" and response.incomplete_details.reason == "max_output_tokens":
                raise Exception("Response incomplete due to output token limit being reached. Please check the token limit for this model")

            # Check if the OpenAI safety system refused the request and generated a refusal instead
            if response.output[0].content[0].type == "refusal":
                # In this case, the .content field will contain the explanation (if any) that the model generated for why it is refusing
                raise Exception("Response refused. Reason: " + response.output[0].content[0]["refusal"])

            # Check if the model's output included restricted content, so the generation of JSON was halted and may be partial
            if response.status == "incomplete" and response.incomplete_details.reason == "content_filter":
                raise Exception("Response incomplete due to restricted content in response. Please check your configured content filter.")

            if response.status == "completed":
                if we_did_not_specify_stop_tokens:
                    # If you didn't specify any stop tokens, then the generation is complete and the content key will contain the serialized JSON object
                    # Log response
                    self._log_response(task_type, response.output_text)
                    return response.output_text
                else:
                    # Check if the response.output_text ends with one of your stop tokens and handle appropriately
                    pass
            
        except Exception as e:
            # Log error
            context = {
                "task_type": task_type,
                "model": model,
                "temperature": temperature
            }
            self._log_error(task_type, e, context)
            
            # Re-raise for retry mechanism
            raise
    
    @retry(
        retry=retry_if_exception_type((openai.RateLimitError, openai.APITimeoutError, openai.APIConnectionError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30)
    )
    def complete(
        self, 
        task_type: str, 
        messages: List[Dict[str, str]], 
        temperature: Optional[float] = None,
        model: Optional[str] = None
    ) -> Dict:
        """
        Generate a completion from the OpenAI API.
        
        Args:
            task_type: Type of task (for logging and model selection)
            messages: List of message dictionaries for the conversation
            temperature: Temperature setting (0-1)
            model: Model to use (overrides default for task type)
            
        Returns:
            Response dictionary
        """
        if self.async_mode:
            raise ValueError("Client initialized for async mode, use async_complete instead")

        # Select model and temperature based on task type
        if model is None:
            model = self.models.get(task_type, self.models["fallback"])
        
        if temperature is None:
            temperature = self.TEMPERATURE_SETTINGS.get(task_type, 0.3)
        
        we_did_not_specify_stop_tokens = True

        # Log request
        self._log_request(task_type, model, messages, temperature)
    
        try:
            # Apply rate limiting
            self._apply_rate_limiting()

            # Extract system message for instructions
            instructions = None
            user_message = None
            for message in messages:
                if message.get("role") == "system":
                    instructions = message.get("content")
                elif message.get("role") == "user":
                    user_message = message.get("content")
        
            # Make request using Responses API with JSON mode
            response = self.client.responses.create(
                model=model,
                instructions=instructions,
                input=user_message,
                temperature=temperature,
                text={"format": {"type": "json_object"}}
            )
        
            # Check if the conversation was too long for the context window, resulting in incomplete JSON 
            if response.status == "incomplete" and response.incomplete_details.reason == "max_output_tokens":
                raise Exception("Response incomplete due to output token limit being reached. Please check the token limit for this model")

            # Check if the OpenAI safety system refused the request and generated a refusal instead
            if response.output[0].content[0].type == "refusal":
                # In this case, the .content field will contain the explanation (if any) that the model generated for why it is refusing
                raise Exception("Response refused. Reason: " + response.output[0].content[0]["refusal"])

            # Check if the model's output included restricted content, so the generation of JSON was halted and may be partial
            if response.status == "incomplete" and response.incomplete_details.reason == "content_filter":
                raise Exception("Response incomplete due to restricted content in response. Please check your configured content filter.")

            if response.status == "completed":
                if we_did_not_specify_stop_tokens:
                    # If you didn't specify any stop tokens, then the generation is complete and the content key will contain the serialized JSON object
                    # Log response
                    self._log_response(task_type, response.output_text)
                    return response.output_text
                else:
                    # Check if the response.output_text ends with one of your stop tokens and handle appropriately
                    pass
            
        except Exception as e:
            # Log error
            context = {
                "task_type": task_type,
                "model": model,
                "temperature": temperature
            }
            self._log_error(task_type, e, context)
            
            # Re-raise for retry mechanism
            raise

    def predict_nutrients(
        self, 
        food_name: str, 
        food_category: str, 
        standard_nutrients: Dict, 
        existing_brain_nutrients: Dict,
        target_nutrients: List[str],
        scientific_context: Optional[str] = None,
        reference_foods: Optional[Dict] = None
    ) -> Dict:
        """
        Predict missing brain-specific nutrients for a food.
        
        Args:
            food_name: Name of the food
            food_category: Food category
            standard_nutrients: Dictionary of standard nutrients
            existing_brain_nutrients: Dictionary of known brain nutrients
            target_nutrients: List of nutrients to predict
            scientific_context: Optional scientific context for the food
            reference_foods: Optional reference foods with known values
            
        Returns:
            Dictionary of predicted nutrient values with confidence scores
        """
        # Prepare template variables
        variables = {
            "food_name": food_name,
            "food_category": food_category,
            "standard_nutrients_json": standard_nutrients,
            "existing_brain_nutrients_json": existing_brain_nutrients,
            "target_nutrients_list": ", ".join(target_nutrients),
            "scientific_context": scientific_context,
            "reference_foods_json": reference_foods
        }
        
        # Create messages from template
        messages = self.create_messages_from_template("brain_nutrient_prediction", variables)
        
        # Make API request
        response = self.complete("nutrient_prediction", messages)
        
        try:
            predicted_nutrients = self._validate_json_response(response)
            return predicted_nutrients
        except ValueError as e:
            logger.error(f"Error parsing nutrient prediction response: {e}")
            logger.error(f"Raw response: {response}")
            return {"error": str(e), "raw_response": response}

    def predict_bioactive_compounds(
        self, 
        food_name: str, 
        food_category: str,
        standard_nutrients: Dict,
        scientific_context: Optional[str] = None,
        processing_method: Optional[str] = None,
        additional_compounds: Optional[str] = None
    ) -> Dict:
        """
        Predict bioactive compounds for a food.
        
        Args:
            food_name: Name of the food
            food_category: Food category
            standard_nutrients: Dictionary of standard nutrients
            scientific_context: Optional scientific context
            processing_method: Optional processing/cooking method
            additional_compounds: Optional additional compounds to predict
            
        Returns:
            Dictionary of predicted bioactive compounds with confidence scores
        """
        # Prepare template variables
        variables = {
            "food_name": food_name,
            "food_category": food_category,
            "standard_nutrients_json": standard_nutrients,
            "scientific_context": scientific_context,
            "processing_method": processing_method,
            "additional_compounds": additional_compounds
        }
        
        # Create messages from template
        messages = self.create_messages_from_template("bioactive_compounds_prediction", variables)
        
        # Make API request
        response = self.complete("bioactive_prediction", messages)
        
        try:
            predicted_compounds = self._validate_json_response(response)
            return predicted_compounds
        except ValueError as e:
            logger.error(f"Error parsing bioactive prediction response: {e}")
            logger.error(f"Raw response: {response}")
            return {"error": str(e), "raw_response": response}

    def predict_mental_health_impacts(
        self,
        food_name: str,
        food_category: str,
        standard_nutrients: Dict,
        brain_nutrients: Dict,
        bioactive_compounds: Dict,
        scientific_context: Optional[str] = None,
        max_impacts: int = 4
    ) -> List[Dict]:
        """
        Generate mental health impacts for a food.
        
        Args:
            food_name: Name of the food
            food_category: Food category
            standard_nutrients: Dictionary of standard nutrients
            brain_nutrients: Dictionary of brain nutrients
            bioactive_compounds: Dictionary of bioactive compounds
            scientific_context: Optional scientific context
            max_impacts: Maximum number of impacts to generate
            
        Returns:
            List of dictionaries with mental health impacts
        """
        # Prepare template variables
        variables = {
            "food_name": food_name,
            "food_category": food_category,
            "standard_nutrients_json": standard_nutrients,
            "brain_nutrients_json": brain_nutrients,
            "bioactive_compounds_json": bioactive_compounds,
            "scientific_context": scientific_context,
            "max_impacts": max_impacts
        }
        
        # Create messages from template
        messages = self.create_messages_from_template("mental_health_impacts", variables)
        
        # Make API request
        response = self.complete("impact_generation", messages)
        
        try:
            mental_health_impacts = self._validate_json_response(response)
            # Handle case where the result isn't a list
            if not isinstance(mental_health_impacts, list):
                if isinstance(mental_health_impacts, dict) and "impacts" in mental_health_impacts:
                    return mental_health_impacts["impacts"]
                else:
                    raise ValueError(f"Expected list of impacts, got: {type(mental_health_impacts)}")
            return mental_health_impacts
        except ValueError as e:
            logger.error(f"Error parsing mental health impacts response: {e}")
            logger.error(f"Raw response: {response}")
            return [{"error": str(e), "raw_response": response}]
    
    def extract_mechanism(
        self,
        food_name: str,
        nutrient: str,
        impact: str,
        scientific_context: Optional[str] = None
    ) -> Dict:
        """Extract detailed mechanism of action for a nutrient-impact relationship."""
        # Prepare template variables
        variables = {
            "food_name": food_name,
            "nutrient": nutrient,
            "impact": impact,
            "scientific_context": scientific_context
        }
        
        # Create messages from template
        messages = self.create_messages_from_template("mechanism_extraction", variables)
        
        # Make API request
        response = self.complete("mechanism_identification", messages)
        
        try:
            if hasattr(response, 'output') and hasattr(response.output, 'content'):
                mechanism_data = self._validate_json_response(response.output.content)
                return mechanism_data
            else:
                # Direct JSON return since we're using JSON mode
                return response
        except ValueError as e:
            logger.error(f"Error parsing mechanism extraction response: {e}")
            return {"error": str(e), "raw_response": str(response)}

    def calibrate_confidence(
        self,
        food_name: str,
        generated_data: Dict,
        data_type: str,
        reference_data: Optional[Dict] = None
    ) -> Dict:
        """Calibrate confidence ratings for generated data."""
        # Prepare template variables
        variables = {
            "food_name": food_name,
            "data_type": data_type,
            "generated_data_json": generated_data,
            "reference_data_json": reference_data
        }
        
        # Create messages from template
        messages = self.create_messages_from_template("confidence_calibration", variables)
        
        # Make API request
        response = self.complete("confidence_calibration", messages)
        
        try:
            if hasattr(response, 'output') and hasattr(response.output, 'content'):
                calibrated_data = self._validate_json_response(response.output.content)
                return calibrated_data
            else:
                # Direct JSON return since we're using JSON mode
                return response
        except ValueError as e:
            logger.error(f"Error parsing confidence calibration response: {e}")
            return {"error": str(e), "raw_response": str(response), "original_data": generated_data}
    
    def get_cost_summary(self) -> Dict:
        """Get summary of API usage costs."""
        return self.cost_tracker.copy()
    
    def reset_cost_tracking(self):
        """Reset cost tracking."""
        self.cost_tracker = {
            "total_tokens": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_cost": 0.0,
            "requests": 0
        }