# Tài liệu kiểm thử (Test Plan/Document)

## 1. Mục đích kiểm thử

- Đảm bảo chương trình kiểm duyệt đúng nội dung văn bản tiếng Việt.
- Kiểm tra giới hạn tối đa 100 ký tự.
- Kiểm tra nội dung rỗng, nội dung sạch và nội dung chứa từ trong blacklist.
- Kiểm tra các cách né từ cấm như tách ký tự, lặp ký tự, dùng số hoặc ký hiệu thay chữ.
- Kiểm tra AI có phân biệt được nội dung vi phạm với nội dung giáo dục, trích dẫn hoặc tìm kiếm trợ giúp hay không.
- Kiểm tra ngưỡng tin cậy của AI và cơ chế fallback khi API lỗi.
- Đảm bảo unit test không gọi API thật và không tốn quota.

## 2. Phạm vi kiểm thử

Các thành phần được kiểm thử:

- `app/utils/text_utils.py`: chuẩn hóa và phân tích dấu hiệu bất thường.
- `app/validators/validate.py`: kiểm tra độ dài, blacklist và loại match.
- `app/services/validate_service.py`: điều phối rule, AI, confidence và fallback.
- `app/Ai_models/models.py`: phục hồi ngữ nghĩa và đánh giá bằng AI.
- `main.py`: nhận input và in kết quả ra terminal.
- `tests/test_validate.py`: các unit test tự động.

## 3. Phương pháp và công cụ kiểm thử

| Nội dung | Công cụ/cách thực hiện |
|---|---|
| Unit test | Python `unittest` |
| AI trong unit test | `FakeAIReviewService`, không gọi API thật |
| Kiểm thử thủ công | Nhập text trực tiếp bằng `python main.py` |
| Kiểm tra cú pháp | `python -m compileall -q main.py app tests` |
| Kiểm thử AI thật | Groq API và biến `GROQ_API_KEY` trong `.env` |

Chạy toàn bộ test tự động:

```powershell
python -m unittest discover -s tests -v
```

Chạy chương trình để nhập text thủ công:

```powershell
python main.py
```

Trước khi chạy `main.py`, cần tạo `.env` có `GROQ_API_KEY` hợp lệ. Code hiện tại khởi tạo AI service ngay khi chương trình bắt đầu, vì vậy kể cả case chỉ dùng rule cũng cần cấu hình key để CLI khởi động được.

Sau đó terminal hiển thị:

```text
Nhập nội dung:
```

Người kiểm thử nhập hoặc dán input rồi nhấn Enter.

## 4. Cách đọc output

Chương trình in bốn dòng chính:

```text
Trạng thái: allow | block | review
Nguồn: rule | ai | fallback
Message: nội dung thông báo
Candidate Words: danh sách từ nghi vấn
```

| Giá trị | Ý nghĩa |
|---|---|
| `allow` | Nội dung được phép |
| `block` | Nội dung bị từ chối |
| `review` | Chưa đủ chắc chắn, cần kiểm tra thêm |
| `source=rule` | Rule tự quyết định, không cần AI |
| `source=ai` | AI tham gia đánh giá |
| `source=fallback` | AI/API bị lỗi, chương trình trả kết quả an toàn |

## 5. Báo cáo unit test tự động

Kết quả chạy ngày 14/07/2026:

```text
Ran 22 tests
OK
```

