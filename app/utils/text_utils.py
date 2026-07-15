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
        "j": "i",
    }
def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFC", text).lower()
    for old, new in REPLACE_WORDS.items():
        text = text.replace(old, new)

    text = re.sub(r"[^\w\s]|_"," ",text,flags=re.UNICODE)    
    text = re.sub(r"(.)\1{2,}", r"\1", text)
    text = re.sub(r"\b(\w+)\s+\1\b", r"\1", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text

def analyze_text(text:str) ->dict:
    normalized = unicodedata.normalize("NFC", text).lower()
    signals=[]
    if re.search(r"\w[^\w\s]+\w", normalized):
        signals.append("special_characters")
    if re.search(r"(\w)\1{2,}", normalized):
        signals.append("repeated_characters")
    if re.search(r"(?:\b\w\b[\s._-]*){3,}", normalized):
        signals.append("spaced_characters")

    if re.search(r"\bdd\w*", normalized):
        signals.append("possible_telex_obfuscation")

    for old, new in REPLACE_WORDS.items():
        if old in normalized:
            signals.append("character_replacement")

        normalized = normalized.replace(old, new)
    normalized = re.sub(r"[^\w\s]|_"," ",normalized,flags=re.UNICODE)
    normalized = re.sub(r"(\w)\1{2,}", r"\1", normalized)
    normalized = re.sub(r"(?<!\w)(\w)(?:\s+\1)+(?!\w)",r"\1",normalized,)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return {
        "normalized_text": normalized,
        # ---------------------
        "signals": signals,
        # ---------------------
    }
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
