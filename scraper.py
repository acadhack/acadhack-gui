"""
scraper.py

Multimodal scraper for AcadHack.
Hardened for specific math parsing, accurate image cropping, and text formatting.
"""

from typing import Any, Dict

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement


def parse_math_expressions(html_content: str | None) -> str:
    """
    Normalize HTML containing <sup>/<sub> into plain-text math-like notation.
    Ensures proper spacing between block elements.
    """
    if not html_content:
        return ""

    soup = BeautifulSoup(html_content, "html.parser")

    # Handle superscripts: x<sup>2</sup> -> x^2
    for sup_tag in soup.find_all("sup"):
        sup_tag.string = f"^{sup_tag.get_text()}"
        sup_tag.unwrap()

    # Handle subscripts: H<sub>2</sub>O -> H_2O
    for sub_tag in soup.find_all("sub"):
        sub_tag.string = f"_{sub_tag.get_text()}"
        sub_tag.unwrap()

    # FIX 1: Use separator=" " to prevent text merging (e.g. "correct?P:" -> "correct? P:")
    text_content = soup.get_text(separator=" ")

    # Normalize whitespace (remove extra spaces/newlines)
    return " ".join(text_content.split())


def _extract_element_content(element: WebElement) -> list[str | bytes]:
    """
    Extract BOTH text and images from an element.
    Returns a list containing strings (text) and bytes (PNG data).
    """
    content_parts = []

    # 1. Extract Text (with math parsing)
    try:
        raw_html = element.get_attribute("innerHTML")
        text = parse_math_expressions(raw_html)
        if text:
            content_parts.append(text)
    except Exception:
        text = (element.text or "").strip()
        if text:
            content_parts.append(text)

    # 2. Extract Images
    try:
        images = element.find_elements(By.TAG_NAME, "img")
        for img in images:
            try:
                if img.is_displayed():
                    # Capture specific image
                    content_parts.append(img.screenshot_as_png)
            except Exception:
                pass
    except Exception:
        pass

    # If nothing found, return empty list (or empty string if strict typing needed elsewhere, but list is safer for new logic)
    return content_parts


def scrape_quiz_data(driver: WebDriver, config, mode: str = "standard") -> Dict[str, Any]:
    """
    Scrape the current quiz question and options from the page.
    """
    wait = WebDriverWait(driver, config.DEFAULT_WAIT_TIMEOUT)

    # Determine question class based on mode
    question_class = config.QUESTION_CLASS
    if mode == "booster":
        question_class = config.BOOSTER_QUESTION_CLASS

    # Wait for the question area to be visible
    question_element: WebElement = wait.until(
        EC.visibility_of_element_located((By.CLASS_NAME, question_class))
    )

    question_content = _extract_element_content(question_element)

    # Wait for all option cards to be present
    option_cards = wait.until(
        EC.presence_of_all_elements_located((By.CLASS_NAME, config.OPTION_CARD_CLASS))
    )

    options_data: Dict[str, Any] = {}
    option_elements: Dict[str, WebElement] = {}

    for card in option_cards:
        try:
            # Get the label (A, B, C, D)
            label_el = card.find_element(By.CLASS_NAME, config.OPTION_LABEL_CLASS)
            label = (label_el.text or "").strip().upper()
        except Exception:
            continue

        if label not in config.SUPPORTED_OPTION_LABELS:
            continue

        # FIX 2: Target the specific content container (.option-text)
        # This prevents scraping the Label ("A") along with the content ("P")
        try:
            # We look for the div that holds the actual text/image
            content_element = card.find_element(By.CLASS_NAME, "option-text")
        except Exception:
            # Fallback to the whole card if the specific class isn't found
            content_element = card

        content = _extract_element_content(content_element)

        options_data[label] = content
        option_elements[label] = card  # We still click the whole card

    if not options_data:
        raise RuntimeError("No valid options (A–D) found on the page.")

    return {
        "question": question_content,
        "options": options_data,
        "option_elements": option_elements,
    }
