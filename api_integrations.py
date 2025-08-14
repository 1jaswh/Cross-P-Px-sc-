"""
api_integrations.py

Functions for fetching market data and symbol search.
"""
import yfinance as yf
import ccxt
import requests
from forex_python.converter import CurrencyRates
import os
from typing import List, Dict
from datetime import datetime

# Load environment variable for News API
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "3d4047894a154d58bc3aa54377b63659")

# ---------------------------
# Price & Market Data Helpers
# ---------------------------
def get_current_prices(symbols: List[str]) -> Dict[str, float]:
    """Fetch current prices for a list of symbols using yfinance/ccxt."""
    prices = {}
    for sym in symbols:
        try:
            # Check if it's crypto/forex (contains -) else treat as stock/commodity
            if "-" in sym:
                exchange = ccxt.binance()
                ticker = exchange.fetch_ticker(sym)
                prices[sym] = round(ticker["last"], 2)
            else:
                ticker = yf.Ticker(sym)
                data = ticker.history(period="1d")
                if not data.empty:
                    prices[sym] = round(data["Close"].iloc[-1], 2)
        except Exception:
            prices[sym] = None
    return prices

def search_symbol(symbol: str) -> Dict:
    """Resolve symbol info using yfinance."""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        return {
            "symbol": symbol.upper(),
            "name": info.get("shortName"),
            "currency": info.get("currency"),
            "exchange": info.get("exchange"),
        }
    except Exception:
        return {"error": "Symbol not found"}

def get_market_news(keyword: str = None) -> List[Dict]:
    """Fetch recent market news from NewsAPI."""
    base_url = "https://newsapi.org/v2/everything"
    params = {
        "apiKey": NEWS_API_KEY,
        "language": "en",
        "pageSize": 10,
        "sortBy": "publishedAt"
    }
    if keyword:
        params["q"] = keyword
    else:
        params["q"] = "stocks OR crypto OR finance"

    try:
        resp = requests.get(base_url, params=params)
        if resp.status_code != 200:
            return []
        articles = resp.json().get("articles", [])
        return [
            {
                "title": a["title"],
                "summary": a.get("description"),
                "url": a["url"],
                "publishedAt": a["publishedAt"]
            }
            for a in articles
        ]
    except Exception:
        return []

# ---------------------------
# Currency Conversion
# ---------------------------
def convert_currency(amount: float, from_currency: str, to_currency: str) -> float:
    """Convert amount from one currency to another using forex-python."""
    try:
        c = CurrencyRates()
        rate = c.get_rate(from_currency, to_currency)
        return round(amount * rate, 2)
    except Exception:
        return amount
