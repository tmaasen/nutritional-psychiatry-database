nutritional-psychiatry-dataset/
├── README.md                       # Project overview and documentation
├── LICENSE                         # MIT license
├── CONTRIBUTING.md                 # Guidelines for contributors
├── schema/
│   ├── food_schema.json            # JSON Schema definition
│   └── validation_rules.json       # Additional validation constraints
├── scripts/
│   ├── data_collection/
│   │   ├── usda_api.py             # Interface with USDA FoodData Central API
│   │   ├── literature_extract.py   # Extract data from research papers
│   │   └── config.py               # Configuration settings
│   ├── data_processing/
│   │   ├── transform.py            # Transform raw data to our schema
│   │   ├── enrich.py               # Enrich with brain nutrients & impacts
│   │   └── validate.py             # Validate against schema and rules
│   └── ai/
│       ├── prompt_templates/        # Templates for AI data enrichment
│       ├── openai_client.py         # OpenAI API integration
│       └── evaluation.py            # Evaluate AI-generated data
├── data/
│   ├── raw/
│   │   ├── usda_foods/              # Raw data from USDA
│   │   ├── literature/              # Literature excerpts and summaries
│   │   └── manual_entries/          # Manually entered data
│   ├── processed/
│   │   ├── base_foods.json          # Processed USDA data
│   │   └── curated_nutrients.json   # Manually curated brain nutrients
│   ├── enriched/
│   │   ├── ai_generated/            # AI-enriched data
│   │   ├── expert_reviewed/         # Expert-reviewed entries
│   │   └── combined/                # Final combined dataset
│   └── metadata/
│       ├── sources.json             # Data source tracking
│       └── version_history.json     # Version tracking
└── docs/
    ├── methodology.md               # Detailed methodology description
    ├── data_dictionary.md           # Field definitions
    ├── literature_review.md         # Literature review for key relationships
    ├── ai_methodology.md            # AI enrichment approach
    └── examples/
        ├── jupyter/                 # Example Jupyter notebooks
        └── visualizations/          # Data visualizations
