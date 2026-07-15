
from app.services.validate_service import ValidateService

def main() -> None:
    service = ValidateService()
    text = input("Nhập nội dung: ")
    result = service.validate(text)
    print("Trạng thái:", result["status"])
    print("Nguồn:", result["source"])
    print("Signal:", result.get("signals", []))
    print("Confidence:", result["confidence"])
    print("Message:", result["message"])
    print("Candidate Words:", result.get("matched_words", []))

if __name__ == "__main__":
    main()
