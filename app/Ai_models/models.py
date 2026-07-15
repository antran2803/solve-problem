import json
import os
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

SYSTEM_PROMPT = """
Bạn là hệ thống kiểm duyệt các nội dung nhạy cảm  tiếng Việt.

Candidate và signal do rule cung cấp chỉ là bằng chứng kỹ thuật để yêu cầu xem
xét, không phải kết luận vi phạm. Không được block chỉ vì một candidate nằm
trong blacklist hoặc vì nội dung đã bị normalize thành candidate đó.

Hãy thực hiện tuần tự quy trình sau:

1. XÁC MINH CANDIDATE
- Đọc nội dung gốc, candidate, match_type, signal và nội dung chuẩn hóa.
- Xác định candidate là confirmed, false_positive hay uncertain.
- Với match_type="unsigned" hoặc "fuzzy", phải xem các từ đứng trước và sau,
  vì một chuỗi không dấu có thể đại diện cho nhiều từ tiếng Việt.
- Khi candidate là unsigned, bắt buộc thực hiện phép thử phục hồi ngữ nghĩa:
  a) Liệt kê các cách hiểu có dấu hợp lý của đoạn không dấu.
  b) Thay từng cách hiểu vào nguyên câu, không đánh giá token riêng lẻ.
  c) So sánh cách nào tạo thành câu đúng ngữ pháp và hợp nghĩa hơn.
  d) Nếu cách hiểu là candidate tạo thành cụm xúc phạm/gây hại rõ ràng còn cách
     hiểu vô hại làm câu vô nghĩa hoặc sai ngữ pháp, đánh giá confirmed.
  e) Nếu cách hiểu vô hại phù hợp ngữ pháp/ngữ cảnh hơn, đánh giá false_positive.
  f) Nếu cả hai cách hiểu đều hợp lý và không đủ dữ kiện phân biệt, đánh giá
     uncertain và decision="review".
- Không được chọn false_positive chỉ vì tồn tại một cách phục hồi vô hại; cách
  phục hồi đó phải phù hợp với toàn bộ cấu trúc câu.
- Với match_type="flexible" hoặc signal biến đổi ký tự, chỉ coi đó là dấu hiệu
  né tránh khi nghĩa của toàn câu cũng ủng hộ cách hiểu vi phạm.

2. ĐÁNH GIÁ Ý ĐỊNH VÀ NGỮ CẢNH
- Sử dụng kết quả phục hồi dấu/ngữ nghĩa được cung cấp như một bằng chứng trung
  gian và đối chiếu lại với nội dung gốc.
- Nếu bước phục hồi cho thấy candidate tạo thành câu đúng ngữ pháp và mang nghĩa
  vi phạm, không được bỏ qua chỉ vì input ban đầu không có dấu.
- Xác định nội dung đang hướng tới ai, đang mô tả điều gì và có mục đích gì.
- Phân biệt sử dụng để công kích với việc hỏi nghĩa, trích dẫn, giáo dục,
  nghiên cứu, đưa tin, hỗ trợ hoặc phản ánh lời nói của người khác.
- Không suy luận vi phạm chỉ từ một token riêng lẻ; phải dùng toàn câu.

3. ÁP DỤNG POLICY THEO CATEGORY
- profanity: block khi từ được dùng để chửi bới, làm nhục hoặc công kích; không
  block khi chỉ được nhắc đến trong ngữ cảnh giải thích hoặc candidate bị nhầm.
- sensitive: block nội dung cổ súy, hướng dẫn hoặc đe dọa hành vi nguy hiểm;
  không block máy móc nội dung tìm kiếm trợ giúp, giáo dục hoặc đưa tin.
- politics: không block chỉ vì nhắc đến tổ chức, cá nhân hay hoạt động chính trị;
  chỉ block nếu nội dung đồng thời vi phạm một policy gây hại cụ thể.
- negative: không block chỉ vì có cảm xúc hoặc từ ngữ tiêu cực; chỉ block khi
  ngữ cảnh cấu thành công kích, đe dọa hoặc hành vi gây hại.

4. RA QUYẾT ĐỊNH
- allow: candidate là false_positive hoặc nội dung không vi phạm policy.
- block: candidate/ý nghĩa vi phạm đã được xác nhận rõ bằng toàn bộ ngữ cảnh.
- review: còn ít nhất hai cách hiểu hợp lý hoặc bằng chứng chưa đủ chắc chắn.
- Nếu decision="allow", category phải là null.
- Decision, reason và message bắt buộc phải thống nhất với nhau.
- Confidence phản ánh độ chắc chắn của đánh giá ngữ cảnh, không phải độ giống
  nhau giữa chuỗi và blacklist.
""".strip()


def create_client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("Không tìm thấy GROQ_API_KEY trong file .env")

    return Groq(api_key=api_key)


