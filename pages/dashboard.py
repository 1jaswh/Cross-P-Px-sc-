"""
pages/dashboard.py (updated)

Adds symbol resolution search and embeds a simple WebSocket client using Streamlit HTML component
to receive live messages from the FastAPI realtime server at ws://127.0.0.1:8000/ws
"""

import streamlit as st
from api_integrations import fetch_yfinance_ticker_snapshot, fetch_ccxt_ticker, fetch_news, fetch_yfinance_history, fetch_ccxt_ohlcv, get_currency_rate, smart_symbol_resolve, yahoo_symbol_search
import plotly.graph_objects as go
import pandas as pd
from database import list_watchlist, add_watch, remove_watch, get_user_by_id
from utils import valid_currency_code
import datetime

def _plot_candles_from_df(df: pd.DataFrame, symbol: str, show_sma: bool=True):
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name="OHLC"
    ))
    if show_sma and 'Close' in df.columns:
        sma = df['Close'].rolling(10).mean()
        fig.add_trace(go.Scatter(x=df.index, y=sma, name='SMA(10)'))
    fig.update_layout(title=f"{symbol} price", xaxis_title="Time", yaxis_title="Price")
    return fig

def app(st, auth):
    st.title("Market Overview")
    user = None
    if auth.get('user_id'):
        user = get_user_by_id(auth['user_id'])
        st.sidebar.markdown(f"Signed in as **{auth['username']}**")
    # Symbol resolve search
    q = st.text_input("Search ticker / name (e.g., AAPL, apple, BTC, EURUSD)","AAPL")
    if st.button("Search"):
        resolved = smart_symbol_resolve(q)
        st.write("Resolved:", resolved)
        if resolved.get('source') == 'yfinance':
            snap = fetch_yfinance_ticker_snapshot(resolved['symbol'])
            st.write("Price:", snap.get('last_price'))
        elif resolved.get('source') == 'ccxt':
            t = fetch_ccxt_ticker(resolved['symbol'])
            st.write("Price:", t.get('last') if isinstance(t, dict) else None)
    currency = st.selectbox("View values in currency", ["USD","EUR","UGX","BTC"], index=0)
    st.markdown("**Snapshot**")
    symbol_override = st.text_input("Or enter exact symbol", "")
    final_symbol = symbol_override or q
    # Determine source by input pattern
    if "/" in final_symbol or final_symbol.endswith("USDT") or final_symbol.upper().startswith("BTC"):
        with st.spinner("Fetching crypto/forex ticker..."):
            ticker = fetch_ccxt_ticker(final_symbol, exchange_name='binance')
            if 'error' in ticker:
                st.error("Ticker error: " + str(ticker['error']))
            else:
                last = ticker.get('last', None)
                st.metric(label=final_symbol, value=last)
                st.json(ticker)
                ohlcv = fetch_ccxt_ohlcv(final_symbol, timeframe='1h', limit=100)
                if ohlcv:
                    df = pd.DataFrame(ohlcv, columns=['ts','open','high','low','close','vol'])
                    df['ts'] = pd.to_datetime(df['ts'], unit='ms')
                    df.set_index('ts', inplace=True)
                    fig = _plot_candles_from_df(df.rename(columns={'open':'Open','high':'High','low':'Low','close':'Close'}), final_symbol)
                    st.plotly_chart(fig, use_container_width=True)
    else:
        with st.spinner("Fetching stock/commodity/indices data..."):
            snap = fetch_yfinance_ticker_snapshot(final_symbol)
            last = snap.get('last_price', None)
            st.metric(label=final_symbol, value=last)
            st.write("Info:")
            st.json({k: snap['info'].get(k) for k in ['shortName','longName','previousClose','currency'] if k in snap['info']})
            hist = fetch_yfinance_history(final_symbol, period='1mo', interval='1d')
            if not hist.empty:
                hist = hist.rename(columns={'Open':'Open','High':'High','Low':'Low','Close':'Close'})
                fig = _plot_candles_from_df(hist.tail(90), final_symbol)
                st.plotly_chart(fig, use_container_width=True)
    # Watchlist
    if user:
        st.sidebar.header("Watchlist")
        watches = list_watchlist(user['id'])
        for w in watches:
            st.sidebar.write(f"{w['symbol']} ({w['asset_type']})")
        if st.sidebar.button("Add to watchlist"):
            add_watch(user['id'], final_symbol, "stock")
            st.sidebar.success("Added to watchlist.")
    # News
    st.markdown("## News")
    with st.spinner("Fetching news..."):
        news = fetch_news(query=final_symbol, page_size=5)
        if news:
            for a in news:
                st.write(f"**{a.get('title')}** — {a.get('source', {}).get('name')}")
                st.write(a.get('description'))
                st.markdown(f"[Read more]({a.get('url')})")
        else:
            st.info("No news (NewsAPI key not configured or no results).")
    st.caption(f"Data refreshed at {datetime.datetime.utcnow().isoformat()} UTC (cached for ~30s).")

    # WebSocket client embedded (receives JSON market updates pushed by realtime server)
    st.markdown("### Live updates (WebSocket)")
    ws_host = st.text_input("Realtime WS host", value="ws://127.0.0.1:8000/ws")
    # embed small JS WebSocket client
    demo_html = f"""
    <div id="wslog">Connecting to {ws_host} ...</div>
    <script>
    const ws = new WebSocket("{ws_host}");
    ws.onopen = () => {{
        document.getElementById('wslog').innerText = "Connected to {ws_host}";
        ws.send("hello from client");
    }};
    ws.onmessage = (evt) => {{
        try {{
            const data = evt.data;
            // append to log
            const el = document.getElementById('wslog');
            el.innerText = "Msg: " + data + "\\n" + el.innerText;
        }} catch(e){{ console.error(e) }}
    }};
    ws.onclose = () => {{
        document.getElementById('wslog').innerText = "WebSocket closed";
    }};
    </script>
    """
    st.components.v1.html(demo_html, height=200)
