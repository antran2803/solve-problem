from validate import Validate_Text
from validate2 import Validate_Text_2
from validate3 import Validate_Text_3


while True:
    print("\n1. Validate phiên bản 1")
    print("2. Validate phiên bản 2")
    print("3. Validate phiên bản 3")
    print("4. Thoát")

    choice = input("Chọn chức năng (1-4): ").strip()

    if choice == "4":
        print("Đã thoát chương trình.")
        break

    if choice == "1":
        validator = Validate_Text()
    elif choice == "2":
        validator = Validate_Text_2()
    elif choice == "3":
        validator = Validate_Text_3()
    else:
        print("Lựa chọn không hợp lệ.")
        continue

    text = input("Nhập text cần kiểm tra: ")
    result = validator.validate_text(text)
    print(result["message"])
