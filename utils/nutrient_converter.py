class NutrientConverter:
    """Utility class for nutrient conversion operations."""
    
    @staticmethod
    def g_to_mg(value: float) -> float:
        """Convert grams to milligrams."""
        return value * 1000
    
    @staticmethod
    def g_to_mcg(value: float) -> float:
        """Convert grams to micrograms."""
        return value * 1000000