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

## 2. Trace test case #3

**Câu hỏi:** Em đã học xong CS101 và MATH101. Cho em biết em có đủ điều kiện đăng ký CS201 không?

### Baseline Chatbot

- Không có quyền truy cập hồ sơ hoặc catalog.
- Không được tự đoán kết quả prerequisite.
- Cần hướng dẫn sinh viên kiểm tra trên hệ thống học vụ.

### ReAct Agent

```text
Thought: Cần kiểm tra môn tiên quyết của CS201 cho sinh viên.
Action: check_prerequisites['2A202601874', ['CS201']]
Observation: ĐỦ ĐIỀU KIỆN đăng ký: CS201.
Final Answer: Sinh viên đủ điều kiện đăng ký CS201.
```

## 3. Đánh giá

Agent chỉ được kết luận dựa trên kết quả tool. Nếu mã môn không tồn tại, thiếu prerequisite, trùng lịch hoặc vượt tải tín chỉ, agent phải trả về cảnh báo và không chốt kế hoạch không hợp lệ.
