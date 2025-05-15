# Nutritional Psychiatry Database Project Structure

This document outlines the structure of the Nutritional Psychiatry Database project, explaining the purpose and organization of directories and key files.

## Directory Structure

```
nutritional-psychiatry-database/
├── config/                       # Configuration management
│   └── __init__.py               # Centralized configuration loading
├── constants/                    # Project constants
│   ├── ai_constants.py           # AI model configuration constants
│   ├── food_data_constants.py    # Food data constants and mappings
│   ├── food_data_enums.py        # Enumeration types for food data
│   └── literature_constants.py   # Literature processing constants
├── docs/                         # Documentation
│   ├── visualizations/           # Mermaid diagrams for documentation
│   ├── ai-methodology.md         # Documentation on AI enrichment approach
│   ├── data-dictionary.md        # Documentation on schema fields
│   ├── literature-review.md      # Scientific literature review
│   └── methodology.md            # Overall methodology documentation
├── schema/                       # Data model definitions
│   ├── food_data.py              # Core data model classes
│   └── schema_validator.py       # Schema validation utilities
├── scripts/                      # Implementation scripts
│   ├── ai/                       # AI-related functionality
│   │   ├── confidence_calibration_system.py   # Confidence rating calibration
│   │   ├── known_answer_tester.py            # Testing against known values
│   │   ├── openai_api.py                     # OpenAI API integration
│   │   └── prompt_templates/                 # AI prompt templates
│   ├── data_collection/                      # Data collection scripts
│   │   ├── literature_extract.py             # Literature data extraction
│   │   ├── openfoodfacts_api.py              # OpenFoodFacts API integration
│   │   └── usda_api.py                       # USDA FoodData Central API integration
│   ├── data_processing/                      # Data processing scripts
│   │   ├── ai_enrichment.py                  # AI-based data enrichment
│   │   ├── food_data_transformer.py          # Data transformation utilities
│   │   └── food_source_prioritization.py     # Source merging and prioritization
│   └── orchestrator.py                       # Main pipeline orchestration
├── utils/                                    # Utility modules
│   ├── api_utils.py                          # API request utilities
│   ├── data_utils.py                         # Data manipulation utilities
│   ├── db_utils.py                           # Database utilities
│   ├── document_utils.py                     # Document processing utilities
│   ├── json_utils.py                         # JSON processing utilities
│   ├── logging_utils.py                      # Logging configuration
│   ├── nutrient_utils.py                     # Nutrient processing utilities
│   ├── prompt_template_utils.py              # AI prompt template utilities
│   └── research_utils.py                     # Research extraction utilities
├── .env                                      # Environment variables (gitignored)
└── requirements.txt                          # Project dependencies
```

## Key Components

### Data Models (`schema/`)

The core data models are defined in `schema/food_data.py`, which provides a comprehensive schema for food data including:

- Standard nutrients (calories, macronutrients, etc.)
- Brain-specific nutrients (tryptophan, omega-3s, etc.)
- Bioactive compounds (polyphenols, flavonoids, etc.)
- Mental health impacts (mood effects, cognitive effects, etc.)
- Nutrient interactions (synergies, antagonisms, etc.)
- Data quality metrics (confidence ratings, sources, etc.)

Validation of these models is handled by `schema/schema_validator.py`.

### Data Collection (`scripts/data_collection/`)

These scripts handle data collection from multiple sources:

- `usda_api.py`: Fetches data from USDA FoodData Central API
- `openfoodfacts_api.py`: Fetches data from OpenFoodFacts API
- `literature_extract.py`: Extracts structured data from scientific literature

### Data Processing (`scripts/data_processing/`)

These scripts transform and enrich collected data:

- `food_data_transformer.py`: Transforms source data to our schema format
- `ai_enrichment.py`: Enriches food data with AI-predicted values
- `food_source_prioritization.py`: Merges data from different sources with intelligent prioritization

### AI Integration (`scripts/ai/`)

AI-related functionality for enriching data:

- `openai_api.py`: Client for OpenAI API interactions
- `prompt_templates/`: JSON templates for different AI tasks
- `known_answer_tester.py`: Tests AI predictions against known values
- `confidence_calibration_system.py`: Calibrates confidence ratings

### Utilities (`utils/`)

Utility modules for common functions:

- `db_utils.py`: PostgreSQL database interactions
- `api_utils.py`: API request handling
- `logging_utils.py`: Logging configuration
- `nutrient_utils.py`: Nutrient-specific processing
- `research_utils.py`: Scientific research extraction

### Main Orchestrator (`scripts/orchestrator.py`)

Coordinates the entire pipeline, allowing execution of individual steps or the full process:

1. Data Collection
2. Data Transformation
3. AI Enrichment
4. Validation
5. Confidence Calibration
6. Source Prioritization & Merging

### Constants (`constants/`)

Configuration constants and enumerations:

- `food_data_constants.py`: Mappings for nutrient names, unit conversions, etc.
- `food_data_enums.py`: Enumeration types for food data
- `ai_constants.py`: AI model settings and default values
- `literature_constants.py`: Constants for literature processing

### Configuration (`config/`)

Centralized configuration management that handles:

- Loading environment variables
- Managing API keys
- Setting processing options

## Database Integration

The project now uses PostgreSQL for data storage instead of the previous file-based approach. Key database-related components:

- `utils/db_utils.py`: PostgreSQL client with connection pooling
- `PostgresClient` class: Handles all database operations
- Schema definitions in `schema/food_data.py` map directly to database tables
- Transaction handling and error recovery for database operations

## Running the Project

The main entry point is `scripts/orchestrator.py`, which can be run in interactive mode:

```bash
python scripts/orchestrator.py --interactive
```

This will present a menu to execute individual pipeline steps or the entire process.
