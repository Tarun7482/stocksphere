from datetime import datetime
from db import db
# noqa: The following import may cause linter errors but is needed for runtime
from flask_login import UserMixin  # noqa
from werkzeug.security import generate_password_hash, check_password_hash
import json

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    funds = db.Column(db.Float, default=100000.0)  # Starting with 100K for mock trading
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    watchlists = db.relationship('Watchlist', backref='user', lazy=True)
    portfolios = db.relationship('Portfolio', backref='user', lazy=True)
    orders = db.relationship('Order', backref='user', lazy=True)
    chat_sessions = db.relationship('ChatSession', backref='user', lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
        
    def __repr__(self):
        return f'<User {self.username}>'


class Watchlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(64), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    stocks = db.relationship('WatchlistItem', backref='watchlist', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Watchlist {self.name}>'


class WatchlistItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    watchlist_id = db.Column(db.Integer, db.ForeignKey('watchlist.id'), nullable=False)
    symbol = db.Column(db.String(20), nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<WatchlistItem {self.symbol}>'


class Portfolio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    symbol = db.Column(db.String(20), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    average_price = db.Column(db.Float, nullable=False)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Portfolio {self.symbol} - {self.quantity}>'


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    symbol = db.Column(db.String(20), nullable=False)
    order_type = db.Column(db.String(10), nullable=False)  # BUY or SELL
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(15), nullable=False, default='COMPLETED')  # PENDING, COMPLETED, CANCELLED
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Order {self.symbol} {self.order_type} {self.quantity}>'


class ChatSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    active = db.Column(db.Boolean, default=True)
    messages = db.relationship('ChatMessage', backref='session', lazy=True, cascade="all, delete-orphan", order_by="ChatMessage.timestamp")
    # Store context data for RAG
    context_data = db.Column(db.Text, nullable=True)
    
    def __init__(self, user_id, active=True):
        self.user_id = user_id
        self.active = active
    
    def to_dict(self):
        return {
            'id': self.id,
            'created_at': self.created_at.isoformat(),
            'last_updated': self.last_updated.isoformat(),
            'messages': [msg.to_dict() for msg in self.messages.all()]
        }
    
    def __repr__(self):
        return f'<ChatSession {self.id} user_id={self.user_id}>'


class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('chat_session.id'), nullable=False)
    is_user = db.Column(db.Boolean, default=True)  # True for user messages, False for AI responses
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    # To store the model that generated this response
    model_name = db.Column(db.String(50), nullable=True)
    
    def __init__(self, session_id, is_user, content, model_name=None):
        self.session_id = session_id
        self.is_user = is_user
        self.content = content
        self.model_name = model_name
    
    def to_dict(self):
        return {
            'id': self.id,
            'is_user': self.is_user,
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'model_name': self.model_name
        }
    
    def __repr__(self):
        return f'<ChatMessage {self.id} is_user={self.is_user}>'


class StockMetadata(db.Model):
    """Store stock metadata for RAG context"""
    def __init__(self, symbol, name, sector, industry, description):
        self.symbol = symbol
        self.name = name
        self.sector = sector
        self.industry = industry
        self.description = description
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=True)
    sector = db.Column(db.String(100), nullable=True)
    industry = db.Column(db.String(100), nullable=True)
    description = db.Column(db.Text, nullable=True)
    # Store precomputed embeddings as text (JSON serialized)
    embedding = db.Column(db.Text, nullable=True)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_embedding(self, embedding_vector):
        """Store embedding vector as JSON string"""
        self.embedding = json.dumps(embedding_vector)
    
    def get_embedding(self):
        """Return embedding vector from JSON string"""
        if self.embedding:
            return json.loads(self.embedding)
        return None
    
    def __repr__(self):
        return f'<StockMetadata {self.symbol}>'
