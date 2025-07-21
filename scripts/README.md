# Web Scraper Service

This directory contains the standalone web scraper service. The scraper is separated from the main API to allow for independent operation and testing.

## Overview

The scraper service handles:
- Extracting product data from Vodafone UK website
- Updating the product database (`data/products.json`)
- Providing sample data for testing
- Logging scraping operations

## Usage

### Basic Commands

```bash
# Run the scraper (will check if data is fresh)
poetry run python scripts/scraper_service.py

# Force scraping even if data is recent
poetry run python scripts/scraper_service.py --force

# Limit the number of products to scrape (e.g., 5)
poetry run python scripts/scraper_service.py --limit 5

# Check scraping status
poetry run python scripts/scraper_service.py --status

# Update with sample data (for testing)
poetry run python scripts/scraper_service.py --sample

# Use custom data directory
poetry run python scripts/scraper_service.py --data-dir /path/to/data
```

### Monitoring and Testing

During development, you can monitor the scraper and test its output:

```bash
# View recent logs
tail -f data/scraper.log

# Check last scraping status
poetry run python scripts/scraper_service.py --status

# Verify data age and file creation
ls -la data/products.json

# Populate with sample data and preview it
poetry run python scripts/scraper_service.py --sample
cat data/products.json | python -m json.tool | head -20
```

## Dependencies

The scraper service requires `playwright` and `beautifulsoup4`, which are included in the project's `pyproject.toml`. These are installed automatically when you run `poetry install`.

The scraper service tries to use the best available scraping method:

1.  **Playwright** (preferred) - For dynamic content and JavaScript rendering
2.  **Requests + BeautifulSoup** - For basic HTML scraping
3.  **Sample Data** - As a fallback for testing

## Output Files

- `data/products.json` - Main product database
- `data/scraped_products.json` - Backup of scraped data
- `data/scraper_metadata.json` - Scraping metadata and timestamps
- `data/scraper.log` - Scraping operation logs

## Architecture Benefits

Separating the scraper from the main API provides:

1. **Performance** - Main API is not blocked by scraping operations
2. **Scalability** - Scraper can run on different servers/schedules
3. **Reliability** - Main API stays available even if scraping fails
4. **Security** - Reduced attack surface on customer-facing API
5. **Flexibility** - Can run scraper independently for testing/updates

## Error Handling

The scraper service includes comprehensive error handling:

- Falls back to different scraping methods if one fails
- Logs all operations for debugging
- Provides sample data if scraping is unavailable
- Checks data freshness to avoid unnecessary scraping 