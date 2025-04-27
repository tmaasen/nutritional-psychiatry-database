#!/usr/bin/env python3
"""
Literature Extraction Script for Nutritional Psychiatry Dataset

This script extracts structured data from scientific literature on nutritional psychiatry,
focusing on food-mood relationships, mechanisms, and evidence quality.

Features:
- Science-Based Evidence Classification: Implements a hierarchical evidence-rating system based on research standards in nutritional psychiatry, with meta-analyses and RCTs at the top
- Nutrient-Mood Relationship Extraction: Uses natural language processing to identify relationships between nutrients and mental health outcomes from scientific text
- Mechanism Identification: Extracts biological mechanisms by which nutrients impact mental health when mentioned in literature
- Confidence Rating System: Automatically assigns confidence ratings based on study design, sample size, and methodology
- Schema Conversion: Converts extracted relationships into the standardized schema format with proper citations
- Multiple Source Support: Handles both PDF papers and web-based articles

Based on nutritional psychiatry research methodology from:
- Marx et al. (2021) - Nutritional Psychiatry: The Present State of the Evidence
- Jacka et al. (2017) - The 'SMILES' trial
- Firth et al. (2019) - Food and mood: how do diet and nutrition affect mental wellbeing?
"""

import os
import json
import re
import csv
import logging
import argparse
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass
from datetime import datetime
import hashlib
import pdfplumber  # For PDF extraction
import requests
from bs4 import BeautifulSoup  # For web page extraction
import nltk
from nltk.tokenize import sent_tokenize
nltk.download('punkt', quiet=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class StudyMetadata:
    """Metadata about a scientific study."""
    title: str
    authors: List[str]
    publication: str
    year: int
    doi: Optional[str] = None
    pmid: Optional[str] = None
    study_type: Optional[str] = None
    sample_size: Optional[int] = None
    
    def to_citation(self) -> str:
        """Format as a citation string."""
        authors_str = ", ".join(self.authors)
        return f"{authors_str} ({self.year}). {self.title}. {self.publication}."
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "title": self.title,
            "authors": self.authors,
            "publication": self.publication,
            "year": self.year,
            "doi": self.doi,
            "pmid": self.pmid,
            "study_type": self.study_type,
            "sample_size": self.sample_size
        }

@dataclass
class NutrientMoodRelationship:
    """Represents a relationship between a nutrient and mental health outcome."""
    nutrient: str  # Normalized nutrient name
    food_source: Optional[str]  # Food source if mentioned
    mental_health_outcome: str  # Effect on mental health
    direction: str  # positive, negative, mixed, neutral
    mechanism: Optional[str]  # Biological mechanism if mentioned
    evidence_type: str  # Type of evidence (RCT, observational, etc.)
    confidence: int  # 1-10 scale
    study_metadata: StudyMetadata
    extracted_text: str  # Original text from which this was extracted
    
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


