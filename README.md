# StockSphere 📈

![License](https://img.shields.io/badge/license-MIT-blue)
![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Flask](https://img.shields.io/badge/Flask-2.0.0%2B-green)

A modern, AI-powered stock trading and portfolio management platform. StockSphere combines real-time market data with personalized AI insights to help users make informed investment decisions.

<div align="center">
  <img src="static/images/dashboard.png" alt="StockSphere Dashboard" width="800"/>
</div>

## ✨ Features

- **Real-Time Market Data**: Track major indices, stock prices, and market trends.
- **Portfolio Management**: Build and track your investment portfolio.
- **Watchlists**: Create custom watchlists to monitor stocks of interest.
- **AI Assistant**: Get personalized insights and answers to financial questions.
- **Interactive Charts**: Visualize stock performance and technical indicators.
- **Virtual Trading**: Practice trading with virtual funds.

## 🧠 AI Assistant

StockSphere features an advanced AI chatbot powered by Llama 3.2, providing:

- Portfolio analysis and recommendations
- Stock research assistance
- Market trend explanations
- Investment strategy guidance

<div align="center">
  <img src="static/images/AI assistant.png" alt="StockSphere AI Assistant" width="800"/>
</div>

## 🛠️ Technology Stack

- **Backend**: Python, Flask
- **Database**: PostgreSQL, SQLAlchemy
- **Frontend**: HTML, CSS, JavaScript, Bootstrap
- **AI Engine**: Ollama (Llama 3.2)
- **Market Data**: Yahoo Finance API
- **Charts**: Chart.js

## 🏗️ Architecture

```
StockSphere
│
├── app.py                 # Flask application initialization
├── routes.py              # Application routes and view functions
├── models.py              # SQLAlchemy database models
├── stock_data.py          # Market data retrieval from Yahoo Finance
├── chatbot.py             # AI assistant with RAG implementation
│
├── static/                # Static files (CSS, JS, images)
│   ├── css/
│   ├── js/
│   └── img/
│
└── templates/             # Jinja2 HTML templates
    ├── base.html          # Base template with common elements
    ├── dashboard.html     # Main dashboard view
    ├── portfolio.html     # Portfolio management
    ├── watchlist.html     # Stock watchlists
    ├── chatbot.html       # AI assistant interface
    └── chart.html         # Stock charts and analysis
```

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- PostgreSQL
- [Ollama](https://ollama.ai/) with Llama 3.2 model installed

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/stocksphere.git
   cd stocksphere
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```bash
   # Create a .env file with the following
   SESSION_SECRET=your_secret_key
   DATABASE_URL=postgresql://username:password@localhost/stocksphere
   ```

4. Initialize the database:
   ```bash
   python
   >>> from app import app, db
   >>> with app.app_context():
   >>>     db.create_all()
   ```

5. Start Ollama with Llama 3.2:
   ```bash
   ollama run llama3.2
   ```

6. Run the application:
   ```bash
   python main.py
   ```

7. Visit `http://localhost:5000` in your browser.

## 💡 How It Works

### Market Data Retrieval

StockSphere uses the Yahoo Finance API via the `yfinance` library to fetch real-time and historical market data:

```python
def get_stock_data(symbol):
    """Get current stock data for a given symbol."""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        # Extract relevant information
        stock_data = {
            'symbol': symbol,
            'name': info.get('shortName', info.get('longName', symbol)),
            'price': info.get('currentPrice', info.get('regularMarketPrice', 0)),
            # ... other fields
        }
        return stock_data
    except Exception as e:
        logger.error(f"Error fetching data for {symbol}: {e}")
        # Return basic data if fetch fails
```

### AI Assistant Architecture

The chatbot implements Retrieval Augmented Generation (RAG) to provide accurate, contextualized responses:

<div align="center">
  <!-- Add a diagram of the RAG process here -->
  <em>RAG Architecture Diagram</em>
</div>

1. **User Context Collection**: Retrieves user portfolio data and current market information.
2. **Query Processing**: Analyzes user questions to identify mentioned stocks or topics.
3. **Data Enrichment**: Pulls specific details about mentioned stocks.
4. **Context Building**: Combines portfolio, market, and query-specific data.
5. **LLM Generation**: Sends enriched context to Llama 3.2 for response generation.

## 📊 Data Flow

1. User logs in and accesses the dashboard
2. Flask routes handle data requests
3. Stock data is fetched from Yahoo Finance
4. Data is processed and stored in the database
5. User interactions trigger appropriate actions:
   - Portfolio updates
   - Watchlist management
   - Chart generation
   - AI assistant conversations

## 📝 API Reference

### Stock Data API

| Function | Description |
|----------|-------------|
| `get_stock_data(symbol)` | Fetches current data for a specific stock |
| `get_market_summary()` | Retrieves data for major market indices |
| `get_stock_historical_data(symbol, period, interval)` | Gets historical price data for charting |
| `search_stocks(query)` | Searches for stocks by symbol or name |
| `get_top_gainers_losers()` | Retrieves top performing and declining stocks |

### Chatbot API

| Function | Description |
|----------|-------------|
| `generate_response(user_message, portfolio_data, session_id)` | Generates AI responses using RAG |
| `get_or_create_chat_session(user_id)` | Manages user chat sessions |
| `store_message(session_id, is_user, content, model_name)` | Records chat messages |

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgements

- [Yahoo Finance](https://finance.yahoo.com/) for market data
- [Ollama](https://ollama.ai/) for the LLM infrastructure
- [Flask](https://flask.palletsprojects.com/) for the web framework
- [Chart.js](https://www.chartjs.org/) for interactive charts
- [Bootstrap](https://getbootstrap.com/) for UI components
