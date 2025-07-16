# TOBI: Conversational Sales Bot Development Guide for Cursor (with Generative AI)

This guide outlines the development of a Proof of Concept (POC) for TOBI, a conversational sales bot for Vodafone UK, leveraging Generative AI.

## Project Goal

Develop a conversational bot that guides Vodafone UK customers to the most appropriate mobile phone and tariff, culminating in directing them to the relevant device URL.

## Target Platform

Vodafone UK website (https://www.vodafone.co.uk/mobile/phones/pay-monthly-contracts)

## Technology Stack

* **Frontend:** Simple HTML/CSS/JavaScript with a lightweight chatbot UI (or build custom chat interface).
* **Backend:** Python with FastAPI.
* **Conversation Management:** LangChain with ConversationBufferMemory for context management + OpenAI function calling for structured interactions.
* **Data Scraping:** Playwright (recommended for dynamic content and JavaScript rendering) or BeautifulSoup + Requests as fallback for static content.
* **Database (Optional):** SQLite or simple JSON files for POC.
* **Generative AI Model:** OpenAI GPT-3.5-turbo or GPT-4 via OpenAI API.
* **LLM Framework:** LangChain for conversation chains, memory management, and prompt templates.
* **Vector Database (Optional):** Faiss (local, no external service) or simple similarity search using sentence-transformers.

## Key Python Packages for POC (using Poetry)

Create a `pyproject.toml` file with the following dependencies:

```toml
[tool.poetry]
name = "tobi-conversational-sales"
version = "0.1.0"
description = "Conversational Sales Bot for Vodafone UK"
authors = ["Your Name <your.email@example.com>"]

[tool.poetry.dependencies]
python = "^3.9"
fastapi = "^0.104.1"
uvicorn = "^0.24.0"
langchain = "^0.0.350"
openai = "^1.3.0"
playwright = "^1.40.0"
beautifulsoup4 = "^4.12.2"
requests = "^2.31.0"
sentence-transformers = "^2.2.2"
faiss-cpu = "^1.7.4"
pydantic = "^2.5.0"
python-dotenv = "^1.0.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.0"
black = "^23.10.0"
flake8 = "^6.0.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

**Setup Commands:**
```bash
poetry install
poetry shell
playwright install  # Install browser binaries
```

## Development Steps

### A. Data Acquisition and Preprocessing

- [x] **Web Scraping:** Extract device data (name, URL, price, storage, data allowance, contract length, etc.) from the Vodafone UK website using Playwright (recommended for handling dynamic content and JavaScript rendering).
- [x] **Data Cleaning and Formatting:** Structure the scraped data into a usable format (JSON files for POC).
- [x] **Embedding Creation:** Generate embeddings for each product using OpenAI's text-embedding-ada-002 or sentence-transformers models.

### B. Conversational Flow Design

- [x] **Prompt Engineering:** Craft effective prompts and prompt templates using LangChain for dynamic and context-aware responses.
- [x] **Context Management:** Use LangChain's ConversationBufferMemory to maintain conversation context and user preferences.
- [ ] **Function Calling:** Implement OpenAI function calling for structured data collection (budget, preferences, usage patterns).
- [ ] **Fallback Handling:** Design fallback mechanisms for inappropriate or irrelevant LLM responses using LangChain's output parsers.

### C. Backend API Development (Python)

- [x] **LangChain Setup:** Set up LangChain with OpenAI integration for conversation management.
- [x] **Conversation Chain:** Create a conversation chain with memory using LangChain's ConversationChain.
- [ ] **Function Calling:** Implement OpenAI function calling for structured user preference collection.
- [ ] **Vector Database Integration (Optional):** Integrate Faiss for semantic search or use simple similarity matching with sentence-transformers.
- [x] **Dynamic Response Generation:** Use LangChain prompt templates and chains for context-aware responses.
- [x] **Semantic Search:** Implement product similarity search using embeddings (OpenAI text-embedding-ada-002 or sentence-transformers).
- [x] **Recommendation Logic:** Combine user preferences collected via function calling with semantic search results.

### D. Frontend Development

- [x] **User Interface:** Create a simple chat interface using HTML, CSS, and JavaScript.
- [x] **API Integration:** Connect the frontend to the backend API.
- [x] **Displaying Recommendations:** Display the recommended device URL clearly.

### E. Testing and Refinement

1. **LLM Response Evaluation:** Evaluate LLM responses for accuracy, relevance, and appropriateness.
2. **Bias Detection and Mitigation:** Test for and mitigate potential biases in LLM responses.
3. **A/B Testing:** Experiment with different prompts and conversational flows.

### F. Deployment (Optional)

Consider deploying the backend API to a platform like Heroku or PythonAnywhere.


## Specific Instructions for Cursor

* **Prioritize a functional POC with minimal dependencies.**
* **Focus on a clear and effective conversational flow using LangChain.**
* **Leverage LangChain's ConversationChain and memory management for context.**
* **Use OpenAI function calling for structured user preference collection.**
* **Prioritize prompt engineering with LangChain's prompt templates.**
* **Implement simple local vector search (Faiss) or similarity matching.**
* **Keep data storage simple (JSON files or SQLite) for POC.**
* **Address ethical implications of LLM use (bias, inappropriate content).**
* **Document LLM integration and prompt engineering strategies.**
* **Use Python wherever possible with minimal external services.**
* **Provide clear instructions for running the application locally.**

This guide provides a roadmap for developing TOBI.  Iterate and refine based on user feedback for the best possible user experience.  Continuous monitoring and refinement are crucial when working with LLMs.