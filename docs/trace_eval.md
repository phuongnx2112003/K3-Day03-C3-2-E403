# 📊 BÁO CÁO GIÁM SÁT & ĐÁNH GIÁ
*Dành cho Role 5A: Trace Analyst*

## 1. Bảng chấm điểm Agentic Fit

**Chủ đề:** Trợ lý kiểm tra điều kiện đăng ký môn và lập kế hoạch học kỳ cho sinh viên.

| Tiêu chí | Điểm | Lý do |
|---|---:|---|
| Multi-step Reasoning | 4/5 | Cần kiểm tra hồ sơ, prerequisite, lịch học và tải tín chỉ. |
| Tool Interaction | 4/5 | Agent cần gọi nhiều tool học vụ theo từng bước. |
| Dynamic Decision | 4/5 | Kết quả kiểm tra trước quyết định kế hoạch tiếp theo. |
| Long Horizon | 3/5 | Kế hoạch thông thường gồm 2–4 bước kiểm tra. |
| **Tổng** | **15/20** | Bài toán phù hợp với ReAct Agent. |

## 2. Đánh giá Baseline — Mốc 2

| Test Case | Kết quả | Phân loại |
|---|---|---|
| #1 — Kiến thức tín chỉ | Trả lời quy đổi giờ học và tự học. | ✅ Correct |
| #2 — Nguyên tắc đăng ký | Nêu prerequisite, corequisite, tải tín chỉ, lịch học và chương trình. | ✅ Correct |
| #3 — COMP1020 | Không tự đoán khi chưa có hồ sơ/catalog thực tế. | 🛡️ Safe Fallback |
| #4 — Kế hoạch AI/ML | Không tự chốt lịch khi thiếu catalog/lịch mở môn. | 🛡️ Safe Fallback |
| #5 — Edge case | Từ chối đăng ký khi thiếu prerequisite hoặc vượt tải. | 🛡️ Safe Fallback |

Baseline chỉ dùng LLM, không gọi tool; đây là cơ sở so sánh với ReAct Agent.

## 3. Trace ReAct — Test case #3

**Câu hỏi:** Em đã học xong COMP1010 và MATH1010. Cho em biết em có đủ điều kiện đăng ký COMP1020 không?

```text
Thought: Cần kiểm tra prerequisite của COMP1020 theo hồ sơ sinh viên.
Action: check_prerequisites['2A202601874', ['COMP1020']]
Observation: ĐỦ ĐIỀU KIỆN đăng ký: COMP1020.
Thought: Tôi đã nhận Observation và chỉ kết luận dựa trên dữ liệu của tool.
Final Answer: ĐỦ ĐIỀU KIỆN đăng ký: COMP1020.
```

## 4. Trace ReAct — Test case #4

```text
Thought: Cần đề xuất kế hoạch dựa trên mục tiêu AI/ML và kiểm tra các điều kiện.
Action: recommend_course_plan['2A202601874', 'AI/ML']
Observation: Kế hoạch sơ bộ chưa đạt tải full-time; các môn tiếp theo còn thiếu prerequisite.
Final Answer: Không chốt kế hoạch; yêu cầu hoàn thành prerequisite và bổ sung môn để đạt tối thiểu 12 credits.
```

## 5. Trace ReAct — Test case #5

```text
Thought: Cần kiểm tra prerequisite của các môn được yêu cầu trước khi lập kế hoạch.
Action: check_prerequisites['2A202601874', ['COMP3020', 'COMP2050', 'COMP4890']]
Observation: CHƯA ĐỦ ĐIỀU KIỆN: COMP3020 thiếu MATH2010, STAT1010, COMP1020, COMP2030; COMP2050 thiếu STAT1010; COMP4890 thiếu COMP1020, COMP2030, COMP3010.
Final Answer: Từ chối chốt đăng ký vì sinh viên chưa đáp ứng prerequisite.
```

## 6. Trace truy xuất tài liệu chính thức

```text
Thought: Cần tra cứu quy định chính thức về credit và study load.
Action: search_official_sources['credit study load']
Observation: Kết quả từ academic_regulations, trang 11; Article 11 Study Load.
Final Answer: Trả lời kèm tên tài liệu và số trang, không khẳng định dữ liệu SIS nếu chưa có Observation.
```

Agent chỉ được kết luận dựa trên kết quả tool. Nếu mã môn không tồn tại, thiếu prerequisite, trùng lịch hoặc vượt tải tín chỉ, agent phải trả về cảnh báo và không chốt kế hoạch không hợp lệ.
