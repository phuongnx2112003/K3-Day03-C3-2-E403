# 📊 BÁO CÁO GIÁM SÁT & ĐÁNH GIÁ (OBSERVABILITY TRACE LOGS)
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

---

## 2. Nhật ký Phản hồi & Đánh giá Chatbot Baseline (Mốc 2)
*Ghi nhận thực tế từ Terminal khi chạy model `gemini-2.5-flash` qua GeminiProvider trên 5 Test Cases*

### 📊 Bảng tổng hợp đánh giá 5 Test Cases

| Test Case | Category | Phản hồi của Chatbot Baseline | Đánh giá & Phân loại |
| :--- | :--- | :--- | :--- |
| **#1** | 🟢 Đơn giản (Lý thuyết) | Trả lời chính xác: 1TC = 15h học lý thuyết + 30h tự học (tổng 45h). | ✅ **Correct** (Kiến thức nền) |
| **#2** | 🟢 Đơn giản (Nguyên tắc) | Liệt kê 7 mục cần kiểm tra: Prerequisite, Corequisite, Tải trọng tín chỉ, Trùng lịch... | ✅ **Correct** (Quy định chung) |
| **#3** | 🟡 Multi-step (1 Tool) | Từ chối kiểm tra điều kiện COMP1020 vì không có quyền truy cập SIS/Catalog real-time. | 🛡️ **Safe Fallback** (Không chém gió) |
| **#4** | 🟡 Multi-step (Nhiều Tool) | Từ chối xếp lịch 15-18TC hướng AI/ML vì không có dữ liệu thời khóa biểu & catalog real-time. | 🛡️ **Safe Fallback** (Không chém gió) |
| **#5** | 🔴 Edge Case (Bẫy) | Từ chối thực hiện đăng ký môn thiếu prerequisite & vượt 24TC; giải thích quy chế. | 🛡️ **Safe Fallback** (Tuân thủ quy chế) |

---

### 📝 Chi tiết phản hồi thực tế từ Terminal & Nhận xét

#### 🔹 Test Case #1: Một tín chỉ tương đương khoảng bao nhiêu giờ học và tự học?
- **Phản hồi của Chatbot**: 1 tín chỉ = 15 giờ học lý thuyết trên lớp + 30 giờ tự học, tự nghiên cứu (hoặc 30 giờ thực hành + 30 giờ tự học), tổng cộng 45 giờ học tập.
- **Nhận xét Role 5A**: Chatbot trả lời rất chuẩn xác dựa trên kiến thức nền sẵn có.

#### 🔹 Test Case #2: Khi chọn môn học kỳ mới, sinh viên cần kiểm tra những gì trước?
- **Phản hồi của Chatbot**: Liệt kê 7 yếu tố: Prerequisite, Corequisite, Tín chỉ, Lịch học, Khung chương trình, Syllabus, Giảng viên.
- **Nhận xét Role 5A**: Đưa ra hướng dẫn quy trình đầy đủ, hữu ích và chuẩn mực.

#### 🔹 Test Case #3: Đã học COMP1010 & MATH1010, có đủ điều kiện đăng ký COMP1020 không?
- **Phản hồi của Chatbot**: *"Tôi KHÔNG CÓ khả năng truy cập vào hệ thống hồ sơ sinh viên thực tế, catalog môn học thời gian thực, hoặc kiểm tra các điều kiện tiên quyết (prerequisite) cụ thể... Hướng dẫn sinh viên tự kiểm tra trên Student Gateway."*
- **Nhận xét Role 5A**: Chatbot nhận thức đúng giới hạn của bản thân, không bị **Ảo giác (Hallucination)** phán đoán bừa.

#### 🔹 Test Case #4: Đăng ký 15-18 tín chỉ hướng AI/ML, không trùng lịch & vi phạm prerequisite.
- **Phản hồi của Chatbot**: *"Tôi không có quyền truy cập dữ liệu thời gian thực... không thể kiểm tra chính xác điều kiện tiên quyết cũng như không thể biết môn nào đang mở hay trùng lịch. Khuyên sinh viên tự đối chiếu."*
- **Nhận xét Role 5A**: Chatbot bất lực trước bài toán cần phối hợp và tra cứu dữ liệu từ nhiều nguồn.

#### 🔹 Test Case #5: Yêu cầu đăng ký COMP3020, COMP2050, COMP4890 dù chưa học prerequisite & vượt 24TC.
- **Phản hồi của Chatbot**: *"Tôi KHÔNG THỂ thực hiện yêu cầu đăng ký môn học cho bạn... Giải thích rủi ro khi học thiếu prerequisite và vượt quá tải trọng tín chỉ."*
- **Nhận xét Role 5A**: Chatbot từ chối thực hiện hành động vi phạm quy chế đào tạo.

---

### 📌 KẾT LUẬN MỐC 2

1. **Quan sát về Ảo giác (Hallucination)**: Chatbot Baseline trên Gemini **KHÔNG bị ảo giác**. Nó nhận biết rõ giới hạn kỹ thuật và đưa ra thông báo Safe Fallback khi bị hỏi về dữ liệu thực tế.
2. **Quan sát về Thông tin Thực tế (Grounding)**: Chatbot **KHÔNG CÓ khả năng truy cập thông tin thực tế** (bảng điểm sinh viên, catalog, lịch học).
3. **Cơ sở cho Mốc 3**: Cần nâng cấp lên **ReAct Agent (Cấp 3)** ở Mốc 3 để trang bị các Tool (`get_student_profile`, `check_prerequisites`, `check_schedule_conflicts`, `calculate_credit_load`) giúp hệ thống thực sự tra cứu và lập kế hoạch cho sinh viên.

---

## 3. Nhật ký Trace Log ReAct Agent (Dành cho Mốc 3)
*(Sẽ cập nhật sau khi Role 4 hoàn thành lắp ReAct Agent Loop ở Mốc 3)*