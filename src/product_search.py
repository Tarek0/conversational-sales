import json
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
import re

# OpenAI and numpy are required for semantic search
try:
    import numpy as np
    from openai import OpenAI
    from dotenv import load_dotenv
    load_dotenv()
except ImportError as e:
    raise ImportError(
        f"Required dependencies missing: {e}\n"
        "This conversational sales bot requires OpenAI integration for product search.\n"
        "Install with: poetry add openai numpy python-dotenv"
    )

# OpenAI API key is required
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError(
        "OPENAI_API_KEY environment variable is required!\n"
        "This conversational sales bot requires OpenAI API access for product search.\n"
        "Set your API key in the .env file: OPENAI_API_KEY=your_key_here"
    )


@dataclass
class Product:
    """Represents a product in the store."""
    name: str
    description: str
    url: str
    storage_options: List[str] = field(default_factory=list)
    brand: str = ""
    features: List[str] = field(default_factory=list)
    device_cost: Optional[float] = None

    def __post_init__(self):
        """Sets the brand based on the product name."""
        name_lower = self.name.lower()
        if "iphone" in name_lower or "apple" in name_lower:
            self.brand = "Apple"
        elif "samsung" in name_lower or "galaxy" in name_lower:
            self.brand = "Samsung"
        elif "google" in name_lower or "pixel" in name_lower:
            self.brand = "Google"
        elif "oneplus" in name_lower:
            self.brand = "OnePlus"
        else:
            self.brand = "Unknown"

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)
    
    def get_searchable_text(self) -> str:
        """Get text for search indexing"""
        return f"{self.name} {self.brand} {self.description} {' '.join(self.features)}"


