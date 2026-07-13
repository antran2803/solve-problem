"""Service điều phối việc đọc dữ liệu và kiểm tra nội dung."""

import json
from pathlib import Path

from app.validators.validate import ValidateText


DEFAULT_BAD_WORDS_PATH = Path(__file__).resolve().parents[1] / "data" / "bad_words.json"


class ValidateService:

    def __init__(self, data_path: str | Path | None = None) -> None:
        self.data_path = Path(data_path) if data_path else DEFAULT_BAD_WORDS_PATH
        self.validator = ValidateText(bad_words=self._load_bad_words())

    def _load_bad_words(self) -> dict[str, list[str]]:
        with self.data_path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def validate(self, text: str) -> dict[str, object]:
        return self.validator.validate(text)

    def validate_text(self, text: str) -> dict[str, object]:
        return self.validate(text)
