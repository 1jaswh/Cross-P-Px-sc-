"""
database.py

SQLite database layer for Cross-P (Px).
Updated with email verification, roles, and TOTP secret columns.
"""

import sqlite3
from sqlite3 import Connection
from typing import Optional, List, Dict, Any
import datetime
import hashlib
import os

DB_PATH = os.environ.get("CROSSP_DB", "crossp.db")

def get_conn() -> Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    # Users with email, is_verified, role, totp_secret
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        email TEXT,
        is_verified INTEGER DEFAULT 0,
        totp_secret TEXT,
        role TEXT DEFAULT 'user',
        preferred_currency TEXT DEFAULT 'USD',
        created_at TEXT
    )
    """)
    # Balances (per user per currency)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS balances (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        currency TEXT NOT NULL,
        amount REAL NOT NULL,
        updated_at TEXT,
        UNIQUE(user_id, currency),
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)
    # Holdings (aggregated)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS holdings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        symbol TEXT NOT NULL,
        asset_type TEXT NOT NULL,
        quantity REAL NOT NULL,
        avg_price REAL NOT NULL,
        last_updated TEXT,
        UNIQUE(user_id, symbol, asset_type),
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)
    # Transactions (order history)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        symbol TEXT NOT NULL,
        asset_type TEXT NOT NULL,
        side TEXT NOT NULL,
        quantity REAL NOT NULL,
        price REAL NOT NULL,
        currency TEXT NOT NULL,
        timestamp TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)
    # Watchlist
    cur.execute("""
    CREATE TABLE IF NOT EXISTS watchlist (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        symbol TEXT NOT NULL,
        asset_type TEXT NOT NULL,
        added_at TEXT,
        UNIQUE(user_id, symbol, asset_type),
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)
    # Verification tokens table (simple)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS email_tokens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        token TEXT NOT NULL,
        created_at TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)
    conn.commit()
    conn.close()

