import pytest
from database import create_user, get_user_by_username, get_user_by_id, get_balance

def test_create_user_and_balance(tmp_path, monkeypatch):
    # use a temp DB path to avoid interfering with real DB
    import os
    monkeypatch.setenv("CROSSP_DB", str(tmp_path / "test.db"))
    # reimport module to init DB with new env var
    import importlib
    import database as dbmod
    importlib.reload(dbmod)
    uid = dbmod.create_user("testuser", b"hash", email="t@example.com")
    u = dbmod.get_user_by_username("testuser")
    assert u is not None
    assert u['id'] == uid
    bal = dbmod.get_balance(uid, "USD")
    assert bal == 100000.0
