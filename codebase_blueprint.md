# AcadHack Codebase Blueprint 📐

This document provides a comprehensive technical breakdown of the `acadhack-gui` application. It details the architecture, file responsibilities, and key function logic without modifying any code.

## 1. High-Level Architecture

AcadHack is a hybrid **Desktop GUI Application** that creates a bridge between a locally running web interface and a powerful backend automation engine.

*   **Frontend (UI)**: HTML/CSS/JS running in a Chromium window (via `pywebview`).
*   **Backend (Logic)**: Python 3.x managing the application state, configuration, and API calls.
*   **Automation Engine**: Selenium WebDriver (Chrome) controlling an external browser instance to take quizzes.
*   **Intelligence**: Google Gemini API (via `google-genai`) solving the extracted questions.

---

## 2. Directory Structure & File Manifest

### root (`acadhack-gui/`)
*   **`main.py`**: The "Coordinator". Orchestrates the Selenium automation loop.
*   **`app_webview.py`**: The "Application Entry Point". Sets up the GUI window and handles JS-Python communication.
*   **`gemini_solver.py`**: The "Brain". Handles image/text payload construction and Gemini API interactions.
*   **`scraper.py`**: The "Eyes". Parses the Acadally quiz DOM to extract questions and images.
*   **`config.py`**: The "Settings Definition". Defines configuration constants and defaults.
*   **`config_manager.py`**: The "Persistence Layer". Reads/Writes `config.json`.
*   **`requirements.txt`**: List of Python dependencies.
*   **`run_linux.sh`**: Launch script for Linux (dependency check + venv activation).
*   **`run_windows.bat`**: Launch script for Windows.
*   **`.gitignore`**: Specifies files to exclude from version control (e.g., secrets, virtualenvs).

### `web/` (Frontend)
*   **`index.html`**: The single-page application structure.
*   **`style.css`**: Application styling (Dark/Light themes).
*   **`script.js`**: Frontend logic, event handling, and communication with Python.
*   **`assets/`**: Icons and logos.

### `.github/` (CI/CD)
*   **`workflows/build_windows.yml`**: GitHub Actions configuration for automated Windows builds.

---

## 3. Detailed Component Analysis

### A. The Entry Point: `app_webview.py`
This file initializes the GUI and exposes Python functions to JavaScript.

*   **`Api` Class**: The bridge object. Methods here are callable from JS via `window.pywebview.api`.
    *   `load_settings()`: Reads current config to populate UI fields.
    *   `save_settings(data)`: Updates and persists config changes.
    *   `toggle_automation()`: Starts/Stops the solving loop.
    *   `launch_chrome()`: Opens the automated browser window.
    *   `copy_to_clipboard(text)`: Cross-platform clipboard handler using `pyperclip`.
*   **`webview.create_window()`**: Creates the main application window pointing to `web/index.html`.
*   **`webview.start()`**: Starts the GUI event loop.

### B. The Coordinator: `main.py`
This file manages the actual work of solving quizzes.

*   **`AutomationController` Class**:
    *   `launch_browser()`: Uses `webdriver_manager` to download/find ChromeDriver and launches a Selenium session.
    *   `run_solver_loop()`: The infinite loop that drives the automation:
        1.  **Wait**: Looks for a "Next" or "Submit" button.
        2.  **Scrape**: Calls `scraper.py` to get current question data.
        3.  **Solve**: Calls `gemini_solver.py` to get an answer (A/B/C/D).
        4.  **Act**: Finds the corresponding radio button in the DOM and clicks it.
        5.  **Submit**: Clicks "Submit" and handles any confirmation popups.
        6.  **Next**: Clicks "Next" to proceed to the next question.
    *   **Logic Handling**:
        *   *Stealth Mode*: Adds random delays between actions.
        *   *Booster Mode*: Detects if the quiz is a "Booster" type and adjusts selectors.
        *   *Blind Mode*: Skips scraping if Guess Mode is active.

### C. The Brain: `gemini_solver.py`
This file interfaces with Google's AI.

*   **`GeminiSolver` Class**:
    *   `__init__`: Sets up the `google-genai` client with the user's API Key.
    *   `get_answer(quiz_data)`: The main public method.
        *   **Guess Mode Check**: If enabled, returns a fixed letter or random choice immediately.
        *   **Rate Limiting**: Enforces `API_RATE_LIMIT_INTERVAL` to prevent bans.
        *   **Payload Construction**: Converts text and raw image bytes into a multimodal prompt for Gemini.
        *   **Extraction**: Parses the model's text response to find a single letter (A, B, C, D).

### D. The Eyes: `scraper.py`
*   **`scrape_quiz_data(driver)`**:
    *   Inspects the active page HTML.
    *   Extracts question text.
    *   Takes screenshots of question images (cropping elements).
    *   Returns a dictionary: `{'question': text, 'options': {A:..., B:...}, ...}`.

### E. Configuration: `config.py` & `config_manager.py`
*   **`config.py`**: Defines defaults (e.g., Default Model: `gemini-3-flash-preview`). Defines data structures (`Stealth`, `Guess`).
*   **`config_manager.py`**: Handles `json` serialization. Ensures `config.json` overrides defaults but preserves new keys.

### F. Frontend: `web/`
*   **`index.html`**: Layout grid. Left panel = Config form. Right panel = Logs & Controls.
*   **`script.js`**:
    *   Listens for button clicks (Save, Launch, Solve).
    *   Calls backend API: `pywebview.api.save_settings(...)`.
    *   Updates the "Session Log" terminal when Python sends events.
    *   Enforces mutual exclusion (e.g., disabling Guess Mode inputs when Stealth Mode is on).

---

## 4. Operational Data Flow

1.  **User Configuration**: User sets API Key and Model in GUI -> Clicks "Save" -> `app_webview.py` updates `config.py` -> Writes to `config.json`.
2.  **Launch**: User clicks "Launch Browser" -> `main.py` starts ChromeDriver.
3.  **Solving**:
    *   User navigates manually to a Quiz.
    *   User clicks "Start Solving" -> `app_webview.py` spawns a thread running `AutomationController.run_solver_loop`.
    *   **Loop**:
        *   `Scraper` reads DOM.
        *   `Solver` sends data to Gemini Cloud (or Guesses).
        *   `Gemini` returns "B".
        *   `Controller` finds inputs with value "B".
        *   `Controller` clicks Input -> Clicks Submit.
        *   `Controller` waits for "Next" button.
