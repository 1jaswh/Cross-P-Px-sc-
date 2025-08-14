import streamlit as st
import requests
import pandas as pd
import json
import asyncio
import websockets
from utils import get_user_id_from_session, format_currency
from database import get_portfolio_positions

st.set_page_config(page_title="Portfolio", page_icon="📊", layout="wide")

st.title("📊 My Portfolio")

user_id = get_user_id_from_session()

if not user_id:
    st.error("You must be logged in to view your portfolio.")
    st.stop()

# Fetch portfolio from database
positions = get_portfolio_positions(user_id)

if not positions:
    st.info("Your portfolio is empty. Go to the Trade page to add assets.")
    st.stop()

df = pd.DataFrame(positions)

# Calculate total value
df["Current Price"] = 0.0
df["Total Value"] = 0.0

async def fetch_live_prices():
    uri = "ws://localhost:8000/ws/prices"
    async with websockets.connect(uri) as websocket:
        await websocket.send(json.dumps({"symbols": df["symbol"].tolist()}))
        while True:
            update = json.loads(await websocket.recv())
            for symbol, price in update.items():
                df.loc[df["symbol"] == symbol, "Current Price"] = price
                df["Total Value"] = df["Current Price"] * df["quantity"]
                st.dataframe(df)

asyncio.run(fetch_live_prices())
