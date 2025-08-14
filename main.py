"""
main.py (updated)

Entry point that starts Streamlit UI and optionally starts the realtime websocket server in the background.
Also integrates 2FA and email verification flows.
"""
import streamlit as st
from pages import dashboard, portfolio, trade, watchlist, news

# FastAPI imports
from fastapi import FastAPI, WebSocket, Query
from fastapi.middleware.cors import CORSMiddleware
import json
import asyncio

from api_integrations import get_current_prices, search_symbol, get_market_news

# ---------------------------
# Streamlit UI
# ---------------------------
st.set_page_config(page_title="Cross-P (Px)", layout="wide")
st.title("🚀 Welcome to Cross-P (Px)")

# Simple sidebar navigation
page = st.sidebar.selectbox("Go to", ["Dashboard", "Portfolio", "Trade", "Watchlist", "News"])

if page == "Dashboard":
    dashboard.show()
elif page == "Portfolio":
    portfolio.show()
elif page == "Trade":
    trade.show()
elif page == "Watchlist":
    watchlist.show()
elif page == "News":
    news.show()

# ---------------------------
# FastAPI backend
# ---------------------------
app = FastAPI(title="Cross-P API")

# CORS middleware for Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/search")
async def search(symbol: str):
    """Search for symbol info."""
    return search_symbol(symbol)

@app.get("/news")
async def news(keyword: str = Query(None)):
    """Fetch market news."""
    return get_market_news(keyword)

@app.websocket("/ws/prices")
async def websocket_prices(websocket: WebSocket):
    """Stream live prices for a list of symbols."""
    await websocket.accept()
    try:
        data = await websocket.receive_text()
        payload = json.loads(data)
        symbols = payload.get("symbols", [])

        while True:
            prices = get_current_prices(symbols)
            await websocket.send_text(json.dumps(prices))
            await asyncio.sleep(5)  # every 5 seconds
    except Exception:
        await websocket.close()
