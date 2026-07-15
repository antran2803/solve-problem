"""Kiểm thử luồng validate chính mà không gọi API AI thật."""

import unittest

from app.services.validate_service import ValidateService


class FakeAIReviewService:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error
        self.call_count = 0
        self.last_text = None
        self.last_rule_result = None

    def review_text(self, text, rule_result):
        self.call_count += 1
        self.last_text = text
        self.last_rule_result = rule_result
        if self.error:
            raise self.error
        return self.result


class ValidateServiceTests(unittest.TestCase):
    # Trường 
    def test_clean_text_is_allowed_without_ai(self):
        ai = FakeAIReviewService()
        service = ValidateService(ai_review_service=ai)

        result = service.validate("Xin chào mọi người")

        self.assertEqual("allow", result["status"])
        self.assertEqual("rule", result["source"])
        self.assertEqual(0, ai.call_count)

    def test_text_longer_than_100_characters_is_blocked_without_ai(self):
        ai = FakeAIReviewService()
        service = ValidateService(ai_review_service=ai)

        result = service.validate("a" * 101)

        self.assertEqual("block", result["status"])
        self.assertEqual("rule", result["source"])
        self.assertEqual(0, ai.call_count)

    def test_empty_text_is_blocked_without_ai(self):
        ai = FakeAIReviewService()
        service = ValidateService(ai_review_service=ai)

        result = service.validate("")

        self.assertEqual("block", result["status"])
        self.assertEqual("rule", result["source"])
        self.assertEqual("Nội dung trống.", result["message"])
        self.assertEqual(0, ai.call_count)

    def test_whitespace_only_text_is_blocked_without_ai(self):
        ai = FakeAIReviewService()
        service = ValidateService(ai_review_service=ai)

        result = service.validate("   \t  ")

        self.assertEqual("block", result["status"])
        self.assertEqual("rule", result["source"])
        self.assertEqual(0, ai.call_count)

    def test_punctuation_only_text_is_blocked_without_ai(self):
        ai = FakeAIReviewService()
        service = ValidateService(ai_review_service=ai)

        result = service.validate("...???")

        self.assertEqual("block", result["status"])
        self.assertEqual("rule", result["source"])
        self.assertEqual("Nội dung trống.", result["message"])
        self.assertEqual(0, ai.call_count)

    def test_text_with_exactly_100_characters_is_not_blocked_by_length(self):
        ai = FakeAIReviewService()
        service = ValidateService(ai_review_service=ai)
        text = ("ab " * 33) + "a"
        self.assertEqual(100, len(text))

        result = service.validate(text)

        self.assertEqual("allow", result["status"])
        self.assertEqual("rule", result["source"])
        self.assertEqual(0, ai.call_count)

    def test_blacklist_word_inside_a_longer_word_is_not_matched(self):
        ai = FakeAIReviewService()
        service = ValidateService(ai_review_service=ai)

        result = service.validate("Bạn có nguồn tài liệu hữu ích")

        self.assertEqual("allow", result["status"])
        self.assertEqual("rule", result["source"])
        self.assertEqual([], result["matched_words"])
        self.assertEqual(0, ai.call_count)

    def test_exact_blacklist_match_is_sent_to_ai(self):
        ai = FakeAIReviewService(
            {
                "status": "allow",
                "confidence": 0.95,
                "message": "Nội dung mang tính giải thích",
                "source": "ai",
            }
        )
        service = ValidateService(ai_review_service=ai)

        result = service.validate("Câu hỏi này giải thích từ ngu")

        self.assertEqual("allow", result["status"])
        self.assertEqual(1, ai.call_count)
        self.assertIn(
            {
                "word": "ngu",
                "category": "Thô tục",
                "match_type": "exact",
            },
            ai.last_rule_result["matched_words"],
        )

    def test_spaced_blacklist_word_is_detected_as_flexible(self):
        ai = FakeAIReviewService(
            {
                "status": "allow",
                "confidence": 0.95,
                "message": "Nội dung minh họa cách tách ký tự",
                "source": "ai",
            }
        )
        service = ValidateService(ai_review_service=ai)

        result = service.validate("Ví dụ n g u để kiểm tra cách tách ký tự")

        self.assertEqual("allow", result["status"])
        self.assertIn("spaced_characters", ai.last_rule_result["signals"])
        self.assertIn(
            {
                "word": "ngu",
                "category": "Thô tục",
                "match_type": "flexible",
            },
            ai.last_rule_result["matched_words"],
        )

    def test_special_characters_are_sent_to_ai_for_review(self):
        ai = FakeAIReviewService(
            {
                "status": "allow",
                "confidence": 0.9,
                "message": "Nội dung hợp lệ",
                "source": "ai",
            }
        )
        service = ValidateService(ai_review_service=ai)

        result = service.validate("xin.chao mọi người")

        self.assertEqual("allow", result["status"])
        self.assertEqual("ai", result["source"])
        self.assertIn("special_characters", ai.last_rule_result["signals"])

    def test_repeated_characters_are_sent_to_ai_for_review(self):
        ai = FakeAIReviewService(
            {
                "status": "allow",
                "confidence": 0.9,
                "message": "Nội dung hợp lệ",
                "source": "ai",
            }
        )
        service = ValidateService(ai_review_service=ai)

        result = service.validate("Hôm nay đẹppp quá")

        self.assertEqual("allow", result["status"])
        self.assertIn("repeated_characters", ai.last_rule_result["signals"])

    def test_character_replacement_is_sent_to_ai_for_review(self):
        ai = FakeAIReviewService(
            {
                "status": "allow",
                "confidence": 0.9,
                "message": "Nội dung hợp lệ",
                "source": "ai",
            }
        )
        service = ValidateService(ai_review_service=ai)

        result = service.validate("h0m nay vui")

        self.assertEqual("allow", result["status"])
        self.assertIn("character_replacement", ai.last_rule_result["signals"])

    def test_possible_telex_obfuscation_is_sent_to_ai_for_review(self):
        ai = FakeAIReviewService(
            {
                "status": "allow",
                "confidence": 0.9,
                "message": "Nội dung hợp lệ",
                "source": "ai",
            }
        )
        service = ValidateService(ai_review_service=ai)

        result = service.validate("dday la noi dung")

        self.assertEqual("allow", result["status"])
        self.assertIn("possible_telex_obfuscation", ai.last_rule_result["signals"])

    def test_multiple_blacklist_categories_are_preserved_for_ai(self):
        ai = FakeAIReviewService(
            {
                "status": "allow",
                "confidence": 0.95,
                "message": "Nội dung phân tích ngôn ngữ",
                "source": "ai",
            }
        )
        service = ValidateService(ai_review_service=ai)

        result = service.validate("Bài viết phân tích hai từ ngu và vô dụng")

        categories = {
            item["category"] for item in ai.last_rule_result["matched_words"]
        }
        self.assertEqual("allow", result["status"])
        self.assertIn("Thô tục", categories)
        self.assertIn("Tiêu cực", categories)

    def test_ai_can_allow_an_unsigned_false_positive(self):
        ai = FakeAIReviewService(
            {
                "status": "allow",
                "confidence": 0.95,
                "category": None,
                "reason": "dang được hiểu là đang",
                "message": "Nội dung hợp lệ",
                "matched_words": [],
                "source": "ai",
            }
        )
        service = ValidateService(ai_review_service=ai)

        result = service.validate("toi dang hoc bai")

        self.assertEqual("allow", result["status"])
        self.assertEqual("ai", result["source"])
        self.assertEqual("Nội dung hợp lệ", result["message"])
        self.assertEqual(1, ai.call_count)
        self.assertIn(
            {
                "word": "đảng",
                "category": "Chính trị",
                "match_type": "unsigned",
            },
            ai.last_rule_result["matched_words"],
        )

    def test_unsigned_allow_requires_high_confidence(self):
        ai = FakeAIReviewService(
            {
                "status": "allow",
                "confidence": 0.8,
                "message": "Nội dung hợp lệ",
                "source": "ai",
            }
        )
        service = ValidateService(ai_review_service=ai)

        result = service.validate("toi dang hoc bai")

        self.assertEqual("review", result["status"])
        self.assertEqual("ai", result["source"])

    def test_unsigned_allow_below_09_requires_review(self):
        ai = FakeAIReviewService(
            {
                "status": "allow",
                "confidence": 0.89,
                "message": "Nội dung hợp lệ",
                "source": "ai",
            }
        )
        service = ValidateService(ai_review_service=ai)

        result = service.validate("cac ban dang lam gi")

        self.assertEqual("review", result["status"])
        self.assertEqual("ai", result["source"])

    def test_unsigned_allow_at_09_is_accepted(self):
        ai = FakeAIReviewService(
            {
                "status": "allow",
                "confidence": 0.9,
                "message": "Nội dung hợp lệ",
                "source": "ai",
            }
        )
        service = ValidateService(ai_review_service=ai)

        result = service.validate("cac ban dang lam gi")

        self.assertEqual("allow", result["status"])
        self.assertEqual("ai", result["source"])

    def test_ai_result_below_confidence_threshold_requires_review(self):
        ai = FakeAIReviewService(
            {
                "status": "block",
                "confidence": 0.79,
                "message": "Nội dung không phù hợp",
                "source": "ai",
            }
        )
        service = ValidateService(ai_review_service=ai)

        result = service.validate("cac bn oi hom nay chung ta")

        self.assertEqual("review", result["status"])
        self.assertEqual("ai", result["source"])

    def test_ai_result_at_confidence_threshold_is_accepted(self):
        ai = FakeAIReviewService(
            {
                "status": "block",
                "confidence": 0.8,
                "message": "Nội dung cần bị chặn theo kết quả AI giả lập",
                "source": "ai",
            }
        )
        service = ValidateService(ai_review_service=ai)

        result = service.validate("h0m nay")

        self.assertEqual("block", result["status"])
        self.assertEqual("ai", result["source"])

    def test_unsigned_educational_content_can_be_allowed_with_high_confidence(self):
        ai = FakeAIReviewService(
            {
                "status": "allow",
                "confidence": 0.95,
                "message": "Nội dung mang tính giáo dục",
                "source": "ai",
            }
        )
        service = ValidateService(ai_review_service=ai)

        result = service.validate("bai hoc phan tich tac hai cua bao luc")

        self.assertEqual("allow", result["status"])
        self.assertEqual("ai", result["source"])

    def test_ai_error_returns_fallback_review(self):
        ai = FakeAIReviewService(error=RuntimeError("API unavailable"))
        service = ValidateService(ai_review_service=ai)

        result = service.validate("cac bn oi hom nay chung ta")

        self.assertEqual("review", result["status"])
        self.assertEqual("fallback", result["source"])


if __name__ == "__main__":
    unittest.main()
