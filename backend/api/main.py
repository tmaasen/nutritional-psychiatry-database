from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel
import os
import sys

# Add the core directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.scripts.orchestrator import DatabaseOrchestrator
from core.utils.db_utils import PostgresClient

app = FastAPI(
    title="Nutritional Psychiatry Database API",
    description="API for accessing the Nutritional Psychiatry Database",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Your React app's URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class FoodSearchResult(BaseModel):
    food_id: str
    name: str
    description: Optional[str]
    confidence_score: float

class FoodDetail(BaseModel):
    food_id: str
    name: str
    description: Optional[str]
    brain_nutrients: List[dict]
    mental_health_impacts: List[dict]
    sources: List[str]
    confidence_score: float

# Dependency for database connection
def get_db():
    db = PostgresClient()
    try:
        yield db
    finally:
        db.close()

@app.get("/api/v1/foods/search", response_model=List[FoodSearchResult])
async def search_foods(
    query: str,
    limit: int = 10,
    db: PostgresClient = Depends(get_db)
):
    """
    Search for foods in the database.
    """
    try:
        # Use your existing database query logic here
        results = db.execute_query(
            """
            SELECT food_id, name, description, confidence_score
            FROM foods
            WHERE name ILIKE %s
            ORDER BY confidence_score DESC
            LIMIT %s
            """,
            (f"%{query}%", limit)
        )
        
        return [
            FoodSearchResult(
                food_id=row["food_id"],
                name=row["name"],
                description=row.get("description"),
                confidence_score=row["confidence_score"]
            )
            for row in results
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/foods/{food_id}", response_model=FoodDetail)
async def get_food_details(
    food_id: str,
    db: PostgresClient = Depends(get_db)
):
    """
    Get detailed information about a specific food.
    """
    try:
        # Get basic food information
        food = db.execute_query(
            """
            SELECT food_id, name, description, food_data, confidence_score
            FROM foods
            WHERE food_id = %s
            """,
            (food_id,)
        )
        
        if not food:
            raise HTTPException(status_code=404, detail="Food not found")
            
        food = food[0]
        
        # Extract brain nutrients and mental health impacts from food_data
        food_data = food["food_data"]
        
        return FoodDetail(
            food_id=food["food_id"],
            name=food["name"],
            description=food.get("description"),
            brain_nutrients=food_data.get("brain_nutrients", []),
            mental_health_impacts=food_data.get("mental_health_impacts", []),
            sources=food_data.get("sources", []),
            confidence_score=food["confidence_score"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/methodology/overview")
async def get_methodology_overview():
    """
    Get an overview of the database methodology.
    """
    return {
        "title": "Nutritional Psychiatry Database Methodology",
        "description": "Our methodology combines traditional food databases with AI-powered enrichment to create a comprehensive database of brain-relevant nutrients and their mental health impacts.",
        "steps": [
            {
                "name": "Data Collection",
                "description": "Gathering data from USDA, OpenFoodFacts, and scientific literature"
            },
            {
                "name": "Data Transformation",
                "description": "Standardizing and structuring the collected data"
            },
            {
                "name": "AI Enrichment",
                "description": "Using AI to predict brain nutrients and mental health impacts"
            },
            {
                "name": "Validation",
                "description": "Validating predictions against known answers"
            },
            {
                "name": "Confidence Calibration",
                "description": "Calibrating confidence scores for predictions"
            }
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 