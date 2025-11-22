"""
Central configuration for AcadHack.

Edit this file to set your API key and tweak selectors/timeouts if the
website changes.
"""

from dataclasses import dataclass

# ==========================
# Google Gemini configuration
# ==========================

import json
import os

# ==========================
# Google Gemini configuration
# ==========================

# Default values
API_KEY = "YOUR_API_KEY_HERE"
GEMINI_MODEL_NAME = "gemini-2.5-flash"
API_RATE_LIMIT_INTERVAL = 2.0  # seconds

# Load overrides from config.json if it exists
_base_dir = os.path.dirname(os.path.abspath(__file__))
_config_json_path = os.path.join(_base_dir, "config.json")

if os.path.exists(_config_json_path):
    try:
        with open(_config_json_path, "r", encoding="utf-8") as _f:
            _data = json.load(_f)
            API_KEY = _data.get("API_KEY", API_KEY)
            GEMINI_MODEL_NAME = _data.get("GEMINI_MODEL_NAME", GEMINI_MODEL_NAME)
            API_RATE_LIMIT_INTERVAL = _data.get("API_RATE_LIMIT_INTERVAL", API_RATE_LIMIT_INTERVAL)
            # We will handle Stealth and Booster updates below after class definitions
    except Exception as e:
        print(f"Error loading config.json: {e}")



# ==========================
# Selenium / site configuration
# ==========================

# Chrome remote debugging
REMOTE_DEBUGGING_ADDRESS = "127.0.0.1:9222"

# Default explicit wait timeout (for WebDriverWait)
DEFAULT_WAIT_TIMEOUT = 300  # seconds

# Core selectors
QUESTION_CLASS = "question"
OPTION_CARD_CLASS = "option-card"
OPTION_LABEL_CLASS = "option-label-box"
ACTION_BUTTON_CLASS = "selected-btn"

POPUP_OVERLAY_CLASS = "popup-overlay"
POPUP_YES_BUTTON_CLASS = "yes-btn"

# Text labels for the action button
NEXT_BUTTON_TEXT = "Next Question"
SUBMIT_BUTTON_TEXT = "Submit Quiz"

# Supported option labels
SUPPORTED_OPTION_LABELS = ["A", "B", "C", "D"]


# ==========================
# Stealth Mode configuration
# ==========================

@dataclass
class Stealth:
    """
    Configuration for Stealth Mode.

    ENABLED:
        Turn Stealth Mode on or off.
    MIN_DELAY_SECONDS / MAX_DELAY_SECONDS:
        When enabled, the script will pause a random amount of time
        between these bounds after moving to the next question.
    """
    ENABLED: bool = False
    MIN_DELAY_SECONDS: float = 5.0
    MAX_DELAY_SECONDS: float = 20.0


# Singleton instance used throughout the app
STEALTH = Stealth()


# ==========================
# Booster Mode configuration
# ==========================

@dataclass
class Booster:
    """
    Configuration for Booster Mode.

    ENABLED:
        Turn Booster Mode on or off.
    """
    ENABLED: bool = False

# Singleton instance used throughout the app
BOOSTER = Booster()

# Apply JSON overrides for Stealth and Booster if loaded
if '_data' in locals():
    STEALTH.ENABLED = _data.get("STEALTH_ENABLED", STEALTH.ENABLED)
    STEALTH.MIN_DELAY_SECONDS = _data.get("MIN_DELAY_SECONDS", STEALTH.MIN_DELAY_SECONDS)
    STEALTH.MAX_DELAY_SECONDS = _data.get("MAX_DELAY_SECONDS", STEALTH.MAX_DELAY_SECONDS)
    BOOSTER.ENABLED = _data.get("BOOSTER_ENABLED", BOOSTER.ENABLED)

# Booster selectors
BOOSTER_QUESTION_CLASS = "boosterQuestion"
BOOSTER_ACTION_BUTTON_SELECTOR = ".v2-btn-rgt, .btn-rgt"
BOOSTER_FINISHED_CLASS = "proficiency-status"