| Test Case ID | Mô tả | Input chính | Output mong đợi | Kết quả |
|---|---|---|---|---|
| AT01 | Nội dung sạch | `Xin chào mọi người` | `allow`, `source=rule`, AI không được gọi | Pass |
| AT02 | Nội dung dài hơn 100 ký tự | `a` lặp 101 lần | `block`, `source=rule`, AI không được gọi | Pass |
| AT03 | Nội dung rỗng | `""` | `block`, thông báo `Nội dung trống.` | Pass |
| AT04 | Chỉ có khoảng trắng/tab | `"   \t  "` | `block`, `source=rule` | Pass |
| AT05 | Nội dung đúng 100 ký tự | Chuỗi `(\"ab \" * 33) + \"a\"` | Không bị chặn do độ dài | Pass |
| AT06 | Không match từ cấm nằm trong từ khác | `Bạn có nguồn tài liệu hữu ích` | Không nhận nhầm `ngu`; `allow` | Pass |
| AT07 | Phát hiện từ blacklist trong câu giải thích | `Câu hỏi này giải thích từ ngu` | Candidate `ngu`, loại `exact`, chuyển AI và được phép theo ngữ cảnh | Pass |
| AT08 | Phát hiện từ bị tách trong câu minh họa | `Ví dụ n g u để kiểm tra cách tách ký tự` | Candidate `ngu`, loại `flexible`, AI giả cho phép | Pass |
| AT09 | Phát hiện ký tự đặc biệt | `xin.chao mọi người` | Có signal `special_characters` | Pass |
| AT10 | Phát hiện ký tự lặp | `Hôm nay đẹppp quá` | Có signal `repeated_characters` | Pass |
| AT11 | Phát hiện số thay chữ | `h0m nay vui` | Có signal `character_replacement` | Pass |
| AT12 | Phát hiện Telex bất thường | `dday la noi dung` | Có signal `possible_telex_obfuscation` | Pass |
| AT13 | Giữ nhiều nhóm candidate trong câu phân tích | `Bài viết phân tích hai từ ngu và vô dụng` | Có nhóm `Thô tục` và `Tiêu cực`; AI giả cho phép theo ngữ cảnh | Pass |
| AT14 | AI cho phép false positive không dấu rõ ngữ cảnh | `toi dang hoc bai` | Rule nhận `dang` thành candidate `đảng`; fake AI hiểu là `đang` và trả `allow` với confidence `0.95` | Pass |
| AT15 | Allow match không dấu chưa đủ ngưỡng | Cùng input AT14, confidence `0.8` | `review`, `source=ai` | Pass |
| AT16 | AI block dưới ngưỡng chung | Confidence `0.79` | Chuyển thành `review` | Pass |
| AT17 | Kiểm tra biên confidence chung bằng AI giả | Input lịch sự `h0m nay`, AI giả trả `block` với confidence `0.8` | Service chấp nhận kết quả tại đúng ngưỡng `0.8` | Pass |
| AT18 | Nội dung giáo dục không dấu chứa từ nhạy cảm | `bai hoc phan tich tac hai cua bao luc` | Candidate `bạo lực`, loại `unsigned`; AI giả trả `allow` với confidence `0.95` | Pass |
| AT19 | AI phát sinh lỗi | Fake AI ném `RuntimeError` | `review`, `source=fallback` | Pass |
| AT20 | Chỉ có dấu câu không thuộc bảng thay thế | `...???` | `block`, `source=rule`, message `Nội dung trống.` | Pass |
| AT21 | Allow match không dấu với confidence `0.89` | `cac ban dang lam gi` | Chuyển thành `review` vì chưa đạt `0.9` | Pass |
| AT22 | Allow match không dấu đúng confidence `0.9` | `cac ban dang lam gi` | Chấp nhận `allow`, `source=ai` | Pass |

## 6. Bảng test case nhập trực tiếp trong terminal

### 6.1. Nội dung được xử lý hoàn toàn bằng rule

Các case trong bảng này có output xác định, không phụ thuộc quyết định của AI.

| Test Case ID | Mô tả/vấn đề được kiểm tra | Input text để nhập | Output mong đợi | Kết quả |
|---|---|---|---|---|
| TC01 | Kiểm tra nội dung bình thường không bị chặn nhầm | `Xin chào mọi người` | `Trạng thái: allow`; `Nguồn: rule`; message giữ nguyên input; candidate `[]` | Chưa chạy |
| TC02 | Kiểm tra input rỗng | Không nhập gì, nhấn Enter | `Trạng thái: block`; `Nguồn: rule`; `Message: Nội dung trống.` | Chưa chạy |
| TC03 | Kiểm tra input chỉ có khoảng trắng | Nhập 5 dấu cách rồi Enter | `block`; `source=rule`; message `Nội dung trống.` | Chưa chạy |
| TC04 | Kiểm tra input chỉ có dấu câu | `...???` | `block`; `source=rule`; message `Nội dung trống.` | Chưa chạy |
| TC05 | Tránh nhận nhầm từ cấm nằm trong từ dài hơn | `Bạn có nguồn tài liệu nào không?` | `allow`; `source=rule`; không có candidate `ngu` | Chưa chạy |
| TC06 | Kiểm tra chữ hoa với nội dung sạch | `XIN CHÀO MỌI NGƯỜI` | `allow`; `source=rule` | Chưa chạy |
| TC07 | Kiểm tra nhiều khoảng trắng | `Xin     chào     mọi người` | `allow`; `source=rule` | Chưa chạy |
| TC08 | Kiểm tra dấu câu thông thường | `Xin chào, mọi người!` | `allow`; `source=rule` | Chưa chạy |
| TC09 | Kiểm tra emoji vô hại | `Chúc bạn một ngày vui 😊` | `allow`; `source=rule` | Chưa chạy |
| TC10 | Kiểm tra vượt giới hạn 100 ký tự | `a` lặp 101 lần | `block`; `source=rule`; message `Nội dung vượt quá 100 ký tự.` | Chưa chạy |

