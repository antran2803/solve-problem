# Solve Problem — Validate Version 4

Validate Version 4 gồm phần kiểm duyệt theo rule kế thừa từ `validate3` và phần **AI review**. Rule chặn nội dung trống hoặc dài hơn 100 ký tự, chuẩn hóa văn bản, nhận diện các phép thay ký tự như `$ → s`, tìm từ trong blacklist thuộc nhóm thô tục, nhạy cảm, chính trị và tiêu cực, đồng thời ghi nhận năm dấu hiệu: ký tự đặc biệt, ký tự lặp, ký tự bị tách, cách viết Telex bất thường và ký tự thay thế. Kết quả do rule phát hiện chỉ là candidate cần xem xét; AI sẽ phục hồi dấu hoặc nghĩa khi cần và đánh giá ngữ cảnh để trả về `allow`, `block` hoặc `review`. Ngưỡng confidence thông thường là `0.8`, riêng việc cho phép candidate `unsigned` cần `0.9`; nếu không đủ ngưỡng hoặc API lỗi, hệ thống giữ `review`. Unit test sử dụng AI giả nên không gọi API thật và không tốn quota.

## Chức năng chính

- Chặn nội dung trống hoặc dài hơn 100 ký tự bằng rule.
- Chuẩn hóa Unicode, chữ thường, dấu câu, khoảng trắng và ký tự lặp.
- Nhận diện một số cách thay ký tự như `0 → o`, `1 → i`, `@ → a`, `z → n`.
- Phát hiện từ trong blacklist theo ba kiểu:
  - `exact`: khớp trực tiếp;
  - `flexible`: ký tự bị tách bởi dấu câu hoặc khoảng trắng;
  - `unsigned`: khớp với phiên bản tiếng Việt không dấu.
- Ghi nhận các dấu hiệu lách luật như ký tự đặc biệt, ký tự lặp, ký tự bị tách
  và một số cách viết Telex bất thường.
- Dùng AI để phục hồi cách hiểu có dấu cho trường hợp mơ hồ rồi đánh giá ngữ
  cảnh theo các category.
- Có confidence threshold và fallback khi AI/API gặp lỗi.
- Unit test không gọi API thật, không tiêu tốn quota.

## Cấu trúc project

solve-problem/
├── .env.example                   
├── .gitignore                      
├── main.py                         
├── README.md                       # Tài liệu project
├── requirements.txt                # Các thư viện Python cần cài
│
├── app/
│   ├── __init__.py                 
│   │
│   ├── Ai_models/
│   │   └── models.py               # Groq client, phục hồi nghĩa và AI review
│   │
│   ├── data/
│   │   ├── __init__.py
│   │   └── bad_words.json          # Blacklist chia theo category
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   └── validate_service.py     # Điều phối rule, AI
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   └── text_utils.py           # Normalize, signals, bỏ dấu và tạo regex
│   │
│   └── validators/
│       ├── __init__.py
│       └── validate.py             # Kiểm tra rule và tạo candidate
│
└── tests/
    ├── __init__.py
    └── test_validate.py           
