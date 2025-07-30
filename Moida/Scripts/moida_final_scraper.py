#!/usr/bin/env python3
"""
Batched Moida Skincare Scraper with Progress Tracking

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

class BatchedMoidaScraper:
    """Batched scraper for Moida skincare products with progress tracking"""
    
    def __init__(self):
        self.base_url = "https://moidaus.com"
        self.skincare_url = "https://moidaus.com/collections/skin-care"
        self.session = requests.Session()
        
        # Ethical scraping headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Referer': 'https://moidaus.com/',
        })
        
        # Rate limiting settings
        self.delay_between_requests = 3  # seconds (more conservative for ethical scraping)
        self.max_retries = 3
        
        # Batch settings
        self.batch_size = 10  # products per category
        self.max_total_products = 60  # maximum products per run
        
        # Progress tracking
        self.progress_file = "scraping_progress.json"
        self.output_file = "output_moida_batched.json"
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
                    wait_time = (attempt + 1) * 15
                    logger.warning(f"Rate limited. Waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.warning(f"Request failed with status {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.delay_between_requests)
                    
        return None
    
    def discover_products_from_main_page(self) -> List[Dict]:
        """Discover products from the main skincare page"""
        logger.info("Discovering products from main skincare page...")
        
        response = self.make_request(self.skincare_url)
        if not response:
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        products = []
        
        # Look for product containers (based on analysis)
        product_containers = soup.find_all(['div', 'article'], class_=lambda x: x and any(word in x.lower() for word in ['product', 'item', 'card', 'grid']))
        
        logger.info(f"Found {len(product_containers)} product containers")
        
        for container in product_containers:
            try:
                # Extract product link
                product_link = container.find('a', href=True)
                if not product_link:
                    continue
                    
                href = product_link.get('href')
                if not href or '/products/' not in href:
                    continue
                
                # Skip if already scraped
                if href in self.scraped_urls:
                    logger.info(f"Skipping already scraped product: {href}")
                    continue
                
                # Extract product name
                name_elem = container.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']) or container.find(class_=lambda x: x and any(word in x.lower() for word in ['title', 'name', 'product']))
                product_name = name_elem.get_text().strip() if name_elem else "Unknown Product"
                
                # Extract price
                price_elem = container.find(string=re.compile(r'\$'))
                price = price_elem.strip() if price_elem else ""
                
                # Extract image
                img_elem = container.find('img', src=True)
                image_url = ""
                if img_elem:
                    src = img_elem.get('src')
                    if src and not src.startswith('http'):
                        src = urljoin(self.base_url, src)
                    image_url = src
                
                # Extract vendor/brand
                vendor_elem = container.find(string=re.compile(r'Vendor:', re.IGNORECASE))
                vendor = vendor_elem.strip() if vendor_elem else ""
                
                product_info = {
                    'name': product_name,
                    'url': href,
                    'price': price,
                    'image_url': image_url,
                    'vendor': vendor,
                    'category': 'skincare',
                    'brand': 'Moida'
                }
                
                products.append(product_info)
                logger.info(f"Found product: {product_name} - {href}")
                
            except Exception as e:
                logger.error(f"Error extracting product from container: {e}")
                continue
        
        # Remove duplicates based on URL
        unique_products = []
        seen_urls = set()
        for product in products:
            if product['url'] not in seen_urls:
                unique_products.append(product)
                seen_urls.add(product['url'])
        
        logger.info(f"Discovered {len(unique_products)} unique products")
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
        
        # Try multiple image extraction strategies for Moida
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
            'img[src*="cdn.shopify.com"]',
            'img[src*="moidaus.com"]',
            'img'
        ]
        
        for selector in img_selectors:
            img_elements = soup.select(selector)
            for img_elem in img_elements:
                img_url = img_elem.get('src') or img_elem.get('data-src') or img_elem.get('data-lazy')
                if img_url and len(img_url) > 10:
                    if not img_url.startswith('http'):
                        img_url = urljoin(self.base_url, img_url)
                    if 'moidaus.com' in img_url.lower() or 'cdn.shopify.com' in img_url.lower():
                        logger.info(f"Found image: {img_url}")
                        return img_url
        
        # If no image found, return empty string
        logger.warning(f"No image found for {product_name}")
        return ""
    
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
                '[data-price]',
                'span:contains("$")',
                'div:contains("$")'
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
                'p[class*="description"]',
                '[class*="product-details"]'
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
                'div[class*="ingredients"]',
                '[class*="product-ingredients"]'
            ]
            
            for selector in ingredients_selectors:
                ingredients_elem = soup.select_one(selector)
                if ingredients_elem and ingredients_elem.get_text().strip():
                    additional_info['ingredients'] = ingredients_elem.get_text().strip()
                    break
            
            # Extract vendor/brand
            vendor_selectors = [
                '[class*="vendor"]',
                '[class*="brand"]',
                'span:contains("Vendor:")',
                'div:contains("Vendor:")'
            ]
            
            for selector in vendor_selectors:
                vendor_elem = soup.select_one(selector)
                if vendor_elem and vendor_elem.get_text().strip():
                    vendor_text = vendor_elem.get_text().strip()
                    if 'Vendor:' in vendor_text:
                        vendor_name = vendor_text.replace('Vendor:', '').strip()
                        additional_info['vendor'] = vendor_name
                    break
            
        except Exception as e:
            logger.error(f"Error scraping individual product page: {e}")
        
        return additional_info
    
    def scrape_batched(self) -> List[Dict]:
        """Batched scraping with progress tracking"""
        logger.info("Starting batched Moida scraping...")
        
        # Step 1: Discover products from main page
        all_products = self.discover_products_from_main_page()
        if not all_products:
            logger.warning("No products found")
            return []
        
        # Step 2: Take only the first batch_size products (or max_total_products)
        batch_products = all_products[:min(self.batch_size, self.max_total_products)]
        logger.info(f"Selected {len(batch_products)} products for scraping")
        
        # Step 3: Scrape individual product pages
        scraped_products = []
        for i, product in enumerate(batch_products):
            logger.info(f"Processing product {i+1}/{len(batch_products)}: {product['name']}")
            
            # Create base product info
            product_info = {
                'name': product['name'],
                'product_url': urljoin(self.base_url, product['url']),
                'category': product['category'],
                'brand': product['brand'],
                'vendor': product.get('vendor', ''),
                'scraped_at': datetime.now().isoformat(),
                'image_url': product.get('image_url', ''),
                'price': product.get('price', ''),
                'detailed_description': '',
                'ingredients': '',
                'main_image': '',
                'additional_images': []
            }
            
            # Extract image from individual product page if not already found
            if not product_info['image_url']:
                image_url = self.extract_image_from_product_page(product_info['product_url'], product['name'])
                if image_url:
                    product_info['image_url'] = image_url
                    product_info['main_image'] = image_url
            
            # Get additional info from individual page
            additional_info = self.scrape_individual_product_page(product_info['product_url'])
            product_info.update(additional_info)
            
            # Mark as scraped
            self.scraped_urls.add(product['url'])
            
            # Only add if we have an image URL
            if product_info['image_url']:
                scraped_products.append(product_info)
                logger.info(f"Added product with image: {product['name']} - {product_info['image_url']}")
            else:
                logger.warning(f"Skipping product without image: {product['name']}")
            
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
                    'scraper_version': '1.0.0',
                    'enhanced_features': [
                        'Batched scraping (10 products per category)',
                        'Maximum 60 products per run',
                        'Progress tracking to avoid duplicates',
                        'Individual product page scraping',
                        'Mandatory image URLs for all products',
                        'Real data only',
                        'Ethical rate limiting',
                        'Comprehensive product information',
                        'Shopify-based website support'
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
        logger.info("Starting Batched Moida scraper...")
        
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
    scraper = BatchedMoidaScraper()
    products = scraper.run()
    
    if products:
        print(f"\nSuccessfully scraped {len(products)} new products!")
        print("Data saved to output_moida_batched.json")
        
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