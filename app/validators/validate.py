"""Thuật toán kiểm tra độ dài và từ cấm trong nội dung."""

import json
from pathlib import Path
from typing import Any
import re
from app.utils.text_utils import normalize_text , remove_vietnamese_tones, create_pattern


DEFAULT_BAD_WORDS_PATH = Path(__file__).resolve().parents[1] / "data" / "bad_words.json"


class ValidateText:

    CATEGORY_NAMES = {
        "sensitive": "Nhạy cảm",
        "profanity": "Thô tục",
        "politics": "Chính trị",
        "negative": "Tiêu cực",
    }

    def __init__(
        self,
        file_path: str | Path | None = None,
        text: str | None = None,
        bad_words: dict[str, list[str]] | None = None,
    ) -> None:
        self.file_path = Path(file_path) if file_path else DEFAULT_BAD_WORDS_PATH
        self.bad_words = bad_words if bad_words is not None else self.load_bad_words()
        self.text = text

    def load_bad_words(self) -> dict[str, list[str]]:
        with self.file_path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def normalize_text(self, text: str) -> str:
        return normalize_text(text)
    def remove_vietnamese_tones(self, text: str) -> str:
        return remove_vietnamese_tones(text)
    def create_pattern(self, normalized_word: str) -> str:
        return create_pattern(normalized_word)
    def find_sensitive_words(self, normalized_text: str) -> list[dict[str, str]]:
        sensitive_words = []
        unsigned_text = self.remove_vietnamese_tones(normalized_text)
        for category, words in self.bad_words.items():
            for word in words:
                normalized_word = self.normalize_text(word)
                pattern = self.create_pattern(normalized_word)
                matched = re.search(pattern, normalized_text)
                unsigned_word = self.remove_vietnamese_tones(normalized_word)
                if (
                    not matched
                    and unsigned_word != normalized_word
                    and " " in normalized_word
                ):
                    unsigned_pattern = self.create_pattern(unsigned_word)
                    matched = re.search(unsigned_pattern, unsigned_text)

                if matched:
                    sensitive_words.append({
                        "category": self.CATEGORY_NAMES.get(
                            category,
                            category,
                        ),
                        "word": word,
                    })

        return sensitive_words

    def validate(self, text: str) -> dict[str, Any]:
        normalized_text = self.normalize_text(text)

        if len(normalized_text) > 100:
            return {
                "valid": False,
                "message": "Nội dung vượt quá 100 ký tự.",
            }

        sensitive_words = self.find_sensitive_words(normalized_text)
        if sensitive_words:
            details = ", ".join(
                f"{item['word']} - {item['category']}" for item in sensitive_words
            )
            return {
                "valid": False,
                "message": f"Nội dung chứa từ cấm: {details}",
            }

        return {
            "valid": True,
            "message": text,
        }

    def validate_text(self, text: str):
        return self.validate(text)