```

## Vai trò từng thành phần

### `main.py`

Điểm chạy của chương trình CLI. File này chỉ:

1. tạo `ValidateService`;
2. nhận nội dung từ người dùng;
3. gọi `service.validate(text)`;
4. hiển thị trạng thái, nguồn, message và candidate.

`main.py` không chứa thuật toán normalize, regex hoặc lời gọi Groq trực tiếp.

### `app/utils/text_utils.py`

Chứa các hàm xử lý văn bản dùng chung:

- `normalize_text()`: trả về nội dung đã chuẩn hóa;
- `analyze_text()`: trả nội dung chuẩn hóa kèm danh sách `signals`;
- `remove_vietnamese_tones()`: chuyển tiếng Việt có dấu sang không dấu;
- `create_pattern()`: tạo regex cho phép khoảng trắng giữa các ký tự.

Ví dụ dữ liệu phân tích:

```python
{
    "normalized_text": "n g u",
    "signals": ["special_characters", "spaced_characters"],
}
```

### `app/data/bad_words.json`

Nguồn dữ liệu blacklist hiện tại, gồm các category:

- `sensitive`: nội dung nhạy cảm, bạo lực, chất cấm;
- `profanity`: từ tục hoặc nội dung xúc phạm;
- `politics`: từ liên quan chính trị;
- `negative`: từ mang sắc thái tiêu cực.

Việc một từ nằm trong file này chỉ làm nó trở thành candidate. Đối với nội dung
cần hiểu ngữ cảnh, AI mới đưa ra đánh giá cuối cùng.

### `app/validators/validate.py`

`ValidateText` thực hiện rule validation:

1. chặn nội dung gốc dài hơn 100 ký tự;
2. phân tích và chuẩn hóa nội dung;
3. chặn nội dung rỗng sau chuẩn hóa;
4. tìm candidate theo `exact`, `flexible`, `unsigned`;
5. trả `review` nếu có candidate hoặc signal;
6. trả `allow` nếu không phát hiện dấu hiệu cần xem xét.

Validator không gọi API và không phụ thuộc giao diện CLI.

### `app/Ai_models/models.py`

`AIReviewService` sử dụng Groq API với model hiện tại:

```text
llama-3.3-70b-versatile
```

Đối với candidate `unsigned`, `fuzzy` hoặc nội dung có signal, AI chạy hai bước:

1. **Context restoration**: phục hồi dấu và cách hiểu tiếng Việt mà không kiểm
   duyệt hay làm nhẹ nghĩa của từ;
2. **Moderation review**: đối chiếu nội dung gốc, candidate, signals và kết quả
   phục hồi để trả `allow`, `block` hoặc `review`.

Groq được yêu cầu trả JSON Object. Code tiếp tục kiểm tra kiểu dữ liệu của
`decision`, `candidate_assessment` và `confidence` trước khi sử dụng.

### `app/services/validate_service.py`

`ValidateService` là lớp điều phối trung tâm:

1. đọc `bad_words.json`;
2. truyền dữ liệu vào `ValidateText`;
3. trả ngay kết quả `allow/block` chắc chắn từ rule;
4. gọi AI nếu rule trả `review`;
5. áp dụng confidence threshold;
6. trả fallback `review` nếu AI/API phát sinh lỗi.

Ngưỡng hiện tại:

- kết quả thông thường cần confidence từ `0.8`;
- AI muốn `allow` một candidate chỉ khớp theo `unsigned` cần confidence từ
  `0.9`;
- dưới ngưỡng, hệ thống giữ trạng thái `review` thay vì tự động kết luận.

## Quy trình hoạt động

```text
Input
  ↓
ValidateService đọc blacklist
  ↓
ValidateText phân tích và normalize
  ↓
Kiểm tra rỗng / độ dài / candidate / signals
  ↓
  ├─ Rule chắc chắn allow hoặc block → trả kết quả ngay
  │
  └─ Rule trả review
       ↓
     Candidate không có dấu hoặc có signal?
       ├─ Có → AI phục hồi dấu/ngữ nghĩa
       └─ Không → dùng nguyên nội dung
       ↓
     AI đánh giá category, ý định và ngữ cảnh
       ↓
     ValidateService kiểm tra confidence (0 -> 1)
       ├─ Đủ ngưỡng → allow / block / review
       ├─ Thiếu ngưỡng → review
       └─ API lỗi → review, source=fallback
       
