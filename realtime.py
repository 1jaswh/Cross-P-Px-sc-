"""
realtime.py

FastAPI WebSocket server for broadcasting market updates.
When started it accepts WebSocket clients at /ws and broadcasts messages.

This module also exposes a simple `start_in_thread()` helper to spawn uvicorn in a background thread
so the Streamlit app can start the websocket server automatically (optional).
"""

import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import uvicorn
import threading
from typing import List
import time

from api_integrations import fetch_yfinance_ticker_snapshot, fetch_ccxt_ticker

app = FastAPI()
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    async def broadcast(self, message: str):
        to_remove = []
        for connection in list(self.active_connections):
            try:
                await connection.send_text(message)
            except Exception:
                to_remove.append(connection)
        for c in to_remove:
            self.disconnect(c)

manager = ConnectionManager()

@app.get("/")
def root():
    return {"message": "Cross-P (Px) realtime websocket server"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # keep connection alive; client may send pings
            data = await websocket.receive_text()
            # echo back
            await websocket.send_text(json.dumps({"echo": data}))
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Background broadcaster coroutine
async def broadcaster(loop_interval: float=5.0):
    """
    Simple broadcaster that sends sample updates for a set of tickers.
    In production you'd subscribe to real feeds. This is a demo: it polls yfinance/ccxt periodically.
    """
    tickers = ["AAPL","BTC/USDT","GC=F"]  # sample
    while True:
        updates = []
        for s in tickers:
            try:
                if "/" in s or "USDT" in s:
                    t = fetch_ccxt_ticker(s)
                    last = t.get('last') if isinstance(t, dict) else None
                else:
                    snap = fetch_yfinance_ticker_snapshot(s)
                    last = snap.get('last_price')
                updates.append({"symbol": s, "last": last, "ts": int(time.time())})
            except Exception:
                updates.append({"symbol": s, "last": None, "ts": int(time.time())})
        payload = json.dumps({"type":"market_updates","data": updates})
        await manager.broadcast(payload)
        await asyncio.sleep(loop_interval)

def run_uvicorn_in_thread(host="127.0.0.1", port: int=8000):
    """Start uvicorn server in a background thread (blocking function starts a thread)."""
    config = uvicorn.Config(app, host=host, port=port, log_level="info")
    server = uvicorn.Server(config=config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    return thread

# convenience: if executed directly, run uvicorn
if __name__ == "__main__":
    # run broadcaster in event loop along with uvicorn
    import asyncio
    threading.Thread(target=lambda: uvicorn.run("realtime:app", host="0.0.0.0", port=8000, log_level="info"), daemon=True).start()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(broadcaster(5.0))
