# Codelab: Trợ lý đăng ký môn và lập kế hoạch học kỳ

## Mục tiêu

Xây dựng một trợ lý có thể:

- kiểm tra hồ sơ và môn đã hoàn thành của sinh viên;
- kiểm tra môn tiên quyết;
- phát hiện trùng lịch học;
- tính tải tín chỉ;
- đề xuất kế hoạch học kỳ hợp lệ.

## Cấu trúc triển khai

| Thành phần | File | Role |
|---|---|---|
| Test cases | `config/test_cases.json` | Role 1 |
| Công cụ học vụ | `src/tools.py` | Role 2 |
| Prompt và guardrails | `src/prompts.py` | Role 3 |
| Agent tích hợp | `src/app.py` | Role 4 |
| Trace và đánh giá | `docs/trace_eval.md` | Role 5A |
| Hybrid flowchart | `docs/hybrid_flowchart.mermaid` | Role 5B |

## Luồng ReAct

```text
User question
    ↓
Thought: xác định thông tin cần kiểm tra
    ↓
Action: gọi tool học vụ
    ↓
Observation: nhận kết quả từ tool
    ↓
Kiểm tra tiếp prerequisite / lịch / tín chỉ
    ↓
Final Answer: kết luận và kế hoạch hợp lệ
```

## Các tool chính

- `get_student_profile(student_id)`
- `search_courses(keywords)`
- `check_prerequisites(student_id, course_codes)`
- `check_schedule_conflicts(course_codes)`
- `calculate_credit_load(student_id, planned_courses)`
- `recommend_course_plan(student_id, goal)`

## Guardrails bắt buộc

- Không bịa thông tin môn học hoặc hồ sơ sinh viên.
- Không chốt môn nếu thiếu prerequisite.
- Không chấp nhận kế hoạch bị trùng lịch.
- Không chấp nhận tải học kỳ vượt 18 tín chỉ.
- Trả về lỗi rõ ràng khi mã sinh viên hoặc mã môn không hợp lệ.
- Dừng vòng lặp khi đạt `MAX_ITERATIONS`.

## Chạy project

```bash
source .venv/bin/activate
LLM_PROVIDER=mock python src/app.py
```

Muốn dùng LLM thật, cấu hình provider và API key trong `.env` trước khi chạy.

## Kiểm thử

Chạy lần lượt 5 test case trong `config/test_cases.json`. Role 5A ghi lại kết quả vào `docs/trace_eval.md`; Role 5B cập nhật sơ đồ tại `docs/hybrid_flowchart.mermaid`.
