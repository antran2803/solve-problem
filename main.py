
from app.services.validate_service import ValidateService


def main() -> None:
    service = ValidateService()
    text = input("Nhập nội dung: ")
    result = service.validate(text)
    print(result["message"])


if __name__ == "__main__":
    main()
