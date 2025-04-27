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
- Configurable model selection (GPT-4/3.5)
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
        "nutrient_prediction": "gpt-4",
        "bioactive_prediction": "gpt-4",
        "impact_generation": "gpt-4",
        "mechanism_identification": "gpt-4",
        "confidence_calibration": "gpt-4-turbo",
        "fallback": "gpt-3.5-turbo"
    }
    
    # Token limits by model
    TOKEN_LIMITS = {
        "gpt-4": 8192,
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
    
    def _update_cost(self, usage: Dict[str, int], model: str):
        """Update cost tracking based on token usage."""
        # Simplified cost approximations - should be updated with current pricing
        cost_per_1k_tokens = {
            "gpt-4": {"prompt": 0.03, "completion": 0.06},
            "gpt-4-turbo": {"prompt": 0.01, "completion": 0.03},
            "gpt-3.5-turbo": {"prompt": 0.0015, "completion": 0.002}
        }
        
        # Default to gpt-4 pricing if model not found
        model_base = model.split("-")[0] + "-" + model.split("-")[1]
        if model_base in cost_per_1k_tokens:
            cost_rates = cost_per_1k_tokens[model_base]
        else:
            cost_rates = cost_per_1k_tokens["gpt-4"]
        
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        
        prompt_cost = (prompt_tokens / 1000) * cost_rates["prompt"]
        completion_cost = (completion_tokens / 1000) * cost_rates["completion"]
        
        self.cost_tracker["prompt_tokens"] += prompt_tokens
        self.cost_tracker["completion_tokens"] += completion_tokens
        self.cost_tracker["total_tokens"] += prompt_tokens + completion_tokens
        self.cost_tracker["total_cost"] += prompt_cost + completion_cost
        self.cost_tracker["requests"] += 1
    
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
        Extract and validate JSON from AI response text.
        
        Args:
            text: Response text possibly containing JSON
            
        Returns:
            Parsed JSON dictionary
        
        Raises:
            ValueError: If valid JSON cannot be extracted
        """
        # Find JSON content between triple backticks, if present
        if "```json" in text:
            parts = text.split("```json")
            if len(parts) > 1:
                json_text = parts[1].split("```")[0].strip()
            else:
                json_text = text
        elif "```" in text:
            parts = text.split("```")
            if len(parts) > 1:
                json_text = parts[1].strip()
            else:
                json_text = text
        else:
            # If no code blocks, try to find JSON brackets
            start_idx = text.find('{')
            end_idx = text.rfind('}')
            if start_idx != -1 and end_idx != -1:
                json_text = text[start_idx:end_idx+1]
            else:
                json_text = text
        
        try:
            return json.loads(json_text)
        except json.JSONDecodeError:
            # Attempt more aggressive JSON extraction
            # Find the outermost curly braces
            start_idx = text.find('{')
            end_idx = text.rfind('}')
            
            if start_idx != -1 and end_idx != -1:
                try:
                    return json.loads(text[start_idx:end_idx+1])
                except json.JSONDecodeError:
                    raise ValueError(f"Could not extract valid JSON from response: {text}")
            else:
                raise ValueError("No valid JSON found in response")
    
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
        
        # Log request
        self._log_request(task_type, model, messages, temperature)
        
        try:
            # Apply rate limiting
            await asyncio.sleep(self.min_request_interval)
            
            # Make request
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature
            )
            
            # Update cost tracking
            if hasattr(response, 'usage'):
                self._update_cost(response.usage, model)
            
            # Log response
            self._log_response(task_type, response)
            
            return response
            
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
        
        # Log request
        self._log_request(task_type, model, messages, temperature)
        
        try:
            # Apply rate limiting
            self._apply_rate_limiting()
            
            # Make request
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature
            )
            
            # Update cost tracking
            if hasattr(response, 'usage'):
                self._update_cost(response.usage.model_dump(), model)
            
            # Log response
            self._log_response(task_type, response.model_dump())
            
            return response
            
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
        scientific_context: Optional[str] = None
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
            
        Returns:
            Dictionary of predicted nutrient values with confidence scores
        """
        # Construct system prompt with scientific guidelines
        system_prompt = """You are a nutritional psychiatry expert specializing in brain-specific nutrients. 
Your task is to predict nutrient levels in foods based on their composition, scientific research, and nutritional databases.
Follow these guidelines:
1. Only predict nutrients specifically requested
2. Base predictions on known nutrient compositions of similar foods
3. Provide confidence levels (1-10 scale) for each prediction
4. Explain your reasoning based on food composition
5. When uncertain, provide conservative ranges rather than precise values
6. Format all responses as JSON with nutrient names as keys and numeric values
7. Use standard units: mg for most nutrients, mcg for B12/D/folate/selenium
8. For nutrients not present in the food, use 0 rather than null
9. Specify when a prediction has high uncertainty"""
        
        # Construct prompt with food data
        user_prompt = f"""Based on nutritional science, predict the following missing brain-specific nutrients for {food_name} (category: {food_category}).

The food has these standard nutrients (per 100g unless specified otherwise):
{json.dumps(standard_nutrients, indent=2)}

Known brain-nutrients (if any):
{json.dumps(existing_brain_nutrients, indent=2)}

Please predict values for these missing brain nutrients:
{', '.join(target_nutrients)}

"""
        if scientific_context:
            user_prompt += f"\nAdditional scientific context:\n{scientific_context}\n"
        
        user_prompt += """
Your response should be in JSON format with nutrient names as keys and numeric values as values, including a confidence rating (1-10) for each prediction. 
Example format:
{
  "tryptophan_mg": 28.4,
  "confidence_tryptophan_mg": 7,
  "vitamin_b12_mcg": 0.0,
  "confidence_vitamin_b12_mcg": 9,
  "omega3_total_g": 0.12,
  "confidence_omega3_total_g": 5,
  "reasoning": "Tryptophan estimate based on protein content (~1.2% of protein). B12 absent in plant foods with high confidence. Omega-3 estimate has moderate confidence based on similar foods."
}

Be conservative with your estimates and prioritize scientific accuracy over comprehensiveness."""
        
        # Make API request
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = self.complete("nutrient_prediction", messages)
        response_text = response.choices[0].message.content
        
        try:
            predicted_nutrients = self._validate_json_response(response_text)
            return predicted_nutrients
        except ValueError as e:
            logger.error(f"Error parsing nutrient prediction response: {e}")
            logger.error(f"Raw response: {response_text}")
            return {"error": str(e), "raw_response": response_text}
    
    def predict_bioactive_compounds(
        self, 
        food_name: str, 
        food_category: str,
        standard_nutrients: Dict,
        scientific_context: Optional[str] = None
    ) -> Dict:
        """
        Predict bioactive compounds for a food.
        
        Args:
            food_name: Name of the food
            food_category: Food category
            standard_nutrients: Dictionary of standard nutrients
            scientific_context: Optional scientific context
            
        Returns:
            Dictionary of predicted bioactive compounds with confidence scores
        """
        # Construct system prompt
        system_prompt = """You are a nutritional biochemistry expert specializing in bioactive compounds in foods.
Your task is to predict bioactive compound levels in foods based on scientific literature, food composition, and phytochemical databases.
Follow these guidelines:
1. Provide realistic estimates for common bioactive compounds
2. Base predictions on research literature and similar foods
3. Include confidence ratings (1-10) for each prediction
4. For compounds absent in a food, use 0 rather than null
5. Explain your reasoning briefly
6. Format all responses as JSON with compound names as keys and numeric values
7. Use appropriate units: mg for most compounds, cfu for probiotics
8. Be conservative when uncertain - better to underestimate than overestimate"""
        
        # Construct user prompt
        user_prompt = f"""Based on nutritional science, predict the bioactive compounds for {food_name} (category: {food_category}).

The food has these standard nutrients (per 100g):
{json.dumps(standard_nutrients, indent=2)}

Please predict values for these bioactive compounds (per 100g):
- polyphenols_mg (total polyphenol content)
- flavonoids_mg (total flavonoids)
- anthocyanins_mg (if applicable)
- carotenoids_mg (total carotenoids)
- probiotics_cfu (for fermented foods)
- prebiotic_fiber_g (fermentable fiber)

"""
        if scientific_context:
            user_prompt += f"\nAdditional scientific context:\n{scientific_context}\n"
        
        user_prompt += """
Your response should be in JSON format with compound names as keys and numeric values as values. Include confidence ratings and reasoning.
Example format:
{
  "polyphenols_mg": 160.5,
  "confidence_polyphenols_mg": 7,
  "flavonoids_mg": 45.2,
  "confidence_flavonoids_mg": 6,
  "anthocyanins_mg": 12.3,
  "confidence_anthocyanins_mg": 8,
  "carotenoids_mg": 0.8,
  "confidence_carotenoids_mg": 5,
  "probiotics_cfu": 0,
  "confidence_probiotics_cfu": 9,
  "prebiotic_fiber_g": 1.2,
  "confidence_prebiotic_fiber_g": 4,
  "reasoning": "High confidence in polyphenol content for berries; probiotics absent in non-fermented foods; moderate confidence in other estimates based on research literature."
}"""
        
        # Make API request
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = self.complete("bioactive_prediction", messages)
        response_text = response.choices[0].message.content
        
        try:
            predicted_compounds = self._validate_json_response(response_text)
            return predicted_compounds
        except ValueError as e:
            logger.error(f"Error parsing bioactive prediction response: {e}")
            logger.error(f"Raw response: {response_text}")
            return {"error": str(e), "raw_response": response_text}
    
    def generate_mental_health_impacts(
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
        # Construct system prompt
        system_prompt = """You are an expert in nutritional psychiatry focusing on food-mood relationships.
Your task is to identify evidence-based connections between specific foods and mental health outcomes.
Follow these guidelines:
1. Only include relationships with scientific support - either direct studies or strong mechanistic evidence
2. Prioritize relationships with stronger evidence (human RCTs > cohort studies > animal studies)
3. Include both positive and negative impacts where relevant
4. Provide confidence ratings (1-10) based on evidence quality
5. Explain mechanisms of action in detail
6. Be conservative - better to identify fewer high-confidence relationships than many speculative ones
7. Format as a JSON array of impact objects with specific fields
8. Include relevant citations with PubMed IDs or DOIs when possible
9. For each impact, specify whether effects are acute (immediate) or cumulative (long-term)"""
        
        # Construct user prompt
        user_prompt = f"""Based on current nutritional psychiatry research, analyze the potential mental health impacts of {food_name} (category: {food_category}).

The food has these standard nutrients:
{json.dumps(standard_nutrients, indent=2)}

Brain-specific nutrients:
{json.dumps(brain_nutrients, indent=2)}

Bioactive compounds:
{json.dumps(bioactive_compounds, indent=2)}

Please identify {max_impacts} evidence-based mental health impacts this food may have. Focus on impacts with the strongest research support.

"""
        if scientific_context:
            user_prompt += f"\nAdditional scientific context:\n{scientific_context}\n"
        
        user_prompt += """
For each impact, provide:
1. Impact type (e.g., mood_elevation, anxiety_reduction, cognitive_enhancement)
2. Direction (positive, negative, neutral, or mixed)
3. Mechanism of action (how nutrients in this food affect the brain/body)
4. Strength of effect (1-10 scale)
5. Confidence level based on research evidence (1-10 scale)
6. Time frame for effect (acute/immediate or cumulative/long-term)
7. Brief research context (types of studies supporting this, limitations)
8. Research citations (PubMed IDs or DOIs)

Your response should be in JSON format. Example:
[
  {
    "impact_type": "mood_elevation",
    "direction": "positive",
    "mechanism": "Omega-3 fatty acids reduce inflammation and support serotonin receptor function",
    "strength": 7,
    "confidence": 8,
    "time_to_effect": "cumulative",
    "research_context": "Multiple RCTs and meta-analyses show mood benefits with regular consumption",
    "research_citations": ["PMID: 26186123", "DOI: 10.1016/j.nut.2015.05.016"]
  },
  {
    "impact_type": "cognitive_function",
    "direction": "positive",
    "mechanism": "Antioxidants reduce oxidative stress in neural tissues",
    "strength": 5,
    "confidence": 6,
    "time_to_effect": "both_acute_and_cumulative",
    "research_context": "Animal models show clear benefits; human studies show mixed but generally positive results",
    "research_citations": ["PMID: 27825512", "DOI: 10.3390/nu8110736"]
  }
]

Base your analysis on known mechanisms in nutritional psychiatry and the specific nutrient profile of this food. Please be evidence-based rather than speculative."""
        
        # Make API request
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = self.complete("impact_generation", messages)
        response_text = response.choices[0].message.content
        
        try:
            mental_health_impacts = self._validate_json_response(response_text)
            # Handle case where the result isn't a list
            if not isinstance(mental_health_impacts, list):
                if isinstance(mental_health_impacts, dict) and "impacts" in mental_health_impacts:
                    return mental_health_impacts["impacts"]
                else:
                    raise ValueError(f"Expected list of impacts, got: {type(mental_health_impacts)}")
            return mental_health_impacts
        except ValueError as e:
            logger.error(f"Error parsing mental health impacts response: {e}")
            logger.error(f"Raw response: {response_text}")
            return [{"error": str(e), "raw_response": response_text}]
    
    def calibrate_confidence(
        self,
        food_name: str,
        generated_data: Dict,
        data_type: str,
        reference_data: Optional[Dict] = None
    ) -> Dict:
        """
        Calibrate confidence ratings for generated data.
        
        Args:
            food_name: Name of the food
            generated_data: Generated data to calibrate
            data_type: Type of data (nutrients, bioactives, impacts)
            reference_data: Optional reference data for calibration
            
        Returns:
            Calibrated data with updated confidence scores
        """
        # Construct system prompt
        system_prompt = """You are a scientific validity assessor specializing in nutritional data quality.
Your task is to calibrate confidence ratings for AI-generated nutrient or health impact data.
Follow these guidelines:
1. Review confidence ratings objectively based on scientific plausibility
2. Lower confidence for speculative or weakly supported claims
3. Consider biological plausibility and alignment with literature
4. Verify numeric values fall within reasonable ranges
5. Check for internal consistency across different nutrients/impacts
6. Use a 1-10 scale where 8-10 requires direct research evidence
7. Format your response with the same structure as the input, updating confidence scores
8. Provide brief reasoning for significant confidence adjustments"""
        
        # Construct user prompt
        user_prompt = f"""Please calibrate the confidence ratings for this AI-generated {data_type} data for {food_name}.

Original data with confidence ratings:
{json.dumps(generated_data, indent=2)}

"""
        if reference_data:
            user_prompt += f"""
Reference data for calibration:
{json.dumps(reference_data, indent=2)}
"""
        
        user_prompt += """
Please review the confidence ratings and adjust them if needed based on:
1. Scientific plausibility of the values or claims
2. Alignment with known research on this food
3. Internal consistency of the data
4. Appropriate ranges for each nutrient/compound/impact

Return the calibrated data in the exact same format, with updated confidence ratings where needed. 
Add a "calibration_notes" field explaining your reasoning for any significant adjustments."""
        
        # Make API request
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = self.complete("confidence_calibration", messages)
        response_text = response.choices[0].message.content
        
        try:
            calibrated_data = self._validate_json_response(response_text)
            return calibrated_data
        except ValueError as e:
            logger.error(f"Error parsing confidence calibration response: {e}")
            logger.error(f"Raw response: {response_text}")
            return {"error": str(e), "raw_response": response_text, "original_data": generated_data}
    
    def extract_mechanism(
        self,
        food_name: str,
        nutrient: str,
        impact: str,
        scientific_context: Optional[str] = None
    ) -> Dict:
        """
        Extract detailed mechanism of action for a nutrient-impact relationship.
        
        Args:
            food_name: Name of the food
            nutrient: Nutrient name
            impact: Mental health impact
            scientific_context: Optional scientific context
            
        Returns:
            Dictionary with detailed mechanism information
        """
        # Construct system prompt
        system_prompt = """You are a neurochemistry and nutritional psychiatry expert.
Your task is to explain precise biological mechanisms by which food compounds affect brain function and mental health.
Follow these guidelines:
1. Focus on molecular and cellular pathways with scientific accuracy
2. Include neurotransmitter systems, receptors, and signaling pathways involved
3. Reference blood-brain barrier transportation when relevant
4. Explain both direct neurological effects and indirect effects (e.g., via gut-brain axis)
5. Note timing considerations (acute vs. chronic effects)
6. Distinguish between established mechanisms and proposed/theoretical ones
7. Include relevant gene expression or epigenetic effects where applicable
8. Format response as structured JSON with clear pathway descriptions"""
        
        # Construct user prompt
        user_prompt = f"""Please explain the detailed biological mechanism by which {nutrient} in {food_name} affects {impact}.

"""
        if scientific_context:
            user_prompt += f"\nRelevant scientific context:\n{scientific_context}\n"
        
        user_prompt += """
Please provide a comprehensive explanation of the mechanism including:
1. Absorption and metabolism pathway
2. Blood-brain barrier crossing (if applicable)
3. Primary biochemical interactions 
4. Key receptors or enzymes involved
5. Cellular signaling cascades
6. Downstream effects on neural function
7. Timing of effects (acute vs. chronic)
8. Dose-dependency considerations

Format your response as a JSON object with the following structure:
{
  "primary_pathway": "Brief (1-2 sentence) description of the main mechanism",
  "detailed_steps": [
    "Step 1: Description of first step in the mechanism",
    "Step 2: Description of second step",
    ...
  ],
  "key_molecules": ["molecule1", "molecule2", ...],
  "confidence": 7,  // 1-10 rating of evidence strength
  "primary_references": ["PMID: 12345678", "DOI: 10.1234/journal.2019.123"],
  "notes": "Any special considerations or limitations"
}"""
        
        # Make API request
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = self.complete("mechanism_identification", messages)
        response_text = response.choices[0].message.content
        
        try:
            mechanism_data = self._validate_json_response(response_text)
            return mechanism_data
        except ValueError as e:
            logger.error(f"Error parsing mechanism extraction response: {e}")
            logger.error(f"Raw response: {response_text}")
            return {"error": str(e), "raw_response": response_text}
    
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