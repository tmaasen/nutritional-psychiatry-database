#!/usr/bin/env python3
import re
import nltk
from nltk.tokenize import sent_tokenize
from typing import Dict, List, Optional, Tuple

from utils.logging_utils import setup_logging
from utils.document_utils import StudyMetadata
from utils.nutrient_utils import NutrientNameNormalizer
from constants.literature_constants import (
    NUTRIENT_KEYWORDS, MENTAL_HEALTH_KEYWORDS, FOOD_SOURCES, 
    DIRECTION_KEYWORDS, EVIDENCE_HIERARCHY, EVIDENCE_ADJUSTMENT_FACTORS,
    STUDY_TYPE_KEYWORDS, MECHANISM_INDICATORS, MECHANISM_EXTRACT_LENGTH
)

# Ensure NLTK data is downloaded
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

# Initialize logger
logger = setup_logging(__name__)

class NutrientMoodRelationship:
    """Represents a relationship between a nutrient and mental health outcome."""
    def __init__(
        self,
        nutrient: str,
        mental_health_outcome: str,
        direction: str,
        evidence_type: str,
        confidence: int,
        study_metadata: StudyMetadata,
        extracted_text: str,
        food_source: Optional[str] = None,
        mechanism: Optional[str] = None
    ):
        self.nutrient = nutrient
        self.food_source = food_source
        self.mental_health_outcome = mental_health_outcome
        self.direction = direction
        self.mechanism = mechanism
        self.evidence_type = evidence_type
        self.confidence = confidence
        self.study_metadata = study_metadata
        self.extracted_text = extracted_text
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "nutrient": self.nutrient,
            "food_source": self.food_source,
            "mental_health_outcome": self.mental_health_outcome,
            "direction": self.direction,
            "mechanism": self.mechanism,
            "evidence_type": self.evidence_type,
            "confidence": self.confidence,
            "study_metadata": self.study_metadata.to_dict(),
            "extracted_text": self.extracted_text
        }

class EvidenceClassifier:
    """Classifies evidence and assigns confidence ratings based on study attributes."""
    
    def __init__(self):
        """Initialize with evidence hierarchies for nutritional psychiatry."""
        # Evidence type hierarchy (from highest to lowest quality)
        self.evidence_hierarchy = EVIDENCE_HIERARCHY
        
        # Adjustment factors
        self.adjustment_factors = EVIDENCE_ADJUSTMENT_FACTORS
        
        # Study type keywords
        self.study_type_keywords = STUDY_TYPE_KEYWORDS
    
    def classify_evidence(self, study_metadata: StudyMetadata, extracted_text: str) -> Tuple[str, int]:
        """
        Classify evidence type and assign confidence rating.
        
        Args:
            study_metadata: Metadata about the study
            extracted_text: Text excerpt discussing the relationship
            
        Returns:
            Tuple of (evidence_type, confidence_rating)
        """
        # Determine study type from metadata or text
        evidence_type = "cross_sectional_small"  # Default
        
        # Check metadata
        if study_metadata.study_type:
            for keyword, study_type in self.study_type_keywords.items():
                if keyword in study_metadata.study_type.lower():
                    evidence_type = study_type
                    break
        
        # Check text if not found in metadata
        if evidence_type == "cross_sectional_small" and extracted_text:
            for keyword, study_type in self.study_type_keywords.items():
                if keyword in extracted_text.lower():
                    evidence_type = study_type
                    break
        
        # Get base confidence from evidence hierarchy
        base_confidence = self.evidence_hierarchy.get(evidence_type, 3)
        
        # Apply adjustments
        adjustments = 0
        
        # Sample size adjustment
        if study_metadata.sample_size:
            if study_metadata.sample_size > 1000:
                adjustments += self.adjustment_factors["sample_size_large"]
            elif study_metadata.sample_size < 100:
                adjustments += self.adjustment_factors["sample_size_small"]
        
        # Mechanistic explanation
        mechanism_keywords = ["mechanism", "pathway", "signaling", "signalling", "receptor", "neurotransmitter"]
        if any(keyword in extracted_text.lower() for keyword in mechanism_keywords):
            adjustments += self.adjustment_factors["mechanistic_explanation"]
        
        # Methodological issues
        issue_keywords = ["limitation", "bias", "confound", "problematic", "drawback"]
        if any(keyword in extracted_text.lower() for keyword in issue_keywords):
            adjustments += self.adjustment_factors["methodological_issues"]
        
        # Direct measurement
        measurement_keywords = ["blood sample", "serum level", "plasma concentration", "measured"]
        if any(keyword in extracted_text.lower() for keyword in measurement_keywords):
            adjustments += self.adjustment_factors["direct_measurement"]
        
        # Calculate final confidence
        confidence = max(1, min(10, base_confidence + adjustments))
        
        return evidence_type, confidence

