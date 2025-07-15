from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import logging
from contextlib import asynccontextmanager

from .conversation import ConversationManager
from .models import ChatRequest, ChatResponse, HealthResponse
from .product_search import ProductSearchEngine
from .logging_config import setup_logging

# Load environment variables
load_dotenv()
# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# --- Global Variables ---
# This will be initialized during the lifespan startup event
conversation_manager: ConversationManager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles application startup and shutdown events."""
    global conversation_manager
    try:
        logger.info("TOBI Backend API starting up...")
        product_search_engine = ProductSearchEngine()
        conversation_manager = ConversationManager(product_search_engine=product_search_engine)
        logger.info("Product search engine and conversation manager initialized.")
        yield
    except Exception as e:
        logger.critical(f"A critical error occurred during startup: {e}", exc_info=True)
    finally:
        logger.info("TOBI Backend API shutting down...")

app = FastAPI(
    title="TOBI - Conversational Sales Bot API",
    description="API for the TOBI conversational sales assistant.",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for simplicity
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# --- API Endpoints ---
@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "TOBI Conversational Sales Bot API",
        "version": "1.0.0",
        "endpoints": {
            "chat": "/chat",
            "health": "/health",
            "products": "/products",
            "search": "/search/{query}",
            "session": "/session/{session_id}"
        },
        "openai_available": conversation_manager.openai_available,
        "products_loaded": len(conversation_manager.search_engine.products)
    }


@app.get("/health", response_model=HealthResponse)
def health_check():
    """Health check endpoint"""
    return HealthResponse(status="ok")


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint"""
    try:
        result = conversation_manager.process_message(
            request.message, 
            request.session_id
        )
        
        return ChatResponse(**result)
    except Exception as e:
        # Log the full error for debugging
        logger.error(f"Error during chat processing for session {request.session_id}: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"message": "An unexpected error occurred. Please try again later."}
        )


@app.get("/products")
async def get_products():
    """Get all loaded products"""
    return {
        "products": conversation_manager.search_engine.get_all_products(),
        "total": len(conversation_manager.search_engine.products)
    }


@app.get("/search/{query}")
async def search_products(query: str):
    """Search for products"""
    results = conversation_manager.search_engine.search(query)
    return {
        "query": query,
        "results": results,
        "total": len(results)
    }


@app.get("/session/{session_id}")
async def get_session_info(session_id: str):
    """Get information about a conversation session"""
    return conversation_manager.get_session_info(session_id)


@app.get("/stats")
async def get_stats():
    """Get API statistics"""
    return {
        "search_engine_stats": conversation_manager.search_engine.get_statistics(),
        "active_sessions": len(conversation_manager.sessions),
        "openai_available": conversation_manager.openai_available
    }


if __name__ == "__main__":
    import uvicorn
    print("🤖 TOBI Backend API")
    print("=" * 40)
    print(f"📱 OpenAI available: {conversation_manager.openai_available}")
    print(f"📦 Products loaded: {len(conversation_manager.search_engine.products)}")
    print("\n🚀 Starting server...")
    print("📍 Backend API: http://localhost:8000")
    print("📖 API Documentation: http://localhost:8000/docs")
    print("🛑 Press Ctrl+C to stop")
    
    uvicorn.run(app, host="0.0.0.0", port=8000) 