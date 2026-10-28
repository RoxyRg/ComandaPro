from __future__ import annotations
import base64, hashlib, hmac, json, os, secrets, time
from datetime import datetime, timezone
from typing import Any

JWT_SECRET = os.getenv("JWT_SECRET", "development-only-change-before-deploy")
ACCESS_MINUTES = int(os.getenv("ACCESS_TOKEN_MINUTES", "15"))
REFRESH_DAYS = int(os.getenv("REFRESH_TOKEN_DAYS", "7"))


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _unb64(data: str) -> bytes:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 310_000)
    return f"pbkdf2_sha256$310000${_b64(salt)}${_b64(digest)}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        scheme, rounds, salt, expected = encoded.split("$", 3)
        if scheme != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), _unb64(salt), int(rounds))
        return hmac.compare_digest(_b64(digest), expected)
    except (ValueError, TypeError):
        return False


def create_access_token(user_id: int, branch_id: int, extra: dict[str, Any] | None = None) -> str:
    now = int(time.time())
    header = {"alg": "HS256", "typ": "JWT"}
    payload: dict[str, Any] = {
        "sub": str(user_id), "sucursal_id": branch_id, "iat": now,
        "exp": now + ACCESS_MINUTES * 60, "type": "access", "jti": secrets.token_hex(12),
    }
    if extra:
        payload.update(extra)
    h = _b64(json.dumps(header, separators=(",", ":")).encode())
    p = _b64(json.dumps(payload, separators=(",", ":")).encode())
    signature = _b64(hmac.new(JWT_SECRET.encode(), f"{h}.{p}".encode(), hashlib.sha256).digest())
    return f"{h}.{p}.{signature}"


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        header, payload, signature = token.split(".")
        expected = _b64(hmac.new(JWT_SECRET.encode(), f"{header}.{payload}".encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected):
            raise ValueError("Firma inválida")
        data = json.loads(_unb64(payload))
        if data.get("type") != "access" or int(data.get("exp", 0)) <= int(time.time()):
            raise ValueError("Token expirado o inválido")
        return data
    except Exception as exc:
        raise ValueError("Token de acceso inválido") from exc


def new_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def refresh_expiry() -> datetime:
    from datetime import timedelta
    return datetime.now(timezone.utc) + timedelta(days=REFRESH_DAYS)