# --- User functions ---
def create_user(username: str, password_hash: str, email: Optional[str]=None, preferred_currency: str='USD', role: str='user', totp_secret: Optional[str]=None) -> int:
    conn = get_conn()
    cur = conn.cursor()
    now = datetime.datetime.utcnow().isoformat()
    cur.execute("INSERT INTO users (username, password_hash, email, preferred_currency, role, totp_secret, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (username, password_hash, email, preferred_currency, role, totp_secret, now))
    user_id = cur.lastrowid
    # seed demo balance USD 100000
    cur.execute("INSERT INTO balances (user_id, currency, amount, updated_at) VALUES (?, ?, ?, ?)",
                (user_id, 'USD', 100000.0, now))
    conn.commit()
    conn.close()
    return user_id

def get_user_by_username(username: str) -> Optional[sqlite3.Row]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = ?", (username,))
    r = cur.fetchone()
    conn.close()
    return r

def get_user_by_id(user_id: int) -> Optional[sqlite3.Row]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    r = cur.fetchone()
    conn.close()
    return r

def set_preferred_currency(user_id: int, currency: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE users SET preferred_currency = ? WHERE id = ?", (currency, user_id))
    conn.commit()
    conn.close()

def set_email_verification(user_id: int, verified: bool=True):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE users SET is_verified = ? WHERE id = ?", (1 if verified else 0, user_id))
    conn.commit()
    conn.close()

def store_email_token(user_id: int, token: str):
    conn = get_conn()
    cur = conn.cursor()
    now = datetime.datetime.utcnow().isoformat()
    cur.execute("INSERT INTO email_tokens (user_id, token, created_at) VALUES (?, ?, ?)", (user_id, token, now))
    conn.commit()
    conn.close()

def pop_email_token(user_id: int, token: str) -> bool:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id FROM email_tokens WHERE user_id = ? AND token = ?", (user_id, token))
    r = cur.fetchone()
    if r:
        cur.execute("DELETE FROM email_tokens WHERE id = ?", (r['id'],))
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False

# --- Balance / holdings / transactions / watchlist ---
def get_balance(user_id: int, currency: str='USD') -> float:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT amount FROM balances WHERE user_id = ? AND currency = ?", (user_id, currency))
    r = cur.fetchone()
    conn.close()
    return float(r['amount']) if r else 0.0

def update_balance(user_id: int, currency: str, amount_delta: float):
    conn = get_conn()
    cur = conn.cursor()
    now = datetime.datetime.utcnow().isoformat()
    cur.execute("SELECT amount FROM balances WHERE user_id = ? AND currency = ?", (user_id, currency))
    r = cur.fetchone()
    if r:
        new_amt = r['amount'] + amount_delta
        cur.execute("UPDATE balances SET amount = ?, updated_at = ? WHERE user_id = ? AND currency = ?",
                    (new_amt, now, user_id, currency))
    else:
        cur.execute("INSERT INTO balances (user_id, currency, amount, updated_at) VALUES (?, ?, ?, ?)",
                    (user_id, currency, amount_delta, now))
    conn.commit()
    conn.close()

def list_balances(user_id: int) -> List[sqlite3.Row]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM balances WHERE user_id = ?", (user_id,))
    r = cur.fetchall()
    conn.close()
    return r

def get_holdings(user_id: int) -> List[sqlite3.Row]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM holdings WHERE user_id = ?", (user_id,))
    r = cur.fetchall()
    conn.close()
    return r

def get_holding(user_id: int, symbol: str, asset_type: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM holdings WHERE user_id = ? AND symbol = ? AND asset_type = ?", (user_id, symbol, asset_type))
    r = cur.fetchone()
    conn.close()
    return r

def upsert_holding(user_id: int, symbol: str, asset_type: str, quantity_delta: float, price: float):
    conn = get_conn()
    cur = conn.cursor()
    now = datetime.datetime.utcnow().isoformat()
    cur.execute("SELECT * FROM holdings WHERE user_id = ? AND symbol = ? AND asset_type = ?", (user_id, symbol, asset_type))
    existing = cur.fetchone()
    if existing:
        new_qty = existing['quantity'] + quantity_delta
        if new_qty <= 0:
            cur.execute("DELETE FROM holdings WHERE id = ?", (existing['id'],))
        else:
            if quantity_delta > 0:
                old_qty = existing['quantity']
                old_avg = existing['avg_price']
                new_avg = ((old_qty * old_avg) + (quantity_delta * price)) / (old_qty + quantity_delta)
            else:
                new_avg = existing['avg_price']
            cur.execute("UPDATE holdings SET quantity = ?, avg_price = ?, last_updated = ? WHERE id = ?",
                        (new_qty, new_avg, now, existing['id']))
    else:
        cur.execute("INSERT INTO holdings (user_id, symbol, asset_type, quantity, avg_price, last_updated) VALUES (?, ?, ?, ?, ?, ?)",
                    (user_id, symbol, asset_type, quantity_delta, price, now))
    conn.commit()
    conn.close()

def add_transaction(user_id: int, symbol: str, asset_type: str, side: str, quantity: float, price: float, currency: str):
    conn = get_conn()
    cur = conn.cursor()
    now = datetime.datetime.utcnow().isoformat()
    cur.execute("INSERT INTO transactions (user_id, symbol, asset_type, side, quantity, price, currency, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (user_id, symbol, asset_type, side, quantity, price, currency, now))
    conn.commit()
    conn.close()

def get_transactions(user_id: int) -> List[sqlite3.Row]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM transactions WHERE user_id = ? ORDER BY timestamp DESC", (user_id,))
    r = cur.fetchall()
    conn.close()
    return r

def add_watch(user_id: int, symbol: str, asset_type: str):
    conn = get_conn()
    cur = conn.cursor()
    now = datetime.datetime.utcnow().isoformat()
    try:
        cur.execute("INSERT INTO watchlist (user_id, symbol, asset_type, added_at) VALUES (?, ?, ?, ?)",
                    (user_id, symbol, asset_type, now))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    conn.close()

def remove_watch(user_id: int, symbol: str, asset_type: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM watchlist WHERE user_id = ? AND symbol = ? AND asset_type = ?", (user_id, symbol, asset_type))
    conn.commit()
    conn.close()

def list_watchlist(user_id: int) -> List[sqlite3.Row]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM watchlist WHERE user_id = ?", (user_id,))
    r = cur.fetchall()
    conn.close()
    return r

# initialize DB on import
init_db()