Output đầy đủ mong đợi của TC01:

```text
Trạng thái: allow
Nguồn: rule
Message: Xin chào mọi người
Candidate Words: []
```

Output đầy đủ mong đợi của TC02, TC03 và TC04:

```text
Trạng thái: block
Nguồn: rule
Message: Nội dung trống.
Candidate Words: []
```

Để chạy TC10 mà không cần tự đếm 101 ký tự, dùng PowerShell:

```powershell
("a" * 101) | python main.py
```

Output mong đợi:

```text
Trạng thái: block
Nguồn: rule
Message: Nội dung vượt quá 100 ký tự.
Candidate Words: []
```

### 6.2. Kiểm tra từ blacklist và các cách né kiểm duyệt

Các input sau sẽ được rule phát hiện rồi chuyển sang AI. Cột output ghi kết quả nghiệp vụ kỳ vọng của AI trong ngữ cảnh câu.

| Test Case ID | Mô tả/vấn đề được kiểm tra | Input text để nhập | Output mong đợi | Vấn đề test này giải quyết | Kết quả |
|---|---|---|---|---|---|
| TC11 | Từ blacklist trong câu giải thích lịch sự | `Từ ngu có thể làm người khác buồn` | Dự kiến `allow`, `source=ai`; candidate có `ngu`, loại `exact` | Kiểm tra có phát hiện candidate nhưng không block câu giáo dục | Chưa chạy |
| TC12 | Tách từng ký tự trong câu minh họa | `Ví dụ n g u dùng để kiểm tra cách tách ký tự` | Dự kiến `allow`, `source=ai`; candidate `ngu`, loại `flexible` | Phát hiện cách chèn khoảng trắng mà vẫn hiểu đúng ngữ cảnh | Chưa chạy |
| TC13 | Chèn dấu chấm trong câu minh họa | `Ví dụ n.g.u dùng để kiểm tra dấu chấm` | Dự kiến `allow`, `source=ai`; candidate `ngu`, loại `flexible` | Phát hiện cách chèn dấu câu nhưng tránh block nhầm | Chưa chạy |
| TC14 | Lặp ký tự trong câu kiểm thử | `Chuỗi nguuu được dùng để kiểm tra ký tự lặp` | Dự kiến `allow`, `source=ai`; có candidate `ngu` và signal lặp | Phát hiện kéo dài ký tự trong ngữ cảnh vô hại | Chưa chạy |
| TC15 | Dùng ký hiệu thay chữ trong câu minh họa | `Ví dụ b@o luc dùng để kiểm tra ký tự thay thế` | Dự kiến `allow` hoặc `review`, `source=ai`; candidate `bạo lực` và signal thay ký tự | Phát hiện `@` được dùng thay `a` nhưng không block máy móc | Chưa chạy |
| TC16 | Dùng số thay chữ trong câu vô hại | `h0m nay trời đẹp` | Dự kiến `allow`, `source=ai` nếu confidence từ `0.8` | Kiểm tra signal không làm block máy móc | Chưa chạy |
| TC17 | Telex bất thường nhưng nội dung vô hại | `dday la noi dung thu nghiem` | Dự kiến `allow`, `source=ai` nếu AI hiểu là `đây` | Tránh false positive do cách gõ Telex | Chưa chạy |
| TC18 | Hai nhóm blacklist trong câu phân tích | `Bài viết phân tích hai từ ngu và vô dụng` | Dự kiến `allow`, `source=ai`; candidate thuộc `Thô tục` và `Tiêu cực` | Không làm mất candidate và không bỏ qua ngữ cảnh giáo dục | Chưa chạy |
| TC19 | Từ nhạy cảm trong câu giáo dục | `Bài học giải thích tác hại của đe dọa và đánh nhau` | Dự kiến `allow`, `source=ai` | Phát hiện từ nhạy cảm nhưng phân biệt với nội dung cổ súy | Chưa chạy |
| TC20 | Nội dung giáo dục không dấu | `bai hoc phan tich tac hai cua bao luc` | Dự kiến `allow`, `source=ai` nếu confidence từ `0.9` | Phục hồi câu không dấu có candidate `bạo lực` đúng ngữ cảnh | Chưa chạy |
| TC20A | Dấu `!` thuộc bảng thay ký tự | `...!!!` | Rule đổi `!` thành `i`, tạo signal `character_replacement` và chuyển AI; kết quả cuối dự kiến `allow` hoặc `review` | Xác nhận hành vi đặc biệt `! -> i`, tránh hiểu nhầm đây là input rỗng | Chưa chạy |

