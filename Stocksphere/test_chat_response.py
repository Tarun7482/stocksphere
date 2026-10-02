import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()

# First import Flask app to set up the context
from app import app, db

# Use a Flask application context
with app.app_context():
    from models import User, ChatSession
    from chatbot import generate_response, get_or_create_chat_session
    
    # Ensure we have at least one user
    user = User.query.filter_by(username='demo').first()
    if not user:
        # Create demo user if it doesn't exist
        user = User(username='demo', email='demo@example.com')
        user.set_password('demo123')
        db.session.add(user)
        db.session.commit()
        print(f"Created demo user with ID: {user.id}")
    else:
        print(f"Using existing demo user with ID: {user.id}")
    
    # Create or get a chat session for this user
    chat_session = get_or_create_chat_session(user.id)
    print(f"Using chat session ID: {chat_session.id}")
    
    # Test message
    test_message = "Hello, tell me about the stock market"
    
    # Call the function directly
    try:
        print(f"Calling generate_response with: {test_message}")
        response, session_id = generate_response(test_message, [], chat_session.id)
        print(f"Response received from session {session_id}: {response[:100]}...")
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc() 