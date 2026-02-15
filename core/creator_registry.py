"""
Creator Registry - Tracks which ECTO files were created on this machine.

Used to distinguish sender (creator) vs reader when opening .ecto files:
- Creator: opens in editor mode (grey/blue dots, can modify)
- Reader: opens in reader mode (green/blue dots, view-only)
"""
import json
import logging
from pathlib import Path
from typing import Set

logger = logging.getLogger(__name__)

# Import config directory from license validator (same app config location)
try:
    from core.license_validator import get_config_directory
except ImportError:
    # Fallback if license_validator not available
    import sys
    def get_config_directory() -> Path:
        if sys.platform == "darwin":
            config_dir = Path.home() / "Library" / "Application Support" / "ECTOFORM"
        elif sys.platform == "win32":
            config_dir = Path.home() / "AppData" / "Local" / "ECTOFORM"
        else:
            config_dir = Path.home() / ".config" / "ectoform"
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir


def _get_registry_path() -> Path:
    """Path to the creator tokens JSON file."""
    return get_config_directory() / "creator_tokens.json"


def _load_tokens() -> Set[str]:
    """Load token set from disk."""
    path = _get_registry_path()
    if not path.exists():
        return set()
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        tokens = data.get("tokens", [])
        return set(tokens) if isinstance(tokens, list) else set()
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"creator_registry: Failed to load tokens: {e}")
        return set()


def _save_tokens(tokens: Set[str]) -> bool:
    """Save token set to disk."""
    path = _get_registry_path()
    try:
        get_config_directory().mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"tokens": sorted(tokens)}, f, indent=2)
        return True
    except IOError as e:
        logger.warning(f"creator_registry: Failed to save tokens: {e}")
        return False


def register_creator_token(token: str) -> None:
    """Add a creator token to the local registry.

    Called when the user exports an .ecto file from this machine.
    """
    if not token:
        return
    tokens = _load_tokens()
    tokens.add(token)
    _save_tokens(tokens)
    logger.debug(f"creator_registry: Registered token {token[:8]}...")


def is_creator(token: str) -> bool:
    """Check if the given token is in the local registry (this machine created the file)."""
    if not token:
        return False
    tokens = _load_tokens()
    return token in tokens
