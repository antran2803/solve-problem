#Flow chinh
"""
Nhap text -> Chuan hoa, kiem tra do dai -> kiem tra tu cam -> tra ve ket qua
"""
import re
import json
import unicodedata

class Validate_Text:
    CATEGORY_NAMES = {
    "sensitive": "Nhạy cảm",
    "profanity": "Thô tục",
    "politics": "Chính trị",
    "negative": "Tiêu cực"
}
    def __init__(self,file_path="bad_words.json",text=None):
        self.file_path = file_path
        self.bad_words = self.load_bad_words()
        self.text = text
    def load_bad_words(self):
        with open(self.file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    def normalize_text(self,text):
        text = text.lower()
        text = unicodedata.normalize('NFC', text)
        text = re.sub(r'\s+',' ',text).strip()
        return text
    def find_sensitive_words(self,text):
        sensitive_words= []
        for category, words in self.bad_words.items():
            for word in words:
                if word in text:
                    sensitive_words.append({
                        "category": self.CATEGORY_NAMES.get(category, category),
                        "word": word
                    })
        return sensitive_words
    def validate_text(self,text):
        normalized_text = self.normalize_text(text)
        if len(normalized_text) > 100:
            return {
                "valid": False,
                "message": "Nội dung vượt quá 100 ký tự."
            }
        sensitive_words = self.find_sensitive_words(normalized_text)
        if sensitive_words:
            sensitive = ', '.join(f"{item['word']} - {item['category']}" for item in sensitive_words)
            return {
                "valid" : False,
                # liet ke ra loi cung phan loai cua loi do 
                "message" : f"Nội dung chứa từ cấm: {sensitive}"
            }
        else:
            return {
                "valid": True,
                "message": text
            }
        
# text= input("Nhập text: ")

# validator = Validate_Text(text=text)
# result = validator.validate_text(text)
# if not result["valid"]:
#     print(result["message"])
# else:
#     print(text)