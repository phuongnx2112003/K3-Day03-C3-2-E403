# Trợ lý kiểm tra điều kiện đăng ký môn và lập kế hoạch học kỳ

Project xây dựng trợ lý học vụ cho sinh viên. Hệ thống kết hợp Chatbot Baseline và ReAct Agent để kiểm tra dữ liệu học tập trước khi đề xuất kế hoạch học kỳ.

## Chức năng

- Tra cứu hồ sơ và các môn đã hoàn thành.
- Kiểm tra môn tiên quyết.
- Phát hiện trùng lịch học.
- Tính và kiểm soát tải tín chỉ 12–18 tín chỉ/kỳ.
- Đề xuất kế hoạch học kỳ theo mục tiêu của sinh viên.
- Từ chối kết luận khi thiếu dữ liệu hoặc gặp mã môn không hợp lệ.

## Cấu trúc project

```text
config/test_cases.json       # Role 1: Test cases
src/tools.py                 # Role 2: Công cụ học vụ
src/prompts.py               # Role 3: Prompt và guardrails
src/app.py                   # Role 4: Baseline và ReAct Agent
docs/trace_eval.md           # Role 5A: Trace và đánh giá
docs/hybrid_flowchart.mermaid # Role 5B: Hybrid flowchart
```

## Luồng hệ thống

```text
Baseline Chatbot: trả lời kiến thức nền, không gọi tool
ReAct Agent: Thought → Action → Observation → Final Answer
```

## Cài đặt và chạy

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
LLM_PROVIDER=mock python src/app.py
```

Để dùng LLM thật, cấu hình `LLM_PROVIDER` và API key trong `.env`.

## Phân công

Chi tiết phân công và checklist nằm trong [docs/PHAN_CONG_CONG_VIEC.md](docs/PHAN_CONG_CONG_VIEC.md).
