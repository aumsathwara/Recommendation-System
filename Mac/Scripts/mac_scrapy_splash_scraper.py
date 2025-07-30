#!/usr/bin/env python3
"""
MAC Cosmetics Scrapy Scraper with Splash for JavaScript Rendering

This script uses Scrapy with Splash to handle JavaScript-rendered content
and extract images from individual product pages.

Author: AI Assistant
Date: 2024
"""

import scrapy
from scrapy_splash import SplashRequest
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
import json
import time
from datetime import datetime
from typing import Dict, List
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MACCosmeticsSpider(scrapy.Spider):
    name = 'mac_cosmetics'
    allowed_domains = ['maccosmetics.com']
    start_urls = ['https://www.maccosmetics.com/skincare']
    
    # Custom settings for Splash
    custom_settings = {
        'SPLASH_URL': 'http://localhost:8050',
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy_splash.SplashCookiesMiddleware': 723,
            'scrapy_splash.SplashMiddleware': 725,
            'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 810,
        },
        'SPIDER_MIDDLEWARES': {
            'scrapy_splash.SplashDeduplicateArgsMiddleware': 100,
        },
        'DUPEFILTER_CLASS': 'scrapy_splash.SplashAwareDupeFilter',
        'HTTPCACHE_STORAGE': 'scrapy_splash.SplashAwareFSCacheStorage',
        'ROBOTSTXT_OBEY': True,
        'DOWNLOAD_DELAY': 3,  # 3 seconds between requests
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'CONCURRENT_REQUESTS': 1,  # Conservative for ethical scraping
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 3,
        'AUTOTHROTTLE_MAX_DELAY': 10,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 1.0,
        'AUTOTHROTTLE_DEBUG': True,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    
    def __init__(self):
        self.products = []
        self.scraped_count = 0
        self.failed_count = 0
        
    def start_requests(self):
        """Start requests with Splash for JavaScript rendering"""
        for url in self.start_urls:
            yield SplashRequest(
                url,
                self.parse,
                endpoint='render.html',
                args={
                    'wait': 5,  # Wait for JavaScript to load
                    'lua_source': self.get_lua_script(),
                    'timeout': 90,
                    'resource_timeout': 30,
                },
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                }
            )
    
    def get_lua_script(self):
        """Lua script for Splash to handle JavaScript rendering"""
        return """
        function main(splash, args)
            splash:set_user_agent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            -- Wait for page to load
            splash:wait(5)
            
            -- Scroll down to load lazy images
            splash:evaljs([[
                function scrollDown() {
                    var height = document.body.scrollHeight;
                    window.scrollTo(0, height);
                    return height;
                }
                scrollDown();
            ]])
            
            -- Wait for images to load
            splash:wait(3)
            
            -- Scroll back up
            splash:evaljs([[
                window.scrollTo(0, 0);
            ]])
            
            -- Wait a bit more for any remaining content
            splash:wait(2)
            
            return {
                html = splash:html(),
                png = splash:png(),
                har = splash:har(),
            }
        end
        """
    
    def parse(self, response):
        """Parse the main skincare page and extract product links"""
        logger.info(f"Parsing main page: {response.url}")
        
        # Extract product links
        product_links = response.css('a[href*="/product/"]::attr(href)').getall()
        
        # Also look for skincare-specific links
        skincare_links = response.css('a[href*="/skincare/"]::attr(href)').getall()
        
        # Combine and deduplicate links
        all_links = list(set(product_links + skincare_links))
        
        logger.info(f"Found {len(all_links)} product links")
        
        # Process each product link
        for i, link in enumerate(all_links[:50]):  # Limit to 50 for ethical scraping
            if link and '/product/' in link:
                full_url = response.urljoin(link)
                logger.info(f"Processing product {i+1}/{min(50, len(all_links))}: {full_url}")
                
                yield SplashRequest(
                    full_url,
                    self.parse_product,
                    endpoint='render.html',
                    args={
                        'wait': 3,
                        'lua_source': self.get_product_lua_script(),
                        'timeout': 60,
                        'resource_timeout': 20,
                    },
                    meta={'product_url': full_url},
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.5',
                        'Accept-Encoding': 'gzip, deflate',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1',
                    }
                )
                
                # Add delay between requests
                time.sleep(3)
    
    def get_product_lua_script(self):
        """Lua script for individual product pages"""
        return """
        function main(splash, args)
            splash:set_user_agent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            -- Wait for page to load
            splash:wait(3)
            
            -- Scroll to load images
            splash:evaljs([[
                function scrollToImages() {
                    var images = document.querySelectorAll('img[src*=".jpg"], img[src*=".png"], img[src*=".webp"]');
                    if (images.length > 0) {
                        images[0].scrollIntoView({behavior: 'smooth', block: 'center'});
                    }
                }
                scrollToImages();
            ]])
            
            -- Wait for images to load
            splash:wait(2)
            
            -- Trigger any lazy loading
            splash:evaljs([[
                function triggerLazyLoading() {
                    var lazyImages = document.querySelectorAll('img[data-src], img[data-lazy]');
                    lazyImages.forEach(function(img) {
                        if (img.dataset.src) {
                            img.src = img.dataset.src;
                        }
                        if (img.dataset.lazy) {
                            img.src = img.dataset.lazy;
                        }
                    });
                }
                triggerLazyLoading();
            ]])
            
            -- Wait a bit more
            splash:wait(1)
            
            return {
                html = splash:html(),
                png = splash:png(),
                har = splash:har(),
            }
        end
        """
    
    def parse_product(self, response):
        """Parse individual product page"""
        product_url = response.meta.get('product_url', '')
        logger.info(f"Parsing product page: {product_url}")
        
        try:
            # Extract product information
            product_info = {
                'name': '',
                'price': '',
                'original_price': '',
                'description': '',
                'image_url': '',
                'product_url': product_url,
                'rating': '',
                'review_count': '',
                'availability': 'Unknown',
                'category': 'skincare',
                'brand': 'MAC Cosmetics',
                'scraped_at': datetime.now().isoformat(),
                'detailed_description': '',
                'ingredients': '',
                'main_image': '',
                'additional_images': []
            }
            
            # Extract product name
            name_selectors = [
                'h1::text',
                'h2::text',
                'h3::text',
                '[class*="title"]::text',
                '[class*="product-name"]::text',
                '[class*="product-title"]::text'
            ]
            
            for selector in name_selectors:
                name = response.css(selector).get()
                if name and name.strip():
                    product_info['name'] = name.strip()
                    break
            
            # Extract price
            price_selectors = [
                '[class*="price"]::text',
                '[class*="cost"]::text',
                'span[class*="price"]::text',
                'div[class*="price"]::text',
                '[data-price]::text'
            ]
            
            for selector in price_selectors:
                price_text = response.css(selector).get()
                if price_text:
                    import re
                    price_match = re.search(r'\$(\d+\.?\d*)', price_text)
                    if price_match:
                        product_info['price'] = f"${price_match.group(1)}"
                        break
            
            # Extract description
            desc_selectors = [
                '[class*="description"]::text',
                '[class*="desc"]::text',
                'p[class*="description"]::text'
            ]
            
            for selector in desc_selectors:
                desc = response.css(selector).get()
                if desc and desc.strip():
                    product_info['description'] = desc.strip()
                    break
            
            # Extract detailed description
            detailed_desc_selectors = [
                '[class*="product-description"]::text',
                '[class*="details"]::text',
                'div[class*="description"]::text'
            ]
            
            for selector in detailed_desc_selectors:
                detailed_desc = response.css(selector).get()
                if detailed_desc and detailed_desc.strip():
                    product_info['detailed_description'] = detailed_desc.strip()
                    break
            
            # Extract ingredients
            ingredients_selectors = [
                '[class*="ingredients"]::text',
                '[class*="ingredient"]::text',
                'div[class*="ingredients"]::text'
            ]
            
            for selector in ingredients_selectors:
                ingredients = response.css(selector).get()
                if ingredients and ingredients.strip():
                    product_info['ingredients'] = ingredients.strip()
                    break
            
            # Extract images - MANDATORY
            image_selectors = [
                'img[src*=".jpg"]::attr(src)',
                'img[src*=".jpeg"]::attr(src)',
                'img[src*=".png"]::attr(src)',
                'img[src*=".webp"]::attr(src)',
                'img[data-src*=".jpg"]::attr(data-src)',
                'img[data-src*=".jpeg"]::attr(data-src)',
                'img[data-src*=".png"]::attr(data-src)',
                'img[data-src*=".webp"]::attr(data-src)',
                'img[data-lazy*=".jpg"]::attr(data-lazy)',
                'img[data-lazy*=".jpeg"]::attr(data-lazy)',
                'img[data-lazy*=".png"]::attr(data-lazy)',
                'img[data-lazy*=".webp"]::attr(data-lazy)',
                'img[class*="product"]::attr(src)',
                'img[class*="main"]::attr(src)',
                'img[alt*="product"]::attr(src)',
                'img::attr(src)'  # Fallback
            ]
            
            images = []
            for selector in image_selectors:
                image_urls = response.css(selector).getall()
                for img_url in image_urls:
                    if img_url and len(img_url) > 10:
                        if not img_url.startswith('http'):
                            img_url = response.urljoin(img_url)
                        if 'mac' in img_url.lower() or 'maccosmetics' in img_url.lower():
                            images.append(img_url)
            
            # Remove duplicates and set images
            unique_images = list(dict.fromkeys(images))  # Preserve order while removing duplicates
            
            if unique_images:
                product_info['image_url'] = unique_images[0]  # Main image
                product_info['main_image'] = unique_images[0]
                product_info['additional_images'] = unique_images[1:]  # Additional images
            
            # Extract availability
            availability_text = response.css('body::text').getall()
            availability_text = ' '.join(availability_text).lower()
            
            if 'sold out' in availability_text or 'out of stock' in availability_text:
                product_info['availability'] = 'Out of Stock'
            elif 'add to bag' in availability_text or 'add to cart' in availability_text:
                product_info['availability'] = 'In Stock'
            
            # Only add product if it has a name and image
            if product_info['name'] and product_info['image_url']:
                self.products.append(product_info)
                self.scraped_count += 1
                logger.info(f"Successfully scraped: {product_info['name']} - {product_info['image_url']}")
            else:
                self.failed_count += 1
                logger.warning(f"Failed to scrape product: {product_info['name']} - No image URL")
                
        except Exception as e:
            self.failed_count += 1
            logger.error(f"Error parsing product {product_url}: {e}")
    
    def closed(self, reason):
        """Called when spider is closed"""
        logger.info(f"Spider closed. Reason: {reason}")
        logger.info(f"Total products scraped: {self.scraped_count}")
        logger.info(f"Failed attempts: {self.failed_count}")
        
        # Save results to JSON
        self.save_results()
    
    def save_results(self):
        """Save scraped products to JSON file"""
        try:
            # Filter products to ensure they have image URLs
            products_with_images = [p for p in self.products if p.get('image_url')]
            
            output_data = {
                'scraper_info': {
                    'scraped_at': datetime.now().isoformat(),
                    'source_url': 'https://www.maccosmetics.com/skincare',
                    'total_products': len(products_with_images),
                    'scraper_version': '4.0.0',
                    'enhanced_features': [
                        'Scrapy with Splash for JavaScript rendering',
                        'Individual product page scraping',
                        'Mandatory image URLs',
                        'Real data only (no fake/sample data)',
                        'Ethical rate limiting',
                        'JavaScript-rendered content extraction'
                    ],
                    'scraping_stats': {
                        'total_scraped': self.scraped_count,
                        'failed_attempts': self.failed_count,
                        'products_with_images': len(products_with_images),
                        'products_without_images': len(self.products) - len(products_with_images)
                    }
                },
                'products': products_with_images
            }
            
            filename = 'output_mac_scrapy_splash.json'
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Successfully saved {len(products_with_images)} products with images to {filename}")
            
            # Print summary
            print(f"\nSuccessfully scraped {len(products_with_images)} products!")
            print(f"Data saved to {filename}")
            
            # Print first few products as preview
            print("\nSample products:")
            for i, product in enumerate(products_with_images[:5]):
                price = product.get('price', 'N/A')
                image = "YES" if product.get('image_url') else "NO"
                print(f"{i+1}. {product.get('name', 'N/A')} - {price} {image}")
            
            # Show statistics
            products_with_prices = sum(1 for p in products_with_images if p.get('price'))
            products_with_urls = sum(1 for p in products_with_images if p.get('product_url'))
            products_with_images_count = sum(1 for p in products_with_images if p.get('image_url'))
            print(f"\nStatistics:")
            print(f"   - Products with prices: {products_with_prices}/{len(products_with_images)}")
            print(f"   - Products with URLs: {products_with_urls}/{len(products_with_images)}")
            print(f"   - Products with images: {products_with_images_count}/{len(products_with_images)}")
            print(f"   - Total products scraped: {len(products_with_images)}")
            
        except Exception as e:
            logger.error(f"Error saving results: {e}")

def run_scrapy_spider():
    """Run the Scrapy spider"""
    # Create a crawler process
    process = CrawlerProcess({
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'ROBOTSTXT_OBEY': True,
        'DOWNLOAD_DELAY': 3,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'CONCURRENT_REQUESTS': 1,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 3,
        'AUTOTHROTTLE_MAX_DELAY': 10,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 1.0,
        'AUTOTHROTTLE_DEBUG': True,
        'LOG_LEVEL': 'INFO',
    })
    
    # Add the spider to the process
    process.crawl(MACCosmeticsSpider)
    
    # Start the crawling process
    process.start()

if __name__ == "__main__":
    print("Starting MAC Cosmetics Scrapy Scraper with Splash...")
    print("Make sure Splash is running on http://localhost:8050")
    print("To install Splash: docker run -p 8050:8050 scrapinghub/splash")
    print("This may take several minutes due to ethical rate limiting...")
    
    try:
        run_scrapy_spider()
    except Exception as e:
        print(f"❌ Error running scraper: {e}")
        print("💡 Make sure Splash is running and accessible at http://localhost:8050") 