from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from pydantic import BaseModel

from services.model_service import init_services
from services.search_service import search_mood_boards, refine_category


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class MoodBoardsRequest(BaseModel):
    brandBrief: str
    indexName: Optional[str] = None
    topK: Optional[int] = 200
    category: Optional[str] = None  # Optional category filter
    diversitySample: Optional[int] = 10  # Sample from top-N for variety (0 = disabled)


class RefineCategoryRequest(BaseModel):
    brandBrief: str
    categoryType: str
    sliderValues: Dict[str, float]
    sliderLabels: Dict[str, Dict[str, str]] = {}
    sliderTuningMeta: Dict[str, Any] = {}
    lockedImageIds: List[str] = []
    currentImagePath: Optional[str] = None
    currentImageId: Optional[str] = None
    indexName: Optional[str] = None


app = FastAPI(title="Branding AI Backend")


@app.on_event("startup")
def startup_event():
    load_dotenv(PROJECT_ROOT / ".env.local")
    init_services()


@app.post("/mood-boards")
def mood_boards(request: MoodBoardsRequest):
    if not request.brandBrief:
        raise HTTPException(status_code=400, detail="brandBrief is required")
    return search_mood_boards(
        brand_brief=request.brandBrief,
        index_name=request.indexName,
        top_k=request.topK or 200,
        category=request.category,  # Pass category filter
        diversity_sample=request.diversitySample or 0,  # Apply diversity sampling
    )


@app.post("/refine-category")
def refine_category_endpoint(request: RefineCategoryRequest):
    if not request.brandBrief:
        raise HTTPException(status_code=400, detail="brandBrief is required")
    if not request.categoryType or not request.sliderValues:
        raise HTTPException(status_code=400, detail="categoryType and sliderValues are required")

    return refine_category(
        brand_brief=request.brandBrief,
        category_type=request.categoryType,
        slider_values=request.sliderValues,
        slider_labels=request.sliderLabels or {},
        slider_tuning_meta=request.sliderTuningMeta or {},
        locked_image_ids=request.lockedImageIds or [],
        current_image_path=request.currentImagePath,
        current_image_id=request.currentImageId,
        project_root=PROJECT_ROOT,
        index_name=request.indexName,
    )
