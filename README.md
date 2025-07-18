# TOBI: A Conversational Sales Assistant

This project is a sophisticated, AI-powered sales assistant for a Vodafone UK. It's designed to help customers find the perfect mobile phone by understanding their needs through natural conversation.

## Key Features

- **AI-Powered Conversations**: Utilizes OpenAI's gpt-4o for realistic, helpful dialogue.
- **Dynamic Product Search**: Intelligently searches product data based on the user's conversation.
- **Multi-Step Upsell Journey**: Guides users through a series of upsell offers after a successful recommendation.
- **Personalized Recommendations**: Gathers user preferences to provide tailored suggestions.
- **Real-time Data Scraping**: A standalone Playwright service keeps product information up-to-date from the Vodafone UK website.
- **Session Management**: Maintains conversation history for a coherent user experience, including full session logging for analysis.
- **Decoupled Architecture**: The FastAPI backend and vanilla JavaScript frontend are fully independent, allowing either to be replaced.

## Technology Stack

- **Backend**: Python 3.9+, FastAPI, LangChain
- **Frontend**: HTML5, CSS3, Vanilla JavaScript (ES6+)
- **AI Engine**: OpenAI gpt-4o
- **Web Scraping**: Playwright
- **Package Management**: Poetry

## Getting Started

### 1. One-Time Setup

Follow these steps once to set up your development environment.

- Python 3.9 or higher
- [Poetry](https://python-poetry.org/docs/#installation) for package management
- An [OpenAI API key](https://platform.openai.com/account/api-keys)

```bash
# Clone the repository and navigate into the directory
git clone https://github.com/Tarek0/conversational-sales.git
cd conversational-sales

# Configure Poetry to create virtual environments inside the project folder
poetry config virtualenvs.in-project true

# Install Python dependencies and browser drivers
poetry install
playwright install

# Create your environment file
cp .env.example .env
```

Now, open the `.env` file and set your `OPENAI_API_KEY`.

```env
OPENAI_API_KEY=your_openai_api_key_here
ENVIRONMENT=development
LOG_LEVEL=INFO
```

### 2. Everyday Usage

#### Activate the Environment
Each time you open a new terminal to work on the project, you must first activate the virtual environment:

```bash
source .venv/bin/activate
```

#### Scrape Product Data (Run At Least Once)

Before starting the application, you need to populate the product database. Run the scraper service to fetch the latest data from the Vodafone UK website.

> **Note**: The first scrape may take a few minutes.

```bash
# Make sure your environment is activated before running
# Run a full scrape of all products
python scripts/scraper_service.py --force

# Or, for a quick test, limit the scrape to 5 products
python scripts/scraper_service.py --force --limit 5
```

#### Running the Application

For the best development experience, run the backend and frontend servers in two separate terminals. This provides clear, independent logs for each service.

**Terminal 1: Start the Backend**

```bash
# Make sure your environment is activated
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```
The FastAPI backend will now be running. The `--reload` flag automatically restarts the server when you make code changes.

**Terminal 2: Start the Frontend**

```bash
# Make sure your environment is activated
python frontend/server.py
```
This serves the static frontend files.

### 5. Access the Services

- **Frontend Application**: [http://localhost:3000](http://localhost:3000)
- **Backend API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Project Structure

```
conversational_sales/
├── data/
│   ├── products.json           # Scraped product data
│   └── product_embeddings.json # Embeddings for search
├── frontend/
│   ├── server.py               # Simple Python web server
│   └── static/                 # HTML, CSS, and JS files
├── logs/
│   ├── conversation.log        # General application logs
│   └── sessions/               # Individual conversation session logs
├── scripts/
│   └── scraper_service.py      # Standalone scraper script
├── src/
│   ├── main.py                 # FastAPI application entrypoint
│   ├── conversation.py         # Manages the conversation state machine and logic
│   ├── product_search.py       # Handles product searching
│   ├── data_provider.py        # Simulates fetching upsell data from a database/API
│   ├── upsell_data.py          # Contains the raw data for upsell products
│   └── models.py               # Pydantic data models
├── .env.example                # Example environment variables
├── pyproject.toml              # Poetry dependencies
└── README.md
```

## API Endpoints

The core API is documented and explorable via Swagger UI at [http://localhost:8000/docs](http://localhost:8000/docs).

- **`POST /chat`**: The main endpoint for sending and receiving messages.
- **`GET /health`**: A simple health check endpoint.
- **`GET /products/count`**: Returns the total number of products in the database.
- **`GET /products/brands`**: Returns a list of all unique product brands.

You can test the chat endpoint directly using `curl`:

```bash
curl -X POST "http://localhost:8000/chat" \
     -H "Content-Type: application/json" \
     -d '{
       "message": "Hi, I need a new phone with a good camera.",
       "session_id": "user-session-123"
     }'
```