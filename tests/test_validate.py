"""Kiểm thử luồng validate chính của ứng dụng."""

import unittest

from app.services.validate_service import ValidateService


class ValidateServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = ValidateService()

    def test_rejects_bad_word(self) -> None:
        result = self.service.validate("địt")

        self.assertFalse(result["valid"])
        self.assertIn("Thô tục", result["message"])

    def test_accepts_clean_text(self) -> None:
        result = self.service.validate("hello")

        self.assertTrue(result["valid"])
        self.assertEqual("hello", result["message"])

    def test_rejects_text_longer_than_100_characters(self) -> None:
        result = self.service.validate("a" * 101)

        self.assertFalse(result["valid"])
        self.assertEqual("Nội dung vượt quá 100 ký tự.", result["message"])


if __name__ == "__main__":
    unittest.main()
