"""Các hàm hỗ trợ xử lý văn bản dùng chung."""

import re
import unicodedata
from unidecode import unidecode
REPLACE_WORDS = {
    "0" : "o",
    "1" : "i",
    "3" : "e",
    "4": "a",
    "5": "s",
    "7": "t",
    "@": "a",
    "$": "s",
    "!": "i",
    "z": "n",
    "j": "i",
    }
def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFC", text).lower()
    for old,new in REPLACE_WORDS.items():
        text = text.replace(old,new)
    text = unidecode(text)
    text = re.sub(r"[^a-z0-9\s]", "", text)
    text = re.sub(r"(.)\1{1,}", r"\1", text)
    return re.sub(r"\s+", " ", text).strip()

