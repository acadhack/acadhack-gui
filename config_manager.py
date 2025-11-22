# config_manager.py

import os
import json
import os
from typing import Any, Dict


class ConfigManager:
    """
    Helper for surgically reading and updating selected settings in config.py
    using carefully-scoped regular expressions.

    It only touches:
      - API_KEY
      - GEMINI_MODEL_NAME
      - API_RATE_LIMIT_INTERVAL
      - Stealth.ENABLED
      - Stealth.MIN_DELAY_SECONDS
      - Stealth.MAX_DELAY_SECONDS
    """

    def __init__(self, config_path: str | None = None) -> None:
        if config_path is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(base_dir, "config.json")
        self.config_path = config_path

    # ----- Internal helpers -----

    def _read_json(self) -> Dict[str, Any]:
        if not os.path.exists(self.config_path):
            return {}
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _write_json(self, data: Dict[str, Any]) -> None:
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    # ----- Public API -----

    def read_settings(self) -> Dict[str, Any]:
        """
        Read current values from config.json, falling back to config.py defaults
        if not present in JSON.
        """
        # Import config here to get the runtime defaults (which might have loaded from JSON already,
        # but this ensures we have the full set of keys).
        # We reload it to ensure we have the latest state if something changed.
        import config
        from importlib import reload
        reload(config)

        # We can just read from the config module directly, as it represents the
        # current effective state (defaults + JSON overrides).
        return {
            "API_KEY": config.API_KEY,
            "GEMINI_MODEL_NAME": config.GEMINI_MODEL_NAME,
            "API_RATE_LIMIT_INTERVAL": config.API_RATE_LIMIT_INTERVAL,
            "STEALTH_ENABLED": config.STEALTH.ENABLED,
            "MIN_DELAY_SECONDS": config.STEALTH.MIN_DELAY_SECONDS,
            "MAX_DELAY_SECONDS": config.STEALTH.MAX_DELAY_SECONDS,
            "BOOSTER_ENABLED": config.BOOSTER.ENABLED,
        }

    def update_settings(self, settings: Dict[str, Any]) -> None:
        """
        Update settings by writing them to config.json.
        """
        # Read existing JSON to preserve any other keys if they exist
        current_data = self._read_json()

        # Update with new values
        current_data["API_KEY"] = str(settings.get("API_KEY", ""))
        current_data["GEMINI_MODEL_NAME"] = str(settings.get("GEMINI_MODEL_NAME", ""))
        current_data["API_RATE_LIMIT_INTERVAL"] = float(settings.get("API_RATE_LIMIT_INTERVAL", 0))
        current_data["STEALTH_ENABLED"] = bool(settings.get("STEALTH_ENABLED", False))
        current_data["MIN_DELAY_SECONDS"] = float(settings.get("MIN_DELAY_SECONDS", 5.0))
        current_data["MAX_DELAY_SECONDS"] = float(settings.get("MAX_DELAY_SECONDS", 20.0))
        current_data["BOOSTER_ENABLED"] = bool(settings.get("BOOSTER_ENABLED", False))

        self._write_json(current_data)

