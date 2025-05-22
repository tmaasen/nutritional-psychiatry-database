
DEFAULT_AI_MODELS = {
    "nutrient_prediction": "gpt-4o-mini",
    "bioactive_prediction": "gpt-4o-mini",
    "impact_generation": "gpt-4o-mini",
    "mechanism_identification": "gpt-4o-mini",
    "confidence_calibration": "gpt-4o-mini",
    "fallback": "gpt-3.5-turbo"
}

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

# Template paths
TEMPLATE_DIR = "scripts/ai/prompt_templates"

# Rate limiting constants
DEFAULT_RATE_LIMIT_DELAY = 0.5  # 500ms minimum between requests

# Retry settings
MAX_RETRIES = 3
BACKOFF_FACTOR = 2.0
REQUEST_TIMEOUT = 120