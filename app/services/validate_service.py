"""Service điều phối việc đọc dữ liệu và kiểm tra nội dung."""

import json
from pathlib import Path

from app.Ai_models.models import AIReviewService
from app.validators.validate import ValidateText


DEFAULT_BAD_WORDS_PATH = Path(__file__).resolve().parents[1] / "data" / "bad_words.json"


class ValidateService:
    def __init__(self, data_path=None, ai_review_service=None):
        self.data_path = Path(data_path) if data_path else DEFAULT_BAD_WORDS_PATH
        self.validator = ValidateText(bad_words=self._load_bad_words())
        self.ai_review_service = ai_review_service or AIReviewService()

    def _load_bad_words(self):
        with self.data_path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def validate(self, text: str):
        rule_result = self.validator.validate(text)

        if rule_result["status"] != "review":
            return rule_result

        try:
            ai_result = self.ai_review_service.review_text(
                text=text,
                rule_result=rule_result,
            )
        except Exception as error:
            print(f"Error occurred while reviewing text: {error!r}")
            return {
                "status": "review",
                "message": "Chưa thể xác định nội dung, vui lòng thử lại",
                "matched_words": rule_result.get("matched_words", []),
                "signals": rule_result.get("signals", []),
                "source": "fallback",
            }

        required_confidence = self._required_confidence(
            ai_result,
            rule_result,
        )
        if ai_result["confidence"] < required_confidence:
            return {
                "status": "review",
                "message": "Nội dung cần được kiểm tra thêm",
                "matched_words": rule_result.get("matched_words", []),
                "signals": rule_result.get("signals", []),
                "source": "ai",
            }

        return ai_result

    @staticmethod
    def _required_confidence(ai_result: dict, rule_result: dict) -> float:
        candidates = rule_result.get("matched_words", [])
        only_unsigned = bool(candidates) and all(
            candidate.get("match_type") == "unsigned"
            for candidate in candidates
        )

        # Với match không dấu, ưu tiên tránh cho lọt nội dung vi phạm:
        # AI cần chắc chắn hơn khi muốn allow, còn block vẫn dùng ngưỡng chung.
        if ai_result.get("status") == "allow" and only_unsigned:
            return 0.9

        return 0.8

    def validate_text(self, text: str) -> dict[str, object]:
        return self.validate(text)
