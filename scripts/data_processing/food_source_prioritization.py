#!/usr/bin/env python3
"""
Source Prioritization Script
Compares and merges data from different sources (USDA, OpenFoodFacts) with intelligent prioritization.
"""

import os
import json
import glob
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SourcePrioritizer:
    """
    Prioritizes and merges data from multiple sources based on data quality.
    """
    
    def __init__(self):
        """Initialize the prioritizer."""
        # Default source priorities (can be overridden per field)
        self.default_priorities = {
            "standard_nutrients": ["usda", "openfoodfacts", "literature", "ai_generated"],
            "brain_nutrients": ["literature", "usda", "openfoodfacts", "ai_generated"],
            "bioactive_compounds": ["literature", "openfoodfacts", "usda", "ai_generated"],
            "mental_health_impacts": ["literature", "ai_generated"],
            "nutrient_interactions": ["literature", "ai_generated"],
            "inflammatory_index": ["literature", "openfoodfacts", "ai_generated"]
        }
        
        # Confidence thresholds for considering a source
        self.confidence_thresholds = {
            "usda": 0,  # Always trust USDA
            "openfoodfacts": 6,  # Decent confidence
            "literature": 0,  # Always trust literature
            "ai_generated": 7  # High confidence for AI
        }
    
    def identify_source(self, food_data: Dict) -> str:
        """
        Identify the source of food data.
        
        Args:
            food_data: Food data dictionary
            
        Returns:
            Source identifier string
        """
        food_id = food_data.get("food_id", "")
        metadata = food_data.get("metadata", {})
        
        if "source_ids" in metadata:
            source_ids = metadata["source_ids"]
            if "usda_fdc_id" in source_ids:
                return "usda"
            elif "openfoodfacts_id" in source_ids:
                return "openfoodfacts"
        
        if food_id.startswith("usda_"):
            return "usda"
        elif food_id.startswith("off_"):
            return "openfoodfacts"
        elif food_id.startswith("lit_"):
            return "literature"
        elif food_id.startswith("ai_"):
            return "ai_generated"
        
        # Check data quality attributes
        data_quality = food_data.get("data_quality", {})
        if data_quality.get("brain_nutrients_source") == "literature_derived":
            return "literature"
        elif data_quality.get("brain_nutrients_source") == "ai_generated":
            return "ai_generated"
        
        return "unknown"
    
    def get_confidence(self, food_data: Dict, section: str) -> float:
        """
        Get confidence rating for a specific section.
        
        Args:
            food_data: Food data dictionary
            section: Section name
            
        Returns:
            Confidence rating (0-10)
        """
        data_quality = food_data.get("data_quality", {})
        
        # Section-specific confidence ratings
        if section == "brain_nutrients" and "brain_nutrients_source" in data_quality:
            if data_quality["brain_nutrients_source"] == "usda_provided":
                return 9
            elif data_quality["brain_nutrients_source"] == "literature_derived":
                return 8
            elif data_quality["brain_nutrients_source"] == "openfoodfacts":
                return 7
            elif data_quality["brain_nutrients_source"] == "ai_generated":
                return data_quality.get("overall_confidence", 5)
        
        # Omega-3 specific confidence
        if section == "omega3" and "brain_nutrients" in food_data:
            brain_nutrients = food_data["brain_nutrients"]
            if "omega3" in brain_nutrients and "confidence" in brain_nutrients["omega3"]:
                return brain_nutrients["omega3"]["confidence"]
        
        # Mental health impacts confidence
        if section == "mental_health_impacts" and "mental_health_impacts" in food_data:
            impacts = food_data.get("mental_health_impacts", [])
            if impacts:
                # Average confidence of all impacts
                confidences = [impact.get("confidence", 0) for impact in impacts if "confidence" in impact]
                if confidences:
                    return sum(confidences) / len(confidences)
        
        # Default to overall confidence
        return data_quality.get("overall_confidence", 5)
    
    def merge_food_data(self, food_entries: List[Dict], output_file: Optional[str] = None) -> Dict:
        """
        Merge food data from multiple sources with intelligent prioritization.
        
        Args:
            food_entries: List of food data dictionaries from different sources
            output_file: Optional path to save merged data
            
        Returns:
            Merged food data dictionary
        """
        if not food_entries:
            logger.warning("No food entries provided for merging")
            return {}
        
        # First, validate that all entries represent the same food
        food_names = [entry.get("name", "") for entry in food_entries]
        if len(set(food_names)) > 1:
            logger.warning(f"Entries may represent different foods: {food_names}")
        
        # Start with the entry that has the highest overall completeness
        entries_with_completeness = [
            (entry, entry.get("data_quality", {}).get("completeness", 0))
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
        merged["metadata"] = self._create_merged_metadata(merged, food_entries)
        
        # Update data quality section
        merged["data_quality"]["source_priority"] = source_priority
        
        # Calculate new completeness score
        merged["data_quality"]["completeness"] = self._calculate_merged_completeness(merged)
        
        # Save to file if requested
        if output_file:
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            with open(output_file, 'w') as f:
                json.dump(merged, f, indent=2)
            logger.info(f"Saved merged data to {output_file}")
        
        return merged
    
    def _merge_standard_nutrients(self, merged: Dict, entries: List[Dict], source_priority: Dict) -> None:
        """Merge standard nutrients section based on source priority."""
        priority_list = self.default_priorities["standard_nutrients"]
        
        # Initialize if missing
        if "standard_nutrients" not in merged:
            merged["standard_nutrients"] = {}
        
        # Track which source was used
        used_source = None
        
        # Try each source in priority order
        for source in priority_list:
            for entry in entries:
                entry_source = self.identify_source(entry)
                if entry_source != source:
                    continue
                
                if "standard_nutrients" in entry and entry["standard_nutrients"]:
                    # Check if this source has better completeness for standard nutrients
                    if (used_source is None or 
                        len(entry["standard_nutrients"]) > len(merged["standard_nutrients"])):
                        
                        merged["standard_nutrients"] = entry["standard_nutrients"].copy()
                        used_source = entry_source
        
        # If we used a source, record it
        if used_source:
            source_priority["standard_nutrients"] = used_source
    
    def _merge_brain_nutrients(self, merged: Dict, entries: List[Dict], source_priority: Dict) -> None:
        """Merge brain nutrients with special handling for omega-3 data."""
        priority_list = self.default_priorities["brain_nutrients"]
        
        # Initialize if missing
        if "brain_nutrients" not in merged:
            merged["brain_nutrients"] = {}
        
        # Special handling for omega-3
        self._merge_omega3(merged, entries)
        
        # For each brain nutrient, take from highest priority source that has it
        brain_nutrients = [
            "tryptophan_mg", "tyrosine_mg", "vitamin_b6_mg", "folate_mcg",
            "vitamin_b12_mcg", "vitamin_d_mcg", "magnesium_mg", "zinc_mg",
            "iron_mg", "selenium_mcg", "choline_mg"
        ]
        
        source_used = {}  # Track which source was used for each nutrient
        
        for nutrient in brain_nutrients:
            for source in priority_list:
                for entry in entries:
                    entry_source = self.identify_source(entry)
                    if entry_source != source:
                        continue
                    
                    # Check confidence threshold
                    confidence = self.get_confidence(entry, "brain_nutrients")
                    if confidence < self.confidence_thresholds.get(entry_source, 0):
                        continue
                    
                    if ("brain_nutrients" in entry and 
                        nutrient in entry["brain_nutrients"] and 
                        entry["brain_nutrients"][nutrient] is not None):
                        
                        merged["brain_nutrients"][nutrient] = entry["brain_nutrients"][nutrient]
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
    
    def _merge_omega3(self, merged: Dict, entries: List[Dict]) -> None:
        """Special handling for omega-3 data which needs component-level merging."""
        # Initialize if missing
        if "brain_nutrients" not in merged:
            merged["brain_nutrients"] = {}
        
        if "omega3" not in merged["brain_nutrients"]:
            merged["brain_nutrients"]["omega3"] = {}
        
        # Components to merge
        components = ["total_g", "epa_mg", "dha_mg", "ala_mg"]
        
        # Source priority for omega-3 specifically
        priority_list = ["literature", "usda", "openfoodfacts", "ai_generated"]
        
        for component in components:
            for source in priority_list:
                for entry in entries:
                    entry_source = self.identify_source(entry)
                    if entry_source != source:
                        continue
                    
                    # Check if entry has omega3 data for this component
                    if ("brain_nutrients" in entry and 
                        "omega3" in entry["brain_nutrients"] and 
                        component in entry["brain_nutrients"]["omega3"] and
                        entry["brain_nutrients"]["omega3"][component] is not None):
                        
                        # Check confidence
                        if "confidence" in entry["brain_nutrients"]["omega3"]:
                            confidence = entry["brain_nutrients"]["omega3"]["confidence"]
                            if confidence < self.confidence_thresholds.get(entry_source, 0):
                                continue
                        
                        # Use this value
                        merged["brain_nutrients"]["omega3"][component] = entry["brain_nutrients"]["omega3"][component]
                        break  # Found highest priority source
        
        # Calculate confidence based on completeness
        filled_components = sum(1 for c in components 
                               if c in merged["brain_nutrients"]["omega3"] and 
                               merged["brain_nutrients"]["omega3"][c] is not None)
        
        if filled_components > 0:
            confidence = 5 + min(5, filled_components)  # 5-10 scale based on completeness
            merged["brain_nutrients"]["omega3"]["confidence"] = confidence
    
    def _merge_bioactive_compounds(self, merged: Dict, entries: List[Dict], source_priority: Dict) -> None:
        """Merge bioactive compounds based on source priority."""
        priority_list = self.default_priorities["bioactive_compounds"]
        
        # Initialize if missing
        if "bioactive_compounds" not in merged:
            merged["bioactive_compounds"] = {}
        
        # Track which source was used
        best_entry = None
        best_source = None
        best_count = 0
        
        # Find entry with most bioactive compounds from highest priority source
        for source in priority_list:
            for entry in entries:
                entry_source = self.identify_source(entry)
                if entry_source != source:
                    continue
                
                if "bioactive_compounds" in entry and entry["bioactive_compounds"]:
                    count = sum(1 for value in entry["bioactive_compounds"].values() if value is not None)
                    if count > best_count:
                        best_entry = entry
                        best_source = entry_source
                        best_count = count
        
        # If we found a better entry, use its bioactive compounds
        if best_entry and "bioactive_compounds" in best_entry:
            merged["bioactive_compounds"] = best_entry["bioactive_compounds"].copy()
            source_priority["bioactive_compounds"] = best_source
    
    def _merge_mental_health_impacts(self, merged: Dict, entries: List[Dict], source_priority: Dict) -> None:
        """Merge mental health impacts from different sources."""
        priority_list = self.default_priorities["mental_health_impacts"]
        
        # Initialize if missing
        if "mental_health_impacts" not in merged:
            merged["mental_health_impacts"] = []
        
        # Used impact types to avoid duplicates
        used_impact_types = {impact.get("impact_type") for impact in merged["mental_health_impacts"] 
                            if "impact_type" in impact}
        
        # Add impacts from all sources, prioritizing by confidence
        all_impacts = []
        source_used = None
        
        for source in priority_list:
            for entry in entries:
                entry_source = self.identify_source(entry)
                if entry_source != source:
                    continue
                
                if "mental_health_impacts" in entry and entry["mental_health_impacts"]:
                    # Add impacts with high enough confidence
                    for impact in entry["mental_health_impacts"]:
                        if "impact_type" not in impact or impact["impact_type"] in used_impact_types:
                            continue
                        
                        confidence = impact.get("confidence", 0)
                        if confidence >= self.confidence_thresholds.get(entry_source, 0):
                            all_impacts.append(impact)
                            used_impact_types.add(impact["impact_type"])
                            source_used = entry_source
        
        # Add all collected impacts
        merged["mental_health_impacts"].extend(all_impacts)
        
        # Record source
        if source_used:
            source_priority["mental_health_impacts"] = source_used
    
    def _merge_contextual_factors(self, merged: Dict, entries: List[Dict]) -> None:
        """Merge contextual factors, combining from all sources."""
        # Initialize if missing
        if "contextual_factors" not in merged:
            merged["contextual_factors"] = {
                "circadian_effects": {"factors": []},
                "food_combinations": [],
                "preparation_effects": []
            }
        
        # Start with the structure of the first entry that has it
        for entry in entries:
            if "contextual_factors" in entry and entry["contextual_factors"]:
                # Use as template if we don't have any
                if not merged["contextual_factors"].get("circadian_effects", {}).get("factors"):
                    merged["contextual_factors"] = entry["contextual_factors"].copy()
                    break
        
        # Now combine unique factors from all entries
        for entry in entries:
            if "contextual_factors" not in entry or not entry["contextual_factors"]:
                continue
            
            # Merge circadian factors
            if "circadian_effects" in entry["contextual_factors"]:
                # Add description if missing
                if "description" not in merged["contextual_factors"]["circadian_effects"] and \
                   "description" in entry["contextual_factors"]["circadian_effects"]:
                    merged["contextual_factors"]["circadian_effects"]["description"] = \
                        entry["contextual_factors"]["circadian_effects"]["description"]
                
                # Merge factors
                if "factors" in entry["contextual_factors"]["circadian_effects"]:
                    existing_factors = set()
                    if "factors" in merged["contextual_factors"]["circadian_effects"]:
                        existing_factors = {factor.get("factor") for factor in 
                                           merged["contextual_factors"]["circadian_effects"]["factors"] 
                                           if "factor" in factor}
                    
                    # Add new unique factors
                    for factor in entry["contextual_factors"]["circadian_effects"].get("factors", []):
                        if "factor" in factor and factor["factor"] not in existing_factors:
                            if "factors" not in merged["contextual_factors"]["circadian_effects"]:
                                merged["contextual_factors"]["circadian_effects"]["factors"] = []
                            merged["contextual_factors"]["circadian_effects"]["factors"].append(factor)
                            existing_factors.add(factor["factor"])
            
            # Merge food combinations
            if "food_combinations" in entry["contextual_factors"]:
                existing_combinations = set()
                if "food_combinations" in merged["contextual_factors"]:
                    existing_combinations = {combo.get("combination") for combo in 
                                           merged["contextual_factors"]["food_combinations"] 
                                           if "combination" in combo}
                
                # Add new unique combinations
                for combo in entry["contextual_factors"].get("food_combinations", []):
                    if "combination" in combo and combo["combination"] not in existing_combinations:
                        if "food_combinations" not in merged["contextual_factors"]:
                            merged["contextual_factors"]["food_combinations"] = []
                        merged["contextual_factors"]["food_combinations"].append(combo)
                        existing_combinations.add(combo["combination"])
            
            # Merge preparation effects
            if "preparation_effects" in entry["contextual_factors"]:
                existing_methods = set()
                if "preparation_effects" in merged["contextual_factors"]:
                    existing_methods = {method.get("method") for method in 
                                      merged["contextual_factors"]["preparation_effects"] 
                                      if "method" in method}
                
                # Add new unique methods
                for method in entry["contextual_factors"].get("preparation_effects", []):
                    if "method" in method and method["method"] not in existing_methods:
                        if "preparation_effects" not in merged["contextual_factors"]:
                            merged["contextual_factors"]["preparation_effects"] = []
                        merged["contextual_factors"]["preparation_effects"].append(method)
                        existing_methods.add(method["method"])
    
    def _merge_nutrient_interactions(self, merged: Dict, entries: List[Dict]) -> None:
        """Merge nutrient interactions, combining from all sources with confidence filtering."""
        # Initialize if missing
        if "nutrient_interactions" not in merged:
            merged["nutrient_interactions"] = []
        
        # Track interaction IDs we've already added
        existing_ids = {interaction.get("interaction_id") for interaction in merged["nutrient_interactions"] 
                       if "interaction_id" in interaction}
        
        # Add interactions from all entries, filtering by confidence
        for entry in entries:
            if "nutrient_interactions" not in entry or not entry["nutrient_interactions"]:
                continue
            
            for interaction in entry["nutrient_interactions"]:
                if "interaction_id" not in interaction:
                    continue
                
                if interaction["interaction_id"] in existing_ids:
                    continue
                
                # Filter by confidence
                confidence = interaction.get("confidence", 0)
                entry_source = self.identify_source(entry)
                if confidence >= self.confidence_thresholds.get(entry_source, 0):
                    merged["nutrient_interactions"].append(interaction)
                    existing_ids.add(interaction["interaction_id"])
    
    def _merge_inflammatory_index(self, merged: Dict, entries: List[Dict]) -> None:
        """Merge inflammatory index data, selecting the highest confidence source."""
        priority_list = self.default_priorities["inflammatory_index"]
        
        # Initialize if missing
        if "inflammatory_index" not in merged:
            # Try to find in any entry
            for source in priority_list:
                for entry in entries:
                    entry_source = self.identify_source(entry)
                    if entry_source != source:
                        continue
                    
                    if "inflammatory_index" in entry and entry["inflammatory_index"]:
                        merged["inflammatory_index"] = entry["inflammatory_index"].copy()
                        return
    
    def _merge_population_variations(self, merged: Dict, entries: List[Dict]) -> None:
        """Merge population variations, combining from all sources."""
        # Initialize if missing
        if "population_variations" not in merged:
            merged["population_variations"] = []
        
        # Track populations we've already added
        existing_populations = {variation.get("population") for variation in merged["population_variations"] 
                              if "population" in variation}
        
        # Add variations from all entries
        for entry in entries:
            if "population_variations" not in entry or not entry["population_variations"]:
                continue
            
            for variation in entry["population_variations"]:
                if "population" not in variation:
                    continue
                
                if variation["population"] in existing_populations:
                    continue
                
                merged["population_variations"].append(variation)
                existing_populations.add(variation["population"])
    
    def _merge_neural_targets(self, merged: Dict, entries: List[Dict]) -> None:
        """Merge neural targets, combining from all sources with confidence filtering."""
        # Initialize if missing
        if "neural_targets" not in merged:
            merged["neural_targets"] = []
        
        # Track neural pathways we've already added
        existing_pathways = {target.get("pathway") for target in merged["neural_targets"] 
                            if "pathway" in target}
        
        # Add targets from all entries, filtering by confidence
        for entry in entries:
            if "neural_targets" not in entry or not entry["neural_targets"]:
                continue
            
            for target in entry["neural_targets"]:
                if "pathway" not in target:
                    continue
                
                if target["pathway"] in existing_pathways:
                    continue
                
                # Filter by confidence
                confidence = target.get("confidence", 0)
                entry_source = self.identify_source(entry)
                if confidence >= self.confidence_thresholds.get(entry_source, 0):
                    merged["neural_targets"].append(target)
                    existing_pathways.add(target["pathway"])
    
    def _create_merged_metadata(self, merged: Dict, entries: List[Dict]) -> Dict:
        """Create merged metadata section."""
        # Start with metadata from our base entry
        if "metadata" in merged:
            metadata = merged["metadata"].copy()
        else:
            metadata = {
                "version": "0.1.0",
                "created": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "source_urls": [],
                "source_ids": {},
                "tags": []
            }
        
        # Update last_updated
        metadata["last_updated"] = datetime.now().isoformat()
        
        # Collect source URLs from all entries
        all_urls = set(metadata.get("source_urls", []))
        
        # Collect source IDs from all entries
        source_ids = metadata.get("source_ids", {})
        
        # Collect tags from all entries
        all_tags = set(metadata.get("tags", []))
        
        for entry in entries:
            if "metadata" not in entry:
                continue
            
            entry_metadata = entry["metadata"]
            
            # Add source URLs
            if "source_urls" in entry_metadata:
                all_urls.update(entry_metadata["source_urls"])
            
            # Add source IDs
            if "source_ids" in entry_metadata:
                for key, value in entry_metadata["source_ids"].items():
                    source_ids[key] = value
            
            # Add tags
            if "tags" in entry_metadata:
                all_tags.update(entry_metadata["tags"])
            
            # Keep image URL if available
            if "image_url" in entry_metadata and "image_url" not in metadata:
                metadata["image_url"] = entry_metadata["image_url"]
        
        # Update metadata
        metadata["source_urls"] = list(all_urls)
        metadata["source_ids"] = source_ids
        metadata["tags"] = list(all_tags)
        
        return metadata
    
    def _calculate_merged_completeness(self, merged: Dict) -> float:
        """Calculate completeness score for merged data."""
        # Count sections with data
        total_sections = 0
        filled_sections = 0
        
        # Standard nutrients
        standard_nutrients = merged.get("standard_nutrients", {})
        if standard_nutrients:
            total_sections += 1
            filled_sections += 1
            
            # Key nutrients we expect
            key_nutrients = [
                "calories", "protein_g", "carbohydrates_g", "fat_g", 
                "fiber_g", "sugars_g"
            ]
            total_sections += len(key_nutrients)
            filled_sections += sum(1 for n in key_nutrients 
                                  if n in standard_nutrients and standard_nutrients[n] is not None)
        
        # Brain nutrients
        brain_nutrients = merged.get("brain_nutrients", {})
        if brain_nutrients:
            total_sections += 1
            filled_sections += 1
            
            # Key brain nutrients
            key_brain_nutrients = [
                "tryptophan_mg", "vitamin_b6_mg", "folate_mcg", 
                "vitamin_b12_mcg", "vitamin_d_mcg", "magnesium_mg"
            ]
            total_sections += len(key_brain_nutrients)
            filled_sections += sum(1 for n in key_brain_nutrients 
                                 if n in brain_nutrients and brain_nutrients[n] is not None)
            
            # Omega-3
            if "omega3" in brain_nutrients:
                total_sections += 1
                filled_sections += 1
                
                # Key omega-3 components
                omega3_components = ["total_g", "epa_mg", "dha_mg", "ala_mg"]
                total_sections += len(omega3_components)
                filled_sections += sum(1 for c in omega3_components 
                                     if c in brain_nutrients["omega3"] and 
                                     brain_nutrients["omega3"][c] is not None)
        
        # Bioactive compounds
        bioactive_compounds = merged.get("bioactive_compounds", {})
        if bioactive_compounds:
            total_sections += 1
            filled_sections += min(1, len(bioactive_compounds))
        
        # Mental health impacts
        mental_health_impacts = merged.get("mental_health_impacts", [])
        if mental_health_impacts:
            total_sections += 1
            filled_sections += min(1, len(mental_health_impacts))
        
        # Nutrient interactions
        nutrient_interactions = merged.get("nutrient_interactions", [])
        if nutrient_interactions:
            total_sections += 1
            filled_sections += min(1, len(nutrient_interactions))
        
        # Inflammatory index
        if "inflammatory_index" in merged and merged["inflammatory_index"]:
            total_sections += 1
            filled_sections += 1
        
        # Calculate completeness
        if total_sections > 0:
            return round(filled_sections / total_sections, 2)
        return 0.0
    
    def merge_directory(self, 
                        usda_dir: str, 
                        openfoodfacts_dir: str,
                        literature_dir: Optional[str] = None,
                        ai_dir: Optional[str] = None,
                        output_dir: str = "data/enriched/merged") -> List[str]:
        """
        Merge food data from different source directories.
        
        Args:
            usda_dir: Directory with USDA food data
            openfoodfacts_dir: Directory with OpenFoodFacts data
            literature_dir: Optional directory with literature-derived data
            ai_dir: Optional directory with AI-generated data
            output_dir: Directory to save merged data
            
        Returns:
            List of paths to merged data files
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # Find matching foods across sources
        merged_files = []
        
        # Get USDA files
        usda_files = glob.glob(os.path.join(usda_dir, "*.json"))
        
        for usda_file in usda_files:
            try:
                with open(usda_file, 'r') as f:
                    usda_data = json.load(f)
                
                # Get USDA food name
                food_name = usda_data.get("name", "").lower()
                if not food_name:
                    continue
                
                # Find matching OpenFoodFacts entry
                off_match = self._find_matching_entry(food_name, openfoodfacts_dir)
                
                # Find matching literature entry
                lit_match = None
                if literature_dir:
                    lit_match = self._find_matching_entry(food_name, literature_dir)
                
                # Find matching AI entry
                ai_match = None
                if ai_dir:
                    ai_match = self._find_matching_entry(food_name, ai_dir)
                
                # Collect all entries
                entries = [usda_data]
                if off_match:
                    entries.append(off_match)
                if lit_match:
                    entries.append(lit_match)
                if ai_match:
                    entries.append(ai_match)
                
                # Skip if only one source
                if len(entries) <= 1:
                    continue
                
                # Create output filename
                basename = os.path.basename(usda_file)
                output_file = os.path.join(output_dir, basename)
                
                # Merge entries
                merged = self.merge_food_data(entries, output_file)
                if merged:
                    merged_files.append(output_file)
                    logger.info(f"Merged data for {food_name}")
            
            except Exception as e:
                logger.error(f"Error processing {usda_file}: {e}")
        
        return merged_files
    
    def _find_matching_entry(self, food_name: str, directory: str) -> Optional[Dict]:
        """Find matching entry in directory based on food name similarity."""
        if not os.path.isdir(directory):
            return None
        
        files = glob.glob(os.path.join(directory, "*.json"))
        
        best_match = None
        best_similarity = 0.5  # Threshold for considering a match
        
        for file in files:
            try:
                with open(file, 'r') as f:
                    data = json.load(f)
                
                entry_name = data.get("name", "").lower()
                
                # Calculate name similarity
                similarity = self._name_similarity(food_name, entry_name)
                
                if similarity > best_similarity:
                    best_match = data
                    best_similarity = similarity
            
            except Exception as e:
                logger.error(f"Error reading {file}: {e}")
        
        return best_match
    
    def _name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between food names."""
        # Simple case: exact match
        if name1 == name2:
            return 1.0
        
        # Simple Jaccard similarity on words
        words1 = set(name1.lower().split())
        words2 = set(name2.lower().split())
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        if union == 0:
            return 0.0
        
        return intersection / union

def main():
    """Main function to execute merging."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Merge food data from different sources")
    parser.add_argument("--usda-dir", default="data/processed/usda", help="Directory with USDA food data")
    parser.add_argument("--openfoodfacts-dir", default="data/raw/openfoodfacts", help="Directory with OpenFoodFacts data")
    parser.add_argument("--literature-dir", help="Directory with literature-derived data")
    parser.add_argument("--ai-dir", help="Directory with AI-generated data")
    parser.add_argument("--output-dir", default="data/enriched/merged", help="Directory to save merged data")
    
    args = parser.parse_args()
    
    prioritizer = SourcePrioritizer()
    
    try:
        merged_files = prioritizer.merge_directory(
            usda_dir=args.usda_dir,
            openfoodfacts_dir=args.openfoodfacts_dir,
            literature_dir=args.literature_dir,
            ai_dir=args.ai_dir,
            output_dir=args.output_dir
        )
        
        logger.info(f"Successfully merged {len(merged_files)} food entries")
        
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    main()