"""
Application settings — user-editable values stored in JSON.
These override the defaults hard-coded in calculations.py.
"""
import json
from src.config import BASE_DIR

SETTINGS_FILE = BASE_DIR / "config_settings.json"

# Default values (used if file missing or key absent)
DEFAULTS = {
    "late_arrival_fine": 100,
    "gp_fund_monthly": 200,
    "overtime_rate_per_hour": 200,
    "school_account": "1007862",
    "bank_name": "MCB Satellite Town Branch Sargodha",
    "social_security_amount": 1300,
    "oab_amount": 480,
    "absentee_fine": 5000,
}


def load_settings():
    """Load settings from JSON, falling back to defaults."""
    if not SETTINGS_FILE.exists():
        # Create file with defaults
        save_settings(DEFAULTS)
        return dict(DEFAULTS)

    try:
        data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        # Merge with defaults so missing keys don't break
        merged = dict(DEFAULTS)
        merged.update(data)
        return merged
    except (json.JSONDecodeError, OSError):
        # Corrupted — reset
        save_settings(DEFAULTS)
        return dict(DEFAULTS)


def save_settings(settings: dict):
    """Save settings to JSON file."""
    SETTINGS_FILE.write_text(
        json.dumps(settings, indent=2),
        encoding="utf-8"
    )


def get(key: str):
    """Get a setting value by key."""
    return load_settings().get(key, DEFAULTS.get(key))


def update(**kwargs):
    """Update one or more settings. Unknown keys are ignored."""
    current = load_settings()
    for key, value in kwargs.items():
        if key in DEFAULTS:
            current[key] = value
    save_settings(current)
    return current