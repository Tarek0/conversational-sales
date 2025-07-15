import os
import json
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

# OpenAI/LangChain are required dependencies
try:
    from langchain_openai import ChatOpenAI
    from langchain.memory import ConversationBufferMemory
    from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
    from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
    from langchain.chains import LLMChain
    import openai
    from dotenv import load_dotenv
    load_dotenv()
except ImportError as e:
    raise ImportError(
        f"Required dependencies missing: {e}\n"
        "This is a conversational AI sales bot that requires OpenAI integration.\n"
        "Install with: poetry add openai langchain python-dotenv"
    )

# OpenAI API key is required
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError(
        "OPENAI_API_KEY environment variable is required!\n"
        "This conversational sales bot requires OpenAI API access.\n"
        "Set your API key in the .env file: OPENAI_API_KEY=your_key_here"
    )

from .product_search import ProductSearchEngine
from .logging_config import setup_logging


@dataclass
class UserPreferences:
    """User preferences for phone recommendations"""
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    brand_preference: Optional[str] = None
    storage_preference: Optional[str] = None
    data_usage: Optional[str] = None
    contract_length: Optional[str] = None
    features: List[str] = None
    
    def __post_init__(self):
        if self.features is None:
            self.features = []


@dataclass
class ConversationTurn:
    """A single conversation turn"""
    timestamp: str
    role: str  # 'user' or 'assistant'
    content: str
    preferences_extracted: Optional[UserPreferences] = None
    recommendations: List[Dict] = None
    
    def __post_init__(self):
        if self.recommendations is None:
            self.recommendations = []


class ConversationSession:
    """Manages a single conversation session"""
    
    def __init__(self, session_id: str, chain: LLMChain):
        self.session_id = session_id
        self.turns: List[ConversationTurn] = []
        self.preferences = UserPreferences()
        self.created_at = datetime.now().isoformat()
        self.chain = chain
        self.memory = ConversationBufferMemory(ai_prefix="AI", memory_key="history")
        
    def add_turn(self, role: str, content: str, preferences: Optional[UserPreferences] = None, 
                 recommendations: List[Dict] = None):
        """Add a conversation turn"""
        turn = ConversationTurn(
            timestamp=datetime.now().isoformat(),
            role=role,
            content=content,
            preferences_extracted=preferences,
            recommendations=recommendations or []
        )
        self.turns.append(turn)
        
        # Update session preferences if provided
        if preferences:
            self.preferences = preferences
            
    def get_context(self, max_turns: int = 10) -> List[Dict]:
        """Get recent conversation context"""
        recent_turns = self.turns[-max_turns:]
        return [{"role": turn.role, "content": turn.content} for turn in recent_turns]
        
    def get_last_user_message(self) -> Optional[str]:
        """Get the last user message"""
        for turn in reversed(self.turns):
            if turn.role == "user":
                return turn.content
        return None


class ConversationManager:
    """Manages the conversation state and logic."""

    def __init__(self, product_search_engine: ProductSearchEngine):
        """
        Initializes the ConversationManager.
        - product_search_engine: An instance of ProductSearchEngine.
        """
        self.product_search_engine = product_search_engine
        self.sessions: Dict[str, ConversationSession] = {}
        self.logger = logging.getLogger(__name__)
        self.prompt_template = self._create_prompt_template()
        self.llm = ChatOpenAI(temperature=0.7, model_name="gpt-3.5-turbo")
        self.chain = self._create_chain()

    def _create_prompt_template(self) -> PromptTemplate:
        """Creates the prompt template for the conversation."""
        template = """
        You are TOBI, a friendly and expert conversational sales assistant for Vodafone UK.
        Your goal is to help customers find the perfect mobile phone and tariff based on their needs and preferences.

        Key Guidelines:
        1. Be friendly, professional, and conversational
        2. Ask relevant questions to understand customer needs (budget, usage, brand preferences, etc.)
        3. Provide helpful recommendations based on their requirements
        4. Always direct customers to specific Vodafone UK product URLs when making recommendations
        5. If you don't have current product information, acknowledge this and suggest they check the Vodafone UK website
        6. Keep responses concise but informative
        7. Ask one question at a time to avoid overwhelming the customer

        Current conversation goal: Understand the customer's mobile phone needs and guide them to the right product.

        Here is some context on products that may be relevant to the user's query:
        {product_context}

        If you recommend products, you MUST use the format:
        [Product Name](Product URL)

        Chat History:
        {history}

        User: {input}
        AI:
        """
        return PromptTemplate(
            input_variables=["history", "input", "product_context"],
            template=template
        )

    def _create_chain(self) -> LLMChain:
        """Creates the LangChain conversation chain."""
        return LLMChain(
            llm=self.llm,
            prompt=self.prompt_template,
            verbose=True,
        )

    def _get_or_create_session(self, session_id: str) -> ConversationSession:
        """Retrieves or creates a conversation session for a given session ID."""
        if session_id not in self.sessions:
            self.logger.info(f"Creating new conversation session: {session_id}")
            self.sessions[session_id] = ConversationSession(session_id=session_id, chain=self.chain)
        return self.sessions[session_id]

    def process_message(self, message: str, session_id: str) -> Dict[str, Any]:
        """Processes a user message and returns the response."""
        try:
            self.logger.info(
                f"User Request: {message}",
                extra={'session_id': session_id, 'user_message': message}
            )
            
            session = self._get_or_create_session(session_id)

            # Search for relevant products
            recommendations = self.product_search_engine.search(message)
            product_context = f"Available Products:\n{json.dumps(recommendations, indent=2)}" if recommendations else "No products found matching the query."

            history = session.memory.load_memory_variables({})['history']

            # Invoke the chain with the message and product context
            response = session.chain.invoke({
                "input": message,
                "product_context": product_context,
                "history": history
            })
            
            response_text = response['text']

            # Save context to memory
            session.memory.save_context({"input": message}, {"output": response_text})

            session.add_turn('user', message)
            session.add_turn('assistant', response_text, recommendations=recommendations)

            result = {
                "response": response_text,
                "recommendations": recommendations
            }

            self.logger.info(
                "LLM Response",
                extra={'session_id': session_id, 'llm_response': response_text, 'recommendations': recommendations}
            )
            return result

        except Exception as e:
            self.logger.error(f"Error in process_message for session {session_id}: {e}", exc_info=True)
            return {"response": "Sorry, I encountered an error. Please try again."}
        
    def get_session_info(self, session_id: str) -> Dict:
        """Get information about a conversation session"""
        if session_id not in self.sessions:
            return {"error": "Session not found"}
            
        session = self.sessions[session_id]
        return {
            "session_id": session_id,
            "created_at": session.created_at,
            "turns": len(session.turns),
            "preferences": asdict(session.preferences)
        } 