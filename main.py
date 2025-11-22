"""
main.py

Refactored AcadHack automation logic into an AutomationController class
with a two-stage lifecycle:

  1. Browser management (launch & shutdown).
  2. Automation loop (scraping + solving + clicking) that runs against
     the already-launched browser.

The GUI is expected to:

  - Instantiate a single AutomationController() once.
  - Call controller.launch_browser(log_queue) (usually from a background
    thread) to start Chrome and navigate to the Acadally dashboard.
  - When the user presses "Start Solving", create:
        log_queue: queue.Queue
        stop_event: threading.Event
    and run controller.run_solver_loop(config, log_queue, stop_event)
    in a background worker thread.
  - On application exit, call controller.shutdown() to clean up the
    persistent browser instance.
"""

import os
import time
import random

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException, StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service

from webdriver_manager.chrome import ChromeDriverManager

from scraper import scrape_quiz_data
from gemini_solver import GeminiSolver


class AutomationController:
    """
    Encapsulates the AcadHack quiz automation logic.

    Lifecycle:

      - __init__(): creates an empty controller with no active browser.
      - launch_browser(log_queue): creates a persistent Selenium driver
        and navigates to the Acadally dashboard.
      - run_solver_loop(config, log_queue, stop_event): runs the main
        automation loop using the existing driver.
      - shutdown(): closes the driver when the app exits.
    """

    def __init__(self) -> None:
        # Persistent WebDriver instance, shared across solver runs
        self.driver: webdriver.Chrome | None = None

    # ------------------------------------------------------------------ #
    # Browser lifecycle                                                  #
    # ------------------------------------------------------------------ #

    def _create_driver(self, log_queue) -> webdriver.Chrome | None:
        """
        Create a new managed Chrome WebDriver instance.

        Uses webdriver_manager to handle ChromeDriver installation.
        Does NOT attach to a remote debugging session.
        """
        chrome_options = ChromeOptions()
        
        # Persistent User Data Directory
        # This saves cookies/login state to a local folder named 'chrome_data'
        user_data_dir = os.path.join(os.getcwd(), "chrome_data")
        chrome_options.add_argument(f"user-data-dir={user_data_dir}")
        
        # Add any desired Chrome options here (e.g., headless).

        try:
            driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=chrome_options,
            )
        except WebDriverException as e:
            log_queue.put(
                "[ERROR] Could not initialize Chrome WebDriver. "
                "Make sure Chrome is installed and accessible. "
                f"Details: {e}"
            )
            return None

        # We rely on explicit waits everywhere
        driver.implicitly_wait(0)
        return driver

    def launch_browser(self, log_queue) -> None:
        """
        Launch a persistent Chrome WebDriver and navigate to the Acadally
        student dashboard.

        This is intended to be called once (e.g., via a 'Launch Chrome' button).

        It must NOT block the GUI; the caller should run this in a
        background thread.
        """
        if self.driver is not None:
            log_queue.put(
                "[WARN] Chrome WebDriver is already running. "
                "Reusing the existing browser session."
            )
            return

        log_queue.put("[INFO] Launching Chrome WebDriver...")
        driver = self._create_driver(log_queue)
        if driver is None:
            # Error already logged
            return

        try:
            driver.get("https://app.acadally.com/student")
            log_queue.put("[INFO] Navigated to Acadally student dashboard.")
        except WebDriverException as e:
            log_queue.put(
                f"[ERROR] Failed to navigate to Acadally student dashboard: {e}"
            )
            try:
                driver.quit()
            except Exception:
                pass
            return

        self.driver = driver
        log_queue.put("[INFO] Chrome WebDriver launched successfully.")

    def shutdown(self) -> None:
        """
        Cleanly shutdown the persistent browser instance.

        Intended to be called when the application is closing.
        """
        if self.driver is not None:
            try:
                self.driver.quit()
            except Exception:
                # Silent best-effort shutdown
                pass
            finally:
                self.driver = None

    # ------------------------------------------------------------------ #
    # Automation loop                                                    #
    # ------------------------------------------------------------------ #

    def run_solver_loop(self, config, log_queue, stop_event) -> None:
        """
        Main automation loop.

        Parameters
        ----------
        config : module
            The config module providing all configuration constants.
        log_queue : queue.Queue
            Queue used to send log messages to the GUI.
        stop_event : threading.Event
            Event used by the GUI to request graceful termination.

        This method does NOT create or close the WebDriver. It assumes
        that launch_browser() has been called already, and that
        self.driver is a valid active session.
        """
        # Basic API key sanity check
        if not getattr(config, "API_KEY", None) or config.API_KEY == "YOUR_API_KEY_HERE":
            log_queue.put(
                "[ERROR] Google Gemini API key is not set or is using the placeholder. "
                "Please update it in config.py before running."
            )
            return

        if self.driver is None:
            log_queue.put(
                "[ERROR] Browser has not been launched yet. "
                "Please click 'Launch Chrome' before starting the solver."
            )
            return

        driver = self.driver

        try:
            # Initialize Gemini solver
            try:
                solver = GeminiSolver(
                    api_key=config.API_KEY,
                    model_name=config.GEMINI_MODEL_NAME,
                    rate_limit_interval=config.API_RATE_LIMIT_INTERVAL,
                )
            except Exception as e:
                log_queue.put(f"[ERROR] Failed to initialize GeminiSolver: {e}")
                return

            wait = WebDriverWait(driver, config.DEFAULT_WAIT_TIMEOUT)

            log_queue.put("[INFO] Connected to existing Chrome WebDriver.")
            log_queue.put(
                "[INFO] Make sure the quiz page is open and a quiz is active."
            )
            log_queue.put("[INFO] Automation loop started. Use the GUI to stop it.")
            
            # DEBUG: Print current config state
            is_booster_enabled = getattr(config, "BOOSTER", None) and config.BOOSTER.ENABLED
            log_queue.put(f"[DEBUG] Config State: BOOSTER.ENABLED = {is_booster_enabled}")
            if is_booster_enabled:
                log_queue.put(f"[DEBUG] Booster Selectors: Question='{config.BOOSTER_QUESTION_CLASS}', Button='{config.BOOSTER_ACTION_BUTTON_SELECTOR}'")

            # Main automation loop
            while True:
                # Early stop check before starting a new question
                if stop_event.is_set():
                    log_queue.put(
                        "[INFO] Stop signal received before scraping next question. "
                        "Terminating automation loop."
                    )
                    break

                # ------------------------------------------------------------------
                # Responsive wait for quiz question/options
                # ------------------------------------------------------------------
                quiz_data = None

                original_timeout = getattr(config, "DEFAULT_WAIT_TIMEOUT", 20)
                per_attempt_timeout = 1.0
                total_waited = 0.0

                # Temporarily reduce the timeout used inside scrape_quiz_data
                try:
                    config.DEFAULT_WAIT_TIMEOUT = per_attempt_timeout
                except Exception:
                    # If not writable, fall back to single attempt with original timeout
                    per_attempt_timeout = original_timeout

                try:
                    while total_waited < original_timeout:
                        if stop_event.is_set():
                            log_queue.put(
                                "[INFO] Stop signal received while waiting for next "
                                "question. Terminating automation loop."
                            )
                            return

                        # Check for Booster Finished State
                        if getattr(config, "BOOSTER", None) and config.BOOSTER.ENABLED:
                            try:
                                finished_el = driver.find_elements(By.CLASS_NAME, config.BOOSTER_FINISHED_CLASS)
                                if finished_el:
                                    log_queue.put("[INFO] Booster Quiz Finished (Completion screen detected).")
                                    
                                    # Try to click the 'Next' (Close) button if it exists
                                    try:
                                        close_btn = driver.find_elements(By.CSS_SELECTOR, config.BOOSTER_ACTION_BUTTON_SELECTOR)
                                        if close_btn:
                                            # Click the first visible/enabled one
                                            for btn in close_btn:
                                                if btn.is_displayed() and btn.is_enabled():
                                                    btn.click()
                                                    log_queue.put("[ACTION] Clicked final 'Next' button to close quiz.")
                                                    time.sleep(1.0)
                                                    break
                                    except Exception:
                                        pass

                                    return # Exit the loop
                            except Exception:
                                pass

                        # Check for Booster Popup (e.g. "Yay! You have aced the concept")
                        if getattr(config, "BOOSTER", None) and config.BOOSTER.ENABLED:
                            try:
                                popup_els = driver.find_elements(By.CLASS_NAME, config.POPUP_OVERLAY_CLASS)
                                for popup in popup_els:
                                    if popup.is_displayed():
                                        # Look for a button inside the popup
                                        try:
                                            # The user reported the button has class 'btn-rgt'
                                            # We'll search for our known action buttons inside the popup
                                            popup_btn = popup.find_element(By.CSS_SELECTOR, config.BOOSTER_ACTION_BUTTON_SELECTOR)
                                            if popup_btn.is_displayed():
                                                log_queue.put("[INFO] Booster Mode: Popup detected.")
                                                popup_btn.click()
                                                log_queue.put("[ACTION] Booster Mode: Clicked popup button (Continue).")
                                                time.sleep(1.0)
                                                # Restart loop to see what happens next (finish screen or next q)
                                                continue 
                                        except Exception:
                                            pass
                            except Exception:
                                pass

                        try:
                            mode = "booster" if (getattr(config, "BOOSTER", None) and config.BOOSTER.ENABLED) else "standard"
                            quiz_data = scrape_quiz_data(driver, config, mode=mode)
                            # Successfully scraped quiz data
                            break
                        except TimeoutException:
                            # No question yet; try again after a short interval
                            total_waited += per_attempt_timeout
                            continue
                        except WebDriverException as e:
                            if "disconnected" in str(e).lower() or "no such window" in str(e).lower():
                                log_queue.put("[INFO] Browser disconnected. Stopping automation.")
                                return
                            log_queue.put(
                                f"[ERROR] WebDriver error while scraping quiz data: {e}"
                            )
                            return
                        except Exception as e:
                            log_queue.put(
                                f"[ERROR] Unexpected error while scraping quiz data: {e}"
                            )
                            return
                finally:
                    # Restore original timeout for the rest of the automation
                    try:
                        config.DEFAULT_WAIT_TIMEOUT = original_timeout
                    except Exception:
                        pass

                if quiz_data is None:
                    log_queue.put(
                        "[ERROR] Timed out waiting for question/options. "
                        "Terminating automation loop."
                    )
                    break

                # 2. Ask Gemini for the answer
                try:
                    answer_letter = solver.get_answer(quiz_data)
                    log_queue.put(
                        f"[SOLVER] Gemini selected answer option: '{answer_letter}'."
                    )
                except Exception as e:
                    log_queue.put(
                        f"[ERROR] Error while obtaining answer from Gemini: {e}"
                    )
                    break

                # 3. Click the chosen option
                option_elements = quiz_data.get("option_elements", {}) or {}
                chosen_element = option_elements.get(answer_letter)

                if chosen_element is None:
                    if option_elements:
                        # Fallback: choose the first available option
                        fallback_label, chosen_element = next(
                            iter(option_elements.items())
                        )
                        log_queue.put(
                            f"[INFO] Desired option '{answer_letter}' not found. "
                            f"Falling back to option '{fallback_label}'."
                        )
                    else:
                        log_queue.put(
                            "[ERROR] No option elements available to click. "
                            "Terminating automation loop."
                        )
                        break

                try:
                    wait.until(EC.element_to_be_clickable(chosen_element))
                except TimeoutException:
                    log_queue.put(
                        "[ERROR] Chosen option never became clickable. "
                        "Terminating automation loop."
                    )
                    break
                except StaleElementReferenceException:
                    log_queue.put(
                        "[WARN] Option element became stale (page updated). Re-scraping..."
                    )
                    continue
                except WebDriverException as e:
                    log_queue.put(
                        f"[ERROR] WebDriver error while waiting for option to be "
                        f"clickable: {e}"
                    )
                    break

                try:
                    chosen_element.click()
                except StaleElementReferenceException:
                    log_queue.put(
                        "[WARN] Option element became stale during click. Re-scraping..."
                    )
                    continue
                except Exception:
                    # Fallback to JavaScript click
                    try:
                        driver.execute_script("arguments[0].click();", chosen_element)
                    except Exception as e:
                        log_queue.put(
                            f"[ERROR] Failed to click chosen option element: {e}"
                        )
                        break

                # 4. Handle the action button (Next / Submit)
                # ------------------------------------------------------------------
                
                # Check if we are in Booster Mode
                is_booster = getattr(config, "BOOSTER", None) and config.BOOSTER.ENABLED

                if is_booster:
                    # --- BOOSTER MODE LOGIC ---
                    try:
                        # Wait for the button to be present (checking both classes)
                        action_button = wait.until(
                            EC.presence_of_element_located(
                                (By.CSS_SELECTOR, config.BOOSTER_ACTION_BUTTON_SELECTOR)
                            )
                        )

                        # Wait for the button to be ENABLED
                        def button_is_enabled(d):
                            btn = d.find_element(By.CSS_SELECTOR, config.BOOSTER_ACTION_BUTTON_SELECTOR)
                            is_disabled = btn.get_attribute("disabled")
                            return is_disabled is None

                        wait.until(button_is_enabled)
                        
                        # Capture current question element to wait for staleness
                        try:
                            current_question = driver.find_element(By.CLASS_NAME, config.BOOSTER_QUESTION_CLASS)
                        except Exception:
                            current_question = None

                        # Click the button
                        action_button.click()
                        log_queue.put("[ACTION] Booster Mode: Clicked Next/Submit button.")

                        # Wait for the page to transition (question becomes stale)
                        if current_question:
                            try:
                                WebDriverWait(driver, 1.0).until(EC.staleness_of(current_question))
                            except TimeoutException:
                                # This is expected if the SPA reuses the same DOM element
                                pass
                        
                        # Small buffer to ensure next question loads
                        time.sleep(1.0)

                    except TimeoutException:
                        log_queue.put(
                            "[ERROR] Booster Mode: Timed out waiting for action button to be enabled."
                        )
                        break
                    except Exception as e:
                        log_queue.put(
                            f"[ERROR] Booster Mode: Error clicking action button: {e}"
                        )
                        break

                else:
                    # --- STANDARD MODE LOGIC (Existing) ---
                    try:
                        action_button = wait.until(
                            EC.element_to_be_clickable(
                                (By.CLASS_NAME, config.ACTION_BUTTON_CLASS)
                            )
                        )
                    except TimeoutException:
                        log_queue.put(
                            "[ERROR] Could not find the action button after selecting an option."
                        )
                        break
                    except WebDriverException as e:
                        log_queue.put(
                            f"[ERROR] WebDriver error while locating action button: {e}"
                        )
                        break

                    action_text = (action_button.text or "").strip()
                    log_queue.put(f"[ACTION] Action button text: '{action_text}'")

                    # ---- NEXT QUESTION ----
                    if action_text == config.NEXT_BUTTON_TEXT:
                        try:
                            action_button.click()
                        except Exception:
                            try:
                                driver.execute_script(
                                    "arguments[0].click();", action_button
                                )
                            except Exception as e:
                                log_queue.put(
                                    f"[ERROR] Failed to click 'Next Question' button: {e}"
                                )
                                break

                        # Give the SPA a brief moment to update
                        time.sleep(0.5)

                        # Stealth Mode: human-like random delay between questions
                        if getattr(config, "STEALTH", None) and config.STEALTH.ENABLED:
                            delay = random.uniform(
                                config.STEALTH.MIN_DELAY_SECONDS,
                                config.STEALTH.MAX_DELAY_SECONDS,
                            )
                            log_queue.put(
                                f"[INFO] Stealth Mode: pausing for {delay:.1f} seconds..."
                            )
                            time.sleep(delay)

                        # Stop check after answering & clicking action button
                        if stop_event.is_set():
                            log_queue.put(
                                "[INFO] Stop signal received. Terminating automation loop."
                            )
                            break

                        continue

                    # ---- SUBMIT QUIZ ----
                    elif action_text == config.SUBMIT_BUTTON_TEXT:
                        log_queue.put(
                            "[ACTION] Submit button detected. Submitting quiz..."
                        )

                        try:
                            action_button.click()
                        except Exception:
                            try:
                                driver.execute_script(
                                    "arguments[0].click();", action_button
                                )
                            except Exception as e:
                                log_queue.put(
                                    f"[ERROR] Failed to click 'Submit Quiz' button: {e}"
                                )
                                break

                        try:
                            # Wait for popup overlay to appear
                            wait.until(
                                EC.presence_of_element_located(
                                    (By.CLASS_NAME, config.POPUP_OVERLAY_CLASS)
                                )
                            )

                            # Wait for the YES button to be clickable
                            yes_button = wait.until(
                                EC.element_to_be_clickable(
                                    (By.CLASS_NAME, config.POPUP_YES_BUTTON_CLASS)
                                )
                            )

                            # Robust JS click to bypass overlays
                            try:
                                driver.execute_script(
                                    "arguments[0].click();", yes_button
                                )
                            except Exception:
                                yes_button.click()

                            log_queue.put("[INFO] Quiz submitted successfully.")
                        except TimeoutException:
                            log_queue.put(
                                "[ERROR] Confirmation popup did not appear in time."
                            )
                        except WebDriverException as e:
                            log_queue.put(
                                f"[ERROR] WebDriver error during submission confirmation: {e}"
                            )
                        except Exception as e:
                            log_queue.put(
                                f"[ERROR] Error while clicking final YES button: {e}"
                            )

                        # After submitting, we consider our job done
                        break

                    # ---- UNEXPECTED ACTION TEXT ----
                    else:
                        log_queue.put(
                            f"[INFO] Unrecognized action button text '{action_text}'. "
                            "Clicking it anyway and continuing."
                        )
                        try:
                            action_button.click()
                        except Exception:
                            try:
                                driver.execute_script(
                                    "arguments[0].click();", action_button
                                )
                            except Exception as e:
                                log_queue.put(
                                    f"[ERROR] Failed to click unrecognized action button: {e}"
                                )
                                break

                    time.sleep(0.5)

                    # Stop check after answering & clicking action button
                    if stop_event.is_set():
                        log_queue.put(
                            "[INFO] Stop signal received. Terminating automation loop."
                        )
                        break

                    continue

        except KeyboardInterrupt:
            log_queue.put(
                "[INFO] Automation interrupted by user (KeyboardInterrupt)."
            )
        except Exception as e:
            log_queue.put(
                f"[ERROR] Unexpected exception in automation loop: {e}"
            )
        finally:
            log_queue.put("[INFO] Automation loop finished.")
