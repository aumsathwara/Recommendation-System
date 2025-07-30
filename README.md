# Skincare Products Scraper

This is an ethical web scraper designed to collect skincare product information from the MAC Cosmetics website.

## Features

- **Ethical Scraping**: Respects robots.txt, uses appropriate delays, and includes proper headers
- **Rate Limiting**: Implements delays between requests to avoid overwhelming the server
- **Error Handling**: Robust error handling with retry mechanisms
- **Data Storage**: Saves scraped data in structured JSON format
- **Logging**: Comprehensive logging for monitoring and debugging

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the scraper:
```bash
python mac_cosmetics_scraper.py
```

The script will:
1. Check robots.txt to ensure scraping is allowed
2. Scrape skincare products from MAC Cosmetics website
3. Save the data to `output_mac.json`

## Output Format

The scraper generates a JSON file with the following structure:

```json
{
  "scraper_info": {
    "scraped_at": "2024-01-01T12:00:00",
    "source_url": "https://www.maccosmetics.com/skincare",
    "total_products": 15,
    "scraper_version": "1.0.0"
  },
  "products": [
    {
      "name": "Product Name",
      "price": "$25.00",
      "original_price": "",
      "description": "Product description",
      "image_url": "https://example.com/image.jpg",
      "product_url": "https://example.com/product",
      "rating": "4.5",
      "review_count": "123",
      "availability": "In Stock",
      "category": "skincare",
      "brand": "MAC Cosmetics",
      "scraped_at": "2024-01-01T12:00:00"
    }
  ]
}
```

## Ethical Considerations

This scraper follows ethical web scraping practices:

- **Respects robots.txt**: Checks the website's robots.txt file before scraping
- **Rate Limiting**: Implements delays between requests (2 seconds by default)
- **Proper Headers**: Uses realistic browser headers
- **Error Handling**: Gracefully handles rate limiting and other errors
- **Minimal Impact**: Designed to minimize server load

## Configuration

You can modify the following settings in the script:

- `delay_between_requests`: Time to wait between requests (default: 2 seconds)
- `max_retries`: Number of retry attempts for failed requests (default: 3)

## Troubleshooting

If the scraper doesn't find products, it might be due to:

1. **Website Structure Changes**: The website's HTML structure may have changed
2. **Rate Limiting**: The website may be blocking requests
3. **JavaScript Content**: Some content may be loaded dynamically with JavaScript

Check the logs for detailed error messages and adjust the scraping patterns if needed.

## Legal Notice

This scraper is for educational and research purposes only. Always:

- Respect the website's Terms of Service
- Check robots.txt before scraping
- Use reasonable delays between requests
- Don't overload the server with too many requests
- Consider reaching out to the website owner for permission if scraping large amounts of data

## License

This project is for educational purposes. Please use responsibly and in accordance with the target website's terms of service. 
