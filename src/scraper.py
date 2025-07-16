import asyncio
import json
import os
import re
from typing import List, Dict, Optional, TYPE_CHECKING
from urllib.parse import urljoin, urlparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Try to import Playwright for advanced scraping
try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

# Import Page only for type checking to avoid runtime errors
if TYPE_CHECKING:
    from playwright.async_api import Page


class VodafoneDataScraper:
    """Vodafone data scraper"""
    
    def __init__(self):
        self.base_url = "https://www.vodafone.co.uk/mobile/phones/pay-monthly-contracts/apple"
        self.data_dir = "data"
        self.data_file = os.path.join(self.data_dir, "products.json")
        
        os.makedirs(self.data_dir, exist_ok=True)
        
        self.playwright_available = PLAYWRIGHT_AVAILABLE
        
        logging.info(f"Scraper initialized:")
        logging.info(f"  - Playwright available: {self.playwright_available}")
    
    def get_sample_products(self) -> List[Dict]:
        """Get sample products for testing/demo purposes"""
        return [
            {
                "name": "Apple iPhone 15 Pro",
                "description": "The latest iPhone with A17 Pro chip, Pro camera system, and USB-C.",
            },
            {
                "name": "Samsung Galaxy S24 Ultra",
                "description": "Experience the new era of mobile AI with Galaxy S24 Ultra.",
            },
        ]

    async def scrape_products(self, limit: int = 0) -> List[Dict]:
        """
        Scrape products from Vodafone UK using the best available method.
        """
        if self.playwright_available:
            return await self.scrape_products_playwright(limit=limit)
        else:
            logging.warning("Playwright not available, returning sample products")
            return self.get_sample_products()

    async def scrape_products_playwright(self, limit: int = 0) -> List[Dict]:
        """Scrape products using Playwright"""
        if not self.playwright_available:
            raise ImportError("Playwright not available")
        
        products: List[Dict] = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            try:
                logging.info(f"Starting Vodafone UK product scraping from {self.base_url}")
                await page.goto(self.base_url, wait_until="networkidle")
                await page.wait_for_timeout(3000)
                
                await self._handle_cookie_consent(page)
                
                product_links = await self._get_product_links(page)
                logging.info(f"Found {len(product_links)} product links")
                
                links_to_scrape = product_links[:limit] if limit > 0 and limit < len(product_links) else product_links
                
                for i, link in enumerate(links_to_scrape):
                    product_page = await browser.new_page()
                    try:
                        logging.info(f"Scraping product {i+1}/{len(links_to_scrape)}: {link}")
                        product_data = await self._scrape_product_page(product_page, link)
                        if product_data:
                            products.append(product_data)
                    except Exception as e:
                        logging.error(f"Error scraping page for product {link}: {e}")
                    finally:
                        await product_page.close()
                
            except Exception as e:
                logging.error(f"Error during Playwright scraping: {e}")
                
            finally:
                await browser.close()
        
        return products

    async def _handle_cookie_consent(self, page: "Page"):
        """Handle cookie consent popup"""
        try:
            # Using get_by_role to find the button by its accessible name is more robust
            accept_button = page.get_by_role("button", name="Accept all cookies")
            logging.info("Found cookie consent button. Clicking 'Accept all cookies'.")
            await accept_button.click(timeout=5000)
            await page.wait_for_timeout(1000) # Wait for animations
            
            # Forcefully remove the cookie banner to prevent it from interfering with clicks
            await page.evaluate("document.getElementById('onetrust-consent-sdk')?.remove()")
            logging.info("Successfully clicked 'Accept all cookies' and removed the banner.")
        except Exception as e:
            logging.warning(f"Could not click the 'Accept all cookies' button. It might not be present or visible. Error: {e}")

    async def _get_product_links(self, page: "Page") -> List[str]:
        """Get product page links from the listing page."""
        links: List[str] = []
        seen_paths = set()
        try:
            # This selector targets links that look like product pages
            product_link_elements = await page.locator('a[href*="/mobile/phones/pay-monthly-contracts/"]').all()
            logging.info(f"Found {len(product_link_elements)} potential product link elements.")
            
            for element in product_link_elements:
                href = await element.get_attribute('href')
                if href:
                    # Ignore links that are clearly not product pages
                    if "/web-shop/login" in href or href.strip() == page.url:
                        continue
                    
                    full_url = urljoin(page.url, href)
                    
                    # Normalize URL to use only the path for duplicate checking
                    parsed_url = urlparse(full_url)
                    clean_path = parsed_url.path

                    # Ensure we are only adding unique product pages.
                    # A product URL path will typically have more than 5 segments.
                    # e.g., /mobile/phones/pay-monthly-contracts/apple/iphone-16-pro-max
                    if clean_path.count('/') >= 5 and clean_path not in seen_paths and clean_path != urlparse(page.url).path:
                        seen_paths.add(clean_path)
                        links.append(full_url)
            
            logging.info(f"Found {len(links)} unique product links after filtering and deduplication.")

        except Exception as e:
            logging.error(f"Error getting product links: {e}")
        return links

    async def _scrape_product_page(self, page: "Page", url: str) -> Optional[Dict]:
        """Scrape a single product page for details, including storage options."""
        try:
            await page.goto(url, wait_until="domcontentloaded")

            # Handle "Already with us?" popup using the provided test ID
            try:
                await page.get_by_test_id("newOrExisting-cta-new").click(timeout=5000)
                logging.info("Clicked 'new customer' button successfully.")
                await page.wait_for_timeout(1000)  # Wait for popup to close
            except Exception:
                logging.info("Did not find or could not click 'new customer' button. Assuming it is not present.")

            # --- Product Name Extraction ---
            name = ""
            # 1. Try H1 tag
            try:
                await page.locator('h1').first.wait_for(timeout=3000)
                h1_text = await page.locator('h1').first.text_content()
                if h1_text and h1_text.strip():
                    name = h1_text.strip()
                    logging.info(f"Found product name in H1: {name}")
            except Exception as e:
                logging.warning(f"Could not get name from H1 for {url}: {e}")

            # 2. If H1 fails, try parsing from URL
            if not name:
                logging.info(f"H1 failed, falling back to URL parsing for name: {url}")
                try:
                    path = urlparse(url).path
                    path_parts = [part for part in path.split('/') if part]
                    if len(path_parts) >= 5: # e.g., ['mobile', 'phones', 'pay-monthly-contracts', 'apple', 'iphone-16']
                        brand = path_parts[-2].title()
                        model_slug = path_parts[-1]
                        model = model_slug.replace('-', ' ').title()
                        
                        if "Iphone" in model:
                            model = model.replace("Iphone", "iPhone")
                        
                        if not model.lower().startswith(brand.lower()):
                            name = f"{brand} {model}"
                        else:
                            name = model
                        logging.info(f"Constructed name from URL: {name}")
                except Exception as e:
                    logging.warning(f"URL parsing for name failed for {url}: {e}")
            
            # 3. If all else fails, use page title
            if not name:
                logging.info(f"URL parsing failed, falling back to page title for name: {url}")
                name = await page.title()
                name = name.split('|')[0].strip()

            if not name:
                name = "Unknown Product"
                logging.error(f"Could not determine product name for {url}")

            # --- Storage/Capacity Extraction using a Scoped DOM search ---
            storage_options = []
            try:
                # Find a container likely to hold capacity options to scope the search
                capacity_container = page.locator('div:has([id*="selectedCapacity"])')
                
                if await capacity_container.count() > 0:
                    logging.info(f"Found capacity container for {url}. Scoping search to this container.")
                    container_to_search = capacity_container.first
                else:
                    logging.warning(f"Could not find capacity container for {url}. Searching entire page.")
                    container_to_search = page.locator('body')

                potential_options = await container_to_search.locator('*:has-text("GB"), *:has-text("TB")').all_text_contents()
                
                raw_options = []
                for text_blob in potential_options:
                    found = re.findall(r'(\d+\s*(?:GB|TB))', text_blob, re.IGNORECASE)
                    if found:
                        raw_options.extend(found)
                
                if raw_options:
                    normalized = [opt.replace(" ", "").upper() for opt in raw_options]
                    storage_options = self._filter_storage_options(list(set(normalized)))

            except Exception as e:
                logging.warning(f"Could not scrape storage options for {url}: {e}")

            # --- Detailed Description Extraction ---
            description = "No description available."
            desc_el = page.locator("meta[name='description']")
            if await desc_el.count() > 0:
                content = await desc_el.get_attribute("content")
                if content:
                    description = content.strip()

            detailed_description = ""
            try:
                desc_container = page.locator('#product-description, [data-test-id*="description"]').first
                if await desc_container.count() > 0 and await desc_container.is_visible():
                    detailed_description = await desc_container.inner_text()
            except Exception as e:
                logging.warning(f"Could not scrape detailed description for {url}: {e}")

            final_description = detailed_description.strip() if detailed_description else description

            # --- Device Cost Extraction ---
            device_cost = None
            try:
                # Look for an element containing the text "Total device cost". This is more robust.
                cost_locator = page.locator('*:text-matches("Total device cost", "i")').first
                await cost_locator.wait_for(timeout=3000)
                cost_text = await cost_locator.text_content()
                
                logging.info(f"Found cost-related text for {url}: '{cost_text}'")

                match = re.search(r'£([\d,]+\.?\d*)', cost_text)
                if match:
                    cost_str = match.group(1).replace(',', '')
                    device_cost = float(cost_str)
                    logging.info(f"Extracted device cost for {url}: £{device_cost}")
                else:
                    logging.warning(f"Could not parse cost from text for {url}: '{cost_text}'")
            except Exception as e:
                logging.warning(f"Could not find or parse device cost for {url}. It might not be on the page. Error: {e}")

            return {
                "name": name,
                "description": final_description,
                "url": url,
                "storage_options": storage_options,
                "device_cost": device_cost,
            }
        except Exception as e:
            logging.error(f"Error scraping detail page {url}: {e}")
            return None
    
    def _filter_storage_options(self, options: List[str]) -> List[str]:
        """
        Filters and sorts a list of storage-like strings to return only plausible
        device storage values.
        """
        # Expanded set of plausible storage sizes
        plausible_storage_gb = {16, 32, 64, 128, 256, 512, 1024}
        plausible_storage_tb = {1, 2, 4}
        
        filtered_options = set()
        for opt in options:
            match = re.match(r'(\d+)(GB|TB)', opt, re.IGNORECASE)
            if match:
                val, unit = int(match.group(1)), match.group(2).upper()
                
                if unit == 'GB':
                    if val in plausible_storage_gb:
                        # Normalize 1024GB to 1TB for consistency
                        if val == 1024:
                            filtered_options.add("1TB")
                        else:
                            filtered_options.add(f"{val}GB")
                elif unit == 'TB':
                    if val in plausible_storage_tb:
                        filtered_options.add(f"{val}TB")
        
        # Define a sort key to handle GB and TB values correctly
        def sort_key(s):
            match = re.match(r'(\d+)(GB|TB)', s, re.IGNORECASE)
            val, unit = int(match.group(1)), match.group(2).upper()
            # Convert TB to GB for sorting (1 TB = 1024 GB)
            return val * 1024 if unit == 'TB' else val

        return sorted(list(filtered_options), key=sort_key)

    def save_products(self, products: List[Dict], filename: Optional[str] = None) -> bool:
        """Saves a list of products to a JSON file."""
        if filename is None:
            filename = self.data_file
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(products, f, indent=2, ensure_ascii=False)
            logging.info(f"Saved {len(products)} products to {filename}")
            return True
        except Exception as e:
            logging.error(f"Error saving products to {filename}: {e}")
            return False

    def update_sample_data(self):
        """Update the main data file with sample products"""
        products = self.get_sample_products()
        return self.save_products(products) 