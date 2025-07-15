# TOBI - Conversational Sales Bot

A sophisticated conversational sales assistant for Vodafone UK that helps customers find the perfect mobile phone and tariff based on their needs and preferences.

## Architecture

TOBI is built with a **separated frontend and backend architecture** for maximum flexibility:

- **Backend**: Pure REST API (FastAPI) that handles conversations, product search, and data scraping
- **Frontend**: Independent web interface that consumes the backend API
- **Separation Benefits**: Easy to replace frontend with website widgets, independent deployment, better scalability

## Features

- 🤖 **AI-Powered Conversations**: Uses OpenAI GPT-3.5-turbo for natural language understanding
- 🔍 **Advanced Product Search**: Finds relevant products based on conversation context.
- 📱 **Mobile-First Design**: Responsive, modern chat interface
- 🎯 **Personalized Recommendations**: Collects user preferences and provides tailored suggestions
- 🌐 **Real-time Scraping**: Automatically gathers the latest product data from Vodafone UK
- 💾 **Session Management**: Maintains conversation context across interactions
- ⚡ **Fast API Backend**: High-performance FastAPI server with async support
- 🔗 **CORS Enabled**: Ready for integration with existing websites

## Technology Stack

- **Backend**: Python 3.9+, FastAPI, LangChain, CORS middleware
- **Frontend**: HTML5, CSS3, JavaScript (ES6+).
- **AI/ML**: OpenAI GPT-3.5-turbo.
- **Web Scraping**: Playwright.
- **Package Management**: Poetry
- **Database**: JSON files (for POC), SQLite (optional)

## Quick Start

### Prerequisites

- Python 3.9 or higher
- Poetry package manager
- OpenAI API key

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd conversational_sales
   ```

2. **Configure Poetry environment (Apple Silicon only)**
   ```bash
   # For Apple Silicon (M1/M2) users, configure Poetry to use native ARM64 Python
   # This prevents architecture compatibility issues with PyTorch/sentence-transformers
   poetry env use /opt/homebrew/bin/python3
   ```

3. **Install dependencies**
   ```bash
   poetry install
   ```

4. **Install Playwright browsers**
   ```bash
   poetry shell
   playwright install
   ```

5. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   ```

6. **Generate Product Data**
   The product search requires an initial data file. Run the scraper to create it.
   
   **Note**: The first scrape may take a few minutes.
   ```bash
   poetry run python scripts/scraper_service.py --force
   ```
   For a smaller test scrape, you can use the `--limit` flag:
   ```bash
   poetry run python scripts/scraper_service.py --force --limit 5
   ```

7. **Run the Backend Server**
   In a dedicated terminal, start the backend API:
   ```bash
   poetry run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
   ```

8. **Run the Frontend Server**
   In a second terminal, start the frontend:
   ```bash
   poetry run python frontend/server.py
   ```

9. **Access the application**:
   - **Frontend**: `http://localhost:3001`
   - **Backend API**: `http://localhost:8000`
   - **API Documentation**: `http://localhost:8000/docs`

## Environment Variables

Create a `.env` file in the project root with the following variables:

```env
OPENAI_API_KEY=your_openai_api_key_here
ENVIRONMENT=development
LOG_LEVEL=INFO
HOST=localhost
PORT=8000
```

## Project Structure

```
conversational_sales/
├── src/                     # Backend API
│   ├── __init__.py
│   ├── main.py              # FastAPI application (API only)
│   ├── conversation.py      # LangChain conversation manager
│   ├── product_search.py    # Product search engine
│   └── scraper.py          # Vodafone website scraper
├── frontend/               # Frontend application
│   ├── server.py           # Simple Python frontend server
│   └── static/
│       ├── index.html
│       ├── styles.css
│       └── script.js
├── data/                   # Data storage
│   ├── products.json       # Scraped product data
├── pyproject.toml          # Poetry configuration
└── README.md
```

## API Endpoints

### Backend API (http://localhost:8000)

- `GET /` - API information and available endpoints
- `POST /chat` - Send messages to the bot
- `GET /health` - Health check endpoint
- `GET /products/count` - Get number of products in database
- `GET /products/brands` - Get all available brands
- `GET /docs` - Interactive API documentation

### Frontend (http://localhost:3000)

- `GET /` - Main chat interface
- Static files served from `frontend/static/`

## Development

### Running Locally (Recommended)

For the best development experience, run the backend and frontend servers in separate terminals. This gives you clear, independent logs for each service.

**1. Start the Backend Server**

In your first terminal, run:
```bash
poetry run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```
This will start the FastAPI backend. The `--reload` flag automatically restarts the server when you make code changes.

**2. Start the Frontend Server**

In a second terminal, run:
```bash
poetry run python frontend/server.py
```
This will serve the static frontend files on `http://localhost:3001`.

**3. Access the Application**
- **Frontend**: `http://localhost:3001`
- **Backend API**: `http://localhost:8000`
- **API Docs**: `http://localhost:8000/docs`

### API Integration

The backend API can be integrated with any frontend. Configure the API base URL in your frontend:

```javascript
const API_BASE_URL = 'http://localhost:8000';
```

### Sample API Usage

**Chat with the bot:**
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I need a new phone with unlimited data",
    "session_id": "test-session-123"
  }'
```

**Get product information:**
```bash
curl "http://localhost:8000/products/count"
curl "http://localhost:8000/products/brands"
```

### Data Scraping

The scraper service is a standalone script for gathering product data from the Vodafone UK website.

**Run a full scrape:**
This will scrape all available products and save them to `data/products.json`.
```bash
poetry run python scripts/scraper_service.py --force
```

**Run a limited scrape:**
For testing, you can limit the number of products scraped:
```bash
poetry run python scripts/scraper_service.py --force --limit 10
```

**Scraper status:**
To check the status of the scraped data without running a new scrape:
```bash
poetry run python scripts/scraper_service.py --status
```

### Testing

You can test the API endpoints using `curl`.

```bash
# Test the API endpoints
curl http://localhost:8000/health

# Test chat functionality
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "session_id": "test-session"}'
```

### Widget Integration

To replace the frontend with a website widget:

1. **Use the Backend API**: The backend is completely independent
2. **Configure API URL**: Set the backend URL in your widget
3. **Implement Chat Interface**: Use the `/chat` endpoint for conversations
4. **Handle Recommendations**: Process the recommendations array from API responses

#### Example Widget Integration

```javascript
// In your website widget
const TOBI_API_URL = 'http://localhost:8000';

async function sendMessage(message, sessionId) {
    const response = await fetch(`${TOBI_API_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            message: message,
            session_id: sessionId
        })
    });
    
    const data = await response.json();
    return {
        response: data.response,
        recommendations: data.recommendations
    };
}
```

### Testing

```bash
# Test the API endpoints
curl http://localhost:8000/health

# Test chat functionality
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "session_id": "test-session"}'
```

### Data Scraping

The scraper service is a standalone script for gathering product data from the Vodafone UK website.

**Run a full scrape:**
This will scrape all available products and save them to `data/products.json`.
```bash
poetry run python scripts/scraper_service.py --force
```

**Run a limited scrape:**
For testing, you can limit the number of products scraped:
```bash
poetry run python scripts/scraper_service.py --force --limit 10
```

**Scraper status:**
To check the status of the scraped data without running a new scrape:
```bash
poetry run python scripts/scraper_service.py --status
```

### Testing

You can test the API endpoints using `curl`.

```bash
# Test the API endpoints
curl http://localhost:8000/health

# Test chat functionality
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "session_id": "test-session"}'
```