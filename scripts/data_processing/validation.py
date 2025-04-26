#!/usr/bin/env python3
"""
Data Validation Script
Validates food data against the schema and checks for data quality issues.
"""

import os
import json
import glob
import logging
import argparse
import jsonschema
from typing import Dict, List, Any, Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataValidator:
    """Validates nutritional psychiatry food data."""
    
    def __init__(self, schema_path: str):
        """
        Initialize the validator with a schema.
        
        Args:
            schema_path: Path to the JSON schema file
        """
        try:
            with open(schema_path, 'r') as f:
                self.schema = json.load(f)
                logger.info(f"Loaded schema from {schema_path}")
        except Exception as e:
            logger.error(f"Error loading schema: {e}")
            raise
    
    def validate_schema(self, food_data: Dict) -> Tuple[bool, Optional[Exception]]:
        """
        Validate food data against the JSON schema.
        
        Args:
            food_data: Food data dictionary
            
        Returns:
            Tuple of (is_valid, error)
        """
        try:
            jsonschema.validate(instance=food_data, schema=self.schema)
            return True, None
        except jsonschema.exceptions.ValidationError as e:
            return False, e
    
    def check_data_quality(self, food_data: Dict) -> List[str]:
        """
        Check for data quality issues beyond schema validation.
        
        Args:
            food_data: Food data dictionary
            
        Returns:
            List of warning messages
        """
        warnings = []
        
        # Check for missing brain nutrients
        if 'brain_nutrients' in food_data:
            brain_nutrients = food_data['brain_nutrients']
            
            # Core brain nutrients we expect to see
            core_nutrients = [
                'tryptophan_mg', 'vitamin_b6_mg', 'folate_mcg', 
                'vitamin_b12_mcg', 'vitamin_d_mcg', 'magnesium_mg', 
                'zinc_mg', 'iron_mg'
            ]
            
            missing = [n for n in core_nutrients if n not in brain_nutrients or brain_nutrients.get(n) is None]
            if missing:
                warnings.append(f"Missing core brain nutrients: {', '.join(missing)}")
            
            # Check omega-3 completeness
            if 'omega3' in brain_nutrients:
                omega3 = brain_nutrients['omega3']
                if 'total_g' not in omega3 or omega3['total_g'] is None:
                    warnings.append("Missing total omega-3 value")
                
                # Check for implausible omega-3 values
                if 'total_g' in omega3 and omega3['total_g'] is not None:
                    total_g = omega3['total_g']
                    
                    # Check if individual components exceed total
                    components_sum = 0
                    for component in ['epa_mg', 'dha_mg', 'ala_mg']:
                        if component in omega3 and omega3[component] is not None:
                            components_sum += omega3[component]
                    
                    if components_sum > 0:
                        components_g = components_sum / 1000  # Convert mg to g
                        if components_g > total_g * 1.1:  # Allow 10% margin for rounding
                            warnings.append(f"Omega-3 components ({components_g:.2f}g) exceed total ({total_g:.2f}g)")
        else:
            warnings.append("Missing brain_nutrients section")
        
        # Check bioactive compounds section
        if 'bioactive_compounds' not in food_data or not food_data['bioactive_compounds']:
            warnings.append("Missing bioactive_compounds section")
        
        # Check mental health impacts
        if 'mental_health_impacts' not in food_data or not food_data['mental_health_impacts']:
            warnings.append("Missing mental_health_impacts section")
        else:
            impacts = food_data['mental_health_impacts']
            
            for i, impact in enumerate(impacts):
                # Check for impacts without research support
                if 'research_support' not in impact or not impact['research_support']:
                    warnings.append(f"Impact #{i+1} ({impact.get('impact_type', 'unknown')}) has no research support")
                
                # Check for high strength with low confidence
                if 'strength' in impact and 'confidence' in impact:
                    strength = impact['strength']
                    confidence = impact['confidence']
                    
                    if strength > 7 and confidence < 5:
                        warnings.append(f"Impact #{i+1} has high strength ({strength}) but low confidence ({confidence})")
        
        # Check data quality metadata
        if 'data_quality' not in food_data:
            warnings.append("Missing data_quality section")
        else:
            quality = food_data['data_quality']
            
            # Check for missing source information
            if 'brain_nutrients_source' not in quality:
                warnings.append("Missing brain_nutrients_source in data_quality")
            
            if 'impacts_source' not in quality:
                warnings.append("Missing impacts_source in data_quality")
            
            # Check completeness calculation
            if 'completeness' in quality:
                completeness = quality['completeness']
                
                # Verify completeness is reasonable
                if completeness == 1.0:
                    # Perfect completeness is suspicious, verify
                    for section in ['standard_nutrients', 'brain_nutrients', 'bioactive_compounds']:
                        if section in food_data and isinstance(food_data[section], dict):
                            has_nulls = any(v is None for v in food_data[section].values())
                            if has_nulls:
                                warnings.append(f"Completeness is 1.0 but {section} has null values")
        
        # Check for inconsistencies in values
        if 'standard_nutrients' in food_data and 'protein_g' in food_data['standard_nutrients']:
            protein = food_data['standard_nutrients']['protein_g']
            
            # Check tryptophan proportion (typically ~1-1.5% of protein)
            if 'brain_nutrients' in food_data and 'tryptophan_mg' in food_data['brain_nutrients']:
                tryptophan = food_data['brain_nutrients']['tryptophan_mg']
                
                if protein is not None and tryptophan is not None and protein > 0:
                    tryptophan_percent = (tryptophan / protein) / 10  # Convert mg/g to percentage
                    
                    if tryptophan_percent < 0.5 or tryptophan_percent > 2.0:
                        warnings.append(f"Unusual tryptophan proportion ({tryptophan_percent:.2f}% of protein)")
        
        return warnings
    
    def validate_file(self, file_path: str, output_warnings: bool = True) -> Tuple[bool, List[str]]:
        """
        Validate a food data file.
        
        Args:
            file_path: Path to the food data JSON file
            output_warnings: Whether to print warnings to the console
            
        Returns:
            Tuple of (is_valid, warnings)
        """
        try:
            with open(file_path, 'r') as f:
                food_data = json.load(f)
            
            # Schema validation
            is_valid, error = self.validate_schema(food_data)
            
            if not is_valid:
                logger.error(f"Schema validation failed for {file_path}: {error}")
                return False, [str(error)]
            
            # Data quality checks
            warnings = self.check_data_quality(food_data)
            
            if warnings and output_warnings:
                logger.warning(f"Quality issues in {file_path}:")
                for warning in warnings:
                    logger.warning(f"  - {warning}")
            
            return is_valid, warnings
            
        except Exception as e:
            logger.error(f"Error validating {file_path}: {e}")
            return False, [str(e)]
    
    def validate_directory(self, input_dir: str, report_path: Optional[str] = None) -> Dict:
        """
        Validate all food data files in a directory.
        
        Args:
            input_dir: Directory with food data files
            report_path: Optional path to save validation report
            
        Returns:
            Dictionary with validation results
        """
        results = {
            "total_files": 0,
            "valid_files": 0,
            "invalid_files": 0,
            "files_with_warnings": 0,
            "details": []
        }
        
        input_files = glob.glob(os.path.join(input_dir, "*.json"))
        results["total_files"] = len(input_files)
        
        for input_file in input_files:
            file_name = os.path.basename(input_file)
            is_valid, warnings = self.validate_file(input_file, output_warnings=False)
            
            file_result = {
                "file_name": file_name,
                "is_valid": is_valid,
                "warnings": warnings,
                "warning_count": len(warnings)
            }
            
            results["details"].append(file_result)
            
            if is_valid:
                results["valid_files"] += 1
            else:
                results["invalid_files"] += 1
            
            if warnings:
                results["files_with_warnings"] += 1
        
        # Sort by warning count (descending)
        results["details"].sort(key=lambda x: x["warning_count"], reverse=True)
        
        # Calculate statistics
        if results["total_files"] > 0:
            results["percent_valid"] = (results["valid_files"] / results["total_files"]) * 100
            results["percent_with_warnings"] = (results["files_with_warnings"] / results["total_files"]) * 100
        
        # Output report
        logger.info(f"Validation summary: {results['valid_files']}/{results['total_files']} files valid")
        logger.info(f"Files with warnings: {results['files_with_warnings']}/{results['total_files']}")
        
        if report_path:
            os.makedirs(os.path.dirname(report_path), exist_ok=True)
            with open(report_path, 'w') as f:
                json.dump(results, f, indent=2)
            logger.info(f"Validation report saved to {report_path}")
        
        return results


def main():
    """Main function to execute validation."""
    parser = argparse.ArgumentParser(description="Validate Nutritional Psychiatry Dataset files")
    parser.add_argument("--input-dir", required=True, help="Directory with food data files")
    parser.add_argument("--schema", default="schema/food_schema.json", help="Path to JSON schema")
    parser.add_argument("--report", help="Path to save validation report")
    parser.add_argument("--file", help="Validate a specific file only")
    
    args = parser.parse_args()
    
    try:
        validator = DataValidator(args.schema)
        
        if args.file:
            is_valid, warnings = validator.validate_file(args.file)
            if is_valid:
                logger.info(f"File {args.file} is valid")
                if warnings:
                    logger.info(f"File has {len(warnings)} quality warnings")
            else:
                logger.error(f"File {args.file} is invalid")
        else:
            validator.validate_directory(args.input_dir, args.report)
            
    except Exception as e:
        logger.error(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