class NutrientNameNormalizer:
    """Normalizes nutrient names to match our schema."""
    
    def __init__(self, mapping_file: Optional[str] = None):
        """
        Initialize with optional mapping file.
        
        Args:
            mapping_file: Path to JSON file with nutrient name mappings
        """
        self.mapping = {
            # Default mappings
            "omega-3": "omega3.total_g",
            "omega-3 fatty acids": "omega3.total_g",
            "epa": "omega3.epa_mg",
            "dha": "omega3.dha_mg",
            "alpha-linolenic acid": "omega3.ala_mg",
            "vitamin b6": "vitamin_b6_mg",
            "pyridoxine": "vitamin_b6_mg",
            "folate": "folate_mcg",
            "folic acid": "folate_mcg",
            "vitamin b12": "vitamin_b12_mcg",
            "cobalamin": "vitamin_b12_mcg",
            "vitamin d": "vitamin_d_mcg",
            "cholecalciferol": "vitamin_d_mcg",
            "magnesium": "magnesium_mg",
            "zinc": "zinc_mg",
            "iron": "iron_mg",
            "selenium": "selenium_mcg",
            "tryptophan": "tryptophan_mg",
            "tyrosine": "tyrosine_mg",
            "choline": "choline_mg",
            "polyphenols": "bioactive_compounds.polyphenols_mg",
            "flavonoids": "bioactive_compounds.flavonoids_mg",
            "anthocyanins": "bioactive_compounds.anthocyanins_mg",
            "carotenoids": "bioactive_compounds.carotenoids_mg",
            "probiotics": "bioactive_compounds.probiotics_cfu",
            "prebiotic fiber": "bioactive_compounds.prebiotic_fiber_g"
        }
        
        # Load additional mappings if provided
        if mapping_file and os.path.exists(mapping_file):
            try:
                with open(mapping_file, 'r') as f:
                    additional_mappings = json.load(f)
                self.mapping.update(additional_mappings)
                logger.info(f"Loaded {len(additional_mappings)} additional nutrient mappings")
            except Exception as e:
                logger.error(f"Error loading nutrient mappings: {e}")
    
    def normalize(self, nutrient_name: str) -> str:
        """
        Normalize a nutrient name to match our schema.
        
        Args:
            nutrient_name: Raw nutrient name from literature
            
        Returns:
            Normalized nutrient name according to our schema
        """
        # Convert to lowercase for matching
        nutrient_lower = nutrient_name.lower()
        
        # Check for exact match
        if nutrient_lower in self.mapping:
            return self.mapping[nutrient_lower]
        
        # Check for partial matches
        for key, value in self.mapping.items():
            if key in nutrient_lower:
                return value
        
        # If no match, return as is
        return nutrient_name


class EvidenceClassifier:
    """Classifies evidence and assigns confidence ratings based on study attributes."""
    
    def __init__(self):
        """Initialize with evidence hierarchies for nutritional psychiatry."""
        # Evidence type hierarchy (from highest to lowest quality)
        self.evidence_hierarchy = {
            "meta_analysis": 10,
            "systematic_review": 9,
            "rct": 8,  # Randomized Controlled Trial
            "cohort_large": 7,  # Large cohort study (>1000 participants)
            "cohort_medium": 6,  # Medium cohort study (100-1000 participants)
            "case_control": 5,
            "cross_sectional_large": 4,
            "cross_sectional_small": 3,
            "case_series": 2,
            "animal_study": 2,
            "in_vitro": 1,
            "expert_opinion": 1
        }
        
        # Adjustment factors
        self.adjustment_factors = {
            "sample_size_large": 1,  # >1000 participants
            "sample_size_medium": 0,  # 100-1000 participants
            "sample_size_small": -1,  # <100 participants
            "mechanistic_explanation": 1,  # Clear mechanism provided
            "replicated_findings": 1,  # Findings replicated in multiple studies
            "methodological_issues": -2,  # Significant methodological issues
            "conflict_of_interest": -1,  # Potential conflicts of interest
            "nutrient_focus": 0,  # Primary focus on nutrient vs. incidental
            "direct_measurement": 1,  # Direct measurement vs. self-report
        }
        
        # Study type keywords
        self.study_type_keywords = {
            "meta-analysis": "meta_analysis",
            "meta analysis": "meta_analysis",
            "systematic review": "systematic_review",
            "randomized controlled trial": "rct",
            "rct": "rct",
            "randomised controlled trial": "rct",
            "double-blind": "rct",
            "double blind": "rct",
            "placebo-controlled": "rct",
            "placebo controlled": "rct",
            "cohort study": "cohort_medium",
            "prospective cohort": "cohort_medium",
            "longitudinal study": "cohort_medium",
            "case-control": "case_control",
            "case control": "case_control",
            "cross-sectional": "cross_sectional_small",
            "cross sectional": "cross_sectional_small",
            "observational study": "cross_sectional_small",
            "case series": "case_series",
            "case report": "case_series",
            "animal study": "animal_study",
            "animal model": "animal_study",
            "in vitro": "in_vitro",
            "cell culture": "in_vitro",
            "expert opinion": "expert_opinion",
            "review": "expert_opinion"
        }
    
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
        self.nutrient_keywords = [
            "omega-3", "omega 3", "epa", "dha", "folate", "vitamin b", "vitamin d",
            "magnesium", "zinc", "iron", "selenium", "tryptophan", "tyrosine",
            "polyphenol", "flavonoid", "probiotic", "prebiotic", "fiber", "fibre",
            "fatty acid", "antioxidant", "choline", "protein", "carbohydrate",
            "sugar", "amino acid", "mineral", "micronutrient", "macronutrient"
        ]
        
        # Keywords for mental health outcomes
        self.mental_health_keywords = [
            "depression", "anxiety", "mood", "stress", "cognition", "cognitive",
            "memory", "attention", "focus", "brain health", "mental health",
            "well-being", "wellbeing", "psychological", "neurodevelopment",
            "neuroplasticity", "bdnf", "serotonin", "dopamine", "neurotransmitter",
            "stress response", "hpa axis", "inflammation", "neuroinflammation"
        ]
        
        # Food sources
        self.food_sources = [
            "fish", "seafood", "salmon", "sardines", "tuna", "mackerel", "nuts",
            "seeds", "vegetables", "fruits", "whole grains", "beans", "legumes",
            "dairy", "yogurt", "cheese", "eggs", "meat", "poultry", "olive oil",
            "fermented foods", "chocolate", "green tea", "berries", "leafy greens"
        ]
        
        # Direction keywords
        self.direction_keywords = {
            "positive": ["improve", "increase", "enhance", "elevate", "promote", "benefit", "positive", "protective"],
            "negative": ["worsen", "decrease", "reduce", "lower", "diminish", "impair", "negative", "harmful"],
            "mixed": ["mixed", "variable", "inconsistent", "context-dependent", "unclear", "varied"],
            "neutral": ["no effect", "no association", "no relationship", "no impact", "no influence", "neutral"]
        }
    
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
        mechanism_indicators = [
            "through", "via", "by", "mechanism", "pathway", "due to",
            "mediated by", "because of", "as a result of"
        ]
        
        for indicator in mechanism_indicators:
            if indicator in text.lower():
                # Find the part of text after the indicator
                parts = text.lower().split(indicator, 1)
                if len(parts) > 1:
                    # Take up to 100 characters after the indicator
                    mechanism = parts[1].strip()[:100]
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


