from pydantic import BaseModel
from typing import List, Optional

class ChatRequest(BaseModel):
    """Request model for the /chat endpoint."""
    message: str
    session_id: str

class Recommendation(BaseModel):
    """Data model for a product recommendation."""
    name: str
    description: str
    url: str
    storage_options: List[str]
    brand: str

class ChatResponse(BaseModel):
    """Response model for the /chat endpoint."""
    response: str
    recommendations: Optional[List[Recommendation]] = None

class HealthResponse(BaseModel):
    """Response model for the /health endpoint."""
    status: str 