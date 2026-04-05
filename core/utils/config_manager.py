"""
config_manager.py
-----------------
Centralized configuration loader for Cortex.

Priority order (highest → lowest):
  1. %LOCALAPPDATA%/Cortex/user_config.json  — personal overrides, Git-ignored
  2. data/default_settings.json              — factory defaults, tracked in Git

load_config()   → merged dict (deep-merge: user values override defaults)
save_user_config(data) → persists only to user_config.json (never touches defaults)
reset_user_config()    → deletes user_config.json so defaults take full effect
"""

import json
import os

from core.utils.path_utils import get_data_path, get_user_data_path

# ── File Paths ────────────────────────────────────────────────────────────────
_DEFAULT_PATH     = os.path.join(get_data_path(), "default_settings.json")
_USER_CONFIG_NAME = "user_config.json"


def _user_config_path() -> str:
    return os.path.join(get_user_data_path(), _USER_CONFIG_NAME)


def _read_json(path: str) -> dict:
    """Read a JSON file safely, returning an empty dict on any error."""
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[ConfigManager] Warning: could not read '{path}': {e}")
        return {}


# ── Public API ────────────────────────────────────────────────────────────────

def load_config() -> dict:
    """
    Return the fully-merged configuration dict.

    Reads default_settings.json as the baseline, then overlays any keys
    present in user_config.json.  Missing keys in user_config always fall
    back to the defaults — so new keys added in Git updates are never lost.
    """
    defaults = _read_json(_DEFAULT_PATH)
    user_cfg = _read_json(_user_config_path())

    # Shallow merge is sufficient (all keys are top-level scalars/booleans)
    merged = {**defaults, **user_cfg}
    return merged


def save_user_config(data: dict) -> None:
    """
    Persist *only* the user-override file.
    This function intentionally never writes to default_settings.json.
    """
    path = _user_config_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"[ConfigManager] Error saving user config: {e}")


def reset_user_config() -> None:
    """
    Delete the user override file so the next load_config() call returns
    pure factory defaults.  Safe to call if the file doesn't exist yet.
    """
    path = _user_config_path()
    try:
        if os.path.exists(path):
            os.remove(path)
            print("[ConfigManager] user_config.json deleted — defaults restored.")
        else:
            print("[ConfigManager] No user_config.json to delete.")
    except Exception as e:
        print(f"[ConfigManager] Error deleting user config: {e}")
