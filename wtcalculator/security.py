from __future__ import annotations

import base64
import hashlib
import hmac
import os
import re


_PASSWORD_POLICY_RE = re.compile(r"^(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$")


def validate_password_policy(password: str) -> bool:
    """Password rules:
    - at least 8 characters
    - at least one uppercase letter
    - at least one digit
    - at least one special character (non-alphanumeric)
    """

    return bool(_PASSWORD_POLICY_RE.match(password or ""))


def hash_password(password: str, *, iterations: int = 210_000) -> str:
    if not password:
        raise ValueError('Password required')

    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iterations)

    salt_b64 = base64.b64encode(salt).decode('ascii')
    dk_b64 = base64.b64encode(dk).decode('ascii')

    return f"pbkdf2_sha256${iterations}${salt_b64}${dk_b64}"


def verify_password(password: str, stored: str) -> bool:
    if not stored:
        return False
    try:
        algo, it_s, salt_b64, dk_b64 = stored.split('$', 3)
        if algo != 'pbkdf2_sha256':
            return False
        iterations = int(it_s)
        salt = base64.b64decode(salt_b64.encode('ascii'))
        expected = base64.b64decode(dk_b64.encode('ascii'))
    except Exception:
        return False

    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iterations)
    return hmac.compare_digest(dk, expected)
