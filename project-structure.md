# Nutritional Psychiatry Dataset Project Structure

nutritional-psychiatry-dataset/
├── README.md                       # Project overview and documentation
├── LICENSE                         # MIT license
├── CONTRIBUTING.md                 # Guidelines for contributors
├── project-structure.md            # This file (not in original structure)
├── schema/
│   ├── schema.json                 # JSON Schema definition (was food_schema.json)
│   └── validation_rules.json       # Additional validation constraints
├── scripts/
│   ├── data_collection/
│   │   ├── usda-api.py             # Interface with USDA FoodData Central API (uses hyphen)
│   │   ├── openfoodfacts-api.py    # OpenFoodFacts API integration (new)
│   │   ├── literature_extract.py   # Extract data from research papers
│   │   └── config.py               # Configuration settings
│   ├── data_processing/
│   │   ├── transform.py            # Transform raw data to our schema
│   │   ├── enrichment.py           # Enrich with brain nutrients & impacts (was enrich.py)
│   │   ├── validation.py           # Validate against schema and rules
│   │   └── food-source-prioritization.py # Multi-source data integration (new)
│   └── ai/
│       ├── prompt_templates/        # Templates for AI data enrichment
│       ├── openai-client.py         # OpenAI API integration
│       └── evaluation.py            # Evaluate AI-generated data
├── data/
│   ├── raw/
│   │   ├── usda_foods/              # Raw data from USDA
│   │   ├── openfoodfacts/           # OpenFoodFacts data (new)
│   │   ├── literature/              # Literature excerpts and summaries
│   │   └── manual_entries/          # Manually entered data
│   ├── processed/
│   │   ├── base_foods/              # Processed base data (directory not JSON file)
│   │   └── curated_nutrients/       # Manually curated brain nutrients
│   ├── enriched/
│   │   ├── ai_generated/            # AI-enriched data
│   │   ├── expert_reviewed/         # Expert-reviewed entries
│   │   └── merged/                  # Multi-source merged data (was combined)
│   └── metadata/
│       ├── sources.json             # Data source tracking
│       └── version_history.json     # Version tracking
└── docs/
    ├── methodology.md               # Detailed methodology description
    ├── data-dictionary.md           # Field definitions (uses hyphen)
    ├── literature_review.md         # Literature review for key relationships
    ├── ai_methodology.md            # AI enrichment approach
    └── examples/
        ├── jupyter/                 # Example Jupyter notebooks
        └── visualizations/          # Data visualizations