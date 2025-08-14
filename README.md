Realtime / WebSocket
--------------------
A FastAPI-based WebSocket server is included (`realtime.py`). By default Streamlit will attempt to start it when main.py runs. The server listens at ws://127.0.0.1:8000/ws and broadcasts market updates.

Redis rate limiting
-------------------
If you provide REDIS_URL in `.env` the app will use Redis for rate limiting. Otherwise the app uses an in-memory fallback (single-process only).

2FA & Email verification
------------------------
- TOTP 2FA is supported (pyotp). On registration a TOTP secret is created for the user.
- To enable email verification and token sending, configure SMTP_* env variables: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS.
- Verification tokens are created and emailed (or printed to Streamlit if SMTP not configured).

Running tests & CI
------------------
Run tests with:

'pytest'
A GitHub Actions workflow is provided in `.github/workflows/ci.yml`.