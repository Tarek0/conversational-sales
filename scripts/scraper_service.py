#!/usr/bin/env python3
"""
TOBI Product Scraper Service
Standalone service for scraping Vodafone UK products
This should be run separately from the main API, typically as a scheduled job
"""

import asyncio
import json
import os
import sys
import argparse
from datetime import datetime
from pathlib import Path

# Add the parent directory to path so we can import from src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.scraper import VodafoneDataScraper


class ScraperService:
    """Service for managing product scraping operations"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.scraper = VodafoneDataScraper()
        
    def log_operation(self, message: str, level: str = "INFO"):
        """Log scraping operations"""
        timestamp = datetime.now().isoformat()
        print(f"[{timestamp}] {level}: {message}")
        
        # Also log to file
        log_file = self.data_dir / "scraper.log"
        with open(log_file, "a") as f:
            f.write(f"[{timestamp}] {level}: {message}\n")
    
    async def scrape_and_update(self, force: bool = False, limit: int = 0, output_file: str = None) -> bool:
        """Scrape products and update data files"""
        self.log_operation("Starting product scraping service")
        
        try:
            # Check if we need to scrape (e.g., if data is old)
            products_file = self.data_dir / "products.json"
            should_scrape = force
            
            if not should_scrape and products_file.exists():
                # Check if data is older than 24 hours
                file_age = datetime.now().timestamp() - products_file.stat().st_mtime
                should_scrape = file_age > 86400  # 24 hours in seconds
                
            if not should_scrape:
                self.log_operation("Product data is fresh, skipping scrape")
                return True
            
            # Perform scraping
            self.log_operation(f"Scraping products from Vodafone UK (limit: {'None' if limit == 0 else limit})...")
            products = await self.scraper.scrape_products(limit=limit)
            
            if not products:
                self.log_operation("No products scraped", "ERROR")
                return False
            
            # Save to the specified (or default) products file
            success = self.scraper.save_products(products, filename=output_file)
            if success:
                self.log_operation(f"Successfully scraped and saved {len(products)} products to {output_file or self.scraper.data_file}")
                
                # Save metadata (still using the default metadata file)
                metadata = {
                    "last_scraped": datetime.now().isoformat(),
                    "product_count": len(products),
                    "scraping_method": "playwright" if self.scraper.playwright_available else "sample",
                }
                
                metadata_file = self.data_dir / "scraper_metadata.json"
                with open(metadata_file, "w") as f:
                    json.dump(metadata, f, indent=2)
                
                return True
            else:
                self.log_operation("Failed to save scraped products", "ERROR")
                return False
                
        except Exception as e:
            self.log_operation(f"Error during scraping: {e}", "ERROR")
            return False
    
    def get_scraping_status(self) -> dict:
        """Get current scraping status and metadata"""
        try:
            metadata_file = self.data_dir / "scraper_metadata.json"
            if metadata_file.exists():
                with open(metadata_file, "r") as f:
                    metadata = json.load(f)
            else:
                metadata = {}
            
            products_file = self.data_dir / "products.json"
            if products_file.exists():
                with open(products_file, "r") as f:
                    products = json.load(f)
                    product_count = len(products)
                    file_age = datetime.now().timestamp() - products_file.stat().st_mtime
                    
                metadata.update({
                    "current_product_count": product_count,
                    "data_age_hours": file_age / 3600,
                    "data_file_exists": True
                })
            else:
                metadata.update({
                    "current_product_count": 0,
                    "data_age_hours": float('inf'),
                    "data_file_exists": False
                })
            
            return metadata
            
        except Exception as e:
            return {"error": str(e)}
    
    def update_sample_data(self) -> bool:
        """Update data with sample products (for testing)"""
        self.log_operation("Updating with sample data")
        return self.scraper.update_sample_data()


async def main():
    """Main function for the scraper service"""
    parser = argparse.ArgumentParser(description="TOBI Product Scraper Service")
    parser.add_argument("--force", action="store_true", help="Force scraping even if data is fresh")
    parser.add_argument("--status", action="store_true", help="Show scraping status")
    parser.add_argument("--sample", action="store_true", help="Update with sample data")
    parser.add_argument("--limit", type=int, default=0, help="Limit the number of products to scrape (0 for no limit)")
    parser.add_argument("--data-dir", default="data", help="Data directory path")
    parser.add_argument("--output", default=None, help="Output file path for the scraped products")
    
    args = parser.parse_args()
    
    # Create service
    service = ScraperService(data_dir=args.data_dir)
    
    print("🕷️  TOBI Product Scraper Service")
    print("=" * 50)
    
    if args.status:
        # Show status
        status = service.get_scraping_status()
        print("📊 Scraping Status:")
        print(json.dumps(status, indent=2))
        return 0
        
    if args.sample:
        # Update with sample data
        success = service.update_sample_data()
        if success:
            print("✅ Sample data updated successfully")
            return 0
        else:
            print("❌ Failed to update sample data")
            return 1
    
    # Run scraping
    success = await service.scrape_and_update(force=args.force, limit=args.limit, output_file=args.output)
    
    if success:
        print("✅ Scraping completed successfully")
        
        # Show final status
        status = service.get_scraping_status()
        print(f"📦 Products: {status.get('current_product_count', 0)}")
        print(f"🕐 Last scraped: {status.get('last_scraped', 'Unknown')}")
        
        return 0
    else:
        print("❌ Scraping failed")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main())) 