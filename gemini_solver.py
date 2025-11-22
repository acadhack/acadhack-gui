"""
gemini_solver.py

The AI brain for AcadHack, powered by Google Gemini.
"""

import time
import re
from typing import Any, Dict, List, Union

import google.generativeai as genai


class GeminiSolver:
    """
    Wrapper around the Google Gemini model to solve multiple-choice questions.

    It:
    - Enforces a simple rate limit (for 15 RPM).
    - Accepts multimodal quiz_data from the scraper.
    - Sends text/images to Gemini.
    - Returns a single capital letter: A, B, C, or D.
    """

    def __init__(self, api_key: str, model_name: str, rate_limit_interval: float) -> None:
        if not api_key:
            raise ValueError("API key is required for GeminiSolver.")

        self.api_key = api_key
        self.model_name = model_name
        self.rate_limit_interval = float(rate_limit_interval)
        self._last_request_time = 0.0

        # Configure the Gemini client
        genai.configure(api_key=self.api_key)

        # System instruction: be strict about the format
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=(
                "You are an expert at solving multiple-choice questions.\n"
                "You will be given one question and up to four options labeled A, B, C, and D.\n"
                "Carefully analyze any text and images.\n"
                "Your entire reply MUST be exactly one single capital letter: A, B, C, or D.\n"
                "Do not include any explanations, punctuation, or extra characters.\n"
                "IMPORTANT: Mathematical expressions may be provided in LaTeX format "
                "(e.g., x^{2}). Interpret this syntax correctly."
            ),
        )

    def _enforce_rate_limit(self) -> None:
        """
        Ensure we wait long enough between requests to respect the rate limit.
        """
        now = time.time()
        elapsed = now - self._last_request_time
        remaining = self.rate_limit_interval - elapsed
        if remaining > 0:
            time.sleep(remaining)

    @staticmethod
    def _content_part_from_value(value: Union[str, bytes, List[Any]], label: str = None) -> List[Any]:
        """
        Convert a value (text, bytes, or list of them) into the list of parts suitable for
        the Gemini API.
        """
        parts: List[Any] = []
        
        # Normalize to list
        items = value if isinstance(value, list) else [value]
        
        # Add label if present
        if label:
            parts.append(f"{label}:")

        for item in items:
            if isinstance(item, bytes):
                parts.append({
                    "mime_type": "image/png",
                    "data": item,
                })
            elif isinstance(item, str):
                text = item.strip()
                if text:
                    parts.append(text)
                    
        return parts

    def _build_contents(self, quiz_data: Dict[str, Any]) -> List[Any]:
        """
        Build the multimodal content list for the Gemini API from quiz_data.
        """
        contents: List[Any] = []

        # High-level instruction as user content (system instruction is separate)
        contents.append(
            "You will receive one question and several answer options. "
            "Identify the single best answer and respond ONLY with its letter."
        )

        # Question
        question_value = quiz_data.get("question")
        contents.extend(self._content_part_from_value(question_value, label="Question"))

        # Options
        options = quiz_data.get("options", {})
        if isinstance(options, dict):
            # Sort by label so A,B,C,D are in order if present
            for label in sorted(options.keys()):
                value = options[label]
                contents.extend(
                    self._content_part_from_value(value, label=f"Option {label}")
                )

        # Very explicit reminder at the end
        contents.append(
            "Final answer: respond with exactly one capital letter: A, B, C, or D."
        )

        return contents

    @staticmethod
    def _extract_letter(raw_text: str) -> str:
        """
        Extract the first capital letter A–D from the model's raw response.
        Fallback: default to 'A' if nothing suitable is found.
        """
        if not raw_text:
            return "A"

        raw = raw_text.strip().upper()

        # Look for A/B/C/D as a standalone token
        match = re.search(r"\b([ABCD])\b", raw)
        if match:
            return match.group(1)

        # Otherwise, scan characters in order and pick the first A–D we see
        for ch in raw:
            if ch in "ABCD":
                return ch

        # Ultra-paranoid fallback
        return "A"

    def get_answer(self, quiz_data: Dict[str, Any]) -> str:
        """
        Call Gemini with the multimodal quiz_data and return a single
        capital letter: A, B, C, or D.
        """
        self._enforce_rate_limit()

        contents = self._build_contents(quiz_data)

        try:
            response = self.model.generate_content(contents)
        except Exception as e:
            print(f"[GeminiSolver] Error calling Gemini API: {e}")
            # When in doubt, pick A—better to click something than crash
            answer = "A"
        else:
            self._last_request_time = time.time()
            raw = getattr(response, "text", "") or ""
            answer = self._extract_letter(raw)

        print(f"[GeminiSolver] Model chose answer: {answer}")
        return answer
