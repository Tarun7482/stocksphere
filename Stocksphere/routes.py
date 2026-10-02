from flask import render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from app import app, db
from models import User, Watchlist, WatchlistItem, Portfolio, Order, ChatSession, ChatMessage
import stock_data  # Import the entire module to avoid shadowing in local scope
from stock_data import get_market_summary, search_stocks, get_stock_historical_data

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Login unsuccessful. Please check your username and password.', 'danger')
    
    return render_template('login.html', title='Login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('register'))
        
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Please choose a different one.', 'danger')
            return redirect(url_for('register'))
        
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            flash('Email already in use. Please use a different one.', 'danger')
            return redirect(url_for('register'))
        
        user = User(username=username, email=email)
        user.set_password(password)
        
        # Create default watchlist
        default_watchlist = Watchlist(name="Default", user=user)
        
        # Add some default stocks to watchlist
        for symbol in ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']:
            default_watchlist.stocks.append(WatchlistItem(symbol=symbol))
        
        db.session.add(user)
        db.session.add(default_watchlist)
        db.session.commit()
        
        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', title='Register')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Get market summary
    market_summary = get_market_summary()
    
    # Get user's watchlist
    watchlists = current_user.watchlists
    default_watchlist = None
    if watchlists:
        default_watchlist = watchlists[0]
        
    # Get portfolio value
    portfolio = Portfolio.query.filter_by(user_id=current_user.id).all()
    portfolio_value = 0
    for item in portfolio:
        current_price = stock_data.get_stock_data(item.symbol)['price']
        portfolio_value += current_price * item.quantity
    
    # Make stock data functions available in the template
    get_stock_data = stock_data.get_stock_data
    get_top_gainers_losers = stock_data.get_top_gainers_losers
    
    return render_template('dashboard.html', 
                           title='Dashboard', 
                           market_summary=market_summary,
                           default_watchlist=default_watchlist,
                           portfolio_value=portfolio_value,
                           available_funds=current_user.funds,
                           get_stock_data=get_stock_data,
                           get_top_gainers_losers=get_top_gainers_losers)

@app.route('/watchlist')
@login_required
def watchlist():
    watchlists = current_user.watchlists
    
    # If no watchlist exists, create a default one
    if not watchlists:
        default_watchlist = Watchlist(name="Default", user=current_user)
        db.session.add(default_watchlist)
        db.session.commit()
        watchlists = [default_watchlist]
    
    # Get stock data for the first watchlist
    stocks_data = []
    active_watchlist = watchlists[0]
    
    for item in active_watchlist.stocks:
        try:
            stock_info = stock_data.get_stock_data(item.symbol)
            stocks_data.append(stock_info)
        except Exception as e:
            app.logger.error(f"Error fetching data for {item.symbol}: {e}")
    
    return render_template('watchlist.html', 
                           title='Watchlist', 
                           watchlists=watchlists,
                           active_watchlist=active_watchlist,
                           stocks_data=stocks_data)

@app.route('/api/watchlist/add', methods=['POST'])
@login_required
def add_to_watchlist():
    data = request.json
    watchlist_id = data.get('watchlist_id')
    symbol = data.get('symbol')
    
    if not symbol:
        return jsonify({'success': False, 'message': 'Symbol is required'}), 400
    
    # Handle case where watchlist_id is empty or not an integer
    try:
        if not watchlist_id or watchlist_id == '':
            # Get the default watchlist or first available one
            watchlist = Watchlist.query.filter_by(user_id=current_user.id).first()
            if not watchlist:
                # Create a default watchlist if none exists
                watchlist = Watchlist(name="Default", user=current_user)
                db.session.add(watchlist)
                db.session.commit()
        else:
            watchlist_id = int(watchlist_id)
            watchlist = Watchlist.query.get(watchlist_id)
            
        if not watchlist or watchlist.user_id != current_user.id:
            return jsonify({'success': False, 'message': 'Watchlist not found'}), 404
        
        # Check if symbol already exists
        existing = WatchlistItem.query.filter_by(watchlist_id=watchlist.id, symbol=symbol).first()
        if existing:
            return jsonify({'success': False, 'message': 'Symbol already in watchlist'}), 400
        
        item = WatchlistItem(watchlist_id=watchlist.id, symbol=symbol)
        db.session.add(item)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Symbol added to watchlist'})
    except Exception as e:
        app.logger.error(f"Error adding to watchlist: {e}")
        return jsonify({'success': False, 'message': 'Error adding to watchlist'}), 500

@app.route('/api/watchlist/remove', methods=['POST'])
@login_required
def remove_from_watchlist():
    data = request.json
    watchlist_id = data.get('watchlist_id')
    symbol = data.get('symbol')
    
    try:
        if not watchlist_id or watchlist_id == '':
            # Default to first watchlist if ID is not provided
            watchlist = Watchlist.query.filter_by(user_id=current_user.id).first()
            if not watchlist:
                return jsonify({'success': False, 'message': 'No watchlist found'}), 404
        else:
            watchlist_id = int(watchlist_id)
            watchlist = Watchlist.query.get(watchlist_id)
        
        if not watchlist or watchlist.user_id != current_user.id:
            return jsonify({'success': False, 'message': 'Watchlist not found'}), 404
        
        item = WatchlistItem.query.filter_by(watchlist_id=watchlist.id, symbol=symbol).first()
        if not item:
            return jsonify({'success': False, 'message': 'Symbol not found in watchlist'}), 404
        
        db.session.delete(item)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Symbol removed from watchlist'})
    except Exception as e:
        app.logger.error(f"Error removing from watchlist: {e}")
        return jsonify({'success': False, 'message': 'Error removing from watchlist'}), 500

@app.route('/portfolio')
@login_required
def portfolio():
    portfolio_items = Portfolio.query.filter_by(user_id=current_user.id).all()
    
    portfolio_data = []
    total_value = 0
    total_investment = 0
    
    for item in portfolio_items:
        try:
            stock_info = stock_data.get_stock_data(item.symbol)
            current_price = stock_info['price']
            current_value = current_price * item.quantity
            investment = item.average_price * item.quantity
            profit_loss = current_value - investment
            profit_loss_percentage = (profit_loss / investment) * 100 if investment > 0 else 0
            
            portfolio_data.append({
                'symbol': item.symbol,
                'company_name': stock_info.get('name', 'Unknown'),
                'quantity': item.quantity,
                'average_price': item.average_price,
                'current_price': current_price,
                'current_value': current_value,
                'profit_loss': profit_loss,
                'profit_loss_percentage': profit_loss_percentage
            })
            
            total_value += current_value
            total_investment += investment
        except Exception as e:
            app.logger.error(f"Error fetching data for {item.symbol}: {e}")
    
    # Calculate overall profit/loss
    overall_profit_loss = total_value - total_investment
    overall_profit_loss_percentage = (overall_profit_loss / total_investment) * 100 if total_investment > 0 else 0
    
    return render_template('portfolio.html', 
                           title='Portfolio',
                           portfolio_data=portfolio_data,
                           total_value=total_value,
                           overall_profit_loss=overall_profit_loss,
                           overall_profit_loss_percentage=overall_profit_loss_percentage,
                           available_funds=current_user.funds)

@app.route('/orders')
@login_required
def orders():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('orders.html', title='Orders', orders=orders)

@app.route('/api/place_order', methods=['POST'])
@login_required
def place_order():
    data = request.json
    symbol = data.get('symbol')
    order_type = data.get('order_type')
    quantity = int(data.get('quantity', 0))
    price = float(data.get('price', 0))
    
    if not all([symbol, order_type, quantity, price]) or quantity <= 0 or price <= 0:
        return jsonify({'success': False, 'message': 'Invalid order parameters'}), 400
    
    if order_type not in ['BUY', 'SELL']:
        return jsonify({'success': False, 'message': 'Invalid order type'}), 400
    
    # Check if user has enough funds for BUY
    if order_type == 'BUY':
        order_total = price * quantity
        if current_user.funds < order_total:
            return jsonify({'success': False, 'message': 'Insufficient funds'}), 400
        
        # Deduct funds from user
        current_user.funds -= order_total
    
    # Check if user has enough stocks for SELL
    elif order_type == 'SELL':
        portfolio_item = Portfolio.query.filter_by(user_id=current_user.id, symbol=symbol).first()
        if not portfolio_item or portfolio_item.quantity < quantity:
            return jsonify({'success': False, 'message': 'Insufficient stocks to sell'}), 400
        
        # Add funds to user
        current_user.funds += price * quantity
    
    # Create order
    order = Order(
        user_id=current_user.id,
        symbol=symbol,
        order_type=order_type,
        quantity=quantity,
        price=price,
        status='COMPLETED'
    )
    db.session.add(order)
    
    # Update portfolio
    portfolio_item = Portfolio.query.filter_by(user_id=current_user.id, symbol=symbol).first()
    
    if order_type == 'BUY':
        if portfolio_item:
            # Update average price
            total_value = (portfolio_item.average_price * portfolio_item.quantity) + (price * quantity)
            portfolio_item.quantity += quantity
            portfolio_item.average_price = total_value / portfolio_item.quantity
        else:
            # Create new portfolio entry
            portfolio_item = Portfolio(
                user_id=current_user.id,
                symbol=symbol,
                quantity=quantity,
                average_price=price
            )
            db.session.add(portfolio_item)
    
    elif order_type == 'SELL':
        portfolio_item.quantity -= quantity
        # Remove from portfolio if quantity becomes zero
        if portfolio_item.quantity == 0:
            db.session.delete(portfolio_item)
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': f'Order {order_type} for {quantity} shares of {symbol} placed successfully'})

@app.route('/chart/<symbol>')
@login_required
def chart(symbol):
    try:
        stock_info = stock_data.get_stock_data(symbol)
        historical_data = get_stock_historical_data(symbol)
        return render_template('chart.html', 
                               title=f'{symbol} Chart',
                               symbol=symbol,
                               stock_info=stock_info,
                               historical_data=historical_data)
    except Exception as e:
        flash(f'Error loading chart data: {str(e)}', 'danger')
        return redirect(url_for('dashboard'))

@app.route('/api/search', methods=['GET'])
@login_required
def search():
    query = request.args.get('q', '')
    if len(query) < 2:
        return jsonify([])
    
    results = search_stocks(query)
    return jsonify(results)

@app.route('/chatbot')
@login_required
def chatbot():
    # Get user's portfolio to share with the chatbot
    portfolio_items = Portfolio.query.filter_by(user_id=current_user.id).all()
    portfolio_data = []
    
    for item in portfolio_items:
        try:
            stock_info = stock_data.get_stock_data(item.symbol)
            current_price = stock_info['price']
            
            portfolio_data.append({
                'symbol': item.symbol,
                'quantity': item.quantity,
                'average_price': item.average_price,
                'current_price': current_price
            })
        except Exception as e:
            app.logger.error(f"Error fetching data for {item.symbol}: {e}")
    
    # Get or create a chat session for the user
    from chatbot import get_or_create_chat_session
    session = get_or_create_chat_session(current_user.id)
    
    # Get messages for this session
    messages = ChatMessage.query.filter_by(session_id=session.id).order_by(ChatMessage.timestamp).all()
    
    # Log the number of messages for debugging
    app.logger.debug(f"Retrieved {len(messages)} messages for session {session.id}")
    for idx, msg in enumerate(messages):
        app.logger.debug(f"Message {idx+1}: is_user={msg.is_user}, content={msg.content[:50]}...")
    
    return render_template('chatbot.html', 
                          title='AI Assistant',
                          portfolio=portfolio_data,
                          messages=messages)

@app.route('/chatbot/message', methods=['POST'])
@login_required
def chatbot_message():
    from chatbot import generate_response, get_or_create_chat_session
    import logging
    
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    
    logger.debug("Entering chatbot_message route")
    
    # Get user message from form
    user_message = request.form.get('message')
    logger.debug(f"Form data: {request.form}")
    
    if user_message:
        logger.debug(f"Received message: {user_message[:50]}...")
    else:
        logger.debug("Received empty message")
    
    if not user_message:
        # Check if this is an AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': 'Please enter a message.'}), 400
        else:
            flash('Please enter a message.', 'warning')
            return redirect(url_for('chatbot'))
    
    # Get user's portfolio for context
    portfolio_items = Portfolio.query.filter_by(user_id=current_user.id).all()
    logger.debug(f"Retrieved {len(portfolio_items)} portfolio items")
    
    # Get or create a chat session for the user
    chat_session = get_or_create_chat_session(current_user.id)
    logger.debug(f"Using chat session id: {chat_session.id}")
    
    try:
        # Generate response using our updated chatbot with RAG
        # This will store messages in the database
        logger.debug("Calling generate_response function")
        response_text, session_id = generate_response(user_message, portfolio_items, chat_session.id)
        logger.debug(f"Received response: {response_text[:50]}...")
        
        if not session_id:
            logger.warning("No session ID returned from generate_response")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': 'There was an error processing your request.'}), 500
            else:
                flash('There was an error processing your request. Please try again.', 'warning')
                return redirect(url_for('chatbot'))
                
        # For AJAX requests, return the response as JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'response': response_text})
            
    except Exception as e:
        logger.error(f"Error generating chatbot response: {str(e)}", exc_info=True)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
        else:
            flash('Sorry, there was an error processing your request. Please try again.', 'danger')
    
    # For traditional form submissions, redirect to the chatbot page
    return redirect(url_for('chatbot'))

@app.route('/chatbot/reset', methods=['POST'])
@login_required
def reset_chatbot():
    # Mark existing chat sessions as inactive
    active_sessions = ChatSession.query.filter_by(user_id=current_user.id, active=True).all()
    for session in active_sessions:
        session.active = False
    db.session.commit()
    
    # Create a new active session
    from chatbot import get_or_create_chat_session
    get_or_create_chat_session(current_user.id)
    
    flash('Chat history has been reset.', 'success')
    return redirect(url_for('chatbot'))
