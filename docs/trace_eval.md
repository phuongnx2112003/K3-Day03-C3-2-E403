# Báo cáo giám sát và đánh giá

## 1. Agentic Fit — Mốc 1

**Chủ đề:** Trợ lý kiểm tra điều kiện đăng ký môn và lập kế hoạch học kỳ cho sinh viên.

| Tiêu chí | Điểm | Bằng chứng trong source |
|---|---:|---|
| Multi-step reasoning | 5/5 | Hồ sơ → catalog → prerequisite → lịch → tải tín chỉ. |
| Tool interaction | 5/5 | 7 tool học vụ được đăng ký trong `AVAILABLE_TOOLS`. |
| Dynamic decision | 4/5 | Kế hoạch chỉ được chốt sau các Observation hợp lệ. |
| Long horizon | 4/5 | ReAct có tối đa 5 bước và timeout cho provider/tool. |
| **Tổng** | **18/20** | Phù hợp dùng ReAct Agent thay vì chatbot đơn thuần. |

## 2. Baseline Chatbot — Mốc 2

`run_baseline_chatbot()` chỉ gửi `CHATBOT_BASELINE_PROMPT` tới provider, không
import hoặc gọi `AVAILABLE_TOOLS`. Vì vậy nó phù hợp để so sánh với ReAct: các
câu #1–#2 có thể trả lời kiến thức chung, còn #3–#5 không được tự khẳng định dữ
liệu hồ sơ, catalog hay lịch nếu thiếu tool.

Chạy offline có thể dùng `LLM_PROVIDER=mock`; mock chỉ xác nhận đường chạy và
không được dùng làm bằng chứng về chất lượng ngôn ngữ của Gemini/Ollama.

## 3. ReAct acceptance trace — Mốc 3

Các trace dưới đây là kết quả fixture có thể lặp lại bằng:

```bash
LLM_PROVIDER=mock python -m unittest discover -s tests -v
```

| Test case | Kết quả mong đợi đã kiểm chứng |
|---|---|
| #3 — COMP1020 | `check_prerequisites` trả `ĐỦ ĐIỀU KIỆN` vì sinh viên đã học `COMP1010`. |
| #4 — kế hoạch AI/ML | Agent gọi đủ 5 bước. Plan là `COMP1020`, `MATH2010`, `STAT1010`, `GENE1010`, `GENE1020`: 16 tín chỉ, không trùng lịch. GenEd chỉ bù tải; ba môn đầu là nền AI/ML. |
| #5 — yêu cầu ép đăng ký | Guardrail vẫn gọi hồ sơ, prerequisite, lịch và tín chỉ. Kết quả thật: thiếu prerequisite, `COMP2050` và `COMP3020` trùng lịch; tổng danh sách là 14 tín chỉ (không bịa thành quá tải). |

### Trace rút gọn cho kế hoạch 16 tín chỉ

```text
Thought: Cần đọc hồ sơ fixture trước khi chọn các môn chưa hoàn thành.
Action: get_student_profile['2A202601874']
Observation: Môn đã hoàn thành: COMP1010, MATH1010

Action: search_courses['AI/ML']
Observation: Có Artificial Intelligence, Machine Learning và các môn nền AI/ML.

Action: check_prerequisites['2A202601874', [...]]
Observation: ĐỦ ĐIỀU KIỆN đăng ký.

Action: check_schedule_conflicts[[...]]
Observation: Không phát hiện trùng lịch học.

Action: calculate_credit_load['2A202601874', [...]]
Observation: Tải học kỳ hợp lệ: 16 tín chỉ.

Final Answer: Kế hoạch học kỳ hợp lệ.
```

## 4. Cross-audit & Mốc 4

- `docs/hybrid_flowchart.mermaid` mô tả đường Baseline, ReAct, lỗi tool,
  timeout và safe fallback.
- `tests/test_acceptance.py` là bộ cross-audit lặp lại được: catalog AI/ML,
  prerequisite, kế hoạch 16 tín chỉ, lịch trùng, quá tải, parser lỗi và yêu cầu
  ép đăng ký.
- Việc một nhóm khác trực tiếp phản biện trên lớp là hoạt động của giảng viên/
  nhóm học viên; source đã có câu bẫy #5 và acceptance test để thực hiện demo đó.

## Kết luận

Deliverable kỹ thuật của Role 1–5B đã được đối chiếu với source hiện tại. Dữ
liệu học vụ là **fixture cục bộ cho lab**, không phải dữ liệu SIS thực tế; agent
luôn nêu lỗi hoặc safe fallback khi không đủ dữ liệu để xác nhận.