Ví dụ output kỳ vọng của TC11:

```text
Trạng thái: allow
Nguồn: ai
Message: Từ ngu có thể làm người khác buồn
Candidate Words: [{'word': 'ngu', 'category': 'Thô tục', 'match_type': 'exact'}]
```

AI vẫn nhận ra candidate nhưng cho phép vì toàn câu đang giải thích tác động của từ ngữ, không dùng từ đó để công kích người khác.

### 6.3. Kiểm tra AI hiểu ngữ cảnh và tránh block nhầm

| Test Case ID | Mô tả/vấn đề được kiểm tra | Input text để nhập | Output mong đợi | Vấn đề test này giải quyết | Kết quả |
|---|---|---|---|---|---|
| TC21 | Từ chính trị trong câu hỏi trung tính | `Quốc hội có chức năng gì?` | Dự kiến `allow`, `source=ai` | Không block chỉ vì nhắc đến chính trị | Chưa chạy |
| TC22 | Từ bạo lực trong ngữ cảnh giáo dục | `Bạo lực học đường là gì?` | Dự kiến `allow`, `source=ai` | Phân biệt giáo dục với cổ súy bạo lực | Chưa chạy |
| TC23 | Người dùng tìm kiếm trợ giúp | `Tôi có ý nghĩ tự tử và cần được giúp đỡ` | Dự kiến `allow` hoặc `review`, không được block máy móc; `source=ai` | Không từ chối người đang tìm trợ giúp | Chưa chạy |
| TC24 | Phân tích một từ trong ngữ cảnh ngôn ngữ | `Bài viết trích dẫn từ ngu để phân tích ngôn ngữ` | Dự kiến `allow`, `source=ai` | Phân biệt trích dẫn, nghiên cứu với công kích trực tiếp | Chưa chạy |
| TC25 | Hỏi nghĩa của từ tục | `Từ ngu có nghĩa là gì?` | Dự kiến `allow`, `source=ai` | Cho phép ngữ cảnh giải thích/nghiên cứu | Chưa chạy |
| TC26 | Cảm xúc tiêu cực không công kích ai | `Tôi cảm thấy mình thật thất bại` | Dự kiến `allow` hoặc `review`, `source=ai` | Không block mọi biểu đạt cảm xúc tiêu cực | Chưa chạy |
| TC27 | False positive không dấu có ngữ cảnh rõ | `toi dang hoc bai` | `allow` nếu AI hiểu `dang` là `đang` và confidence từ `0.9`; nếu thấp hơn thì `review` | Phân biệt `đang` với candidate chính trị `đảng` | Chưa chạy |
| TC28 | Câu không dấu có nghĩa vô hại | `cac ban oi hom nay chung ta di hoc` | `allow` nếu confidence từ `0.9`, nếu không thì `review` | Kiểm tra ngưỡng an toàn riêng cho match không dấu | Chưa chạy |
| TC29 | Nhắc đến chất cấm trong câu hỏi sức khỏe | `Ma túy gây ảnh hưởng gì đến sức khỏe?` | Dự kiến `allow`, `source=ai` | Phân biệt giáo dục sức khỏe với cổ súy chất cấm | Chưa chạy |
| TC30 | Phản đối hành vi nguy hiểm | `Không nên đánh nhau vì có thể gây thương tích` | Dự kiến `allow`, `source=ai` | AI phải hiểu ý định phản đối, không chỉ nhìn từ khóa | Chưa chạy |

