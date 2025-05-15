# Nutritional Psychiatry Database

A comprehensive database connecting food composition to mental health outcomes.

## Overview

The Nutritional Psychiatry Database integrates data from USDA, OpenFoodFacts, and scientific literature with AI-enriched predictions to create a unique resource mapping the relationship between nutrition and mental health.

[Data Collection & Processing Methodology](/docs/methodology.md)

[AI Methodology](/docs/ai-methodology.md)

[Data Dictionary](/docs/data-dictionary.md)

[Literature Review Methodology](/docs/literature-review.md)

## Key Features

- **Brain-specific nutrients**: Tryptophan, omega-3 fatty acids, B vitamins, etc.
- **Bioactive compounds**: Polyphenols, flavonoids, anthocyanins, etc.
- **Mental health impacts**: Evidence-based connections between foods and mental wellness
- **Nutrient interactions**: Synergistic and antagonistic relationships between nutrients
- **Confidence ratings**: Calibrated uncertainty representation for all predictions

### The Problem

Current food databases like USDA FoodData Central provide excellent general nutritional information but lack:
1. Complete data on brain-specific nutrients (omega-3s, tryptophan, etc.)
2. Information about bioactive compounds relevant to brain health
3. Evidence-based connections to mental health impacts
4. Confidence ratings to communicate data quality

### Our Approach

We're building a database that:
- Starts with trusted USDA data as a foundation
- Enriches it with brain-specific nutrients often missing from standard databases
- Adds research-backed mood impact relationships with confidence ratings
- Includes comprehensive metadata for transparency and quality tracking

## Schema

The data follows a comprehensive schema that includes:

### Basic Food Information
- Unique identifier
- Name and description
- Food category
- Serving size information

### Standard Nutrients
- Macronutrients (protein, carbs, fat)
- Vitamins
- Minerals
- Fiber
- Sugars

### Brain-Specific Nutrients
- Omega-3 fatty acids (EPA, DHA, ALA)
- Tryptophan (serotonin precursor)
- Tyrosine (dopamine precursor)
- B vitamins (B6, B9/folate, B12)
- Vitamin D
- Magnesium, zinc, iron, selenium
- Choline

### Bioactive Compounds
- Polyphenols
- Flavonoids
- Anthocyanins
- Carotenoids
- Prebiotic fiber
- Probiotic content

### Mental Health Impacts
- Impact type (mood, anxiety, cognition, etc.)
- Direction of effect (positive, negative, neutral)
- Mechanism of action
- Strength of effect (1-10 scale)
- Confidence rating based on research evidence
- Time to effect (acute vs. cumulative)
- Research citations

### Data Quality Metrics
- Completeness scores
- Overall confidence rating
- Source tracking (measured, literature-derived, AI-generated)

## Project Structure

Please see [project-structure.md](/project-structure.md)

## Data Sources

The database is built from multiple sources:

1. **USDA FoodData Central**: Provides the foundation of standard nutrient data
2. **Open Food Facts**: Open-source database that contains many data points on food items that FoodDataCentral does not contain.
3. **Published Research Literature**: Source for specific brain-nutrient connections and mental health impacts
4. **AI-Assisted Generation**: For filling gaps in data where direct measurements aren't available
5. **Expert Validation**: For quality control and confidence rating

All data includes source tracking and confidence ratings.

## Getting Started

### Prerequisites