```

## Kết quả trả về

Ví dụ cấu trúc kết quả:

```python
{
    "status": "allow",
    "source": "ai",
    "message": "Nội dung hợp lệ",
    "confidence": 0.9,
    "candidate_assessment": "false_positive",
    "matched_words": [
        {
            "word": "...",
            "category": "...",
            "match_type": "unsigned",
        }
    ],
}
```

### `status`

| Giá trị | Ý nghĩa |
|---|---|
| `allow` | Nội dung được phép |
| `block` | Nội dung bị từ chối |
| `review` | Chưa đủ chắc chắn, cần kiểm tra thêm |

### `source`

| Giá trị | Ý nghĩa |
|---|---|
| `rule` | Kết quả được quyết định mà không gọi AI |
| `ai` | AI đã tham gia đánh giá |
| `fallback` | AI/API lỗi, hệ thống giữ trạng thái an toàn `review` |

`matched_words` là danh sách candidate khiến nội dung được xem xét, không phải
kết luận cuối cùng rằng tất cả các candidate đều vi phạm.

## Yêu cầu môi trường

- Python 3.10 trở lên;
- kết nối Internet khi chạy AI review;
- Groq API key cho chế độ chạy thật.

Các dependency trong `requirements.txt`:

| Package | Mục đích |
|---|---|
| `Unidecode` | Hỗ trợ xử lý văn bản không dấu |
| `groq` | Groq Python SDK |
| `python-dotenv` | Đọc API key từ `.env` |

## Cài đặt

Tạo virtual environment:

```powershell
python -m venv .venv
```

Kích hoạt trên Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Trên macOS/Linux:

```bash
source .venv/bin/activate
```

Cài dependency:

```powershell
python -m pip install -r requirements.txt
```

## Lấy và cấu hình Groq API key

1. Đăng nhập hoặc tạo tài khoản tại [GroqCloud Console](https://console.groq.com/).
2. Mở trang [API Keys](https://console.groq.com/keys).
3. Chọn **Create API Key**, đặt tên cho key và tạo key. Theo GroqCloud, chỉ
   owner hoặc thành viên có role developer mới có thể tạo/quản lý API key.
4. Sao chép key và lưu ở nơi an toàn; không gửi key qua chat và không commit vào
   Git.
5. Tại thư mục gốc project, tạo `.env` từ file mẫu.

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

macOS/Linux:

```bash
cp .env.example .env
```

6. Mở `.env` và thay giá trị mẫu:

```env
GROQ_API_KEY=gsk_your_real_key_here
```

Project sử dụng `python-dotenv` để đọc `.env`, sau đó khởi tạo Groq client bằng
`GROQ_API_KEY`. Xem thêm [Groq Quickstart](https://console.groq.com/docs/quickstart).

### Bảo mật API key

- `.env` đã nằm trong `.gitignore` và không được commit.
- `.env.example` chỉ chứa placeholder và được phép commit.
- Nếu key từng xuất hiện trong Git, log hoặc ảnh chụp công khai, hãy thu hồi key
  đó trên GroqCloud và tạo key mới.

## Chạy chương trình

Sau khi kích hoạt virtual environment và cấu hình `.env`:

```powershell
python main.py
```

Output CLI gồm:

```text
Trạng thái: allow | block | review
Nguồn: rule | ai | fallback
Message: ...
Candidate Words: [...]
```

Nội dung sạch hoặc bị rule chặn có thể không gọi Groq. Nội dung cần phục hồi
ngữ nghĩa có thể thực hiện hai API request: một request phục hồi và một request
moderation.

## Chạy test

Chạy toàn bộ unit test từ thư mục gốc:

```powershell
python -m unittest discover -s tests -v
```

Unit test dùng AI giả nên:

- không cần Internet;
- không gọi Groq;
- không tốn API quota;
- có kết quả ổn định.

Chạy một test cụ thể:

```powershell
python -m unittest tests.test_validate.ValidateServiceTests.test_clean_text_is_allowed_without_ai -v
```

Kiểm tra syntax toàn bộ code:

```powershell
python -m compileall -q main.py app tests
```

### Test tích hợp với AI thật

1. Cấu hình `GROQ_API_KEY` trong `.env`.
2. Đảm bảo máy có Internet.
3. Chạy `python main.py`.
4. Thử các nhóm input:
   - nội dung sạch;
   - nội dung quá 100 ký tự;
   - từ khớp trực tiếp;
   - từ bị tách bởi dấu câu/khoảng trắng;
   - nội dung không dấu có nhiều cách hiểu;
   - câu hỏi, trích dẫn hoặc nội dung giáo dục;
   - mỗi category trong `bad_words.json`.
5. Kiểm tra `status`, `source`, `message`, `confidence` và candidate có thống
   nhất hay không.

Không nên coi một lần chạy thủ công là đủ để đánh giá độ chính xác. Hãy lưu các
case đã xác nhận vào test dataset với kết quả mong đợi để theo dõi false positive
và false negative qua từng version.

## Tích hợp với Django

Django View chỉ cần gọi service thay vì viết lại validator:

```python
from app.services.validate_service import ValidateService


service = ValidateService()
result = service.validate(request.POST.get("text", ""))
```

View chịu trách nhiệm chuyển `result` thành HTTP response; service, validator và
AI review không cần biết request đến từ CLI hay Django.

## Giới hạn hiện tại

- AI có thể đánh giá sai hoặc không ổn định; confidence không phải bằng chứng
  tuyệt đối.
- Văn bản không dấu có thể có nhiều cách hiểu và phục hồi sai.
- Các phép thay ký tự có thể tạo false positive.
- Blacklist không thể bao phủ mọi cách lách luật.
- Trạng thái `review` cần được xử lý phù hợp, ví dụ chuyển sang người kiểm duyệt
  hoặc yêu cầu người dùng sửa nội dung.
- Việc gọi AI làm tăng độ trễ và có thể tiêu tốn quota/chi phí.

Version 4 ưu tiên giữ `review` khi chưa đủ chắc chắn thay vì ép hệ thống luôn
phải chọn `allow` hoặc `block`.