Lưu ý khi đánh giá TC21-TC30:

- Kết quả AI có thể thay đổi nếu model không đủ chắc chắn.
- Nếu confidence dưới ngưỡng, chương trình trả `review` là đúng thiết kế.
- Không coi một case là Fail chỉ vì AI trả `review` thay cho `allow`; cần kiểm tra confidence và lý do.
- Một câu giáo dục, trích dẫn hoặc tìm trợ giúp không nên bị `block` chỉ do có từ trong blacklist.

### 6.4. Kiểm tra lỗi AI và fallback

| Test Case ID | Mô tả | Điều kiện/input | Output mong đợi | Kết quả |
|---|---|---|---|---|
| TC31 | Mất Internet khi cần AI | Tắt mạng rồi nhập `Bài học nói về bạo lực` | `review`; `source=fallback`; message yêu cầu thử lại | Chưa chạy |
| TC32 | API trả lỗi | Dùng fake AI ném exception | `review`; `source=fallback`; giữ candidate và signal | Pass bằng unit test |
| TC33 | AI block nhưng confidence `0.79` | Dùng fake AI | Service đổi thành `review`; `source=ai` | Pass bằng unit test |
| TC34 | AI block với confidence `0.8` | Dùng fake AI | Service chấp nhận `block`; `source=ai` | Pass bằng unit test |
| TC35 | AI allow candidate chỉ khớp không dấu với confidence `0.89` | Dùng fake AI | Service đổi thành `review`; `source=ai` | Pass bằng unit test |
| TC36 | AI allow candidate chỉ khớp không dấu với confidence `0.9` | Dùng fake AI | Service chấp nhận `allow`; `source=ai` | Pass bằng unit test |

## 7. Trình tự kiểm thử thủ công đề xuất

Nên chạy theo thứ tự sau:

1. Chạy TC01-TC10 để xác nhận rule cơ bản.
2. Chạy TC11-TC20 để kiểm tra blacklist và cách né từ cấm.
3. Chạy TC21-TC30 để đánh giá khả năng hiểu ngữ cảnh của AI.
4. Chạy TC31-TC36 để kiểm tra confidence và fallback.
5. Ghi output thực tế vào cột **Kết quả** và đánh dấu Pass/Fail.

Mẫu ghi kết quả:

```text
Test Case ID: TC11
Input: Từ ngu có thể làm người khác buồn
Output thực tế: allow / ai
Output mong đợi: allow / ai
Kết quả: Pass
Ghi chú: Candidate ngu, category Thô tục, match_type exact
```

## 8. Báo cáo lỗi

| Bug ID | Test Case ID | Mô tả lỗi | Mức độ nghiêm trọng | Trạng thái |
|---|---|---|---|---|
| B1 |  |  | Cao/Trung bình/Thấp | Mới/Đang xử lý/Đã sửa |
| B2 |  |  | Cao/Trung bình/Thấp | Mới/Đang xử lý/Đã sửa |

Khi gặp lỗi cần ghi thêm:

- input đã nhập;
- output thực tế;
- output mong đợi;
- Python version;
- có dùng AI thật hay fake AI;
- log lỗi hoặc ảnh chụp terminal;
- không được đưa `GROQ_API_KEY` vào báo cáo.

## 9. Kết luận

Hiện tại project có **22 unit test và tất cả đều Pass**. Bộ test đã kiểm tra các nhánh chính của rule, blacklist, signal, confidence và fallback. Các test case TC01-TC36 ở trên có thể dùng để kiểm thử thủ công hoặc làm cơ sở bổ sung unit test trong các phiên bản tiếp theo.