class PDFExtractor:
    """Extracts text from PDF files."""
    
    def extract_text(self, pdf_path: str) -> Tuple[str, Optional[StudyMetadata]]:
        """
        Extract text and metadata from a PDF file.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Tuple of (extracted_text, metadata)
        """
        text = ""
        metadata = None
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # Extract metadata from first page
                first_page = pdf.pages[0]
                first_page_text = first_page.extract_text()
                
                # Try to extract metadata
                metadata = self._extract_metadata(first_page_text, pdf.metadata)
                
                # Extract text from all pages
                for page in pdf.pages:
                    text += page.extract_text() + "\n"
            
            return text, metadata
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF {pdf_path}: {e}")
            return "", None
    
    def _extract_metadata(self, first_page_text: str, pdf_metadata: Dict) -> Optional[StudyMetadata]:
        """Extract study metadata from PDF first page and metadata."""
        # Default values
        title = ""
        authors = []
        publication = ""
        year = 2000
        doi = None
        
        # Try to extract title (usually first line or pdf title)
        if pdf_metadata and "title" in pdf_metadata:
            title = pdf_metadata["title"]
        else:
            # Try first line of first page
            lines = first_page_text.split('\n')
            if lines:
                title = lines[0]
        
        # Try to extract authors
        author_line = ""
        for line in first_page_text.split('\n')[:10]:  # Check first 10 lines
            if "," in line and not line.startswith("Abstract") and not line.startswith("Keywords"):
                author_line = line
                break
        
        if author_line:
            # Simple heuristic: split by commas and "and"
            author_parts = re.split(r',|\sand\s', author_line)
            authors = [part.strip() for part in author_parts if part.strip()]
        
        # Try to extract year
        year_match = re.search(r'(19|20)\d{2}', first_page_text[:1000])
        if year_match:
            try:
                year = int(year_match.group(0))
            except ValueError:
                pass
        
        # Try to extract DOI
        doi_match = re.search(r'doi:?\s*([^\s]+)', first_page_text, re.IGNORECASE)
        if doi_match:
            doi = doi_match.group(1)
        
        # Try to extract publication
        publication_indicators = ["journal", "proceedings", "conference", "volume", "issue"]
        for line in first_page_text.split('\n')[:20]:  # Check first 20 lines
            if any(indicator in line.lower() for indicator in publication_indicators):
                publication = line.strip()
                break
        
        if title and year:
            return StudyMetadata(
                title=title,
                authors=authors,
                publication=publication,
                year=year,
                doi=doi
            )
        
        return None


