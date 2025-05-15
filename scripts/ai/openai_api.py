#!/usr/bin/env python3
"""
OpenAI API for Nutritional Psychiatry Database

This module handles all interactions with the OpenAI API for data enrichment:
- Brain-specific nutrient prediction
- Bioactive compound estimation
- Mental health impact relationship generation
- Mechanism of action identification
- Confidence scoring calibration
"""

import asyncio
import os
import time
from typing import Dict, List, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import openai
from openai import OpenAI

# Import project utilities
from utils.logging_utils import (
    setup_logging, log_execution_time, 
    log_api_request, log_api_response, log_api_error
)
from utils.prompt_template_utils import TemplateManager
from utils.json_utils import JSONParser
from utils.db_utils import PostgresClient

# Import data models
from schema.food_data import (
    BrainNutrients, NutrientInteraction, Omega3, BioactiveCompounds, MentalHealthImpact, ResearchSupport
)

# Constants
from constants.ai_constants import (
    DEFAULT_AI_MODELS, TEMPERATURE_SETTINGS, MAX_RETRIES, 
    BACKOFF_FACTOR, REQUEST_TIMEOUT, DEFAULT_RATE_LIMIT_DELAY
)

# Initialize logger
logger = setup_logging(__name__)

class OpenAIAPI:
    """
    Client for interacting with OpenAI API for nutritional psychiatry data enrichment.
    """
    
    def __init__(
        self, 
        api_key: Optional[str] = None,
        models: Optional[Dict[str, str]] = None,
        db_client: Optional[PostgresClient] = None,
        max_retries: int = MAX_RETRIES,
        backoff_factor: float = BACKOFF_FACTOR,
        request_timeout: int = REQUEST_TIMEOUT,
        rate_limit_delay: float = DEFAULT_RATE_LIMIT_DELAY
    ):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set it as an argument or as OPENAI_API_KEY environment variable.")
        
        # Configuration
        self.models = models or DEFAULT_AI_MODELS
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.request_timeout = request_timeout
        self.rate_limit_delay = rate_limit_delay
        
        self.db_client = db_client        
        self.client = OpenAI(api_key=self.api_key, timeout=request_timeout)
        self.last_request_time = 0
    
    def get_model_for_task(self, task_type: str) -> str:
        return self.models.get(task_type, self.models.get("fallback", "gpt-4o-mini"))
    
    def get_temperature_for_task(self, task_type: str) -> float:
        return TEMPERATURE_SETTINGS.get(task_type, 0.3)
    
    async def _apply_rate_limiting(self):
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.rate_limit_delay:
            await asyncio.sleep(self.rate_limit_delay - time_since_last_request)
        
        self.last_request_time = time.time()
    
    @retry(
        retry=retry_if_exception_type((openai.RateLimitError, openai.APITimeoutError, openai.APIConnectionError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30)
    )
    @log_execution_time
    async def complete(
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
        # Select model and temperature based on task type
        if model is None:
            model = self.get_model_for_task(task_type)
        
        if temperature is None:
            temperature = self.get_temperature_for_task(task_type)

        # Log request
        log_api_request(logger, "openai", task_type, model, messages, {"temperature": temperature})
    
        try:
            # Apply rate limiting
            await self._apply_rate_limiting()

            # Extract system message for instructions
            instructions = None
            user_message = None
            for message in messages:
                if message.get("role") == "system":
                    instructions = message.get("content")
                elif message.get("role") == "user":
                    user_message = message.get("content")
        
            response = await self.client.responses.create(
                model=model,
                instructions=instructions,
                input=user_message,
                temperature=temperature,
                text={"format": {"type": "json_object"}}
            )
        
            if response.status == "incomplete":
                if response.incomplete_details.reason == "max_output_tokens":
                    raise ValueError("Response incomplete due to output token limit")
                elif response.incomplete_details.reason == "content_filter":
                    raise ValueError("Response incomplete due to content filter")
            
            if response.status == "completed":
                log_api_response(logger, "openai", task_type, response.output_text)
                return response.output_text
            
            raise ValueError(f"Unexpected response status: {response.status}")
            
        except Exception as e:
            context = {
                "task_type": task_type,
                "model": model,
                "temperature": temperature
            }
            log_api_error(logger, "openai", task_type, e, context)
            
            # Re-raise for retry mechanism
            raise
    
    async def save_prediction(self, food_id: str, prediction_type: str, data: Dict):
        """
        Save prediction to database.
        
        Args:
            food_id: Food ID
            prediction_type: Type of prediction (e.g., "brain_nutrients")
            data: Prediction data
            
        Returns:
            True if saved successfully, False otherwise
        """
        if not self.db_client:
            logger.warning("No database client available for saving prediction")
            return False
        
        try:
            # Get existing food data
            food_data = await self.db_client.get_food_by_id(food_id)
            if not food_data:
                logger.warning(f"Food {food_id} not found in database")
                return False
            
            # Update with prediction data
            if prediction_type == "brain_nutrients":
                food_data.brain_nutrients = data
                food_data.data_quality.brain_nutrients_source = "ai_generated"
            elif prediction_type == "bioactive_compounds":
                food_data.bioactive_compounds = data
            elif prediction_type == "mental_health_impacts":
                food_data.mental_health_impacts = data
                food_data.data_quality.impacts_source = "ai_generated"
            
            # Save to database
            await self.db_client.import_food_from_json(food_data)
            return True
            
        except Exception as e:
            logger.error(f"Failed to save prediction to database: {e}")
            return False
    
    @log_execution_time
    async def predict_nutrients(
        self, 
        food_name: str, 
        food_category: str, 
        standard_nutrients: Dict, 
        existing_brain_nutrients: Dict,
        target_nutrients: List[str],
        food_id: Optional[str] = None,
        scientific_context: Optional[str] = None,
        reference_foods: Optional[Dict] = None
    ) -> BrainNutrients:
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
        messages = TemplateManager.create_messages_from_template("brain_nutrient_prediction", variables)
        
        response = await self.complete("nutrient_prediction", messages)
        
        try:
            # Parse and validate prediction
            predicted_nutrients = JSONParser.parse_json(response, {})
            
            # Create BrainNutrients object to validate structure
            # Note: We can't use full validation here since we only have partial data
            brain_nutrients_dict = BrainNutrients()
            
            # Process normal brain nutrients
            for nutrient, value in predicted_nutrients.items():
                if nutrient.startswith("confidence_") or nutrient == "reasoning":
                    continue
                
                if "omega" in nutrient.lower():
                    # Skip omega-3 for separate handling
                    continue
                
                brain_nutrients_dict.nutrients[nutrient] = value
            
            # Process omega-3 nutrients if present
            omega3_dict = {}
            for omega_key in ["omega3_total_g", "omega3.total_g", "total_g"]:
                if omega_key in predicted_nutrients:
                    omega3_dict["total_g"] = predicted_nutrients[omega_key]
                    break
            
            for component in ["epa_mg", "dha_mg", "ala_mg"]:
                omega_key = f"omega3_{component}"
                alt_key = f"omega3.{component}"
                
                if omega_key in predicted_nutrients:
                    omega3_dict[component] = predicted_nutrients[omega_key]
                elif alt_key in predicted_nutrients:
                    omega3_dict[component] = predicted_nutrients[alt_key]
            
            # Add confidence if present
            for conf_key in ["confidence_omega3", "omega3_confidence", "confidence_omega3_total_g"]:
                if conf_key in predicted_nutrients:
                    omega3_dict["confidence"] = predicted_nutrients[conf_key]
                    break
            
            # Add omega3 object if we have data
            if omega3_dict:
                brain_nutrients_dict.omega3 = omega3_dict
            
            # Save to database if ID provided
            if food_id and self.db_client:
                await self.save_prediction(food_id, "brain_nutrients", brain_nutrients_dict.to_dict())
            
            return brain_nutrients_dict
            
        except Exception as e:
            logger.error(f"Error parsing nutrient prediction response: {e}")
            logger.error(f"Raw response: {response}")
            return {"error": str(e), "raw_response": response}
    
    @log_execution_time
    async def predict_bioactive_compounds(
        self, 
        food_name: str, 
        food_category: str,
        standard_nutrients: Dict,
        food_id: Optional[str] = None,
        scientific_context: Optional[str] = None,
        processing_method: Optional[str] = None,
        additional_compounds: Optional[str] = None
    ) -> BioactiveCompounds:
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
        messages = TemplateManager.create_messages_from_template("bioactive_compounds_prediction", variables)
        
        response = await self.complete("bioactive_prediction", messages)
        
        try:
            # Parse and validate prediction
            predicted = JSONParser.parse_json(response, {})
            
            # Filter to just the bioactive compounds and their confidence
            bioactive_dict = BioactiveCompounds()
            
            for key, value in predicted.items():
                if key.startswith("confidence_") or key == "reasoning":
                    continue
                
                bioactive_dict.compounds[key] = value
                
                # Include confidence if present
                conf_key = f"confidence_{key}"
                if conf_key in predicted:
                    bioactive_dict.confidence[conf_key] = predicted[conf_key]
            
            # Save to database if ID provided
            if food_id and self.db_client:
                await self.save_prediction(food_id, "bioactive_compounds", bioactive_dict.to_dict())
            
            return bioactive_dict
            
        except Exception as e:
            logger.error(f"Error parsing bioactive prediction response: {e}")
            logger.error(f"Raw response: {response}")
            return {"error": str(e), "raw_response": response}
    
    @log_execution_time
    async def predict_mental_health_impacts(
        self,
        food_name: str,
        food_category: str,
        standard_nutrients: Dict,
        brain_nutrients: Dict,
        bioactive_compounds: Dict,
        food_id: Optional[str] = None,
        scientific_context: Optional[str] = None,
        max_impacts: int = 4
    ) -> List[MentalHealthImpact]:
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
        messages = TemplateManager.create_messages_from_template("mental_health_impacts", variables)
        
        response = await self.complete("impact_generation", messages)
        
        try:
            # Parse the response
            parsed = JSONParser.parse_json(response, [])
            
            # Handle case where the result isn't a list
            impacts = MentalHealthImpact()
            if isinstance(parsed, list):
                impacts.impacts = parsed
            elif isinstance(parsed, dict) and "impacts" in parsed:
                impacts.impacts = parsed["impacts"]
            else:
                impacts.impacts = [parsed]  # Treat as single impact
            
            # Validate each impact
            valid_impacts = []
            required_fields = ["impact_type", "direction", "mechanism", "strength", "confidence"]
            
            for impact in impacts.impacts:
                if isinstance(impact, dict) and all(field in impact for field in required_fields):
                    # Convert research support to proper format if needed
                    if "research_citations" in impact and "research_support" not in impact:
                        impact.research_support = []
                        for citation in impact["research_citations"]:
                            support = {"citation": citation}
                            if citation.startswith("PMID:"):
                                support["pmid"] = citation.split(":", 1)[1].strip()
                            elif citation.startswith("DOI:"):
                                support["doi"] = citation.split(":", 1)[1].strip()
                            impact.research_support.append(support)
                    
                    valid_impacts.append(impact)
            
            # Save to database if ID provided
            if food_id and self.db_client:
                await self.save_prediction(food_id, "mental_health_impacts", valid_impacts)
            
            return valid_impacts
            
        except Exception as e:
            logger.error(f"Error parsing mental health impacts response: {e}")
            logger.error(f"Raw response: {response}")
            return [{"error": str(e), "raw_response": response}]
    
    @log_execution_time
    async def extract_mechanism(
        self,
        food_name: str,
        nutrient: str,
        impact: str,
        scientific_context: Optional[str] = None
    ) -> NutrientInteraction:
        # Prepare template variables
        variables = {
            "food_name": food_name,
            "nutrient": nutrient,
            "impact": impact,
            "scientific_context": scientific_context
        }
        
        # Create messages from template
        messages = TemplateManager.create_messages_from_template("mechanism_extraction", variables)
        
        response = await self.complete("mechanism_identification", messages)
        
        try:
            # Parse the response
            mechanism_data = JSONParser.parse_json(response, NutrientInteraction())
            
            # Validate required fields
            required_fields = ["primary_pathway", "detailed_steps", "key_molecules", "confidence"]
            if not JSONParser.validate_json_schema(mechanism_data.to_dict(), required_fields):
                logger.warning(f"Mechanism response missing required fields: {mechanism_data.to_dict()}")
            
            return mechanism_data.to_dict()
            
        except Exception as e:
            logger.error(f"Error parsing mechanism extraction response: {e}")
            logger.error(f"Raw response: {response}")
            return {"error": str(e), "raw_response": response}
    
    @log_execution_time
    async def calibrate_confidence(
        self,
        food_name: str,
        generated_data: Dict,
        data_type: str,
        reference_data: Optional[Dict] = None
    ) -> Dict:
        """
        Calibrate confidence ratings for generated data.
        
        Args:
            food_name: Food name
            generated_data: Generated data to calibrate
            data_type: Type of data (brain_nutrients, mental_health_impacts, etc.)
            reference_data: Optional reference data for comparison
            
        Returns:
            Calibrated data dictionary
        """
        # Prepare template variables
        variables = {
            "food_name": food_name,
            "data_type": data_type,
            "generated_data_json": generated_data,
            "reference_data_json": reference_data
        }
        
        # Create messages from template
        messages = TemplateManager.create_messages_from_template("confidence_calibration", variables)
        
        # Make API request
        response = await self.complete("confidence_calibration", messages)
        
        try:
            # Parse the response
            calibrated_data = JSONParser.parse_json(response, generated_data)
            
            # If parsing fails, return original with note
            if not calibrated_data or "error" in calibrated_data:
                logger.warning(f"Confidence calibration failed, returning original data")
                return generated_data
            
            return calibrated_data
            
        except Exception as e:
            logger.error(f"Error parsing confidence calibration response: {e}")
            logger.error(f"Raw response: {response}")
            return {"error": str(e), "raw_response": response, "original_data": generated_data}