#!/usr/bin/env python3
from datetime import datetime
import re
from typing import Dict, List, Optional

from schema.food_data import (
    CircadianEffects, ContextualFactors, FoodData, StandardNutrients, BrainNutrients, Omega3, BioactiveCompounds,
    DataQuality, Metadata
)

from utils.data_utils import identify_source, normalize_food_name
from utils.logging_utils import setup_logging
from utils.db_utils import PostgresClient
from utils.data_utils import calculate_completeness

from constants.sql_queries import *
from constants.food_data_constants import BRAIN_NUTRIENTS_TO_PREDICT
from constants.literature_constants import SOURCE_PRIORITY_MAPPING, SOURCE_CONFIDENCE_THRESHOLDS

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
        
        base_entry, _ = entries_with_completeness[0]
        merged = base_entry.copy()
        
        source_priority = {}
        
        self._merge_standard_nutrients(merged, food_entries, source_priority)
        self._merge_brain_nutrients(merged, food_entries, source_priority)
        self._merge_bioactive_compounds(merged, food_entries, source_priority)
        self._merge_mental_health_impacts(merged, food_entries, source_priority)
        self._merge_contextual_factors(merged, food_entries)
        
        self._merge_nutrient_interactions(merged, food_entries)
        self._merge_inflammatory_index(merged, food_entries)
        self._merge_population_variations(merged, food_entries)
        self._merge_neural_targets(merged, food_entries)
        
        merged.metadata = self._create_merged_metadata(merged, food_entries)
        
        if not merged.data_quality:
            merged.data_quality = DataQuality()
        merged.data_quality.source_priority = source_priority
        
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
            # Get all matching entries for this source
            matching_entries = [entry for entry in entries 
                            if identify_source(entry) == source and entry.standard_nutrients]
            
            if matching_entries:
                # Find the most complete entry from this source
                best_entry = max(matching_entries, 
                            key=lambda e: self._count_non_null_attrs(e.standard_nutrients))
                
                if used_source is None or self._count_non_null_attrs(best_entry.standard_nutrients) > self._count_non_null_attrs(merged.standard_nutrients):
                    merged.standard_nutrients = best_entry.standard_nutrients.copy()
                    used_source = source
        
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

    def has_conflicting_nutrients(food1: FoodData, food2: FoodData, tolerance: float = 0.5) -> bool:
        """
        Check if two foods have conflicting nutrient values.
        
        Args:
            food1: First food
            food2: Second food
            tolerance: Tolerance for difference as a percentage (0.0-1.0)
            
        Returns:
            True if foods have conflicting nutrients, False otherwise
        """
        if not hasattr(food1, 'standard_nutrients') or not hasattr(food2, 'standard_nutrients'):
            return False
            
        key_nutrients = ["calories", "protein_g", "carbohydrates_g", "fat_g"]
        
        for nutrient in key_nutrients:
            if (not hasattr(food1.standard_nutrients, nutrient) or 
                not hasattr(food2.standard_nutrients, nutrient) or
                getattr(food1.standard_nutrients, nutrient) is None or
                getattr(food2.standard_nutrients, nutrient) is None):
                continue
            
            value1 = getattr(food1.standard_nutrients, nutrient)
            value2 = getattr(food2.standard_nutrients, nutrient)
            
            # Skip if either is zero (avoid division by zero)
            if value1 == 0 or value2 == 0:
                continue
            
            # Calculate difference as percentage
            diff = abs(value1 - value2) / max(value1, value2)
            
            if diff > tolerance:
                # Nutrient values differ too much
                logger.debug(f"Conflicting nutrient {nutrient}: {value1} vs {value2} (diff: {diff:.2f})")
                return True
        
        return False

    def should_merge_foods(self, food1: FoodData, food2: FoodData) -> bool:
        name1 = normalize_food_name(food1.name)
        name2 = normalize_food_name(food2.name)
        
        if name1 == name2:
            return True
        
        if name1 in name2 or name2 in name1:
            return not self.has_conflicting_nutrients(food1, food2)
        
        return False
    
    def merge_foods_by_name(self, food_name: str) -> Dict[str, str]:
        try:
            foods = self.db_client.get_foods_by_name(food_name)
            
            if not foods:
                logger.info(f"No foods found for '{food_name}'")
                return {}
                
            if len(foods) == 1:
                logger.info(f"Only one food found for '{food_name}', no merging needed")
                return {normalize_food_name(foods[0].name): foods[0].food_id}
            
            groups = {}
            
            for food in foods:
                found_group = False
                for group_key, group_foods in groups.items():
                    if self.should_merge_foods(food, group_foods[0]):
                        group_foods.append(food)
                        found_group = True
                        break
                
                if not found_group:
                    group_key = normalize_food_name(food.name)
                    groups[group_key] = [food]
            
            for group_key, group_foods in groups.items():
                logger.info(f"Food group '{group_key}' has {len(group_foods)} foods: {[f.name for f in group_foods]}")
            
            merged_food_ids = {}
            
            for group_key, group_foods in groups.items():
                if len(group_foods) >= 2:
                    logger.info(f"Merging group '{group_key}' with {len(group_foods)} foods")
                    merged_data = self.merge_food_data(group_foods)
                    
                    if merged_data:
                        group_id = re.sub(r'[^\w]', '_', group_key).lower()
                        merged_data.food_id = f"merged_{group_id}"
                        
                        merged_id = self.db_client.import_food_from_json(merged_data)
                        merged_food_ids[group_key] = merged_id
                        logger.info(f"Successfully merged group '{group_key}' as {merged_id}")
                else:
                    merged_food_ids[group_key] = group_foods[0].food_id
                    logger.info(f"Group '{group_key}' has only 1 food, using existing {group_foods[0].food_id}")
            
            return merged_food_ids
            
        except Exception as e:
            logger.error(f"Error merging foods for '{food_name}': {e}", exc_info=True)
            return {}
    
    def merge_all_foods(self, batch_size: int = 100) -> Dict[str, List[str]]:
        try:
            food_names_results = self.db_client.execute_query(FOOD_GET_DISTINCT_NAMES)
            
            if not food_names_results:
                logger.warning("No foods found in database")
                return {}
            
            food_names = [result["name"] for result in food_names_results]
            logger.info(f"Found {len(food_names)} distinct food names to merge")
            
            all_merged_foods = {}
            
            for i in range(0, len(food_names), batch_size):
                batch = food_names[i:i+batch_size]
                
                for food_name in batch:
                    merged_groups = self.merge_foods_by_name(food_name)
                    if merged_groups:
                        all_merged_foods[food_name] = merged_groups
            
            total_merged = sum(len(groups) for groups in all_merged_foods.values())
            logger.info(f"Successfully merged foods into {total_merged} groups")
            
            return all_merged_foods
            
        except Exception as e:
            logger.error(f"Error merging all foods: {e}", exc_info=True)
            return {}