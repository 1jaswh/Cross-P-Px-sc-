import streamlit as st
import pandas as pd
import json
import asyncio
import websockets
import requests
from utils import get_user_id_from_session
from database import get_watchlist, add_to_watchlist, remove_from_watchlist

st.set_page_config(page_title="Watchlist", page_icon="👀", layout="wide")
st.title("👀 My Watchlist")

user_id = get_user_id_from_session()

if not user_id:
    st.error("You must be logged in to view your watchlist.")
    st.stop()

# Add asset search
query = st.text_input("Search asset symbol (e.g., AAPL, BTC-USD):")
if query:
    search_res = requests.get(f"http://localhost:8000/search?symbol={query}").json()
    st.write(search_res)
    if st.button(f"Add {query} to Watchlist"):
        add_to_watchlist(user_id, query)
        st.success(f"{query} added to watchlist.")

# Fetch current watchlist
watchlist = get_watchlist(user_id)
df = pd.DataFrame(watchlist, columns=["symbol"])
df["Current Price"] = 0.0

async def stream_watchlist_prices():
    uri = "ws://localhost:8000/ws/prices"
    async with websockets.connect(uri) as websocket:
        await websocket.send(json.dumps({"symbols": df["symbol"].tolist()}))
        while True:
            update = json.loads(await websocket.recv())
            for symbol, price in update.items():
                df.loc[df["symbol"] == symbol, "Current Price"] = price
                st.dataframe(df)

asyncio.run(stream_watchlist_prices())
