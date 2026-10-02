import os
import logging
import json
import requests
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from models import ChatSession, ChatMessage, StockMetadata, Portfolio
from app import db

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create a system prompt that contains background context about StockSphere
SYSTEM_PROMPT = """
You are StockSphere AI Assistant, a financial advisor chatbot built into the StockSphere trading platform.
You help users understand their portfolio, provide trading insights, and answer questions about stocks and investing.
Use the user's portfolio data to provide personalized insights when available.
Keep your responses concise, informative, and focused on financial topics.
Avoid making definitive trading recommendations - instead, present options and their potential implications.
Base your advice on the following data when available:
1. User's portfolio composition and performance
2. Historical stock price data and trends
3. General market conditions and news
4. Financial knowledge and best practices

When the user asks about a specific stock in their portfolio, provide detailed analysis.
"""

# Default model configuration
DEFAULT_CONFIG = {
    "temperature": 0.2,
    "top_p": 0.95,
    "max_tokens": 1024,
}

class LLMProvider:
    """Base class for LLM providers"""
    
    def __init__(self, model_name: str = "default", **kwargs):
        self.model_name = model_name
        self.config = DEFAULT_CONFIG.copy()
        self.config.update(kwargs)
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embeddings for the given text"""
        # Should be implemented by subclasses
        raise NotImplementedError
    
    def generate_completion(self, messages: List[Dict[str, str]]) -> str:
        """Generate a completion for the given messages"""
        # Should be implemented by subclasses
        raise NotImplementedError


class OllamaProvider(LLMProvider):
    """Provider for Ollama API"""
    
    def __init__(self, model_name: str = "llama3.2:latest", base_url: str = "http://localhost:11434", **kwargs):
        super().__init__(model_name, **kwargs)
        self.base_url = base_url
        # Connect to the Ollama API
        try:
            # Test connection
            response = requests.get(f"{self.base_url}/api/version")
            if response.status_code == 200:
                logger.info(f"Connected to Ollama API: {response.json()}")
            else:
                logger.warning(f"Could not connect to Ollama API: {response.status_code}")
        except Exception as e:
            logger.error(f"Error connecting to Ollama API: {str(e)}")
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embeddings using Ollama"""
        try:
            response = requests.post(
                f"{self.base_url}/api/embeddings",
                json={"model": self.model_name, "prompt": text}
            )
            if response.status_code == 200:
                return response.json().get("embedding", [])
            else:
                logger.error(f"Embedding error: {response.status_code} - {response.text}")
                return []
        except Exception as e:
            logger.error(f"Error generating embedding with Ollama: {str(e)}")
            return []
    
    def generate_completion(self, messages: List[Dict[str, str]]) -> str:
        """Generate a completion using Ollama"""
        try:
            # Format messages for Ollama
            prompt = ""
            for message in messages:
                role = message.get("role", "user")
                content = message.get("content", "")
                
                if role == "system":
                    prompt += f"System: {content}\n\n"
                elif role == "user":
                    prompt += f"User: {content}\n\n"
                elif role == "assistant":
                    prompt += f"Assistant: {content}\n\n"
            
            # Add the final assistant prompt
            prompt += "Assistant: "
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "temperature": self.config.get("temperature", 0.2),
                    "top_p": self.config.get("top_p", 0.95),
                    "max_tokens": self.config.get("max_tokens", 1024),
                    "stream": False
                }
            )
            
            if response.status_code == 200:
                return response.json().get("response", "")
            else:
                logger.error(f"Completion error: {response.status_code} - {response.text}")
                return "Sorry, I encountered an error generating a response."
        except Exception as e:
            logger.error(f"Error generating completion with Ollama: {str(e)}")
            return f"Sorry, I encountered an error: {str(e)}"


# You can add other providers here in the future
# class OpenAIProvider(LLMProvider):
#     def __init__(self, api_key, model_name="gpt-4o", **kwargs):
#         super().__init__(model_name, **kwargs)
#         # Implementation for OpenAI


# Factory function to get the right provider
def get_llm_provider(provider_name: str = "ollama", **kwargs) -> LLMProvider:
    """Get the appropriate LLM provider based on configuration"""
    if provider_name.lower() == "ollama":
        return OllamaProvider(**kwargs)
    # elif provider_name.lower() == "openai":
    #     return OpenAIProvider(**kwargs)
    else:
        logger.warning(f"Unknown provider {provider_name}, using Ollama as fallback")
        return OllamaProvider(**kwargs)


