#!/usr/bin/env python3
"""
Literature Extraction Script for Nutritional Psychiatry Dataset

This script extracts structured data from scientific literature on nutritional psychiatry,
focusing on food-mood relationships, mechanisms, and evidence quality.
"""

import argparse
from datetime import datetime
from typing import Dict, List, Optional

from constants.food_data_constants import BRAIN_NUTRIENTS_TO_PREDICT
from constants.literature_constants import LITERATURE_COMPLETENESS_DEFAULT, LITERATURE_CONFIDENCE_DEFAULT

from schema.food_data import DataQuality, FoodData, MentalHealthImpact, Metadata, ResearchSupport
from utils.logging_utils import setup_logging
from utils.db_utils import PostgresClient
from utils.document_utils import PDFExtractor, WebPageExtractor
from utils.research_utils import EvidenceClassifier, RelationshipExtractor
from utils.nutrient_utils import NutrientNameNormalizer
from config import get_config

logger = setup_logging(__name__)

class LiteratureExtractor:
    """Extracts structured data from scientific literature for nutritional psychiatry."""
    
    def __init__(self, db_client: PostgresClient = None):
        self.config = get_config()        
        self.db_client = db_client or PostgresClient()
        
        # Initialize components
        self.nutrient_normalizer = NutrientNameNormalizer()
        self.evidence_classifier = EvidenceClassifier()
        self.relationship_extractor = RelationshipExtractor(self.nutrient_normalizer, self.evidence_classifier)
        self.pdf_extractor = PDFExtractor()
        self.web_extractor = WebPageExtractor()

    def process_literature(self, pdf_path: Optional[str] = None, url: Optional[str] = None) -> str:
        """
        Process a PDF file or URL and extract relationships.
        
        Returns:
            Food ID of the imported data
        """
        if pdf_path:
            logger.info(f"Processing PDF: {pdf_path}")
            text, metadata = self.pdf_extractor.extract_text(pdf_path)
        elif url:
            logger.info(f"Processing URL: {url}")
            text, metadata = self.web_extractor.extract_text(url)
        else:
            raise ValueError("Either pdf_path or url must be provided")
        
        if not text or not metadata:
            logger.warning(f"Failed to extract text or metadata from {pdf_path}")
            return ""

        # Extract relationships
        relationships = self.relationship_extractor.extract_relationships(text, metadata)
        logger.info(f"Extracted {len(relationships)} relationships from {pdf_path}")
        
        # Convert to schema format
        food_data = self._relationships_to_food_data(relationships)
        
        # Save to database
        food_id = self.db_client.import_food_from_json(food_data)
        logger.info(f"Imported literature data with ID: {food_id}")
        
        return food_id
    
    def _relationships_to_food_data(self, relationships: List) -> FoodData:
        if not relationships:
            return {}
        
        # Group relationships by food
        food_relationships = {}
        for rel in relationships:
            food_name = rel.food_source or "Unknown"
            if food_name not in food_relationships:
                food_relationships[food_name] = []
            food_relationships[food_name].append(rel)
        
        # Process each food
        result = {}
        for food_name, food_rels in food_relationships.items():
            # Create food ID if needed
            food_id = f"lit_{food_name.lower().replace(' ', '_')}"
            
            # Initialize sections
            mental_health_impacts = []
            brain_nutrients = {}
            
            # Process relationships
            for rel in food_rels:
                # Add mental health impact
                impact = self._create_mental_health_impact(rel)
                if impact:
                    mental_health_impacts.append(impact)
                
                # Add brain nutrient if mentioned
                nutrient = rel.nutrient
                if nutrient in BRAIN_NUTRIENTS_TO_PREDICT and rel.direction == "positive":
                    brain_nutrients[nutrient] = "literature_evidence"
            
            food_data = FoodData(
                food_id=food_id,
                name=food_name,
                category="Literature-derived",
                mental_health_impacts=mental_health_impacts,
                data_quality=DataQuality(
                    completeness=LITERATURE_COMPLETENESS_DEFAULT,  # Use constant instead of hardcoded value
                    overall_confidence=LITERATURE_CONFIDENCE_DEFAULT,  # Use constant instead of hardcoded value
                    brain_nutrients_source="literature_derived",
                    impacts_source="literature_review"
                ),
                metadata=Metadata(
                    version="0.1.0",
                    created=datetime.now().isoformat(),
                    last_updated=datetime.now().isoformat(),
                    source_urls=[],
                    tags=["literature-derived"]
                )
            )
            
            # Add brain nutrients if found
            if brain_nutrients:
                food_data.brain_nutrients = brain_nutrients
            
            # Add source URLs from relationships
            for rel in food_rels:
                if rel.study_metadata.doi:
                    source_url = f"https://doi.org/{rel.study_metadata.doi}"
                    if source_url not in food_data.metadata.source_urls:
                        food_data.metadata.source_urls.append(source_url)
            
            # Use the first relationship's food as the result
            if not result:
                result = food_data
        
        return result
    
    def _create_mental_health_impact(self, relationship) -> MentalHealthImpact:
        # Map relationship direction to schema format
        direction_mapping = {
            "positive": "positive",
            "negative": "negative",
            "mixed": "mixed",
            "neutral": "neutral",
            "unclear": "mixed"  # Default unclear to mixed
        }
        
        # Map mental health outcome to impact type
        impact_mapping = {
            "depression": "mood_depression" if relationship.direction == "negative" else "mood_elevation",
            "anxiety": "anxiety_increase" if relationship.direction == "negative" else "anxiety_reduction",
            "stress": "anxiety_increase" if relationship.direction == "negative" else "stress_reduction",
            "cognition": "cognitive_decline" if relationship.direction == "negative" else "cognitive_enhancement",
            "cognitive": "cognitive_decline" if relationship.direction == "negative" else "cognitive_enhancement",
            "memory": "cognitive_decline" if relationship.direction == "negative" else "cognitive_enhancement",
            "attention": "cognitive_decline" if relationship.direction == "negative" else "cognitive_enhancement",
            "focus": "cognitive_decline" if relationship.direction == "negative" else "cognitive_enhancement",
            "mood": "mood_depression" if relationship.direction == "negative" else "mood_elevation",
            "energy": "energy_decrease" if relationship.direction == "negative" else "energy_increase",
            "sleep": "sleep_improvement" if relationship.direction != "negative" else "anxiety_increase",
            "gut": "gut_health_improvement" if relationship.direction != "negative" else "mood_depression"
        }
        
        # Determine impact type
        impact_type = "mood_elevation"  # Default
        outcome = relationship.mental_health_outcome.lower() if relationship.mental_health_outcome else ""
        for keyword, impact in impact_mapping.items():
            if keyword in outcome:
                impact_type = impact
                break
        
        # Determine time to effect based on study type
        time_to_effect = "cumulative"  # Default
        
        # Create citation
        citation = relationship.study_metadata.to_citation()
        if relationship.study_metadata.doi:
            citation_doi = relationship.study_metadata.doi
        else:
            citation_doi = None
        
        return MentalHealthImpact(
            impact_type=impact_type,
            direction=direction_mapping.get(relationship.direction, "mixed"),
            mechanism=relationship.mechanism or f"Effect on {relationship.mental_health_outcome}",
            strength=min(relationship.confidence, 9),  # Slightly lower than confidence
            confidence=relationship.confidence,
            time_to_effect=time_to_effect,
            research_context=f"Based on {relationship.evidence_type} study",
            research_support=ResearchSupport(
                citation=citation,
                doi=citation_doi,
                study_type=relationship.evidence_type,
                year=relationship.study_metadata.year
            )
        )
    
def main():
    parser = argparse.ArgumentParser(description="Extract data from PDFs and URLs.")
    parser.add_argument("--pdfs", nargs="*", help="List of PDF file paths")
    parser.add_argument("--urls", nargs="*", help="List of URLs")
    args = parser.parse_args()

    db_client = PostgresClient()
    extractor = LiteratureExtractor(db_client)

    processed_ids = []

    # Process PDFs
    if args.pdfs:
        for pdf_path in args.pdfs:
            food_id = extractor.process_pdf(pdf_path)
            if food_id:
                processed_ids.append(food_id)
                logger.info(f"Successfully processed PDF and saved with ID: {food_id}")

    # Process URLs
    if args.urls:
        for url in args.urls:
            food_id = extractor.process_url(url)
            if food_id:
                processed_ids.append(food_id)
                logger.info(f"Successfully processed URL and saved with ID: {food_id}")

    # Report results
    if processed_ids:
        logger.info(f"Successfully processed {len(processed_ids)} literature sources")
    else:
        logger.warning("No literature sources were successfully processed")

if __name__ == "__main__":
    main()