class WebPageExtractor:
    """Extracts text from web pages."""
    
    def extract_text(self, url: str) -> Tuple[str, Optional[StudyMetadata]]:
        """
        Extract text and metadata from a web page.
        
        Args:
            url: URL of web page
            
        Returns:
            Tuple of (extracted_text, metadata)
        """
        try:
            response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.extract()
            
            # Extract text
            text = soup.get_text()
            
            # Clean text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            # Try to extract metadata
            metadata = self._extract_metadata(soup, url)
            
            return text, metadata
            
        except Exception as e:
            logger.error(f"Error extracting text from web page {url}: {e}")
            return "", None
    
    def _extract_metadata(self, soup: BeautifulSoup, url: str) -> Optional[StudyMetadata]:
        """Extract study metadata from web page."""
        # Try to extract title
        title = ""
        title_tag = soup.find('title')
        if title_tag:
            title = title_tag.text
        
        # Try meta tags
        meta_title = soup.find('meta', {'property': 'og:title'}) or soup.find('meta', {'name': 'title'})
        if meta_title and 'content' in meta_title.attrs:
            title = meta_title['content']
        
        # Try to extract authors
        authors = []
        author_meta = soup.find('meta', {'name': 'author'}) or soup.find('meta', {'property': 'article:author'})
        if author_meta and 'content' in author_meta.attrs:
            authors = [author.strip() for author in author_meta['content'].split(',')]
        
        # Try to extract publication
        publication = ""
        site_name = soup.find('meta', {'property': 'og:site_name'})
        if site_name and 'content' in site_name.attrs:
            publication = site_name['content']
        
        # Try to extract year
        year = datetime.now().year
        pub_date = soup.find('meta', {'property': 'article:published_time'}) or soup.find('meta', {'name': 'date'})
        if pub_date and 'content' in pub_date.attrs:
            try:
                year_match = re.search(r'(19|20)\d{2}', pub_date['content'])
                if year_match:
                    year = int(year_match.group(0))
            except (ValueError, TypeError):
                pass
        
        # Try to extract DOI
        doi = None
        doi_link = soup.find('a', href=re.compile(r'doi.org'))
        if doi_link:
            doi_match = re.search(r'doi.org/([^/\s]+/[^/\s]+)', doi_link['href'])
            if doi_match:
                doi = doi_match.group(1)
        
        if title:
            return StudyMetadata(
                title=title,
                authors=authors,
                publication=publication or url,
                year=year,
                doi=doi
            )
        
        return None


