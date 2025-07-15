# TOBI Scraper Service

This directory contains the standalone scraper service for TOBI. The scraper is separated from the main API to allow for independent operation and testing.

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

# Check scraping status
poetry run python scripts/scraper_service.py --status

# Update with sample data (for testing)
poetry run python scripts/scraper_service.py --sample

# Use custom data directory
poetry run python scripts/scraper_service.py --data-dir /path/to/data
```

### Status Check

```bash
poetry run python scripts/scraper_service.py --status
```

This will show:
- When data was last scraped
- Number of products in the database
- Data age in hours
- Scraping capabilities available

### Sample Data

For development and testing, you can populate the database with sample data:

```bash
poetry run python scripts/scraper_service.py --sample
```

## Dependencies

The scraper service tries to use the best available scraping method:

1. **Playwright** (preferred) - For dynamic content and JavaScript rendering
2. **Requests + BeautifulSoup** - For basic HTML scraping
3. **Sample Data** - As a fallback for testing

### Installing Dependencies

```bash
# For Playwright support
poetry add playwright beautifulsoup4
poetry run playwright install

# For basic scraping
poetry add requests beautifulsoup4

# No dependencies needed for sample data
```

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

## Local Development

### Running the Scraper

During development, you can run the scraper manually:

```bash
# Run from project root
poetry run python scripts/scraper_service.py

# Check current status
poetry run python scripts/scraper_service.py --status

# Use sample data for testing
poetry run python scripts/scraper_service.py --sample
```

### Monitoring

Check scraper health with:

```bash
# View recent logs
tail -f data/scraper.log

# Check last scraping status
poetry run python scripts/scraper_service.py --status

# Verify data age
ls -la data/products.json
```

### Testing

Test the scraper with sample data:

```bash
# Populate with sample data
poetry run python scripts/scraper_service.py --sample

# Check the generated data
cat data/products.json | python -m json.tool | head -20
``` 