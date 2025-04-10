from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from functools import lru_cache
import os

# Configuration
class Config:
    DEBUG = os.getenv('FLASK_DEBUG', 'True') == 'True'
    CACHE_TIMEOUT = int(os.getenv('CACHE_TIMEOUT', '3600'))  # 1 hour

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# Rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Helper functions
@lru_cache(maxsize=128)
def fetch_stock_data(ticker: str, period: str = "1d"):
    """Fetch stock data with caching"""
    stock = yf.Ticker(ticker)
    return stock.history(period=period)

def validate_ticker(ticker: str):
    """Basic ticker validation"""
    if not ticker or not isinstance(ticker, str) or len(ticker) > 5:
        raise ValueError("Invalid ticker symbol")

# Routes
@app.route('/')
def home():
    return jsonify({
        "message": "Stock Price Predictor API",
        "status": "running",
        "version": "1.0"
    })

@app.route('/stock/<ticker>', methods=['GET'])
@limiter.limit("10 per minute")
def get_stock_price(ticker):
    try:
        validate_ticker(ticker)
        data = fetch_stock_data(ticker)
        if data.empty:
            return jsonify({"error": "No data found"}), 404
        latest_price = data['Close'].iloc[-1]
        return jsonify({
            "ticker": ticker, 
            "price": latest_price,
            "timestamp": datetime.utcnow().isoformat()
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "Internal server error"}), 500

@app.route('/stock/history/<ticker>', methods=['GET'])
@limiter.limit("10 per minute")
def get_stock_history(ticker):
    try:
        validate_ticker(ticker)
        period = request.args.get("period", "1mo")
        
        # Validate period
        valid_periods = ['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y']
        if period not in valid_periods:
            return jsonify({"error": "Invalid period"}), 400
            
        data = fetch_stock_data(ticker, period)
        if data.empty:
            return jsonify({"error": "No data found"}), 404
            
        data.reset_index(inplace=True)
        history = data[['Date', 'Close']].rename(columns={"Close": "price"})
        return jsonify({
            "ticker": ticker, 
            "history": history.to_dict(orient="records"),
            "period": period
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(debug=app.config['DEBUG'])