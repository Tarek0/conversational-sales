# Backend Source (`src`)

This directory contains the core backend logic for the Conversational Sales Assistant. It's a FastAPI application responsible for handling chat interactions, managing conversation state, and searching for products.

## Key Modules

-   **`main.py`**: The main entry point for the FastAPI application. It defines the API endpoints, handles application startup and shutdown events, and integrates all other modules.

-   **`conversation.py`**: The heart of the conversational logic. It manages the conversation state machine, orchestrates the interaction with the OpenAI language model, and handles the multi-step upsell journey.

-   **`product_search.py`**: Implements the product search functionality. It uses OpenAI's embeddings to perform semantic searches on the product data, allowing the assistant to find relevant products based on the user's conversational input.

-   **`scraper.py`**: Contains the `VodafoneDataScraper` class, which is responsible for scraping product information from the Vodafone UK website. This module uses Playwright to handle dynamic web content.

-   **`upsell_data.py`**: Stores the data for the upsell products (insurance, accessories, etc.). This is currently a simple in-memory data store but could be replaced with a database or external API.

-   **`data_provider.py`**: A simple data provider that simulates fetching upsell data. It's designed to be easily replaceable with a more robust data source.

-   **`models.py`**: Defines the Pydantic data models used for API request and response validation, such as `ChatRequest` and `ChatResponse`.

-   **`logging_config.py`**: Configures the application's logging, ensuring that all important events are recorded for debugging and analysis.

## Architecture

The backend is built with a decoupled architecture in mind. The `ConversationManager` in `conversation.py` is the central orchestrator, using the `ProductSearchEngine` for product lookups and the `data_provider` for upsell information. This separation of concerns makes the system easier to maintain and extend.

## Architecture Diagram

```mermaid
graph TD
    subgraph "FastAPI Application"
        main["main.py<br/>(API Entry Point)"]
    end

    subgraph "Core Logic"
        conv["ConversationManager<br/>(conversation.py)"]
        search["ProductSearchEngine<br/>(product_search.py)"]
        provider["DataProvider<br/>(data_provider.py)"]
    end

    subgraph "Data"
        upsell["upsell_data.py"]
        products["(from data/products.json)"]
    end
    
    subgraph "External Services"
        llm["OpenAI LLM"]
    end

    main -- "Receives user message via /chat" --> conv
    conv -- "1. Orchestrates response" --> llm
    conv -- "2. Searches for products" --> search
    conv -- "3. Gets upsell offers" --> provider
    search -- "Reads product data" --> products
    provider -- "Reads upsell data" --> upsell
    
    llm -- "Generates text" --> conv
    search -- "Returns results" --> conv
    provider -- "Returns data" --> conv
    
    conv -- "Returns final response" --> main
``` 