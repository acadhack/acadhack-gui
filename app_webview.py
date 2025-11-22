"""
app_webview.py

Main entry point for the AcadHack desktop application.
"""

import os
import threading
import queue
import webview
from importlib import reload

from main import AutomationController
from config_manager import ConfigManager
import config

# --- ARCHITECT OPTIMIZATION: FORCE HARDWARE ACCELERATION ---
# These flags ensure QtWebEngine (Chromium) uses the GPU for
# CSS animations, fixing the "choppy" rendering on Linux.
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--enable-gpu-rasterization --ignore-gpu-blocklist --enable-zero-copy"

# Global references used by the poller and closing handler
api = None
window = None


class Api:
    """Bridge object exposed to JavaScript as window.pywebview.api."""

    def __init__(self):
        # Runtime state
        self.is_running = False
        self.browser_running = False  # Track browser state
        self.worker_thread: threading.Thread | None = None
        self.stop_event: threading.Event | None = None

        # Shared log queue
        self.log_queue: queue.Queue = queue.Queue()

        # Config handling
        self.config_manager = ConfigManager()

        # Persistent automation controller
        self.controller = AutomationController()

    def load_settings(self):
        """Called by JS on startup."""
        try:
            settings = self.config_manager.read_settings()
            return {
                "apiKey": settings.get("API_KEY", ""),
                "modelName": settings.get("GEMINI_MODEL_NAME", ""),
                "rateLimitSeconds": settings.get("API_RATE_LIMIT_INTERVAL", 0),
                "stealthEnabled": settings.get("STEALTH_ENABLED", False),
                "minDelaySeconds": settings.get("MIN_DELAY_SECONDS", 5.0),
                "maxDelaySeconds": settings.get("MAX_DELAY_SECONDS", 20.0),
                "boosterEnabled": settings.get("BOOSTER_ENABLED", False),
            }
        except Exception as e:
            return {"error": f"Failed to read settings: {e}"}

    def save_settings(self, settings_dict):
        """Called by JS with the settings form data."""
        try:
            cleaned_settings = {
                "API_KEY": str(settings_dict.get("apiKey", "")),
                "GEMINI_MODEL_NAME": str(settings_dict.get("modelName", "")),
                "API_RATE_LIMIT_INTERVAL": float(settings_dict.get("rateLimitSeconds", 0)),
                "STEALTH_ENABLED": bool(settings_dict.get("stealthEnabled", False)),
                "MIN_DELAY_SECONDS": float(settings_dict.get("minDelaySeconds", 5.0)),
                "MAX_DELAY_SECONDS": float(settings_dict.get("maxDelaySeconds", 20.0)),
                "BOOSTER_ENABLED": bool(settings_dict.get("boosterEnabled", False)),
            }
            self.config_manager.update_settings(cleaned_settings)
            return {"status": "success"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # ------------------------------------------------------------------ #
    # Browser Control (Launch / Close)                                   #
    # ------------------------------------------------------------------ #

    def launch_chrome(self):
        """Called by 'Launch Chrome'."""
        global window

        if self.browser_running:
            self.log_queue.put("[WARN] Browser already running.")
            return {"status": "already_running"}

        def _worker():
            self.controller.launch_browser(self.log_queue)

            # Check if launch succeeded
            if self.controller.driver is not None:
                self.browser_running = True
                if window:
                    # Pass 'true' (boolean) to JS
                    window.evaluate_js("set_browser_state(true)")
            else:
                self.browser_running = False
                if window:
                    window.evaluate_js("set_browser_state(false)")

        t = threading.Thread(target=_worker, name="ChromeLauncher", daemon=True)
        t.start()
        return {"status": "launching"}

    def close_browser(self):
        """Called by 'Close Browser'."""
        global window

        def _worker():
            self.log_queue.put("[INFO] Closing Chrome...")
            self.controller.shutdown()
            self.browser_running = False
            if window:
                window.evaluate_js("set_browser_state(false)")
            self.log_queue.put("[INFO] Chrome closed.")

        t = threading.Thread(target=_worker, name="ChromeCloser", daemon=True)
        t.start()
        return {"status": "closing"}

    # ------------------------------------------------------------------ #
    # Automation Control (Start Solving / Stop Solving)                  #
    # ------------------------------------------------------------------ #

    def toggle_automation(self):
        """Called by 'Start Solving'."""
        global window

        if not self.is_running:
            self.start_automation()
            if window:
                window.evaluate_js("set_ui_state(true)")
        else:
            self.stop_automation()
            if window:
                window.evaluate_js("set_ui_state(false)")

        return {"isRunning": self.is_running}

    def start_automation(self):
        if self.is_running:
            return

        self.stop_event = threading.Event()
        reload(config)

        def _worker():
            self.controller.run_solver_loop(config, self.log_queue, self.stop_event)

        self.worker_thread = threading.Thread(
            target=_worker, name="AcadHackSolver", daemon=True
        )
        self.worker_thread.start()
        self.is_running = True
        self.log_queue.put("[INFO] Automation loop thread started.")

    def stop_automation(self):
        if self.stop_event:
            self.stop_event.set()
        self.log_queue.put("[INFO] Stop signal sent to automation loop.")
        self.is_running = False


def _js_escape(text: str) -> str:
    """Escapes strings to be safely embedded in a JS function call."""
    text = str(text).replace("\\", "\\\\").replace("'", "\\'").replace("\r", "").replace("\n", "\\n")
    return text


def poll_background_tasks(win: webview.Window):
    """Heartbeat to sync Python state with UI."""
    global api

    if api:
        # 1. Logs
        if api.log_queue:
            while True:
                try:
                    msg = api.log_queue.get_nowait()
                    win.evaluate_js(f"append_log('{_js_escape(msg)}')")
                    
                    # Check for completion messages to trigger sound
                    if "Quiz submitted successfully" in msg or "Booster Quiz Finished" in msg:
                        win.evaluate_js("play_success_sound()")
                        
                except queue.Empty:
                    break

        # 2. Heartbeat: Solver Thread Death
        if api.is_running and (api.worker_thread is None or not api.worker_thread.is_alive()):
            print("Heartbeat: Solver thread ended. Resetting UI.")
            api.is_running = False
            try:
                win.evaluate_js("set_ui_state(false)")
                win.evaluate_js("append_log('[INFO] Solver loop terminated.')")
            except Exception:
                pass

        # 3. Heartbeat: Manual Browser Closure
        # If we think browser is running, but driver is dead/gone, reset state.
        if api.browser_running:
            is_alive = False
            if api.controller.driver:
                try:
                    # Ping the driver to see if it's still connected
                    _ = api.controller.driver.title
                    is_alive = True
                except Exception:
                    is_alive = False

            if not is_alive:
                print("Heartbeat: Browser closed manually. Resetting UI.")
                api.browser_running = False
                api.controller.shutdown() # Cleanup
                try:
                    win.evaluate_js("set_browser_state(false)")
                    win.evaluate_js("append_log('[WARN] Browser closed manually.')")
                except Exception:
                    pass

    timer = threading.Timer(0.2, poll_background_tasks, args=(win,))
    timer.daemon = True
    timer.start()


if __name__ == "__main__":
    api = Api()

    # Auto-create config.json if it doesn't exist (for portable exe users)
    if not os.path.exists(api.config_manager.config_path):
        print("First run detected. Creating default config.json...")
        try:
            # Load defaults (from config.py)
            defaults = api.load_settings()
            # Save them to file (creates config.json)
            api.save_settings(defaults)
        except Exception as e:
            print(f"Failed to create default config: {e}")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    index_path = os.path.join(base_dir, "web", "index.html")

    window = webview.create_window(
        "AcadHack Control Panel",
        index_path,
        js_api=api,
        width=1200,
        height=800,
        resizable=True,
    )

    def on_closing():
        if api and getattr(api, "controller", None):
            try:
                api.controller.shutdown()
            except Exception:
                pass

    window.events.closed += on_closing

    initial_timer = threading.Timer(0.2, poll_background_tasks, args=(window,))
    initial_timer.daemon = True
    initial_timer.start()

    # FIX: Explicitly use 'qt' to match the installed dependencies
    # and ensure Chromium-level CSS performance.
    webview.start(debug=False, gui="qt")