class SchemaConverter:
    """Converts extracted relationships to our schema format."""
    
    def relationship_to_mental_health_impact(self, relationship: NutrientMoodRelationship) -> Dict:
        """
        Convert relationship to mental health impact format for schema.
        
        Args:
            relationship: Extracted relationship
            
        Returns:
            Dictionary in mental_health_impacts schema format
        """
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
        for keyword, impact in impact_mapping.items():
            if keyword in relationship.mental_health_outcome.lower():
                impact_type = impact
                break
        
        # Determine time to effect based on study type
        time_to_effect = "cumulative"  # Default
        if relationship.evidence_type in ["rct"]:
            if relationship.study_metadata.sample_size and relationship.study_metadata.sample_size < 100:
                time_to_effect = "acute"  # Small RCTs are often short-term
        
        # Create citation
        citation = relationship.study_metadata.to_citation()
        if relationship.study_metadata.doi:
            citation_doi = f"DOI: {relationship.study_metadata.doi}"
        else:
            citation_doi = None
        
        research_support = [
            {
                "citation": citation,
                "doi": citation_doi,
                "study_type": relationship.evidence_type,
                "year": relationship.study_metadata.year
            }
        ]
        
        return {
            "impact_type": impact_type,
            "direction": direction_mapping.get(relationship.direction, "mixed"),
            "mechanism": relationship.mechanism or f"Effect on {relationship.mental_health_outcome}",
            "strength": min(relationship.confidence, 9),  # Slightly lower than confidence
            "confidence": relationship.confidence,
            "time_to_effect": time_to_effect,
            "research_context": f"Based on {relationship.evidence_type} study",
            "research_support": research_support,
            "notes": relationship.extracted_text
        }
    
    def relationships_to_schema(self, relationships: List[NutrientMoodRelationship]) -> Dict:
        """
        Convert relationships to our schema format.
        
        Args:
            relationships: List of extracted relationships
            
        Returns:
            Dictionary in our schema format
        """
        # Group relationships by nutrient
        nutrient_groups = {}
        for relationship in relationships:
            if relationship.nutrient not in nutrient_groups:
                nutrient_groups[relationship.nutrient] = []
            nutrient_groups[relationship.nutrient].append(relationship)
        
        # Process each nutrient group
        result = {}
        
        for nutrient, nutrient_relationships in nutrient_groups.items():
            # Determine nutrient path in schema
            if "." in nutrient:
                # Compound path (e.g., omega3.total_g)
                parts = nutrient.split(".")
                section = parts[0]
                field = ".".join(parts[1:])
            else:
                # Simple nutrient
                if "brain_nutrients" in nutrient or nutrient.endswith("_mg") or nutrient.endswith("_mcg") or nutrient.endswith("_g"):
                    section = "brain_nutrients"
                    field = nutrient
                elif "bioactive" in nutrient:
                    section = "bioactive_compounds"
                    field = nutrient.replace("bioactive_compounds.", "")
                else:
                    section = "brain_nutrients"
                    field = nutrient
            
            # Create section if doesn't exist
            if section not in result:
                result[section] = {}
            
            # Add value based on evidence
            # For this example, we'll just note that it has literature evidence
            # In a real implementation, you might extract actual values
            if "." in field:
                # Handle nested fields (e.g., omega3.total_g)
                subparts = field.split(".")
                subsection = subparts[0]
                subfield = ".".join(subparts[1:])
                
                if subsection not in result[section]:
                    result[section][subsection] = {}
                
                result[section][subsection][subfield] = "literature_evidence"
            else:
                result[section][field] = "literature_evidence"
            
            # Convert relationships to mental health impacts
            if "mental_health_impacts" not in result:
                result["mental_health_impacts"] = []
            
            for relationship in nutrient_relationships:
                impact = self.relationship_to_mental_health_impact(relationship)
                result["mental_health_impacts"].append(impact)
        
        # Add data quality metadata
        if relationships:
            if "data_quality" not in result:
                result["data_quality"] = {}
            
            result["data_quality"]["brain_nutrients_source"] = "literature_derived"
            result["data_quality"]["impacts_source"] = "literature_review"
            
            # Calculate overall confidence based on highest quality evidence
            max_confidence = max(r.confidence for r in relationships)
            result["data_quality"]["overall_confidence"] = max_confidence
        
        # Add metadata
        if "metadata" not in result:
            result["metadata"] = {}
        
        result["metadata"]["version"] = "0.1.0"
        result["metadata"]["created"] = datetime.now().isoformat()
        result["metadata"]["last_updated"] = datetime.now().isoformat()
        
        # Add source URLs
        result["metadata"]["source_urls"] = []
        for relationship in relationships:
            if relationship.study_metadata.doi:
                source_url = f"https://doi.org/{relationship.study_metadata.doi}"
                if source_url not in result["metadata"]["source_urls"]:
                    result["metadata"]["source_urls"].append(source_url)
        
        return result


