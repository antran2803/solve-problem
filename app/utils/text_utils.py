"""Các hàm hỗ trợ xử lý văn bản dùng chung."""

import re
import unicodedata


def normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFC", text).lower()
    return re.sub(r"\s+", " ", normalized).strip()
