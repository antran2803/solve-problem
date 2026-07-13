from validate import Validate_Text
import re
from unidecode import unidecode
class Validate_Text_2(Validate_Text):
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
    def normalize_text(self, text):
        text = super().normalize_text(text)

        for old, new in self.REPLACE_WORDS.items():
            text = text.replace(old, new)

        text = unidecode(text)

        text = re.sub(r"[^a-z0-9\s]", "", text)
        text = re.sub(r"(.)\1{2,}", r"\1", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def find_sensitive_words(self, normalized_text):
        
        sensitive_words = []

        for category, words in self.bad_words.items():
            for word in words:
                normalized_word = self.normalize_text(word)
        
                pattern = rf"\b{re.escape(normalized_word)}\b"

                if re.search(pattern, normalized_text):
                    sensitive_words.append({
                        "category": self.CATEGORY_NAMES.get(category, category),
                        "word": word,
                    })

        return sensitive_words

