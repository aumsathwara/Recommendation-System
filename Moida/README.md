# Moida Skincare Scraper

This scraper extracts skincare product information from [Moida](https://moidaus.com/collections/skin-care) in an ethical and respectful manner.

## Features

- **Batched Scraping**: Processes 10 products at a time, maximum 60 products per run
- **Progress Tracking**: Avoids scraping the same products on subsequent runs
- **Ethical Rate Limiting**: 3-second delays between requests
- **Image Extraction**: Extracts product images from individual product pages
- **Comprehensive Data**: Captures product names, prices, descriptions, vendors, and images
- **Shopify Support**: Optimized for Shopify-based e-commerce sites

## Installation

1. Install required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the scraper from the Scripts directory:
```bash
cd Scripts
python moida_final_scraper.py
```

## Output

The scraper generates:
- `output_moida_batched.json`: Main output file with scraped products
- `scraping_progress.json`: Progress tracking to avoid duplicates

## Ethical Considerations

- Respects robots.txt
- Implements rate limiting (3-second delays)
- Uses proper User-Agent headers
- Avoids overwhelming the server
- Tracks progress to prevent duplicate scraping

## Data Structure

Each product contains:
- `name`: Product name
- `product_url`: Full product URL
- `category`: Product category (skincare)
- `brand`: Brand name (Moida)
- `vendor`: Product vendor/brand
- `price`: Product price
- `image_url`: Main product image
- `detailed_description`: Product description
- `ingredients`: Product ingredients (if available)
- `scraped_at`: Timestamp of scraping

## Compliance

This scraper follows ethical web scraping practices:
- Respects website terms of service
- Implements proper rate limiting
- Uses respectful headers
- Avoids automated purchasing or checkout flows
- Only extracts publicly available information 