class RAGEngine:
    """Retrieval-Augmented Generation engine for financial context"""
    
    def __init__(self, llm_provider: LLMProvider):
        self.llm_provider = llm_provider
    
    def get_stock_metadata(self, symbol: str) -> Optional[StockMetadata]:
        """Get stock metadata from the database or fetch it if not available"""
        metadata = StockMetadata.query.filter_by(symbol=symbol).first()
        
        if not metadata:
            # Fetch metadata and store it
            try:
                from stock_data import get_stock_data
                stock_info = get_stock_data(symbol)
                
                metadata = StockMetadata(
                    symbol=symbol,
                    name=stock_info.get('name', ''),
                    sector=stock_info.get('sector', ''),
                    industry=stock_info.get('industry', ''),
                    description=stock_info.get('description', '')
                )
                
                # Generate and store embedding
                if metadata.description:
                    embedding = self.llm_provider.generate_embedding(metadata.description)
                    metadata.set_embedding(embedding)
                
                db.session.add(metadata)
                db.session.commit()
                logger.debug(f"Created new stock metadata for {symbol}")
            except Exception as e:
                logger.error(f"Error fetching stock metadata for {symbol}: {str(e)}")
                return None
        
        return metadata
    
    def format_portfolio_for_context(self, portfolio_data: List[Portfolio]) -> str:
        """Format portfolio data as context for the chatbot"""
        portfolio_context = "User Portfolio:\n"
        
        if not portfolio_data:
            return "User Portfolio: No stocks in portfolio."
        
        # Format the portfolio data
        total_value = 0
        for item in portfolio_data:
            try:
                from stock_data import get_stock_data
                stock_info = get_stock_data(item.symbol)
                current_price = stock_info.get('price', item.average_price)
                position_value = item.quantity * current_price
                total_value += position_value
                
                # Get additional metadata
                metadata = self.get_stock_metadata(item.symbol)
                company_name = metadata.name if metadata else ""
                sector = metadata.sector if metadata else ""
                
                portfolio_context += (
                    f"- {item.symbol} ({company_name}): {item.quantity} shares at avg. price "
                    f"₹{item.average_price:.2f}, current price ₹{current_price:.2f}, "
                    f"total value ₹{position_value:.2f}, sector: {sector}\n"
                )
            except Exception as e:
                logger.error(f"Error formatting portfolio item {item.symbol}: {str(e)}")
                portfolio_context += f"- {item.symbol}: {item.quantity} shares at avg. price ₹{item.average_price:.2f}\n"
        
        portfolio_context += f"\nTotal Portfolio Value: ₹{total_value:.2f}"
        return portfolio_context

    def get_relevant_market_data(self) -> str:
        """Get relevant market data for context"""
        try:
            from stock_data import get_market_summary
            market_data = get_market_summary()
            if not market_data:
                return ""
            
            market_context = "Current Market Conditions:\n"
            # Make sure market_data is a dictionary
            if isinstance(market_data, dict):
                for index, data in market_data.items():
                    market_context += f"- {index}: {data.get('price', 0):.2f} ({data.get('change', 0):.2f}%)\n"
            
            return market_context
        except Exception as e:
            logger.error(f"Error getting market data: {str(e)}")
            return ""
    
    def build_context(self, user_id: int, portfolio_data: List[Portfolio], query: str) -> str:
        """Build context for RAG from portfolio and market data"""
        # Get portfolio context
        portfolio_context = self.format_portfolio_for_context(portfolio_data)
        
        # Get market context
        market_context = self.get_relevant_market_data()
        
        # Combined context
        context = f"{portfolio_context}\n\n{market_context}"
        
        # If query mentions specific stocks, add more details
        mentioned_symbols = self.extract_stock_symbols(query, portfolio_data)
        if mentioned_symbols:
            stock_details = self.get_stock_details(mentioned_symbols)
            if stock_details:
                context += f"\n\nDetailed Stock Information:\n{stock_details}"
        
        return context
    
    def extract_stock_symbols(self, query: str, portfolio_data: List[Portfolio]) -> List[str]:
        """Extract stock symbols mentioned in the query"""
        # Simple extraction based on portfolio items
        symbols = []
        for item in portfolio_data:
            if item.symbol.lower() in query.lower():
                symbols.append(item.symbol)
        
        return symbols
    
    def get_stock_details(self, symbols: List[str]) -> str:
        """Get detailed information about specific stocks"""
        stock_details = ""
        
        for symbol in symbols:
            try:
                from stock_data import get_stock_data
                stock_info = get_stock_data(symbol)
                metadata = self.get_stock_metadata(symbol)
                
                if stock_info and metadata:
                    stock_details += f"Stock: {symbol} ({metadata.name})\n"
                    stock_details += f"Price: ₹{stock_info.get('price', 0):.2f}\n"
                    stock_details += f"Change: {stock_info.get('change', 0):.2f}%\n"
                    stock_details += f"52-week High: ₹{stock_info.get('year_high', 0):.2f}\n"
                    stock_details += f"52-week Low: ₹{stock_info.get('year_low', 0):.2f}\n"
                    stock_details += f"Sector: {metadata.sector}\n"
                    stock_details += f"Industry: {metadata.industry}\n"
                    stock_details += f"Description: {metadata.description[:200]}...\n\n"
            except Exception as e:
                logger.error(f"Error getting details for {symbol}: {str(e)}")
        
        return stock_details


