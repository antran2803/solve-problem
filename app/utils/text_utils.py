"""Các hàm hỗ trợ xử lý văn bản dùng chung."""

import re
import unicodedata
from unidecode import unidecode
REPLACE_WORDS = {
        "0": "o",
        "1": "i",
        "3": "e",
        "4": "a",
        "5": "s",
        "7": "t",
        "@": "a",
        "$": "s",
        "z": "n",
        "!": "i",
    }
def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFC", text).lower()
    for old, new in REPLACE_WORDS.items():
        text = text.replace(old, new)

    text = re.sub(r"[^\w\s]|_"," ",text,flags=re.UNICODE)    
    text = re.sub(r"(.)\1{1,}", r"\1", text)    
    text = re.sub(r"\s+", " ", text).strip()

    return text

def remove_vietnamese_tones(text: str) -> str:
    text = text.replace("đ", "d").replace("Đ", "D")
    text = unicodedata.normalize("NFD", text)
    text = "".join(
        character for character in text if not unicodedata.combining(character)
    )
    return unicodedata.normalize("NFC", text)

def create_pattern(normalized_word: str) -> str:
    word_parts = normalized_word.split()
    flexible_parts = []
    for part in word_parts:
        characters = [re.escape(character) for character in part]
        flexible_parts.append(r"\s*".join(characters))

    flexible_word = r"\s+".join(flexible_parts)
    return rf"(?<!\w){flexible_word}(?!\w)"