class AIReviewService:
    def __init__(self, client=None):
        self.client = client or create_client()

    def review_text(self, text: str, rule_result: dict) -> dict:
        candidates = json.dumps(
            rule_result.get("matched_words", []),
            ensure_ascii=False,
        )
        signals = json.dumps(
            rule_result.get("signals", []),
            ensure_ascii=False,
        )
        restoration = self._restore_context(text, rule_result)
        restoration_json = json.dumps(restoration, ensure_ascii=False)

        query = f"""
Nội dung gốc:
---BEGIN CONTENT---
{text}
---END CONTENT---

Candidate rule phát hiện:
{candidates}

Dấu hiệu biến đổi:
{signals}

Nội dung sau chuẩn hóa:
{rule_result.get("normalized_text", "")}

Kết quả phục hồi dấu và ngữ nghĩa:
{restoration_json}

Chỉ trả về một JSON object theo cấu trúc:
{{
    "candidate_assessment": "confirmed, false_positive hoặc uncertain",
    "decision": "allow, block hoặc review",
    "confidence": 0.0,
    "category": "profanity, sensitive, politics, negative hoặc null",
    "reason": "lý do ngắn gọn",
    "message": "thông báo thống nhất với decision"
}}
""".strip()

        response = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": query,
                },
            ],
        )

        content = response.choices[0].message.content
        result = json.loads(content)
        decision = result.get("decision")
        confidence = result.get("confidence")

        candidate_assessment = result.get("candidate_assessment")

        if candidate_assessment not in {
            "confirmed",
            "false_positive",
            "uncertain",
        }:
            raise ValueError("AI trả về candidate_assessment không hợp lệ")

        if decision not in {"allow", "block", "review"}:
            raise ValueError("AI trả về decision không hợp lệ")

        if (
            isinstance(confidence, bool)
            or not isinstance(confidence, (int, float))
            or not 0 <= confidence <= 1
        ):
            raise ValueError("AI trả về confidence không hợp lệ")

        if decision == "allow":
            message = text
            category = None
        elif decision == "review":
            message = "Nội dung cần được kiểm tra thêm"
            category = result.get("category")
        else:
            message = result.get("message") or "Nội dung không phù hợp"
            category = result.get("category")

        return {
            "status": decision,
            "candidate_assessment": candidate_assessment,
            "confidence": confidence,
            "category": category,
            "reason": result.get("reason"),
            "message": message,
            "signals": rule_result.get("signals", []),
            "confidence": confidence,
            "matched_words": rule_result.get("matched_words", []),
            "source": "ai",
        }

    def _restore_context(self, text: str, rule_result: dict) -> dict:
        candidates = rule_result.get("matched_words", [])
        signals = rule_result.get("signals", [])
        needs_restoration = bool(signals) or any(
            candidate.get("match_type") in {"unsigned", "fuzzy"}
            for candidate in candidates
        )

        if not needs_restoration:
            return {
                "restored_text": text,
                "interpretations": [],
                "confidence": 1.0,
            }

        restoration_query = f"""
Phục hồi dấu và cách hiểu tiếng Việt cho nội dung sau. Không kiểm duyệt, không
làm nhẹ từ tục và không thay đổi ý nghĩa. Hãy xét toàn bộ cấu trúc ngữ pháp,
không đánh giá từng token riêng lẻ.

Nội dung gốc:
---BEGIN CONTENT---
{text}
---END CONTENT---

Candidate từ rule:
{json.dumps(candidates, ensure_ascii=False)}

Dấu hiệu biến đổi:
{json.dumps(signals, ensure_ascii=False)}

Chỉ trả về một JSON object:
{{
    "restored_text": "câu được phục hồi theo cách hiểu phù hợp nhất",
    "interpretations": [
        {{
            "candidate": "candidate đang xét",
            "meaning_in_context": "nghĩa trong toàn câu",
            "assessment": "confirmed, false_positive hoặc uncertain"
        }}
    ],
    "confidence": 0.0
}}
""".strip()

        response = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Bạn chỉ làm nhiệm vụ phục hồi dấu và nghĩa tiếng Việt, "
                        "kể cả từ tục. Không kiểm duyệt và không làm nhẹ ý nghĩa."
                    ),
                },
                {
                    "role": "user",
                    "content": restoration_query,
                },
            ],
        )

        content = response.choices[0].message.content
        restoration = json.loads(content)
        restored_text = restoration.get("restored_text")
        interpretations = restoration.get("interpretations")
        confidence = restoration.get("confidence")

        if not isinstance(restored_text, str) or not restored_text.strip():
            raise ValueError("AI trả về restored_text không hợp lệ")
        if not isinstance(interpretations, list):
            raise ValueError("AI trả về interpretations không hợp lệ")
        if (
            isinstance(confidence, bool)
            or not isinstance(confidence, (int, float))
            or not 0 <= confidence <= 1
        ):
            raise ValueError("AI trả về restoration confidence không hợp lệ")

        return {
            "restored_text": restored_text,
            "interpretations": interpretations,
            "confidence": confidence,
        }
