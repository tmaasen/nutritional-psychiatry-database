#!/usr/bin/env python3
"""
Source Prioritization System
Compares and merges data from different sources (USDA, OpenFoodFacts) with intelligent prioritization.
"""

import argparse
from datetime import datetime
import sys
from typing import Dict, List, Optional, Tuple

from schema.food_data import (
    CircadianEffects, ContextualFactors, FoodData, NeuralTarget, PopulationVariation, StandardNutrients, BrainNutrients, Omega3, BioactiveCompounds,
    MentalHealthImpact, ResearchSupport, NutrientInteraction, DataQuality,
    SourcePriority, Metadata
)

# Import utilities
from utils.data_utils import identify_source
from utils.logging_utils import setup_logging
from utils.db_utils import PostgresClient
from utils.data_utils import calculate_completeness

from constants.sql_queries import *
from constants.food_data_constants import BRAIN_NUTRIENTS_TO_PREDICT
from constants.literature_constants import (
    SOURCE_PRIORITY_MAPPING, SOURCE_CONFIDENCE_THRESHOLDS, SOURCE_PRIORITY_FIELD
)

# Initialize logger
logger = setup_logging(__name__)

class SourcePrioritizer:
    """
    Prioritizes and merges data from multiple sources based on data quality.
    """
    
    def __init__(self, db_client: Optional[PostgresClient] = None):
        self.db_client = db_client or PostgresClient()
        self.default_priorities = SOURCE_PRIORITY_MAPPING        
        self.confidence_thresholds = SOURCE_CONFIDENCE_THRESHOLDS
    
    def get_confidence(self, food_data: FoodData, section: str) -> float:
        """
        Get confidence rating for a specific section.
            
        Returns:
            Confidence rating (0-10)
        """
        data_quality = food_data.data_quality
        
        # Section-specific confidence ratings
        if section == "brain_nutrients" and "brain_nutrients_source" in data_quality:
            if data_quality.brain_nutrients_source == "usda_provided":
                return 9
            elif data_quality.brain_nutrients_source == "literature_derived":
                return 8
            elif data_quality.brain_nutrients_source == "openfoodfacts":
                return 7
            elif data_quality.brain_nutrients_source == "ai_generated":
                return data_quality.overall_confidence
        
        # Omega-3 specific confidence
        if section == "omega3" and "brain_nutrients" in food_data:
            brain_nutrients = food_data.brain_nutrients
            if "omega3" in brain_nutrients and "confidence" in brain_nutrients.omega3:
                return brain_nutrients.omega3.confidence
        
        # Mental health impacts confidence
        if section == "mental_health_impacts" and "mental_health_impacts" in food_data:
            impacts = food_data.mental_health_impacts
            if impacts:
                # Average confidence of all impacts
                confidences = [impact.confidence for impact in impacts if "confidence" in impact]
                if confidences:
                    return sum(confidences) / len(confidences)
        
        # Default to overall confidence
        return data_quality.overall_confidence
    
    def merge_food_data(self, food_entries: List[FoodData]) -> FoodData:
        """
        Merge multiple food entries into one, prioritizing data sources.
        
        This version works with the normalized database schema.
        
        Args:
            food_entries: List of FoodData objects to merge
            
        Returns:
            Merged FoodData object
        """
        if not food_entries:
            logger.warning("No food entries provided for merging")
            return FoodData()
        
        # First, validate that all entries represent the same food
        food_names = [entry.name for entry in food_entries]
        if len(set(food_names)) > 1:
            logger.warning(f"Entries may represent different foods: {food_names}")
        
        # Start with the entry that has the highest overall completeness
        entries_with_completeness = [
            (entry, entry.data_quality.completeness)
            for entry in food_entries
        ]
        entries_with_completeness.sort(key=lambda x: x[1], reverse=True)
        
        # Use the most complete entry as the base
        base_entry, _ = entries_with_completeness[0]
        merged = base_entry.copy()
        
        # Track sources used for each section
        source_priority = {}
        
        # Merge each section according to priority rules
        self._merge_standard_nutrients(merged, food_entries, source_priority)
        self._merge_brain_nutrients(merged, food_entries, source_priority)
        self._merge_bioactive_compounds(merged, food_entries, source_priority)
        self._merge_mental_health_impacts(merged, food_entries, source_priority)
        self._merge_contextual_factors(merged, food_entries)
        
        # Additional new schema sections
        self._merge_nutrient_interactions(merged, food_entries)
        self._merge_inflammatory_index(merged, food_entries)
        self._merge_population_variations(merged, food_entries)
        self._merge_neural_targets(merged, food_entries)
        
        # Update metadata
        merged.metadata = self._create_merged_metadata(merged, food_entries)
        
        # Update data quality section with source priority
        if not merged.data_quality:
            merged.data_quality = DataQuality()
        merged.data_quality.source_priority = source_priority
        
        # Calculate new completeness score
        merged.data_quality.completeness = calculate_completeness(merged)
        
        return merged
    
    def _merge_standard_nutrients(self, merged: FoodData, entries: List[FoodData], source_priority: Dict) -> None:
        """Merge standard nutrients section based on source priority."""
        priority_list = self.default_priorities["standard_nutrients"]
        
        # Initialize if missing
        if not merged.standard_nutrients:
            merged.standard_nutrients = StandardNutrients()
        
        # Track which source was used
        used_source = None
        
        # Try each source in priority order
        for source in priority_list:
            for entry in entries:
                entry_source = identify_source(entry)
                if entry_source != source:
                    continue
                
                if entry.standard_nutrients:
                    # Check if this source has better completeness for standard nutrients
                    if used_source is None or self._count_non_null_attrs(entry.standard_nutrients) > self._count_non_null_attrs(merged.standard_nutrients):
                        merged.standard_nutrients = entry.standard_nutrients.copy()
                        used_source = entry_source
        
        # If we used a source, record it
        if used_source:
            source_priority["standard_nutrients"] = used_source
    
    def _count_non_null_attrs(self, obj):
        """Count non-null attributes in an object."""
        if not obj:
            return 0
        return sum(1 for name in dir(obj) 
                  if not name.startswith('_') and 
                  not callable(getattr(obj, name)) and 
                  getattr(obj, name) is not None)
    
    def _merge_brain_nutrients(self, merged: FoodData, entries: List[FoodData], source_priority: Dict) -> None:
        """Merge brain nutrients with special handling for omega-3 data."""
        priority_list = self.default_priorities["brain_nutrients"]
        
        # Initialize if missing
        if not merged.brain_nutrients:
            merged.brain_nutrients = BrainNutrients()
        
        # Special handling for omega-3
        self._merge_omega3(merged, entries)
        
        # For each brain nutrient, take from highest priority source that has it
        brain_nutrients = BRAIN_NUTRIENTS_TO_PREDICT
        
        source_used = {}  # Track which source was used for each nutrient
        
        for nutrient in brain_nutrients:
            # Skip omega3 which is handled separately
            if nutrient.startswith("omega3"):
                continue
                
            for source in priority_list:
                for entry in entries:
                    entry_source = identify_source(entry)
                    if entry_source != source:
                        continue
                    
                    # Check confidence threshold
                    confidence = self.get_confidence(entry, "brain_nutrients")
                    if confidence < self.confidence_thresholds.get(entry_source, 0):
                        continue
                    
                    if (entry.brain_nutrients and
                        hasattr(entry.brain_nutrients, nutrient) and 
                        getattr(entry.brain_nutrients, nutrient) is not None):
                        
                        setattr(merged.brain_nutrients, nutrient, getattr(entry.brain_nutrients, nutrient))
                        source_used[nutrient] = entry_source
                        break  # Found highest priority source for this nutrient
        
        # Determine predominant source
        if source_used:
            source_counts = {}
            for source in source_used.values():
                source_counts[source] = source_counts.get(source, 0) + 1
            
            # Use source with most nutrients
            predominant_source = max(source_counts.items(), key=lambda x: x[1])[0]
            source_priority["brain_nutrients"] = predominant_source
    
    def _merge_omega3(self, merged: FoodData, entries: List[FoodData]) -> None:
        """Special handling for omega-3 data which needs component-level merging."""
        # Initialize if missing
        if not merged.brain_nutrients:
            merged.brain_nutrients = BrainNutrients()
        
        if not merged.brain_nutrients.omega3:
            merged.brain_nutrients.omega3 = Omega3()
        
        # Components to merge
        components = ["total_g", "epa_mg", "dha_mg", "ala_mg"]
        
        # Source priority for omega-3 specifically
        priority_list = ["literature", "usda", "openfoodfacts", "ai_generated"]
        
        for component in components:
            for source in priority_list:
                for entry in entries:
                    entry_source = identify_source(entry)
                    if entry_source != source:
                        continue
                    
                    # Check if entry has omega3 data for this component
                    if (entry.brain_nutrients and 
                        entry.brain_nutrients.omega3 and 
                        hasattr(entry.brain_nutrients.omega3, component) and
                        getattr(entry.brain_nutrients.omega3, component) is not None):
                        
                        # Check confidence
                        if hasattr(entry.brain_nutrients.omega3, "confidence"):
                            confidence = entry.brain_nutrients.omega3.confidence
                            if confidence < self.confidence_thresholds.get(entry_source, 0):
                                continue
                        
                        # Use this value
                        setattr(merged.brain_nutrients.omega3, component, 
                               getattr(entry.brain_nutrients.omega3, component))
                        break  # Found highest priority source
        
        # Calculate confidence based on completeness
        filled_components = sum(1 for c in components 
                               if hasattr(merged.brain_nutrients.omega3, c) and 
                               getattr(merged.brain_nutrients.omega3, c) is not None)
        
        if filled_components > 0:
            confidence = 5 + min(5, filled_components)  # 5-10 scale based on completeness
            merged.brain_nutrients.omega3.confidence = confidence
    
    def _merge_bioactive_compounds(self, merged: FoodData, entries: List[FoodData], source_priority: Dict) -> None:
        """Merge bioactive compounds based on source priority."""
        priority_list = self.default_priorities["bioactive_compounds"]
        
        # Initialize if missing
        if not merged.bioactive_compounds:
            merged.bioactive_compounds = BioactiveCompounds()
        
        # Track which source was used
        best_entry = None
        best_source = None
        best_count = 0
        
        # Find entry with most bioactive compounds from highest priority source
        for source in priority_list:
            for entry in entries:
                entry_source = identify_source(entry)
                if entry_source != source:
                    continue
                
                if entry.bioactive_compounds:
                    count = self._count_non_null_attrs(entry.bioactive_compounds)
                    if count > best_count:
                        best_entry = entry
                        best_source = entry_source
                        best_count = count
        
        # If we found a better entry, use its bioactive compounds
        if best_entry and best_entry.bioactive_compounds:
            merged.bioactive_compounds = best_entry.bioactive_compounds.copy()
            source_priority["bioactive_compounds"] = best_source
    
    def _merge_mental_health_impacts(self, merged: FoodData, entries: List[FoodData], source_priority: Dict) -> None:
        """Merge mental health impacts from different sources."""
        priority_list = self.default_priorities["mental_health_impacts"]
        
        # Initialize if missing
        if not merged.mental_health_impacts:
            merged.mental_health_impacts = []
        
        # Used impact types to avoid duplicates
        used_impact_types = {impact.impact_type for impact in merged.mental_health_impacts 
                           if hasattr(impact, "impact_type")}
        
        # Add impacts from all sources, prioritizing by confidence
        all_impacts = []
        source_used = None
        
        for source in priority_list:
            for entry in entries:
                entry_source = identify_source(entry)
                if entry_source != source:
                    continue
                
                if entry.mental_health_impacts:
                    # Add impacts with high enough confidence
                    for impact in entry.mental_health_impacts:
                        if not hasattr(impact, "impact_type") or impact.impact_type in used_impact_types:
                            continue
                        
                        confidence = impact.confidence if hasattr(impact, "confidence") else 0
                        if confidence >= self.confidence_thresholds.get(entry_source, 0):
                            all_impacts.append(impact)
                            used_impact_types.add(impact.impact_type)
                            source_used = entry_source
        
        # Add all collected impacts
        merged.mental_health_impacts.extend(all_impacts)
        
        # Record source
        if source_used:
            source_priority["mental_health_impacts"] = source_used
    
    def _merge_contextual_factors(self, merged: FoodData, entries: List[FoodData]) -> None:
        """Merge contextual factors, combining from all sources."""
        # Initialize if missing
        if not merged.contextual_factors:
            merged.contextual_factors = ContextualFactors()
        
        # Start with the structure of the first entry that has it
        for entry in entries:
            if entry.contextual_factors:
                # Use as template if we don't have any
                if not merged.contextual_factors.circadian_effects or not merged.contextual_factors.circadian_effects.factors:
                    merged.contextual_factors = entry.contextual_factors.copy()
                    break
        
        # Now combine unique factors from all entries
        for entry in entries:
            if not entry.contextual_factors:
                continue
            
            # Merge circadian factors
            if entry.contextual_factors.circadian_effects:
                # Add description if missing
                if (not merged.contextual_factors.circadian_effects or 
                    not merged.contextual_factors.circadian_effects.description) and \
                   entry.contextual_factors.circadian_effects.description:
                    if not merged.contextual_factors.circadian_effects:
                        merged.contextual_factors.circadian_effects = CircadianEffects()
                    merged.contextual_factors.circadian_effects.description = \
                        entry.contextual_factors.circadian_effects.description
                
                # Merge factors
                if entry.contextual_factors.circadian_effects.factors:
                    existing_factors = set()
                    if merged.contextual_factors.circadian_effects and merged.contextual_factors.circadian_effects.factors:
                        existing_factors = {factor.factor for factor in 
                                           merged.contextual_factors.circadian_effects.factors 
                                           if hasattr(factor, "factor")}
                    
                    # Add new unique factors
                    for factor in entry.contextual_factors.circadian_effects.factors:
                        if hasattr(factor, "factor") and factor.factor not in existing_factors:
                            if not merged.contextual_factors.circadian_effects:
                                merged.contextual_factors.circadian_effects = CircadianEffects()
                            if not merged.contextual_factors.circadian_effects.factors:
                                merged.contextual_factors.circadian_effects.factors = []
                            merged.contextual_factors.circadian_effects.factors.append(factor)
                            existing_factors.add(factor.factor)
            
            # Merge food combinations
            if entry.contextual_factors.food_combinations:
                existing_combinations = set()
                if merged.contextual_factors.food_combinations:
                    existing_combinations = {combo.combination for combo in 
                                           merged.contextual_factors.food_combinations 
                                           if hasattr(combo, "combination")}
                
                # Add new unique combinations
                for combo in entry.contextual_factors.food_combinations:
                    if hasattr(combo, "combination") and combo.combination not in existing_combinations:
                        if not merged.contextual_factors.food_combinations:
                            merged.contextual_factors.food_combinations = []
                        merged.contextual_factors.food_combinations.append(combo)
                        existing_combinations.add(combo.combination)
            
            # Merge preparation effects
            if entry.contextual_factors.preparation_effects:
                existing_methods = set()
                if merged.contextual_factors.preparation_effects:
                    existing_methods = {method.method for method in 
                                      merged.contextual_factors.preparation_effects 
                                      if hasattr(method, "method")}
                
                # Add new unique methods
                for method in entry.contextual_factors.preparation_effects:
                    if hasattr(method, "method") and method.method not in existing_methods:
                        if not merged.contextual_factors.preparation_effects:
                            merged.contextual_factors.preparation_effects = []
                        merged.contextual_factors.preparation_effects.append(method)
                        existing_methods.add(method.method)
    
    def _merge_nutrient_interactions(self, merged: FoodData, entries: List[FoodData]) -> None:
        """Merge nutrient interactions, combining from all sources with confidence filtering."""
        # Initialize if missing
        if not merged.nutrient_interactions:
            merged.nutrient_interactions = []
        
        # Track interaction IDs we've already added
        existing_ids = {interaction.interaction_id for interaction in merged.nutrient_interactions 
                       if hasattr(interaction, "interaction_id")}
        
        # Add interactions from all entries, filtering by confidence
        for entry in entries:
            if not entry.nutrient_interactions:
                continue
            
            for interaction in entry.nutrient_interactions:
                if not hasattr(interaction, "interaction_id"):
                    continue
                
                if interaction.interaction_id in existing_ids:
                    continue
                
                # Filter by confidence
                confidence = interaction.confidence if hasattr(interaction, "confidence") else 0
                entry_source = identify_source(entry)
                if confidence >= self.confidence_thresholds.get(entry_source, 0):
                    merged.nutrient_interactions.append(interaction)
                    existing_ids.add(interaction.interaction_id)
    
    def _merge_inflammatory_index(self, merged: FoodData, entries: List[FoodData]) -> None:
        """Merge inflammatory index data, selecting the highest confidence source."""
        priority_list = self.default_priorities.get("inflammatory_index", 
                                                 ["literature", "openfoodfacts", "ai_generated"])
        
        # Initialize if missing
        if not merged.inflammatory_index:
            # Try to find in any entry
            for source in priority_list:
                for entry in entries:
                    entry_source = identify_source(entry)
                    if entry_source != source:
                        continue
                    
                    if entry.inflammatory_index:
                        merged.inflammatory_index = entry.inflammatory_index.copy()
                        return
    
    def _merge_population_variations(self, merged: FoodData, entries: List[FoodData]) -> None:
        """Merge population variations, combining from all sources."""
        # Initialize if missing
        if not merged.population_variations:
            merged.population_variations = []
        
        # Track populations we've already added
        existing_populations = {variation.population for variation in merged.population_variations 
                              if hasattr(variation, "population")}
        
        # Add variations from all entries
        for entry in entries:
            if not entry.population_variations:
                continue
            
            for variation in entry.population_variations:
                if not hasattr(variation, "population"):
                    continue
                
                if variation.population in existing_populations:
                    continue
                
                merged.population_variations.append(variation)
                existing_populations.add(variation.population)
    
    def _merge_neural_targets(self, merged: FoodData, entries: List[FoodData]) -> None:
        """Merge neural targets, combining from all sources with confidence filtering."""
        # Initialize if missing
        if not merged.neural_targets:
            merged.neural_targets = []
        
        # Track neural pathways we've already added
        existing_pathways = {target.pathway for target in merged.neural_targets 
                            if hasattr(target, "pathway")}
        
        # Add targets from all entries, filtering by confidence
        for entry in entries:
            if not entry.neural_targets:
                continue
            
            for target in entry.neural_targets:
                if not hasattr(target, "pathway"):
                    continue
                
                if target.pathway in existing_pathways:
                    continue
                
                # Filter by confidence
                confidence = target.confidence if hasattr(target, "confidence") else 0
                entry_source = identify_source(entry)
                if confidence >= self.confidence_thresholds.get(entry_source, 0):
                    merged.neural_targets.append(target)
                    existing_pathways.add(target.pathway)
    
    def _create_merged_metadata(self, merged: FoodData, entries: List[FoodData]) -> Metadata:
        """Create merged metadata section."""
        # Start with metadata from our base entry
        if merged.metadata:
            metadata = merged.metadata.copy()
        else:
            metadata = Metadata(
                version='0.1.0',
                created=datetime.now().isoformat(),
                last_updated=datetime.now().isoformat(),
                source_urls=[],
                source_ids={},
                tags=[]
            )
        
        # Update last_updated
        metadata.last_updated = datetime.now().isoformat()
        
        # Collect source URLs from all entries
        all_urls = set(metadata.source_urls)
        
        # Collect source IDs from all entries
        source_ids = metadata.source_ids.copy()
        
        # Collect tags from all entries
        all_tags = set(metadata.tags)
        
        for entry in entries:
            if not entry.metadata:
                continue
            
            entry_metadata = entry.metadata
            
            # Add source URLs
            if entry_metadata.source_urls:
                all_urls.update(entry_metadata.source_urls)
            
            # Add source IDs
            if entry_metadata.source_ids:
                for key, value in entry_metadata.source_ids.items():
                    source_ids[key] = value
            
            # Add tags
            if entry_metadata.tags:
                all_tags.update(entry_metadata.tags)
            
            # Keep image URL if available
            if entry_metadata.image_url and not metadata.image_url:
                metadata.image_url = entry_metadata.image_url
        
        # Update metadata
        metadata.source_urls = list(all_urls)
        metadata.source_ids = source_ids
        metadata.tags = list(all_tags)
        
        return metadata
    
    def merge_foods_by_name(self, food_name: str) -> Optional[str]:
        try:
            foods = self.get_foods_by_name(food_name)
            
            if not foods:
                return None
            
            if len(foods) == 1:
                return foods[0]['food_id']
            
            merged_data = self.merge_food_data(foods)
            
            if not merged_data:
                return None
            
            if self.save_merged_food(merged_data):
                return merged_data['food_id']
            
            logger.warning(f"Failed to save merged data for '{food_name}'")
            return None
            
        except Exception as e:
            logger.error(f"Error merging foods for '{food_name}': {e}", exc_info=True)
            return None
    
    def merge_all_foods(self, batch_size: int = 100) -> List[str]:
        try:
            food_names_results = self.db_client.execute_query(FOOD_GET_DISTINCT_NAMES)
            
            if not food_names_results:
                logger.warning("No foods found in database")
                return []
            
            food_names = [result["name"] for result in food_names_results]
            logger.info(f"Found {len(food_names)} distinct food names to merge")
            
            merged_ids = []
            
            for i in range(0, len(food_names), batch_size):
                batch = food_names[i:i+batch_size]
                
                for food_name in batch:
                    merged_id = self.merge_foods_by_name(food_name)
                    if merged_id:
                        merged_ids.append(merged_id)
            
            logger.info(f"Successfully merged {len(merged_ids)} foods")
            return merged_ids
            
        except Exception as e:
            logger.error(f"Error merging all foods: {e}", exc_info=True)
            return []


def main():
    """Main function to execute merging."""
    parser = argparse.ArgumentParser(description="Merge food data from different sources")
    parser.add_argument("--food-name", help="Name of food to merge (if not specified, all foods will be merged)")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size for processing")
    
    args = parser.parse_args()
    
    try:
        # Initialize database client
        db_client = PostgresClient()
        
        # Initialize source prioritizer
        prioritizer = SourcePrioritizer(db_client)
        
        if args.food_name:
            # Merge specific food
            merged_id = prioritizer.merge_foods_by_name(args.food_name)
            if merged_id:
                logger.info(f"Successfully merged food '{args.food_name}' with ID {merged_id}")
            else:
                logger.error(f"Failed to merge food '{args.food_name}'")
                sys.exit(1)
        else:
            # Merge all foods
            merged_ids = prioritizer.merge_all_foods(batch_size=args.batch_size)
            logger.info(f"Successfully merged {len(merged_ids)} foods")
    
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()