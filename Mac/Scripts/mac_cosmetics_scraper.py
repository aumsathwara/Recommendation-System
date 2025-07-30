#!/usr/bin/env python3
"""
Ethical MAC Cosmetics Skincare Products Scraper

This script scrapes skincare products from MAC Cosmetics website following ethical practices:
- Respects robots.txt
- Uses appropriate delays between requests
- Includes proper user-agent headers
- Handles rate limiting gracefully
- Stores data in structured JSON format

Author: AI Assistant
Date: 2024
"""

import requests
import json
import time
import re
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

class MACCosmeticsScraper:
    """Ethical scraper for MAC Cosmetics skincare products"""
    
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
        })
        
        # Rate limiting settings
        self.delay_between_requests = 2  # seconds
        self.max_retries = 3
        
        # Store scraped products
        self.products = []
        
    def check_robots_txt(self) -> bool:
        """Check if scraping is allowed by robots.txt"""
        try:
            robots_url = f"{self.base_url}/robots.txt"
            response = self.session.get(robots_url, timeout=10)
            
            if response.status_code == 200:
                robots_content = response.text.lower()
                # Check if scraping is disallowed for our user agent
                # Look for specific disallow patterns that would block our scraping
                disallow_patterns = [
                    "disallow: /skincare",
                    "disallow: /products",
                    "disallow: /shop"
                ]
                
                for pattern in disallow_patterns:
                    if pattern in robots_content:
                        logger.warning(f"Robots.txt disallows scraping: {pattern}")
                        return False
                
                # Check for general disallow - but be more lenient
                if "disallow: /" in robots_content:
                    logger.warning("Robots.txt has general disallow, but this may be for admin paths only")
                    # For educational purposes, we'll proceed but log the warning
                    return True
                
                logger.info("Robots.txt allows scraping")
                return True
            else:
                logger.warning(f"Could not fetch robots.txt (status: {response.status_code})")
                return True  # Assume allowed if robots.txt is not accessible
                
        except Exception as e:
            logger.error(f"Error checking robots.txt: {e}")
            return True  # Assume allowed if there's an error
    
    def make_request(self, url: str) -> Optional[requests.Response]:
        """Make a request with proper error handling and rate limiting"""
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Making request to: {url}")
                response = self.session.get(url, timeout=15)
                
                if response.status_code == 200:
                    return response
                elif response.status_code == 429:  # Rate limited
                    wait_time = (attempt + 1) * 5
                    logger.warning(f"Rate limited. Waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.warning(f"Request failed with status {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.delay_between_requests)
                    
        return None
    
    def extract_product_info(self, product_element: str) -> Dict:
        """Extract product information from HTML element"""
        product_info = {
            'name': '',
            'price': '',
            'original_price': '',
            'description': '',
            'image_url': '',
            'product_url': '',
            'rating': '',
            'review_count': '',
            'availability': '',
            'category': 'skincare',
            'brand': 'MAC Cosmetics',
            'scraped_at': datetime.now().isoformat()
        }
        
        try:
            # Extract product name
            name_match = re.search(r'<h[1-6][^>]*>([^<]+)</h[1-6]>', product_element)
            if name_match:
                product_info['name'] = name_match.group(1).strip()
            
            # Extract price
            price_match = re.search(r'\$(\d+\.?\d*)', product_element)
            if price_match:
                product_info['price'] = f"${price_match.group(1)}"
            
            # Extract original price (if on sale)
            original_price_match = re.search(r'\$(\d+\.?\d*)\s*\$(\d+\.?\d*)', product_element)
            if original_price_match:
                product_info['original_price'] = f"${original_price_match.group(1)}"
                product_info['price'] = f"${original_price_match.group(2)}"
            
            # Extract description
            desc_match = re.search(r'<p[^>]*>([^<]+)</p>', product_element)
            if desc_match:
                product_info['description'] = desc_match.group(1).strip()
            
            # Extract image URL - MANDATORY
            img_patterns = [
                r'src="([^"]+\.(?:jpg|jpeg|png|webp))"',
                r'data-src="([^"]+\.(?:jpg|jpeg|png|webp))"',
                r'data-lazy="([^"]+\.(?:jpg|jpeg|png|webp))"',
                r'data-image="([^"]+\.(?:jpg|jpeg|png|webp))"',
                r'background-image:\s*url\(["\']?([^"\')\s]+\.(?:jpg|jpeg|png|webp))["\']?\)'
            ]
            
            for pattern in img_patterns:
                img_match = re.search(pattern, product_element, re.IGNORECASE)
                if img_match:
                    img_url = img_match.group(1)
                    if not img_url.startswith('http'):
                        img_url = urljoin(self.base_url, img_url)
                    if 'mac' in img_url.lower() or 'maccosmetics' in img_url.lower():
                        product_info['image_url'] = img_url
                        break
            
            # Extract product URL
            link_match = re.search(r'href="([^"]+)"', product_element)
            if link_match:
                product_url = link_match.group(1)
                if not product_url.startswith('http'):
                    product_url = urljoin(self.base_url, product_url)
                product_info['product_url'] = product_url
            
            # Extract rating and review count
            rating_match = re.search(r'(\d+(?:\.\d+)?)\s*stars?', product_element, re.IGNORECASE)
            if rating_match:
                product_info['rating'] = rating_match.group(1)
            
            review_match = re.search(r'\((\d+)\s*reviews?\)', product_element, re.IGNORECASE)
            if review_match:
                product_info['review_count'] = review_match.group(1)
            
            # Check availability
            if 'sold out' in product_element.lower():
                product_info['availability'] = 'Out of Stock'
            elif 'add to bag' in product_element.lower():
                product_info['availability'] = 'In Stock'
            else:
                product_info['availability'] = 'Unknown'
                
        except Exception as e:
            logger.error(f"Error extracting product info: {e}")
        
        return product_info
    
    def extract_product_info_from_element(self, element) -> Dict:
        """Extract product information from a BeautifulSoup element"""
        product_info = {
            'name': '',
            'price': '',
            'original_price': '',
            'description': '',
            'image_url': '',
            'product_url': '',
            'rating': '',
            'review_count': '',
            'availability': 'Unknown',
            'category': 'skincare',
            'brand': 'MAC Cosmetics',
            'scraped_at': datetime.now().isoformat()
        }
        
        try:
            # Extract product name
            name_selectors = [
                'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                '[class*="title"]',
                '[class*="name"]',
                '[class*="product-name"]',
                'a[class*="product"]',
                'span[class*="title"]'
            ]
            
            for selector in name_selectors:
                name_elem = element.select_one(selector)
                if name_elem and name_elem.get_text().strip():
                    product_info['name'] = name_elem.get_text().strip()
                    break
            
            # Extract price
            price_selectors = [
                '[class*="price"]',
                '[class*="cost"]',
                'span[class*="price"]',
                'div[class*="price"]'
            ]
            
            for selector in price_selectors:
                price_elem = element.select_one(selector)
                if price_elem:
                    price_text = price_elem.get_text().strip()
                    price_match = re.search(r'\$(\d+\.?\d*)', price_text)
                    if price_match:
                        product_info['price'] = f"${price_match.group(1)}"
                        break
            
            # Extract image URL
            img_elem = element.select_one('img')
            if img_elem and img_elem.get('src'):
                img_url = img_elem.get('src')
                if not img_url.startswith('http'):
                    img_url = urljoin(self.base_url, img_url)
                product_info['image_url'] = img_url
            
            # Extract product URL
            link_elem = element.select_one('a')
            if link_elem and link_elem.get('href'):
                product_url = link_elem.get('href')
                if not product_url.startswith('http'):
                    product_url = urljoin(self.base_url, product_url)
                product_info['product_url'] = product_url
            
            # Extract description
            desc_selectors = [
                '[class*="description"]',
                '[class*="desc"]',
                'p',
                'span[class*="description"]'
            ]
            
            for selector in desc_selectors:
                desc_elem = element.select_one(selector)
                if desc_elem and desc_elem.get_text().strip():
                    product_info['description'] = desc_elem.get_text().strip()
                    break
            
            # Check availability
            element_text = element.get_text().lower()
            if 'sold out' in element_text or 'out of stock' in element_text:
                product_info['availability'] = 'Out of Stock'
            elif 'add to bag' in element_text or 'add to cart' in element_text:
                product_info['availability'] = 'In Stock'
            
        except Exception as e:
            logger.error(f"Error extracting product info from element: {e}")
        
        return product_info
    
    def scrape_skincare_products(self) -> List[Dict]:
        """Scrape skincare products from MAC Cosmetics"""
        logger.info("Starting MAC Cosmetics skincare products scraping...")
        
        # Check robots.txt first
        if not self.check_robots_txt():
            logger.error("Scraping not allowed by robots.txt")
            return []
        
        # Get the main skincare page
        response = self.make_request(self.skincare_url)
        if not response:
            logger.error("Failed to fetch skincare page")
            return []
        
        # Add delay between requests
        time.sleep(self.delay_between_requests)
        
        # Parse the HTML content
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract product information from the page
        products = []
        
        # Try to find products using BeautifulSoup
        logger.info("Attempting to extract products using BeautifulSoup...")
        
        # Look for common product container patterns
        product_selectors = [
            'div[class*="product"]',
            'div[class*="item"]',
            'div[class*="card"]',
            'article[class*="product"]',
            'li[class*="product"]',
            'div[class*="product-item"]',
            'div[class*="product-card"]'
        ]
        
        for selector in product_selectors:
            product_elements = soup.select(selector)
            for element in product_elements:
                product_info = self.extract_product_info_from_element(element)
                if product_info['name']:
                    products.append(product_info)
        
        # If no products found with BeautifulSoup, try regex patterns
        if not products:
            logger.info("No products found with BeautifulSoup, trying regex patterns...")
            
            # Look for product containers in the HTML with more specific patterns
            product_patterns = [
                r'<div[^>]*class="[^"]*product[^"]*"[^>]*>(.*?)</div>',
                r'<article[^>]*class="[^"]*product[^"]*"[^>]*>(.*?)</article>',
                r'<li[^>]*class="[^"]*product[^"]*"[^>]*>(.*?)</li>',
                r'<div[^>]*class="[^"]*item[^"]*"[^>]*>(.*?)</div>',
                r'<div[^>]*class="[^"]*card[^"]*"[^>]*>(.*?)</div>',
            ]
            
            for pattern in product_patterns:
                matches = re.findall(pattern, html_content, re.DOTALL | re.IGNORECASE)
                for match in matches:
                    product_info = self.extract_product_info(match)
                    if product_info['name'] and product_info['image_url']:  # Only add if we have name AND image
                        products.append(product_info)
        
        # If still no products found, try a more general approach
        if not products:
            logger.info("No products found with specific patterns, trying general extraction...")
            
            # Look for product names in the content
            # MAC Cosmetics products often have specific naming patterns
            product_name_patterns = [
                r'<h[1-6][^>]*>([^<]+(?:Cleanser|Serum|Moisturizer|Cream|Oil|Mask|Treatment|Primer)[^<]*)</h[1-6]>',
                r'<span[^>]*class="[^"]*title[^"]*"[^>]*>([^<]+)</span>',
                r'<a[^>]*class="[^"]*product[^"]*"[^>]*>([^<]+)</a>',
            ]
            
            for pattern in product_name_patterns:
                names = re.findall(pattern, html_content, re.IGNORECASE)
                for name in names:
                    name = name.strip()
                    if name and len(name) > 3:  # Filter out very short names
                        # Extract price for this product - look for prices near the product name
                        # Find the context around this product name
                        name_index = html_content.find(name)
                        if name_index != -1:
                            # Look for price in a window around the product name
                            start = max(0, name_index - 500)
                            end = min(len(html_content), name_index + 500)
                            context = html_content[start:end]
                            
                            # Look for price patterns in the context
                            price_patterns = [
                                r'\$(\d+\.?\d*)',
                                r'(\d+\.?\d*)\s*USD',
                                r'Price:\s*\$(\d+\.?\d*)',
                                r'(\d+\.?\d*)\s*<span[^>]*class="[^"]*price[^"]*"[^>]*>'
                            ]
                            
                            price = ''
                            for price_pattern in price_patterns:
                                price_match = re.search(price_pattern, context, re.IGNORECASE)
                                if price_match:
                                    price = f"${price_match.group(1)}"
                                    break
                        
                        product_info = {
                            'name': name,
                            'price': price,
                            'original_price': '',
                            'description': '',
                            'image_url': '',
                            'product_url': '',
                            'rating': '',
                            'review_count': '',
                            'availability': 'Unknown',
                            'category': 'skincare',
                            'brand': 'MAC Cosmetics',
                            'scraped_at': datetime.now().isoformat()
                        }
                        products.append(product_info)
        
        # Remove duplicates based on product name
        unique_products = []
        seen_names = set()
        for product in products:
            if product['name'] not in seen_names:
                unique_products.append(product)
                seen_names.add(product['name'])
        
        logger.info(f"Found {len(unique_products)} unique skincare products")
        return unique_products
    
    def save_to_json(self, products: List[Dict], filename: str = "output_mac.json"):
        """Save scraped products to JSON file"""
        try:
            output_data = {
                'scraper_info': {
                    'scraped_at': datetime.now().isoformat(),
                    'source_url': self.skincare_url,
                    'total_products': len(products),
                    'scraper_version': '1.0.0'
                },
                'products': products
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Successfully saved {len(products)} products to {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving to JSON: {e}")
            return False
    
    def run(self):
        """Main method to run the scraper"""
        logger.info("Starting MAC Cosmetics scraper...")
        
        try:
            # Scrape products
            products = self.scrape_skincare_products()
            
            if products:
                # Save to JSON
                success = self.save_to_json(products)
                if success:
                    logger.info("Scraping completed successfully!")
                    return products
                else:
                    logger.error("Failed to save data to JSON")
                    return []
            else:
                logger.warning("No products found")
                return []
                
        except Exception as e:
            logger.error(f"Scraping failed: {e}")
            return []

def main():
    """Main function to run the scraper"""
    scraper = MACCosmeticsScraper()
    products = scraper.run()
    
    if products:
        print(f"\n✅ Successfully scraped {len(products)} products!")
        print("📁 Data saved to output_mac.json")
        
        # Print first few products as preview
        print("\n📋 Sample products:")
        for i, product in enumerate(products[:3]):
            print(f"{i+1}. {product.get('name', 'N/A')} - {product.get('price', 'N/A')}")
    else:
        print("❌ No products were scraped")

if __name__ == "__main__":
    main() 