class ProductSearchEngine:
    """Handles product search and management."""
    
    def __init__(self):
        self.products: List[Product] = []
        self.openai_client = OpenAI(api_key=OPENAI_API_KEY)
        self.product_embeddings = None
        self.product_texts = None
        
        # Load products on initialization
        self.load_products()
        
        # Initialize search capabilities
        self._initialize_search()
    
    def load_products(self) -> bool:
        """Load products from JSON file"""
        data_file = os.path.join("data", "products.json")
        
        if not os.path.exists(data_file):
            print(f"No product data found at {data_file}")
            return False
            
        try:
            with open(data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.products = [Product(**product) for product in data]
            
            print(f"Loaded {len(self.products)} products from {data_file}")
            
            # Re-initialize search if products were reloaded
            if self.products:
                self._initialize_search()
                
            return True
            
        except Exception as e:
            print(f"Error loading products: {e}")
            self.products = []
            return False
    
    def _initialize_search(self):
        """Initialize OpenAI-powered search capabilities"""
        if not self.products:
            return
            
        try:
            # Create embeddings for all products
            self.product_texts = [product.get_searchable_text() for product in self.products]
            
            # Check if we have cached embeddings
            embeddings_file = os.path.join("data", "product_embeddings.json")
            if os.path.exists(embeddings_file):
                try:
                    with open(embeddings_file, 'r') as f:
                        cached_data = json.load(f)
                        if len(cached_data) == len(self.products):
                            self.product_embeddings = np.array(cached_data)
                            print(f"Loaded cached embeddings for {len(self.products)} products")
                            return
                except Exception as e:
                    print(f"Error loading cached embeddings: {e}")
            
            # Generate new embeddings
            print("Generating OpenAI embeddings for products...")
            embeddings = []
            for text in self.product_texts:
                try:
                    response = self.openai_client.embeddings.create(
                        model="text-embedding-ada-002",
                        input=text
                    )
                    embeddings.append(response.data[0].embedding)
                except Exception as e:
                    raise RuntimeError(f"Failed to generate embeddings: {e}")
            
            self.product_embeddings = np.array(embeddings)
            
            # Cache embeddings
            os.makedirs("data", exist_ok=True)
            with open(embeddings_file, 'w') as f:
                json.dump(self.product_embeddings.tolist(), f)
            
            print(f"OpenAI semantic search initialized with {len(self.products)} products")
            
        except Exception as e:
            raise RuntimeError(
                f"Error initializing OpenAI search: {e}\n"
                "This conversational sales bot requires OpenAI for product search.\n"
                "Please check your API key and connection."
            )
    
    def search_simple(self, query: str, max_results: int = 5) -> List[Dict]:
        """Simple text-based search"""
        if not query or not self.products:
            return []
        
        query_lower = query.lower()
        results = []
        
        for product in self.products:
            score = 0
            
            # Search in different fields with different weights
            if query_lower in product.name.lower():
                score += 5
            if query_lower in product.brand.lower():
                score += 4
            if query_lower in product.description.lower():
                score += 2
            
            # Feature matching
            for feature in product.features:
                if query_lower in feature.lower():
                    score += 3
            
            # Exact brand match gets highest score
            if product.brand.lower() == query_lower:
                score += 10
            
            # Model name matching
            if any(word in product.name.lower() for word in query_lower.split()):
                score += 3
            
            if score > 0:
                result = product.to_dict()
                result['score'] = score
                results.append(result)
        
        # Sort by score and return top results
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:max_results]
    
    def search_advanced(self, query: str, max_results: int = 5) -> List[Dict]:
        """Advanced semantic search using OpenAI embeddings"""
        if not self.products or self.product_embeddings is None:
            return self.search_simple(query, max_results)
        
        try:
            # Generate embedding for query
            response = self.openai_client.embeddings.create(
                model="text-embedding-ada-002",
                input=query
            )
            query_embedding = np.array(response.data[0].embedding)
            
            # Calculate cosine similarity with all products
            similarities = []
            for i, product_embedding in enumerate(self.product_embeddings):
                # Cosine similarity
                similarity = np.dot(query_embedding, product_embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(product_embedding)
                )
                similarities.append((similarity, i))
            
            # Sort by similarity and get top results
            similarities.sort(key=lambda x: x[0], reverse=True)
            
            results = []
            for similarity, idx in similarities[:max_results]:
                if idx < len(self.products):
                    result = self.products[idx].to_dict()
                    result['score'] = float(similarity)
                    results.append(result)
            
            return results
            
        except Exception as e:
            print(f"Error in OpenAI search: {e}")
            return self.search_simple(query, max_results)
    
    def search(self, query: str, max_results: int = 5) -> List[Dict]:
        """Main search function - uses OpenAI search if available, otherwise simple"""
        return self.search_advanced(query, max_results)
    
    def search_by_preferences(self, preferences: Dict, max_results: int = 5) -> List[Dict]:
        """Search products based on user preferences"""
        if not self.products:
            return []
        
        results = []
        
        for product in self.products:
            score = 0
            
            # Brand preference
            if preferences.get('brand_preference'):
                if product.brand.lower() == preferences['brand_preference'].lower():
                    score += 10
            
            # Budget filtering
            try:
                # Extract numeric price from monthly cost
                price_match = re.search(r'£?(\d+)', product.monthly_cost)
                if price_match:
                    monthly_price = int(price_match.group(1))
                    
                    budget_min = preferences.get('budget_min', 0)
                    budget_max = preferences.get('budget_max', 1000)
                    
                    if budget_min <= monthly_price <= budget_max:
                        score += 5
                    elif monthly_price > budget_max:
                        score -= 5  # Penalize if over budget
            except:
                pass
            
            # Data usage preference
            data_usage = preferences.get('data_usage', '').lower()
            if data_usage == 'unlimited' and 'unlimited' in product.data_allowance.lower():
                score += 8
            elif data_usage == 'heavy' and any(word in product.data_allowance.lower() for word in ['100gb', 'unlimited', '150gb']):
                score += 6
            elif data_usage == 'light' and any(word in product.data_allowance.lower() for word in ['1gb', '2gb', '5gb']):
                score += 6
            
            # Feature preferences
            for feature in preferences.get('features', []):
                if feature.lower() in product.get_searchable_text().lower():
                    score += 4
            
            # Storage preference
            storage_pref = preferences.get('storage_preference', '').lower()
            if storage_pref and storage_pref in product.storage.lower():
                score += 3
            
            if score > 0:
                result = product.to_dict()
                result['score'] = score
                results.append(result)
        
        # Sort by score and return top results
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:max_results]
    
    def get_all_products(self) -> List[Dict]:
        """Get all products"""
        return [product.to_dict() for product in self.products]
    
    def get_product_by_name(self, name: str) -> Optional[Dict]:
        """Get a specific product by name"""
        for product in self.products:
            if product.name.lower() == name.lower():
                return product.to_dict()
        return None
    
    def get_brands(self) -> List[str]:
        """Get all unique brands"""
        brands = set(product.brand for product in self.products)
        return sorted(list(brands))
    
    def get_price_range(self) -> Dict[str, float]:
        """Get price range of all products"""
        prices = []
        for product in self.products:
            try:
                price_match = re.search(r'£?(\d+)', product.monthly_cost)
                if price_match:
                    prices.append(int(price_match.group(1)))
            except:
                continue
        
        if prices:
            return {
                "min": min(prices),
                "max": max(prices),
                "avg": sum(prices) / len(prices)
            }
        return {"min": 0, "max": 0, "avg": 0}
    
    def get_statistics(self) -> Dict:
        """Get search engine statistics"""
        return {
            "total_products": len(self.products),
            "brands": self.get_brands(),
            "price_range": self.get_price_range(),
            "advanced_search_available": True, # Semantic search is always available with OpenAI
            "search_capabilities": {
                "simple_text_search": True,
                "openai_semantic_search": True,
                "preference_based_search": True
            }
        }
    
    def refresh_index(self):
        """Refresh the search index (useful after adding new products)"""
        self._initialize_search()
        print("Search index refreshed")
    
    def add_product(self, product_data: Dict) -> bool:
        """Add a new product to the search engine"""
        try:
            product = Product(**product_data)
            self.products.append(product)
            
            # Refresh index if advanced search is enabled
            self._initialize_search()
            
            return True
        except Exception as e:
            print(f"Error adding product: {e}")
            return False
    
    def save_products(self, filename: Optional[str] = None) -> bool:
        """Save current products to JSON file"""
        if filename is None:
            filename = os.path.join("data", "products.json")
        
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            products_data = [product.to_dict() for product in self.products]
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(products_data, f, indent=2, ensure_ascii=False)
            
            print(f"Saved {len(self.products)} products to {filename}")
            return True
            
        except Exception as e:
            print(f"Error saving products: {e}")
            return False 