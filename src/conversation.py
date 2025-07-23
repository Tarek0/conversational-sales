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
from .data_provider import data_provider

# Conversation states
CONVERSATION_STATE_INITIAL = "initial"
CONVERSATION_STATE_INSURANCE = "insurance_upsell"
CONVERSATION_STATE_ACCESSORIES = "accessories_upsell"
CONVERSATION_STATE_WATCH = "watch_upsell"
CONVERSATION_STATE_FINAL = "final"


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
    recommendations: List[Dict] = None
    
    def __post_init__(self):
        if self.recommendations is None:
            self.recommendations = []


class ConversationSession:
    """Manages a single conversation session"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.turns: List[ConversationTurn] = []
        self.preferences = UserPreferences()
        self.created_at = datetime.now().isoformat()
        self.memory = ConversationBufferMemory(ai_prefix="AI", memory_key="history")
        self.state = CONVERSATION_STATE_INITIAL
    
    def add_turn(self, role: str, content: str, recommendations: List[Dict] = None):
        """Add a conversation turn"""
        turn = ConversationTurn(
            timestamp=datetime.now().isoformat(),
            role=role,
            content=content,
            recommendations=recommendations or []
        )
        self.turns.append(turn)
        
        # Update session preferences if provided
        
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
        self.llm = ChatOpenAI(temperature=0.7, model_name="gpt-4o")
        self.data_provider = data_provider

    def _get_prompt_for_state(self, state: str) -> PromptTemplate:
        """Creates the prompt template for the conversation based on the state."""
        
        if state == CONVERSATION_STATE_INITIAL:
            template = """
            You are TOBI, a friendly and expert conversational sales assistant for Vodafone UK.
            Your goal is to help customers find the perfect mobile phone and tariff based on their needs and preferences.

            Key Guidelines:
            1. Be friendly, professional, and conversational.
            2. If the user's query is broad (e.g., "latest iPhone"), ask clarifying questions to narrow down the options. Avoid listing more than 2-3 products at once.
            3. Provide helpful recommendations based on their requirements.
            4. When the user selects a phone, *reinforce their choice* (e.g., "Excellent choice, the iPhone 16 Pro is a powerhouse!") before transitioning.
            5. If the user confirms they are happy with the recommendation, you MUST respond with "Great! Let's get you set up with some insurance." and nothing else.
            6. Always direct customers to specific Vodafone UK product URLs when making recommendations.
            7. If you don't have current product information, acknowledge this and suggest they check the Vodafone UK website.
            8. Keep responses concise but informative.
            9. Ask one question at a time to avoid overwhelming the customer.

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
        
        elif state == CONVERSATION_STATE_INSURANCE:
            insurance_plans = self.data_provider.get_insurance_plans()
            insurance_context = "\n".join([f"- {plan['name']} ({plan['price']}): {plan['description']}" for plan in insurance_plans.values()])

            template = f"""
            You are TOBI, a friendly and expert conversational sales assistant for Vodafone UK.
            Your current goal is to offer the customer insurance for their new device.

            Available Insurance Plans:
            {insurance_context}

            Key Guidelines:
            1. Proactively recommend a specific plan based on the user's phone choice. For premium phones, recommend the 'Loss, theft, damage and breakdown cover'.
            2. If the user chooses a plan, confirm their choice and respond with "Great! Now, let's look at some accessories for your new phone."
            3. If the user declines insurance, respond with "No problem. Let's look at some accessories for your new phone."
            4. Keep the tone helpful and not pushy. Do not start your response with a generic greeting.

            Chat History:
            {{history}}

            User: {{input}}
            AI:
            """
            return PromptTemplate(
                input_variables=["history", "input"],
                template=template
            )
            
        elif state == CONVERSATION_STATE_ACCESSORIES:
            accessories = self.data_provider.get_accessories()
            accessories_context = "\n".join(
                [f"- {acc['name']} ({acc['price']}): {acc['description']}" for acc in accessories.values()]
            )

            template = f"""
            You are TOBI, a friendly and expert conversational sales assistant for Vodafone UK.
            Your current goal is to offer the customer accessories for their new phone.

            Available Accessories:
            {accessories_context}

            Key Guidelines:
            1. Your absolute first priority is to check if the user has already said no or expressed a negative sentiment. If so, you MUST respond with "No problem. Finally, would you like to pair your new phone with a watch?" and nothing else.
            2. Proactively recommend a specific accessory that complements their new phone (e.g., a case or screen protector).
            3. If the user asks for the price, provide it from the context. Do not make up prices.
            4. If the user chooses any accessories, confirm their choice and respond with "Excellent choices! Finally, would you like to pair your new phone with a watch?"
            5. If the user declines, respond with "No problem. Finally, would you like to pair your new phone with a watch?"
            6. Keep the tone helpful and not pushy.

            Chat History:
            {{history}}

            User: {{input}}
            AI:
            """
            return PromptTemplate(
                input_variables=["history", "input"],
                template=template
            )

        elif state == CONVERSATION_STATE_WATCH:
            watches = self.data_provider.get_watches()
            watches_context = "\n".join(
                [f"- [{watch['name']}]({watch['url']}) ({watch['price']}): {watch['description']}" for watch in watches.values()]
            )

            template = f"""
            You are TOBI, a friendly and expert conversational sales assistant for Vodafone UK.
            Your current goal is to offer the customer a watch to pair with their new phone.

            Available Watches:
            {watches_context}

            Key Guidelines:
            1. Offer the watches listed above, making sure to use the markdown format to make them clickable links.
            2. If the user chooses a watch, confirm their choice and respond with "Perfect! We've added that to your order. Is there anything else I can help you with today?"
            3. If the user declines, respond with "No problem at all. Is there anything else I can help you with today?"
            4. This is the final step, so be prepared to end the conversation gracefully.

            Chat History:
            {{history}}

            User: {{input}}
            AI:
            """
            return PromptTemplate(
                input_variables=["history", "input"],
                template=template
            )

        elif state == CONVERSATION_STATE_FINAL:
            template = """
            You are TOBI, a friendly and expert conversational sales assistant for Vodafone UK.
            The user has indicated they are finished with the conversation. Your goal is to end the conversation politely and naturally.

            Key Guidelines:
            1. If the user says "no" or "that's all", respond with a friendly closing like "Thank you for chatting with me today. Have a great day!"
            2. If the user says a simple "thanks", respond with "You're welcome!".
            3. If they ask another question, answer it helpfully.
            4. Do not try to sell anything else.

            Chat History:
            {history}

            User: {input}
            AI:
            """
            return PromptTemplate(
                input_variables=["history", "input"],
                template=template
            )
            
        # Fallback to the initial prompt if state is unknown
        return self._get_prompt_for_state(CONVERSATION_STATE_INITIAL)


    def _create_chain(self, state: str) -> LLMChain:
        """Creates the LangChain conversation chain for a given state."""
        prompt = self._get_prompt_for_state(state)
        return LLMChain(
            llm=self.llm,
            prompt=prompt,
            verbose=True,
        )

    def _get_or_create_session(self, session_id: str) -> ConversationSession:
        """Retrieves or creates a conversation session for a given session ID."""
        if session_id not in self.sessions:
            self.logger.info(f"Creating new conversation session: {session_id}")
            self.sessions[session_id] = ConversationSession(session_id=session_id)
        return self.sessions[session_id]

    def _save_session_to_file(self, session: ConversationSession):
        """Saves the conversation session to a file."""
        session_data = {
            "session_id": session.session_id,
            "created_at": session.created_at,
            "state": session.state,
            "preferences": asdict(session.preferences),
            "turns": [asdict(turn) for turn in session.turns]
        }
        
        # Ensure the logs/sessions directory exists
        os.makedirs("logs/sessions", exist_ok=True)
        
        file_path = f"logs/sessions/{session.session_id}.json"
        with open(file_path, "w") as f:
            json.dump(session_data, f, indent=2)

    def process_message(self, message: str, session_id: str) -> Dict[str, Any]:
        """Processes a user message and returns the response."""
        try:
            self.logger.info(
                f"User Request: {message}",
                extra={'session_id': session_id, 'user_message': message}
            )
            
            session = self._get_or_create_session(session_id)

            # Search for relevant products only in the initial state
            recommendations = []
            product_context = "No products found matching the query."
            if session.state == CONVERSATION_STATE_INITIAL:
                recommendations = self.product_search_engine.search(message)
                if recommendations:
                    product_context = f"Available Products:\n{json.dumps(recommendations, indent=2)}"

            history = session.memory.load_memory_variables({})['history']

            # Create a chain for the current state
            chain = self._create_chain(session.state)

            # Invoke the chain with the message and product context
            response = chain.invoke({
                "input": message,
                "product_context": product_context,
                "history": history
            })
            
            response_text = response['text']

            # State transition logic
            if "Great! Let's get you set up with some insurance." in response_text:
                session.state = CONVERSATION_STATE_INSURANCE
            elif "Let's look at some accessories for your new phone." in response_text:
                session.state = CONVERSATION_STATE_ACCESSORIES
            elif "would you like to pair your new phone with a watch?" in response_text.lower():
                session.state = CONVERSATION_STATE_WATCH
            elif "Is there anything else I can help you with today?" in response_text:
                session.state = CONVERSATION_STATE_FINAL

            # Save context to memory
            session.memory.save_context({"input": message}, {"output": response_text})

            # Only associate recommendations with the turn if the response contains a product link
            logged_recommendations = []
            if re.search(r'\[.*?\]\(https?://', response_text):
                logged_recommendations = recommendations

            session.add_turn('user', message)
            session.add_turn('assistant', response_text, recommendations=logged_recommendations)

            self._save_session_to_file(session)

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