from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from itsdangerous import BadSignature, SignatureExpired, TimestampSigner

from app.config import settings

_pin_hasher = PasswordHasher()
_session_signer = TimestampSigner(settings.secret_key, salt="kahvikassa-session")

SESSION_COOKIE_NAME = "kahvikassa_session"


def hash_pin(raw_pin: str) -> str:
    return _pin_hasher.hash(raw_pin)


def verify_pin(raw_pin: str, stored_hash: str) -> bool:
    try:
        return _pin_hasher.verify(stored_hash, raw_pin)
    except VerifyMismatchError:
        return False


def create_session_token(user_id: int) -> str:
    return _session_signer.sign(str(user_id).encode()).decode()


def read_session_token(token: str) -> int | None:
    """Validate a signed session cookie. Returns the user id, or None if invalid/expired.

    The kiosk is a single shared terminal, so session lifetime is intentionally
    short (see settings.session_max_age_seconds) to force logout between users.
    """
    try:
        raw = _session_signer.unsign(token, max_age=settings.session_max_age_seconds)
        return int(raw.decode())
    except (BadSignature, SignatureExpired, ValueError):
        return None
