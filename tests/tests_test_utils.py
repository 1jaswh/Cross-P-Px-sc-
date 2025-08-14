import pytest
from utils import hash_password, check_password, generate_totp_secret, verify_totp, generate_email_token, confirm_email_token

def test_password_hashing():
    p = "Secret123!"
    h = hash_password(p)
    assert check_password(p, h)
    assert not check_password("wrong", h)

def test_totp():
    s = generate_totp_secret()
    import pyotp, time
    t = pyotp.TOTP(s)
    code = t.now()
    assert verify_totp(s, code)

def test_email_token():
    token = generate_email_token(1)
    uid = confirm_email_token(token)
    assert uid == 1
