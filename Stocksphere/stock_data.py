import yfinance as yf
import pandas as pd
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Cache for stock data to reduce API calls
stock_cache = {}
cache_expiry = {}
CACHE_DURATION = 300  # Cache duration in seconds (5 minutes)

def get_stock_data(symbol):
    """Get current stock data for a given symbol."""
    current_time = datetime.now()
    
    # Check if we have cached data that's still valid
    if symbol in stock_cache and symbol in cache_expiry:
        if current_time < cache_expiry[symbol]:
            return stock_cache[symbol]
    
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        # Extract relevant information
        stock_data = {
            'symbol': symbol,
            'name': info.get('shortName', info.get('longName', symbol)),
            'price': info.get('currentPrice', info.get('regularMarketPrice', 0)),
            'change': info.get('regularMarketChange', 0),
            'change_percent': info.get('regularMarketChangePercent', 0),
            'volume': info.get('regularMarketVolume', 0),
            'market_cap': info.get('marketCap', 0),
            'day_high': info.get('dayHigh', 0),
            'day_low': info.get('dayLow', 0),
            'open': info.get('regularMarketOpen', 0),
            'prev_close': info.get('regularMarketPreviousClose', 0),
        }
        
        # Cache the data
        stock_cache[symbol] = stock_data
        cache_expiry[symbol] = current_time + timedelta(seconds=CACHE_DURATION)
        
        return stock_data
    except Exception as e:
        logger.error(f"Error fetching data for {symbol}: {e}")
        # Return basic data if fetch fails
        return {
            'symbol': symbol,
            'name': symbol,
            'price': 0,
            'change': 0,
            'change_percent': 0,
            'volume': 0,
            'error': str(e)
        }

def get_stock_historical_data(symbol, period='1mo', interval='1d'):
    """Get historical stock data for charts."""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period, interval=interval)
        
        # Convert to list format for Chart.js
        dates = hist.index.strftime('%Y-%m-%d').tolist()
        prices = hist['Close'].tolist()
        volumes = hist['Volume'].tolist()
        
        return {
            'dates': dates,
            'prices': prices,
            'volumes': volumes
        }
    except Exception as e:
        logger.error(f"Error fetching historical data for {symbol}: {e}")
        return {'dates': [], 'prices': [], 'volumes': []}

def get_market_summary():
    """Get summary of major market indices."""
    indices = ['^GSPC', '^DJI', '^IXIC', '^RUT']  # S&P 500, Dow Jones, NASDAQ, Russell 2000
    
    market_data = []
    for index in indices:
        try:
            data = get_stock_data(index)
            if '^GSPC' == index:
                data['name'] = 'S&P 500'
            elif '^DJI' == index:
                data['name'] = 'Dow Jones'
            elif '^IXIC' == index:
                data['name'] = 'NASDAQ'
            elif '^RUT' == index:
                data['name'] = 'Russell 2000'
            market_data.append(data)
        except Exception as e:
            logger.error(f"Error fetching market data for {index}: {e}")
    
    return market_data

def search_stocks(query):
    """Search for stocks based on symbol or name."""
    try:
        # This is a simple implementation. For production, you might want to use a more comprehensive API
        tickers = yf.Tickers(query).tickers
        
        results = []
        for symbol, ticker in tickers.items():
            try:
                info = ticker.info
                results.append({
                    'symbol': symbol,
                    'name': info.get('shortName', info.get('longName', symbol))
                })
            except:
                # Skip tickers that raise errors
                continue
                
        return results[:10]  # Limit to 10 results
    except Exception as e:
        logger.error(f"Error searching stocks: {e}")
        return []

def get_top_gainers_losers():
    """Get top gainers and losers for the day."""
    # This is a simplified version. For a real app, you'd use a specific API endpoint
    # that provides this information directly
    
    # Common large cap stocks for demonstration
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'FB', 'NVDA', 'JPM', 'V', 'JNJ',
               'WMT', 'BAC', 'PG', 'PYPL', 'DIS', 'NFLX', 'INTC', 'CMCSA', 'PFE', 'CSCO']
    
    stocks_data = []
    for symbol in symbols:
        try:
            data = get_stock_data(symbol)
            stocks_data.append(data)
        except:
            continue
    
    # Sort by percentage change
    if stocks_data:
        gainers = sorted(stocks_data, key=lambda x: x.get('change_percent', 0), reverse=True)[:5]
        losers = sorted(stocks_data, key=lambda x: x.get('change_percent', 0))[:5]
        return {'gainers': gainers, 'losers': losers}
    
    return {'gainers': [], 'losers': []}