class RelationshipExtractor:
    """Extracts nutrient-mood relationships from scientific text."""
    
    def __init__(self, nutrient_normalizer: NutrientNameNormalizer, evidence_classifier: EvidenceClassifier):
        """
        Initialize with necessary components.
        
        Args:
            nutrient_normalizer: For normalizing nutrient names
            evidence_classifier: For classifying evidence and confidence
        """
        self.nutrient_normalizer = nutrient_normalizer
        self.evidence_classifier = evidence_classifier
        
        # Keywords for nutrients/foods
        self.nutrient_keywords = NUTRIENT_KEYWORDS
        
        # Keywords for mental health outcomes
        self.mental_health_keywords = MENTAL_HEALTH_KEYWORDS
        
        # Food sources
        self.food_sources = FOOD_SOURCES
        
        # Direction keywords
        self.direction_keywords = DIRECTION_KEYWORDS
    
    def _find_nutrient_in_text(self, text: str) -> Optional[str]:
        """Find nutrient mentioned in text."""
        for nutrient in self.nutrient_keywords:
            if nutrient in text.lower():
                # Find more specific version including surrounding words
                pattern = r'\b\w*\s*' + re.escape(nutrient) + r'\s*\w*\b'
                matches = re.findall(pattern, text.lower())
                if matches:
                    # Return the longest match
                    longest_match = max(matches, key=len)
                    return longest_match
                return nutrient
        return None
    
    def _find_mental_health_outcome(self, text: str) -> Optional[str]:
        """Find mental health outcome mentioned in text."""
        for outcome in self.mental_health_keywords:
            if outcome in text.lower():
                # Find more specific version including surrounding words
                pattern = r'\b\w*\s*' + re.escape(outcome) + r'\s*\w*\b'
                matches = re.findall(pattern, text.lower())
                if matches:
                    # Return the longest match
                    longest_match = max(matches, key=len)
                    return longest_match
                return outcome
        return None
    
    def _find_food_source(self, text: str) -> Optional[str]:
        """Find food source mentioned in text."""
        for food in self.food_sources:
            if food in text.lower():
                return food
        return None
    
    def _determine_direction(self, text: str) -> str:
        """Determine direction of effect (positive, negative, etc.)."""
        for direction, keywords in self.direction_keywords.items():
            for keyword in keywords:
                if keyword in text.lower():
                    return direction
        return "unclear"
    
    def _extract_mechanism(self, text: str) -> Optional[str]:
        """Extract mechanism of action if mentioned."""
        for indicator in MECHANISM_INDICATORS:
            if indicator in text.lower():
                # Find the part of text after the indicator
                parts = text.lower().split(indicator, 1)
                if len(parts) > 1:
                    # Take up to specified characters after the indicator
                    mechanism = parts[1].strip()[:MECHANISM_EXTRACT_LENGTH]
                    return mechanism
        
        return None
    
    def extract_relationships(self, text: str, study_metadata: StudyMetadata) -> List[NutrientMoodRelationship]:
        """
        Extract nutrient-mood relationships from text.
        
        Args:
            text: Scientific text to extract from
            study_metadata: Metadata about the source study
            
        Returns:
            List of extracted relationships
        """
        relationships = []
        
        # Split into sentences
        sentences = sent_tokenize(text)
        
        for sentence in sentences:
            # Only process sentences that have both nutrient and mental health keywords
            nutrient_mentioned = any(keyword in sentence.lower() for keyword in self.nutrient_keywords)
            mental_health_mentioned = any(keyword in sentence.lower() for keyword in self.mental_health_keywords)
            
            if nutrient_mentioned and mental_health_mentioned:
                # Extract components
                nutrient_raw = self._find_nutrient_in_text(sentence)
                if not nutrient_raw:
                    continue
                
                nutrient = self.nutrient_normalizer.normalize(nutrient_raw)
                mental_health_outcome = self._find_mental_health_outcome(sentence)
                food_source = self._find_food_source(sentence)
                direction = self._determine_direction(sentence)
                mechanism = self._extract_mechanism(sentence)
                
                # Classify evidence and confidence
                evidence_type, confidence = self.evidence_classifier.classify_evidence(
                    study_metadata, sentence
                )
                
                # Create relationship
                relationship = NutrientMoodRelationship(
                    nutrient=nutrient,
                    food_source=food_source,
                    mental_health_outcome=mental_health_outcome,
                    direction=direction,
                    mechanism=mechanism,
                    evidence_type=evidence_type,
                    confidence=confidence,
                    study_metadata=study_metadata,
                    extracted_text=sentence
                )
                
                relationships.append(relationship)
        
        return relationships