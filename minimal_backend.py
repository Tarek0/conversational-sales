#!/usr/bin/env python3
"""
TOBI Backend - Conversational Sales Bot with OpenAI Integration
"""

import json
import os
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import asyncio
import sys

# Check if we can import the required dependencies
try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    import uvicorn
    import openai
    from dotenv import load_dotenv
    load_dotenv()
except ImportError as e:
    print(f"❌ Required dependencies missing: {e}")
    print("This conversational sales bot requires OpenAI integration.")
    print("Install with: poetry add fastapi uvicorn openai python-dotenv")
    sys.exit(1)

# OpenAI API key is required
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("❌ OPENAI_API_KEY environment variable is required!")
    print("This conversational sales bot requires OpenAI API access.")
    print("Set your API key in the .env file: OPENAI_API_KEY=your_key_here")
    sys.exit(1)

@dataclass
class Product:
    name: str
    url: str
    price: str
    monthly_cost: str
    data_allowance: str
    contract_length: str
    brand: str
    storage: str
    description: str
    features: List[str]

class ProductSearch:
    def __init__(self):
        self.products: List[Product] = []
        self.openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
        self.load_products()
    
    def load_products(self):
        """Load products from JSON file"""
        data_file = "data/products.json"
        if os.path.exists(data_file):
            try:
                with open(data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.products = [Product(**product) for product in data]
                print(f"Loaded {len(self.products)} products from {data_file}")
            except Exception as e:
                print(f"Error loading products: {e}")
                self.products = []
        else:
            print(f"No product data found at {data_file}")
    
    def search(self, query: str) -> List[Dict]:
        """Simple text-based search"""
        if not query:
            return []
        
        query_lower = query.lower()
        results = []
        
        for product in self.products:
            score = 0
            text_fields = [
                product.name.lower(),
                product.brand.lower(),
                product.description.lower(),
                ' '.join(product.features).lower()
            ]
            
            for field in text_fields:
                if query_lower in field:
                    score += 1
            
            if product.brand.lower() == query_lower:
                score += 3
            
            if score > 0:
                results.append({
                    "name": product.name,
                    "url": product.url,
                    "price": product.price,
                    "monthly_cost": product.monthly_cost,
                    "data_allowance": product.data_allowance,
                    "contract_length": product.contract_length,
                    "brand": product.brand,
                    "storage": product.storage,
                    "description": product.description,
                    "features": product.features,
                    "score": score
                })
        
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:5]

class ConversationManager:
    def __init__(self):
        self.conversations = {}
        self.search_engine = ProductSearch()
    
    def process_message(self, message: str, session_id: str) -> Dict:
        """Process a message and return response"""
        
        # Initialize conversation if needed
        if session_id not in self.conversations:
            self.conversations[session_id] = {
                "messages": [],
                "preferences": {}
            }
        
        # Add user message
        self.conversations[session_id]["messages"].append({
            "role": "user",
            "content": message
        })
        
        # Simple response logic
        message_lower = message.lower()
        
        # Check for product searches
        recommendations = []
        if any(word in message_lower for word in ['iphone', 'apple', 'samsung', 'google', 'pixel', 'phone']):
            recommendations = self.search_engine.search(message)
        
        # Generate response
        if "hello" in message_lower or "hi" in message_lower:
            response = "Hello! I'm TOBI, your Vodafone sales assistant. I can help you find the perfect mobile phone. What are you looking for today?"
        elif "iphone" in message_lower:
            response = "Great choice! iPhones are very popular. I can show you our current iPhone deals. What's your budget range?"
            recommendations = self.search_engine.search("iPhone")
        elif "samsung" in message_lower:
            response = "Samsung phones are excellent! They offer great cameras and displays. Here are our current Samsung options:"
            recommendations = self.search_engine.search("Samsung")
        elif "unlimited" in message_lower or "data" in message_lower:
            response = "Looking for unlimited data? That's a great choice for heavy users. Let me show you our unlimited data plans:"
            recommendations = self.search_engine.search("unlimited")
        elif "budget" in message_lower or "cheap" in message_lower:
            response = "I can help you find great value options! What's your monthly budget?"
            recommendations = self.search_engine.search("OnePlus")
        elif "camera" in message_lower:
            response = "Looking for a great camera? I'd recommend checking out these options with excellent camera systems:"
            recommendations = self.search_engine.search("camera")
        else:
            response = "I can help you find the perfect phone! Could you tell me more about what you're looking for? For example, your budget range, preferred brand, or specific features?"
        
        # Add bot response
        self.conversations[session_id]["messages"].append({
            "role": "assistant", 
            "content": response
        })
        
        return {
            "message": response,
            "recommendations": recommendations
        }

# Create FastAPI app
app = FastAPI(title="TOBI API", version="1.0.0")

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize conversation manager
conversation_manager = ConversationManager()

class ChatRequest(BaseModel):
    message: str
    session_id: str

class ChatResponse(BaseModel):
    response: str
    session_id: str
    recommendations: list = []

@app.get("/")
async def root():
    return {
        "message": "TOBI API",
        "status": "running",
        "openai_available": True,
        "products_loaded": len(conversation_manager.search_engine.products)
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        response = conversation_manager.process_message(
            request.message, request.session_id
        )
        return ChatResponse(
            response=response["message"],
            session_id=request.session_id,
            recommendations=response.get("recommendations", [])
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def main():
    """Main function to run the backend"""
    print("🤖 TOBI Backend")
    print("=" * 40)
    
    # Initialize search engine
    search_engine = ProductSearch()
    print(f"📦 Products loaded: {len(search_engine.products)}")
    
    if len(search_engine.products) == 0:
        print("⚠️  No products found. Make sure data/products.json exists.")
    
    print("\n🚀 Starting server...")
    print("📍 Backend API: http://localhost:8000")
    print("📖 API Documentation: http://localhost:8000/docs")
    print("🛑 Press Ctrl+C to stop")
    
    try:
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 