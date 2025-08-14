"""
utils.py

Helpers: password hashing, validation, rate limiting (Redis-backed optional), CSV export,
2FA (TOTP) helpers, email token generation using itsdangerous.
"""

import bcrypt
#from typing import Tuple, Optional
import re
import time
import csv
import io
import os
import redis
import base64
import pyotp
from itsdangerous import URLSafeTimedSerializer

# --- Password hashing ---
def hash_password(password: str) -> bytes:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def check_password(password: str, password_hash: bytes) -> bool:
    try:
        return bcrypt.checkpw(password.encode('utf-8'), password_hash)
    except Exception:
        return False

# --- Input validation ---
def valid_username(u: str) -> bool:
    return bool(re.match(r'^[A-Za-z0-9_.-]{3,40}$', u))

def valid_currency_code(c: str) -> bool:
    return bool(re.match(r'^[A-Z]{3,4}$', c.upper()))

# --- Redis-backed rate limiter with in-memory fallback ---
_redis_client = None
REDIS_URL = os.environ.get("REDIS_URL")
if REDIS_URL:
    try:
        _redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        _redis_client.ping()
    except Exception:
        _redis_client = None

_mem_buckets = {}

def rate_limit(key: str, limit: int=10, per_seconds: int=60) -> bool:
    """
    Redis sliding window rate limiter. Returns True if allowed.
    If Redis not available, fallback to in-memory bucket (not shared between processes).
    """
    now = int(time.time())
    if _redis_client:
        redis_key = f"rl:{key}"
        pipe = _redis_client.pipeline()
        # trim older than window
        pipe.zremrangebyscore(redis_key, 0, now - per_seconds)
        pipe.zcard(redis_key)
        pipe.execute()
        # add now
        _redis_client.zadd(redis_key, {str(now): now})
        _redis_client.expire(redis_key, per_seconds + 5)
        count = _redis_client.zcard(redis_key)
        return count <= limit
    else:
        # in-memory fallback
        bucket = _mem_buckets.get(key, [])
        bucket = [t for t in bucket if t > time.time() - per_seconds]
        if len(bucket) >= limit:
            _mem_buckets[key] = bucket
            return False
        bucket.append(time.time())
        _mem_buckets[key] = bucket
        return True

# --- CSV export ---
def portfolio_to_csv(rows, holdings, balances) -> Tuple[str, bytes]:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Transactions"])
    writer.writerow(["id","symbol","asset_type","side","quantity","price","currency","timestamp"])
    for r in rows:
        writer.writerow([r['id'], r['symbol'], r['asset_type'], r['side'], r['quantity'], r['price'], r['currency'], r['timestamp']])
    writer.writerow([])
    writer.writerow(["Holdings"])
    writer.writerow(["id","symbol","asset_type","quantity","avg_price","last_updated"])
    for h in holdings:
        writer.writerow([h['id'], h['symbol'], h['asset_type'], h['quantity'], h['avg_price'], h['last_updated']])
    writer.writerow([])
    writer.writerow(["Balances"])
    writer.writerow(["id","currency","amount","updated_at"])
    for b in balances:
        writer.writerow([b['id'], b['currency'], b['amount'], b['updated_at']])
    data = output.getvalue().encode('utf-8')
    filename = f"crossp_portfolio_{int(time.time())}.csv"
    return filename, data

# --- 2FA (TOTP) helpers ---
def generate_totp_secret() -> str:
    return pyotp.random_base32()

def get_totp_uri(secret: str, username: str, issuer_name: str='Cross-P (Px)') -> str:
    return pyotp.totp.TOTP(secret).provisioning_uri(name=username, issuer_name=issuer_name)

def verify_totp(secret: str, code: str) -> bool:
    try:
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=1)
    except Exception:
        return False

# --- Email token generation (email verification) ---
SECRET_KEY = os.environ.get("CROSSP_SECRET") or "dev-secret-change-me"
serializer = URLSafeTimedSerializer(SECRET_KEY)

def generate_email_token(user_id: int, salt: str='email-confirm') -> str:
    return serializer.dumps({"user_id": user_id}, salt=salt)

def confirm_email_token(token: str, max_age: int=3600, salt: str='email-confirm') -> Optional[int]:
    try:
        data = serializer.loads(token, salt=salt, max_age=max_age)
        return data.get("user_id")
    except Exception:
        return None