- Python 3.8+
- Required packages: `pip install -r requirements.txt`
- USDA FoodData Central API key (free from [data.gov](https://api.data.gov/signup/))
- OpenAI API key (for AI-assisted enrichment)

### Installation

```bash
# Clone the repository
git clone https://github.com/tmaasen/nutritional-psychiatry-database.git
cd nutritional-psychiatry-database

# Install dependencies
pip install -r requirements.txt

# Set environment variables in a .env file
USDA_API_KEY=your_api_key
OPENAI_API_KEY=your_openai_key

DB_HOST=localhost
DB_PORT=5432
DB_NAME=nutritional_psychiatry
DB_USER=your_username
DB_PASSWORD=your_password
DB_SSLMODE=require

AI_MODEL=gpt-4o-mini
AI_TEMPERATURE=0.2
AI_MAX_TOKENS=2000   
```

### Usage

### Running the Pipeline

Use the orchestrator script to run the full pipeline or specific steps:

```bash
# Run interactively
python scripts/orchestrator.py --interactive

# Process specific foods
python scripts/orchestrator.py --foods "blueberries raw" "salmon atlantic raw"

# Run specific steps only
python scripts/orchestrator.py --only "usda_data_collection" "data_transformation"
```

## Roadmap

1. **Phase 1: Data Collection & Foundation**
   - Establish USDA data as base
   - Define schema for brain-specific nutrients
   - Create data pipeline structure

2. **Phase 2: AI-Assisted Enrichment**
   - Use GPT-4 or similar models to generate missing nutrient data
   - Extract relationships from nutritional psychiatry literature
   - Implement confidence scoring system

3. **Phase 3: Quality Control**
   - Create validation interfaces
   - Document data sources and generation methods
   - Prepare for expert review

4. **Phase 4: Public Release & Expansion**
   - Expand coverage to more foods
   - Incorporate community contributions

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

We especially welcome:
- Nutritional scientists
- Mental health professionals
- Data scientists
- Developers building nutrition and wellness applications

## Scientific Validation

```mermaid
flowchart TD
    %% Input
    FOOD[Food Data Entry]
    
    %% Schema Validation
    SCHEMA[Schema Validation]
    
    %% Validation Types
    subgraph "Validation Rules"
        NUTRIENT_PLAUS[Nutrient Plausibility\nChecks]
        NUTRIENT_REL[Nutrient Relationship\nChecks]
        IMPACT_EVIDENCE[Mental Health Impact\nEvidence Checks]
        CITATIONS[Citation\nRequirements]
        CONFIDENCE[Confidence Rating\nCalibration]
    end
    
    %% Known-Answer Testing
    KNOWN[Known-Answer Testing]
    
    %% Output Branches
    PASS[Validation Passed]
    ADJUST[Needs Adjustment]
    REJECT[Validation Failed]
    
    %% Flow
    FOOD --> SCHEMA
    
    SCHEMA -- Valid Schema --> NUTRIENT_PLAUS & NUTRIENT_REL & IMPACT_EVIDENCE & CITATIONS & CONFIDENCE
    SCHEMA -- Invalid Schema --> REJECT
    
    NUTRIENT_PLAUS & NUTRIENT_REL & IMPACT_EVIDENCE & CITATIONS & CONFIDENCE --> KNOWN
    
    KNOWN -- All Tests Pass --> PASS
    KNOWN -- Minor Issues --> ADJUST
    KNOWN -- Major Issues --> REJECT
    
    ADJUST --> CONFIDENCE
    
    %% Styling
    classDef input fill:#e6f3ff,stroke:#333,stroke-width:2px
    classDef validation fill:#fff2cc,stroke:#333,stroke-width:2px
    classDef rules fill:#d5e8d4,stroke:#333,stroke-width:2px
    classDef output fill:#ffe6cc,stroke:#333,stroke-width:2px
    
    class FOOD input
    class SCHEMA,KNOWN validation
    class NUTRIENT_PLAUS,NUTRIENT_REL,IMPACT_EVIDENCE,CITATIONS,CONFIDENCE rules
    class PASS,ADJUST,REJECT output
```

This database is being developed with scientific rigor in mind:

- All AI-generated data is clearly marked and confidence-scored
- Literature-based connections include citations to research
- Transparent methodology for all data generation
- Planned expert validation phase

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- USDA FoodData Central and OpenFoodFacts for the foundation nutritional data
- Researchers advancing the field of nutritional psychiatry
- Contributors and advisors to this project

## Contact

- GitHub Issues: For bug reports and feature requests

---

**Note:** This database is intended for research and educational purposes. It should not be used as the sole basis for medical decisions. Always consult healthcare professionals for medical advice.
