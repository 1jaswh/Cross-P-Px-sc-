"""
pages/trade.py (updated: simple permission check)
"""

import streamlit as st
from api_integrations import fetch_yfinance_ticker_snapshot, fetch_ccxt_ticker, get_currency_rate
from database import get_user_by_id, get_balance, update_balance, add_transaction, upsert_holding
import math

ASSET_TYPES = ["stock", "crypto", "forex", "commodity", "index"]

def app(st, auth):
    st.title("Trade")
    if not auth.get('user_id'):
        st.info("Please sign in to trade.")
        return
    user = get_user_by_id(auth['user_id'])
    # role/permission check
    if user['role'] not in ['user','trader','admin']:
        st.error("Your account does not have permission to trade.")
        return
    st.write(f"Welcome, **{user['username']}** — Preferred currency: {user['preferred_currency']}")
    symbol = st.text_input("Symbol (e.g., AAPL, BTC/USDT, EUR/USD, GC=F)")
    asset_type = st.selectbox("Asset type", ASSET_TYPES, index=0)
    side = st.radio("Side", ["Buy", "Sell"])
    qty = st.number_input("Quantity (units)", min_value=0.0, value=1.0, step=1.0)
    # Fetch price
    price = None
    if st.button("Get Price"):
        if "/" in symbol or asset_type in ["crypto", "forex"]:
            t = fetch_ccxt_ticker(symbol)
            price = t.get('last') if isinstance(t, dict) else None
        else:
            snap = fetch_yfinance_ticker_snapshot(symbol)
            price = snap.get('last_price')
        st.write("Price:", price)
        st.session_state.get('last_price', price)
    if st.button("Execute Order"):
        if "/" in symbol or asset_type in ["crypto", "forex"]:
            t = fetch_ccxt_ticker(symbol)
            price = t.get('last') if isinstance(t, dict) else None
            tx_currency = symbol.split("/")[-1] if "/" in symbol else "USD"
        else:
            snap = fetch_yfinance_ticker_snapshot(symbol)
            price = snap.get('last_price')
            tx_currency = snap['info'].get('currency', 'USD')
        if not price or price <= 0:
            st.error("Could not determine price.")
            return
        cost = price * qty
        pref = user['preferred_currency']
        if pref != tx_currency:
            rate = get_currency_rate(tx_currency, pref)
            cost_in_pref = cost * rate
        else:
            cost_in_pref = cost
        if side == "Buy":
            bal = get_balance(user['id'], pref)
            if bal < cost_in_pref:
                st.error(f"Insufficient balance: have {bal} {pref}, need {cost_in_pref:.2f} {pref}")
                return
            update_balance(user['id'], pref, -cost_in_pref)
            upsert_holding(user['id'], symbol, asset_type, quantity_delta=qty, price=price)
            add_transaction(user['id'], symbol, asset_type, "BUY", qty, price, tx_currency)
            st.success(f"Bought {qty} {symbol} @ {price} {tx_currency} (≈ {cost_in_pref:.2f} {pref})")
        else:
            from database import get_holding
            h = get_holding(user['id'], symbol, asset_type)
            if not h or h['quantity'] < qty:
                st.error("Not enough holdings to sell.")
                return
            update_balance(user['id'], pref, cost_in_pref)
            upsert_holding(user['id'], symbol, asset_type, quantity_delta=-qty, price=price)
            add_transaction(user['id'], symbol, asset_type, "SELL", qty, price, tx_currency)
            st.success(f"Sold {qty} {symbol} @ {price} {tx_currency} (≈ {cost_in_pref:.2f} {pref})")
