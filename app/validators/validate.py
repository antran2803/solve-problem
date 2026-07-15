"""Thuật toán kiểm tra độ dài và từ cấm trong nội dung."""

import json
from pathlib import Path
from typing import Any
import re
from app.utils.text_utils import normalize_text , remove_vietnamese_tones, create_pattern , analyze_text


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
    def analyze_text(self, text: str) -> dict:
        return analyze_text(text)
    def remove_vietnamese_tones(self, text: str) -> str:
        return remove_vietnamese_tones(text)
    def create_pattern(self, normalized_word: str) -> str:
        return create_pattern(normalized_word)
    def find_sensitive_words(self, normalized_text: str) -> list[dict]:
        candidates = []
        for category, words in self.bad_words.items():
            for word in words:
                normalized_word = self.normalize_text(word)
                # pattern = self.create_pattern(normalized_word)
                # matched = re.search(pattern, normalized_text)
                matched = None
                match_type= None
                exact_pattern = rf"(?<!\w){re.escape(normalized_word)}(?!\w)"
                matched = re.search(exact_pattern, normalized_text)
                if matched:
                    match_type = "exact"

                if not matched:
                    flexible_pattern = self.create_pattern(normalized_word)
                    matched = re.search(flexible_pattern, normalized_text)
                    if matched:
                        match_type = "flexible"
                if not matched:
                    unsigned_word = self.remove_vietnamese_tones(normalized_word)
                    if unsigned_word != normalized_word:
                        unsigned_pattern = self.create_pattern(unsigned_word)
                        matched = re.search(unsigned_pattern, normalized_text)
                        if matched:
                            match_type = "unsigned"
                if matched:
                    candidates.append(
                        {
                            "word": word,
                            "category": self.CATEGORY_NAMES.get(category, category),
                            "match_type": match_type,
                        }
                    )
        return candidates

    def validate(self, text: str) -> dict[str, Any]:
        if len(text) > 100:
            return {
                "status": "block",
                "message": "Nội dung vượt quá 100 ký tự.",
                "source": "rule",
            }

        analysis = self.analyze_text(text)
        # normalized_text = self.normalize_text(text)
        normalized_text = analysis["normalized_text"]
        signals = analysis["signals"]
        if not normalized_text:
            return {
                "status": "block",
                "message": "Nội dung trống.",
                "source": "rule",
            }

        sensitive_words = self.find_sensitive_words(normalized_text)
        if sensitive_words or signals:
            # details = ", ".join(
            #     f"{item['word']} - {item['category']}" for item in sensitive_words
            # )
            return {
                "status":"review",
                "message": "Nội dung có sử dụng từ cấm hoặc dấu hiệu khả nghi cần được kiểm duyệt.",
                "matched_words": sensitive_words,
                "signals": signals,
                "normalized_text": normalized_text,
                "source": "rule",
            }

        return {
            "status": "allow",
            "message": text,
            "matched_words": [],
            "signals": [],
            "source": "rule",
        }

    def validate_text(self, text: str):
        return self.validate(text)
