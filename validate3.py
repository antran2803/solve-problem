import re
import unicodedata

from validate import Validate_Text


class Validate_Text_3(Validate_Text):
    REPLACE_WORDS = {
        "0": "o",
        "1": "i",
        "3": "e",
        "4": "a",
        "5": "s",
        "7": "t",
        "@": "a",
        "$": "s",
        "!": "i",
    }

    def normalize_text(self, text):
        text = text.lower()
        text = unicodedata.normalize("NFC", text)

        for old, new in self.REPLACE_WORDS.items():
            text = text.replace(old, new)

        # Giữ chữ tiếng Việt có dấu
        text = re.sub(
            r"[^\w\s]|_",
            " ",
            text,
            flags=re.UNICODE,
        )

     
        text = re.sub(r"(.)\1{1,}", r"\1", text)
        text = re.sub(r"\s+", " ", text).strip()

        return text

    def remove_vietnamese_tones(self, text):
        text = text.replace("đ", "d").replace("Đ", "D")
        text = unicodedata.normalize("NFD", text)
        text = "".join(
            character
            for character in text
            if not unicodedata.combining(character)
        )
        return unicodedata.normalize("NFC", text)

    def create_pattern(self, normalized_word):
        word_parts = normalized_word.split()
        flexible_parts = []

        for part in word_parts:
            characters = [
                re.escape(character)
                for character in part
            ]

            # VD: "từ cấm" -> "từ\s*cấm"
            flexible_parts.append(r"\s*".join(characters))

        flexible_word = r"\s+".join(flexible_parts)

        return rf"(?<!\w){flexible_word}(?!\w)"

    def find_sensitive_words(self, normalized_text):
        sensitive_words = []
        unsigned_text = self.remove_vietnamese_tones(normalized_text)

        for category, words in self.bad_words.items():
            for word in words:
                normalized_word = self.normalize_text(word)
                pattern = self.create_pattern(normalized_word)
                matched = re.search(pattern, normalized_text)

                unsigned_word = self.remove_vietnamese_tones(normalized_word)
                if (
                    not matched
                    and unsigned_word != normalized_word
                    and " " in normalized_word
                ):
                    unsigned_pattern = self.create_pattern(unsigned_word)
                    matched = re.search(unsigned_pattern, unsigned_text)

                if matched:
                    sensitive_words.append({
                        "category": self.CATEGORY_NAMES.get(
                            category,
                            category,
                        ),
                        "word": word,
                    })

        return sensitive_words
