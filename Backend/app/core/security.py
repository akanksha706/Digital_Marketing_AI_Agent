"""Authentication, password hashing, and JWT token management."""

from datetime import datetime, timedelta, timezone
from typing import Optional, Any
import bcrypt
import jwt
from app.core.config import settings

# JWT Secret & Algorithm
SECRET_KEY = settings.CLOUDFLARE_API_TOKEN or "default_secret_signing_key_for_studio_jwt_token_auth"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours


def hash_password(password: str) -> str:
    """Hash plaintext password using bcrypt with salt."""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plaintext password against bcrypt hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception:
        # Fallback for plain mock passwords in dev
        return plain_password == hashed_password


def create_access_token(data: dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Encode user claims into a signed JWT token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Optional[dict[str, Any]]:
    """Decode and validate a signed JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except Exception:
        return None