def get_or_create_chat_session(user_id: int) -> ChatSession:
    """Get the active chat session for a user or create a new one"""
    # Look for an active session
    session = ChatSession.query.filter_by(user_id=user_id, active=True).order_by(ChatSession.last_updated.desc()).first()
    
    if not session:
        # Create a new session
        session = ChatSession(user_id=user_id, active=True)
        db.session.add(session)
        db.session.commit()
        logger.debug(f"Created new chat session {session.id} for user {user_id}")
    
    return session


def store_message(session_id: int, is_user: bool, content: str, model_name: str = "") -> ChatMessage:
    """Store a message in the database"""
    message = ChatMessage(
        session_id=session_id,
        is_user=is_user,
        content=content,
        model_name=model_name
    )
    
    db.session.add(message)
    db.session.commit()
    logger.debug(f"Stored new message {message.id} in session {session_id}")
    
    return message


def generate_response(user_message: str, portfolio_data: List[Portfolio] = [], session_id: int = 0) -> Tuple[str, int]:
    """Generate a response using RAG and the LLM"""
    logger.debug(f"Starting generate_response with message: {user_message[:50]}...")
    
    try:
        # Get LLM provider
        llm_provider = get_llm_provider()
        
        # Initialize RAG engine
        rag_engine = RAGEngine(llm_provider)
        
        # Get or create chat session if not provided
        if session_id > 0:
            chat_session = ChatSession.query.get(session_id)
            if not chat_session:
                logger.error(f"Chat session {session_id} not found")
                # Create a fallback session
                fallback_session = get_or_create_chat_session(1)  # Default to user ID 1 
                return "Sorry, there was an error retrieving your chat history.", fallback_session.id
        else:
            # If no session ID provided, create a new session
            fallback_session = get_or_create_chat_session(1)  # Default to user ID 1
            return "Sorry, there was an error with the chat session.", fallback_session.id
        
        # Update session timestamp
        chat_session.last_updated = datetime.utcnow()
        db.session.commit()
        
        # Store user message
        store_message(chat_session.id, True, user_message)
        
        # Build context with RAG
        context = rag_engine.build_context(chat_session.user_id, portfolio_data, user_message)
        
        # Get previous messages for context (limit to last 10)
        previous_messages = ChatMessage.query.filter_by(session_id=chat_session.id).order_by(ChatMessage.timestamp.desc()).limit(10).all()
        previous_messages.reverse()  # Get in chronological order
        
        # Build messages for LLM
        messages = [
            {"role": "system", "content": f"{SYSTEM_PROMPT}\n\nContext Information:\n{context}"}
        ]
        
        # Add previous messages
        for msg in previous_messages:
            role = "user" if msg.is_user else "assistant"
            messages.append({"role": role, "content": msg.content})
        
        # Generate response
        response_text = llm_provider.generate_completion(messages)
        
        # Store AI response
        store_message(chat_session.id, False, response_text, llm_provider.model_name)
        
        return response_text, chat_session.id
    
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}", exc_info=True)
        return f"Sorry, I encountered an error: {str(e)}", session_id