class LiteratureExtractor:
    """Main class for extracting structured data from literature."""
    
    def __init__(self, output_dir: str = "data/literature"):
        """
        Initialize with necessary components.
        
        Args:
            output_dir: Directory to save extracted data
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize components
        self.nutrient_normalizer = NutrientNameNormalizer()
        self.evidence_classifier = EvidenceClassifier()
        self.relationship_extractor = RelationshipExtractor(
            self.nutrient_normalizer, self.evidence_classifier
        )
        self.pdf_extractor = PDFExtractor()
        self.web_extractor = WebPageExtractor()
        self.schema_converter = SchemaConverter()
        
        # Set up subdirectories
        self.raw_dir = os.path.join(output_dir, "raw")
        self.processed_dir = os.path.join(output_dir, "processed")
        self.schema_dir = os.path.join(output_dir, "schema")
        
        os.makedirs(self.raw_dir, exist_ok=True)
        os.makedirs(self.processed_dir, exist_ok=True)
        os.makedirs(self.schema_dir, exist_ok=True)
    
    def process_pdf(self, pdf_path: str) -> Tuple[List[NutrientMoodRelationship], Dict]:
        """
        Process a PDF file and extract relationships.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Tuple of (relationships, schema_data)
        """
        logger.info(f"Processing PDF: {pdf_path}")
        
        # Extract text and metadata
        text, metadata = self.pdf_extractor.extract_text(pdf_path)
        
        if not text or not metadata:
            logger.warning(f"Failed to extract text or metadata from {pdf_path}")
            return [], {}
        
        # Save raw text
        filename = os.path.basename(pdf_path)
        raw_path = os.path.join(self.raw_dir, f"{filename}.txt")
        with open(raw_path, 'w', encoding='utf-8') as f:
            f.write(text)
        
        # Extract relationships
        relationships = self.relationship_extractor.extract_relationships(text, metadata)
        logger.info(f"Extracted {len(relationships)} relationships from {pdf_path}")
        
        # Save relationships
        relationships_path = os.path.join(self.processed_dir, f"{filename}.json")
        with open(relationships_path, 'w', encoding='utf-8') as f:
            relationships_data = [r.to_dict() for r in relationships]
            json.dump(relationships_data, f, indent=2)
        
        # Convert to schema format
        schema_data = self.schema_converter.relationships_to_schema(relationships)
        
        # Save schema data
        schema_path = os.path.join(self.schema_dir, f"{filename}.json")
        with open(schema_path, 'w', encoding='utf-8') as f:
            json.dump(schema_data, f, indent=2)
        
        return relationships, schema_data
    
    def process_url(self, url: str) -> Tuple[List[NutrientMoodRelationship], Dict]:
        """
        Process a web page and extract relationships.
        
        Args:
            url: URL of web page
            
        Returns:
            Tuple of (relationships, schema_data)
        """
        logger.info(f"Processing URL: {url}")
        
        # Extract text and metadata
        text, metadata = self.web_extractor.extract_text(url)
        
        if not text or not metadata:
            logger.warning(f"Failed to extract text or metadata from {url}")
            return [], {}
        
        # Create filename from URL
        filename = hashlib.md5(url.encode()).hexdigest()
        
        # Save raw text
        raw_path = os.path.join(self.raw_dir, f"{filename}.txt")
        with open(raw_path, 'w', encoding='utf-8') as f:
            f.write(text)
        
        # Extract relationships
        relationships = self.relationship_extractor.extract_relationships(text, metadata)
        logger.info(f"Extracted {len(relationships)} relationships from {url}")
        
        # Save relationships
        relationships_path = os.path.join(self.processed_dir, f"{filename}.json")
        with open(relationships_path, 'w', encoding='utf-8') as f:
            relationships_data = [r.to_dict() for r in relationships]
            json.dump(relationships_data, f, indent=2)
        
        # Convert to schema format
        schema_data = self.schema_converter.rel