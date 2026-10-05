"""
Security & Cryptographic Integrity Helpers for Chakravyuha
HMAC-SHA256 request verification, constant-time comparisons, and nonce handling.
"""

import hashlib
import hmac
import os
import secrets
from typing import Optional


def generate_secure_token(length: int = 32) -> str:
    return secrets.token_hex(length // 2)


def generate_nonce() -> str:
    return secrets.token_urlsafe(16)


def compute_hmac(key: str, message: str) -> str:
    return hmac.new(key.encode(), message.encode(), hashlib.sha256).hexdigest()


def verify_hmac(key: str, message: str, signature: str) -> bool:
    if not signature:
        return False
    expected = compute_hmac(key, message)
    return hmac.compare_digest(expected, signature)


def constant_time_compare(val1: str, val2: str) -> bool:
    return hmac.compare_digest(val1.encode(), val2.encode())


def verify_flag(submitted_flag: str, stored_salted_hash: str) -> bool:
    """Verifies submitted flag against stored 'salt:hash' string in constant time."""
    if not stored_salted_hash or ":" not in stored_salted_hash:
        return False
    salt, expected_hash = stored_salted_hash.split(":", 1)
    computed = hashlib.sha256((salt + submitted_flag).encode()).hexdigest()
    return hmac.compare_digest(expected_hash, computed)


def hash_user_agent(ua_string: Optional[str]) -> str:
    if not ua_string:
        return "none"
    return hashlib.sha256(ua_string.encode()).hexdigest()[:16]
