# 💻 AcadHack GUI (Windows Desktop Application) [WIP]

AcadHack GUI is the final, user-friendly desktop application designed for non-technical users on Windows. It provides a modern interface, real-time logging, and automatic setup for solving online quizzes using AI.

## ✨ Key Features

*   **Simple Interface:** Modern, two-pane design built with CustomTkinter.
*   **One-Click Automation:** Automatically launches and manages its own Chrome browser session—no manual setup required.
*   **Real-time Feedback:** Live log updates show the progress of solving each question.
*   **Persistent Configuration:** Saves your Gemini API key and settings locally.
*   **Robustness:** Uses `webdriver-manager` to ensure compatibility with all Chrome browser updates.

## 🏗 Architectural Overview

This application separates concerns using a standard desktop architecture pattern:

*   **Frontend (Main Thread):** `app_gui.py` handles the CustomTkinter interface, user input, and logging display.
*   **Backend (Worker Thread):** `main.py` (containing the `AutomationController` class) runs the long-running Selenium tasks, ensuring the GUI never freezes.
*   **Communication:** Utilizes Python's `threading` and `queue` for thread-safe logging and control.

## Installation (Windows)

The simplest way to run AcadHack is using the pre-packaged executable:

1.  Download the latest `AcadHack.exe` from the [Releases page].
2.  Run the executable.
3.  Enter your Gemini API Key in the settings panel and click "Save."
4.  Navigate to your quiz page in the opened Chrome browser and click "START."

## 📚 Core Components

| File | Role |
| :--- | :--- |
| `app_gui.py` | The CustomTkinter graphical interface and thread manager. |
| `main.py` | Contains the `AutomationController` (the automation engine). |
| `config_manager.py` | Handles reading and writing persistent settings to `config.py`. |
| `scraper.py` / `gemini_solver.py` | Core reusable logic for web interaction and AI solving. |

## Development and Contribution

If you wish to run from source, ensure you install all dependencies:
`pip install customtkinter selenium webdriver-manager google-generativeai`

We welcome contributions focused on improving the GUI, UX, and the configuration management features.
