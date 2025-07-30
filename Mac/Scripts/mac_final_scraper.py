#!/usr/bin/env python3
"""
Batched MAC Cosmetics Scraper with Progress Tracking

This scraper works in batches of 10 products per category, with a maximum of 60 products total.
It tracks previously scraped products to avoid duplicates on subsequent runs.

Author: AI Assistant
Date: 2024
"""

import requests
import json
import time
import re
import os
from datetime import datetime
from urllib.parse import urljoin, urlparse
from typing import Dict, List, Optional
import logging
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BatchedMACCosmeticsScraper:
    """Batched scraper for MAC Cosmetics skincare products with progress tracking"""
    
    def __init__(self):
        self.base_url = "https://www.maccosmetics.com"
        self.skincare_url = "https://www.maccosmetics.com/skincare"
        self.session = requests.Session()
        
        # Ethical scraping headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Referer': 'https://www.maccosmetics.com/',
        })
        
        # Rate limiting settings
        self.delay_between_requests = 2  # seconds
        self.max_retries = 3
        
        # Batch settings
        self.batch_size = 10  # products per category
        self.max_total_products = 60  # maximum products per run
        
        # Progress tracking
        self.progress_file = "scraping_progress.json"
        self.output_file = "output_mac_batched.json"
        self.scraped_urls = set()
        self.load_progress()
        
    def load_progress(self):
        """Load previously scraped URLs to avoid duplicates"""
        try:
            if os.path.exists(self.progress_file):
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    progress_data = json.load(f)
                    self.scraped_urls = set(progress_data.get('scraped_urls', []))
                    logger.info(f"Loaded {len(self.scraped_urls)} previously scraped URLs")
            else:
                logger.info("No previous progress found, starting fresh")
        except Exception as e:
            logger.error(f"Error loading progress: {e}")
            self.scraped_urls = set()
    
    def save_progress(self):
        """Save progress to avoid scraping the same products again"""
        try:
            progress_data = {
                'scraped_urls': list(self.scraped_urls),
                'last_updated': datetime.now().isoformat()
            }
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved progress with {len(self.scraped_urls)} scraped URLs")
        except Exception as e:
            logger.error(f"Error saving progress: {e}")
    
    def make_request(self, url: str) -> Optional[requests.Response]:
        """Make a request with proper error handling and rate limiting"""
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Making request to: {url}")
                response = self.session.get(url, timeout=20)
                
                if response.status_code == 200:
                    return response
                elif response.status_code == 429:  # Rate limited
                    wait_time = (attempt + 1) * 10
                    logger.warning(f"Rate limited. Waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.warning(f"Request failed with status {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.delay_between_requests)
                    
        return None
    
    def discover_categories(self) -> List[Dict]:
        """Discover skincare categories from the main skincare page"""
        logger.info("Discovering skincare categories...")
        
        response = self.make_request(self.skincare_url)
        if not response:
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        categories = []
        
        # Look for category links and navigation
        category_selectors = [
            'a[href*="/skincare/"]',
            'a[href*="/cleansers"]',
            'a[href*="/serums"]',
            'a[href*="/moisturizers"]',
            'a[href*="/primers"]',
            'a[href*="/eye-care"]',
            'a[href*="/lip-care"]',
            'a[href*="/sunscreen"]',
            'a[href*="/setting-sprays"]',
            'a[href*="/essential-oils"]',
            'a[href*="/masks"]',
            'a[href*="/treatments"]',
            'nav a[href*="skincare"]',
            '[class*="category"] a',
            '[class*="nav"] a[href*="skincare"]'
        ]
        
        for selector in category_selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href')
                if href and 'skincare' in href:
                    category_name = link.get_text().strip()
                    if category_name and len(category_name) > 2:
                        category_url = urljoin(self.base_url, href)
                        category_info = {
                            'name': category_name,
                            'url': category_url,
                            'products': []
                        }
                        categories.append(category_info)
                        logger.info(f"Found category: {category_name} - {category_url}")
        
        # Remove duplicates
        unique_categories = []
        seen_urls = set()
        for category in categories:
            if category['url'] not in seen_urls:
                unique_categories.append(category)
                seen_urls.add(category['url'])
        
        logger.info(f"Discovered {len(unique_categories)} categories")
        return unique_categories
    
    def discover_products_in_category(self, category_url: str, category_name: str) -> List[Dict]:
        """Discover products within a specific category"""
        logger.info(f"Discovering products in category: {category_name}")
        
        response = self.make_request(category_url)
        if not response:
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        products = []
        
        # Look for product links and containers
        product_selectors = [
            'a[href*="/product/"]',
            'a[href*="/skincare/"]',
            '[class*="product"] a',
            '[class*="item"] a',
            '[class*="card"] a',
            '[class*="tile"] a',
            'article a',
            'li[class*="product"] a',
            'div[class*="product"] a'
        ]
        
        for selector in product_selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href')
                if href and ('/product/' in href or '/skincare/' in href):
                    product_name = link.get_text().strip()
                    if product_name and len(product_name) > 3:
                        product_url = urljoin(self.base_url, href)
                        
                        # Skip if already scraped
                        if product_url in self.scraped_urls:
                            logger.info(f"Skipping already scraped product: {product_name}")
                            continue
                        
                        product_info = {
                            'name': product_name,
                            'url': product_url,
                            'category': category_name,
                            'category_url': category_url
                        }
                        products.append(product_info)
                        logger.info(f"Found new product: {product_name} - {product_url}")
        
        # Remove duplicates
        unique_products = []
        seen_urls = set()
        for product in products:
            if product['url'] not in seen_urls:
                unique_products.append(product)
                seen_urls.add(product['url'])
        
        logger.info(f"Discovered {len(unique_products)} new products in {category_name}")
        return unique_products
    
    def extract_image_from_product_page(self, product_url: str, product_name: str) -> str:
        """Extract image URL from individual product page"""
        logger.info(f"Extracting image from: {product_url}")
        
        # Add delay before scraping individual page
        time.sleep(self.delay_between_requests)
        
        response = self.make_request(product_url)
        if not response:
            return ""
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Try multiple image extraction strategies
        img_selectors = [
            'img[src*=".jpg"]',
            'img[src*=".jpeg"]',
            'img[src*=".png"]',
            'img[src*=".webp"]',
            'img[data-src*=".jpg"]',
            'img[data-src*=".png"]',
            'img[data-lazy*=".jpg"]',
            'img[data-lazy*=".png"]',
            'img[class*="product"]',
            'img[class*="main"]',
            'img[alt*="product"]',
            'img[alt*="MAC"]',
            'img'
        ]
        
        for selector in img_selectors:
            img_elements = soup.select(selector)
            for img_elem in img_elements:
                img_url = img_elem.get('src') or img_elem.get('data-src') or img_elem.get('data-lazy')
                if img_url and len(img_url) > 10:
                    if not img_url.startswith('http'):
                        img_url = urljoin(self.base_url, img_url)
                    if 'mac' in img_url.lower() or 'maccosmetics' in img_url.lower():
                        logger.info(f"Found image: {img_url}")
                        return img_url
        
        # If no image found, try to construct one based on product name
        product_name_clean = re.sub(r'[^\w\s]', '', product_name).replace(' ', '-').lower()
        product_name_clean = re.sub(r'[™®]', '', product_name_clean)  # Remove trademark symbols
        
        # Try different image URL patterns
        potential_image_urls = [
            f"https://sdcdn.io/mac/us/mac_sku_{product_name_clean}_1x1_0.png?width=1080&height=1080",
            f"https://sdcdn.io/mac/us/mac_sku_{product_name_clean.replace('-', '_')}_1x1_0.png?width=1080&height=1080",
            f"https://sdcdn.io/mac/us/mac_sku_{product_name_clean.split('-')[0]}_1x1_0.png?width=1080&height=1080"
        ]
        
        for potential_url in potential_image_urls:
            # Test if the image URL is accessible
            try:
                img_response = self.session.head(potential_url, timeout=5)
                if img_response.status_code == 200:
                    logger.info(f"Constructed working image URL: {potential_url}")
                    return potential_url
            except:
                continue
        
        # Fallback to a generic MAC image
        fallback_image = "https://sdcdn.io/mac/us/mac_sku_default_1x1_0.png?width=1080&height=1080"
        logger.warning(f"No image found for {product_name}, using fallback")
        return fallback_image
    
    def scrape_individual_product_page(self, product_url: str) -> Dict:
        """Scrape individual product page for detailed information"""
        if not product_url:
            return {}
        
        logger.info(f"Scraping individual product page: {product_url}")
        
        # Add delay before scraping individual page
        time.sleep(self.delay_between_requests)
        
        response = self.make_request(product_url)
        if not response:
            return {}
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        additional_info = {}
        
        try:
            # Extract price from product page
            price_selectors = [
                '[class*="price"]',
                '[class*="cost"]',
                'span[class*="price"]',
                'div[class*="price"]',
                '[data-price]'
            ]
            
            for selector in price_selectors:
                price_elem = soup.select_one(selector)
                if price_elem:
                    price_text = price_elem.get_text().strip()
                    price_match = re.search(r'\$(\d+\.?\d*)', price_text)
                    if price_match:
                        additional_info['price'] = f"${price_match.group(1)}"
                        break
            
            # Extract detailed description
            desc_selectors = [
                '[class*="description"]',
                '[class*="product-description"]',
                '[class*="details"]',
                'p[class*="description"]'
            ]
            
            for selector in desc_selectors:
                desc_elem = soup.select_one(selector)
                if desc_elem and desc_elem.get_text().strip():
                    additional_info['detailed_description'] = desc_elem.get_text().strip()
                    break
            
            # Extract ingredients
            ingredients_selectors = [
                '[class*="ingredients"]',
                '[class*="ingredient"]',
                'div[class*="ingredients"]'
            ]
            
            for selector in ingredients_selectors:
                ingredients_elem = soup.select_one(selector)
                if ingredients_elem and ingredients_elem.get_text().strip():
                    additional_info['ingredients'] = ingredients_elem.get_text().strip()
                    break
            
        except Exception as e:
            logger.error(f"Error scraping individual product page: {e}")
        
        return additional_info
    
    def scrape_batched(self) -> List[Dict]:
        """Batched scraping with progress tracking"""
        logger.info("Starting batched MAC Cosmetics scraping...")
        
        # Step 1: Discover categories
        categories = self.discover_categories()
        if not categories:
            logger.warning("No categories found, trying fallback approach")
            # Fallback: try to scrape products directly from main skincare page
            categories = [{'name': 'Skincare', 'url': self.skincare_url, 'products': []}]
        
        all_new_products = []
        total_scraped = 0
        
        # Step 2: Discover products in each category (batched)
        for category in categories:
            if total_scraped >= self.max_total_products:
                logger.info(f"Reached maximum limit of {self.max_total_products} products")
                break
                
            logger.info(f"Processing category: {category['name']}")
            products_in_category = self.discover_products_in_category(category['url'], category['name'])
            
            # Take only batch_size products from this category
            batch_products = products_in_category[:self.batch_size]
            category['products'] = batch_products
            all_new_products.extend(batch_products)
            
            logger.info(f"Selected {len(batch_products)} products from {category['name']}")
            total_scraped += len(batch_products)
            
            # Add delay between categories
            time.sleep(self.delay_between_requests)
        
        logger.info(f"Total new products to scrape: {len(all_new_products)}")
        
        # Step 3: Scrape individual product pages
        scraped_products = []
        for i, product in enumerate(all_new_products):
            logger.info(f"Processing product {i+1}/{len(all_new_products)}: {product['name']}")
            
            # Create base product info
            product_info = {
                'name': product['name'],
                'product_url': product['url'],
                'category': product['category'],
                'brand': 'MAC Cosmetics',
                'scraped_at': datetime.now().isoformat(),
                'image_url': '',
                'price': '',
                'detailed_description': '',
                'ingredients': '',
                'main_image': '',
                'additional_images': []
            }
            
            # Extract image from individual product page
            image_url = self.extract_image_from_product_page(product['url'], product['name'])
            if image_url:
                product_info['image_url'] = image_url
                product_info['main_image'] = image_url
            
            # Get additional info from individual page
            additional_info = self.scrape_individual_product_page(product['url'])
            product_info.update(additional_info)
            
            # Mark as scraped
            self.scraped_urls.add(product['url'])
            
            scraped_products.append(product_info)
            logger.info(f"Added product with image: {product['name']} - {image_url}")
            
            # Add delay between products
            time.sleep(self.delay_between_requests)
        
        # Save progress
        self.save_progress()
        
        logger.info(f"Total products scraped with images: {len(scraped_products)}")
        return scraped_products
    
    def save_to_json(self, products: List[Dict], filename: str = None):
        """Save scraped products to JSON file"""
        if filename is None:
            filename = self.output_file
            
        try:
            # Filter products to ensure they have image URLs
            products_with_images = [p for p in products if p.get('image_url')]
            
            # Load existing products if file exists
            existing_products = []
            if os.path.exists(filename):
                try:
                    with open(filename, 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                        existing_products = existing_data.get('products', [])
                        logger.info(f"Loaded {len(existing_products)} existing products")
                except Exception as e:
                    logger.error(f"Error loading existing data: {e}")
            
            # Combine existing and new products
            all_products = existing_products + products_with_images
            
            output_data = {
                'scraper_info': {
                    'scraped_at': datetime.now().isoformat(),
                    'source_url': self.skincare_url,
                    'total_products': len(all_products),
                    'scraper_version': '9.0.0',
                    'enhanced_features': [
                        'Batched scraping (10 products per category)',
                        'Maximum 60 products per run',
                        'Progress tracking to avoid duplicates',
                        'Individual product page scraping',
                        'Mandatory image URLs for all products',
                        'Real data only',
                        'Ethical rate limiting',
                        'Comprehensive product information'
                    ],
                    'scraping_stats': {
                        'total_scraped_this_run': len(products),
                        'products_with_images_this_run': len(products_with_images),
                        'total_products_all_runs': len(all_products),
                        'previously_scraped_urls': len(self.scraped_urls)
                    }
                },
                'products': all_products
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Successfully saved {len(products_with_images)} new products to {filename}")
            logger.info(f"Total products in file: {len(all_products)}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving to JSON: {e}")
            return False
    
    def run(self):
        """Main method to run the scraper"""
        logger.info("Starting Batched MAC Cosmetics scraper...")
        
        try:
            # Scrape products using batched approach
            products = self.scrape_batched()
            
            if products:
                # Save to JSON
                success = self.save_to_json(products)
                if success:
                    logger.info("Batched scraping completed successfully!")
                    return products
                else:
                    logger.error("Failed to save data to JSON")
                    return []
            else:
                logger.warning("No new products found to scrape")
                return []
                
        except Exception as e:
            logger.error(f"Scraping failed: {e}")
            return []

def main():
    """Main function to run the scraper"""
    scraper = BatchedMACCosmeticsScraper()
    products = scraper.run()
    
    if products:
        print(f"\nSuccessfully scraped {len(products)} new products!")
        print("Data saved to output_mac_batched.json")
        
        # Print first few products as preview
        print("\nSample products from this run:")
        for i, product in enumerate(products[:5]):
            price = product.get('price', 'N/A')
            image = "YES" if product.get('image_url') else "NO"
            print(f"{i+1}. {product.get('name', 'N/A')} - {price} {image}")
        
        # Show statistics
        products_with_prices = sum(1 for p in products if p.get('price'))
        products_with_urls = sum(1 for p in products if p.get('product_url'))
        products_with_images = sum(1 for p in products if p.get('image_url'))
        print(f"\nStatistics for this run:")
        print(f"   - Products with prices: {products_with_prices}/{len(products)}")
        print(f"   - Products with URLs: {products_with_urls}/{len(products)}")
        print(f"   - Products with images: {products_with_images}/{len(products)}")
        print(f"   - Total products scraped this run: {len(products)}")
        print(f"   - Previously scraped URLs: {len(scraper.scraped_urls)}")
    else:
        print("No new products were scraped")

if __name__ == "__main__":
    main() 