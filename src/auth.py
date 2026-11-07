"""
Authentication module — password management.
Stores password hash in a JSON file.
"""
import json
import hashlib
from src.config import SECRETS_FILE, DEFAULT_PASSWORD


def _hash_password(password: str) -> str:
    """SHA-256 hash of the password."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def _load_secrets() -> dict:
    """Load secrets from JSON. Create default if not exists."""
    if not SECRETS_FILE.exists():
        # Create default secrets file
        data = {
            "password_hash": _hash_password(DEFAULT_PASSWORD),
            "password_changed": False,
        }
        SECRETS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return data

    try:
        return json.loads(SECRETS_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        # Corrupted file — reset to default
        data = {
            "password_hash": _hash_password(DEFAULT_PASSWORD),
            "password_changed": False,
        }
        SECRETS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return data


def _save_secrets(data: dict):
    """Save secrets to JSON."""
    SECRETS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def verify_password(password: str) -> bool:
    """Check if the given password matches stored hash."""
    secrets = _load_secrets()
    stored_hash = secrets.get("password_hash", "")
    return _hash_password(password) == stored_hash


def change_password(new_password: str) -> bool:
    """Change the password. Returns True on success."""
    if not new_password or len(new_password) < 4:
        return False
    secrets = _load_secrets()
    secrets["password_hash"] = _hash_password(new_password)
    secrets["password_changed"] = True
    _save_secrets(secrets)
    return True


def is_default_password() -> bool:
    """Check if default password is still in use."""
    secrets = _load_secrets()
    return not secrets.get("password_changed", False)