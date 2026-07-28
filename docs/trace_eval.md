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



(.venv) x-phuong@x-phuong-Vostro-3590:~/Code/VinUni/Day03-2A202601874-NguyenXuanPhuong$ python src/app.py
==================================================
🏫 ĐẠI HỌC VINUNI - BÀI LAB 3: CHATBOT VS REACT AGENT
==================================================
🔌 LLM Provider đang hoạt động: GeminiProvider (Model: gemini-2.5-flash)
✅ Đã tải thành công 5 Test Cases từ config/test_cases.json


--- MỐC 2: ĐÁNH GIÁ CHATBOT BASELINE ---
📋 Tổng số test case: 5

===== TEST CASE #1 =====
🏷️ Category: 🟢 Đơn giản (LLM chỉ cần kiến thức nền)

💬 [CHATBOT BASELINE] Câu hỏi: Một tín chỉ trong hệ đào tạo đại học thường tương đương khoảng bao nhiêu giờ học và tự học?
🤖 Chatbot trả lời:
Chào bạn,

Một tín chỉ trong hệ đào tạo đại học theo học chế tín chỉ thường được quy định là một đơn vị đo lường khối lượng học tập. Định mức khối lượng học tập cho một tín chỉ có thể có sự khác biệt nhỏ giữa các trường hoặc chương trình đào tạo, nhưng phổ biến nhất là quy định sau:

**1 tín chỉ tương đương với:**

*   **15 giờ học lý thuyết trên lớp:** Đây là thời gian sinh viên dành để tham gia các buổi giảng bài, thảo luận, thuyết trình dưới sự hướng dẫn của giảng viên.
*   **30 giờ tự học, tự nghiên cứu:** Đây là thời gian sinh viên cần dành ra ngoài giờ lên lớp để đọc tài liệu, làm bài tập, chuẩn bị bài, ôn tập, nghiên cứu chuyên sâu về môn học.

Hoặc đối với các môn học thực hành, thí nghiệm, đồ án:

*   **30 giờ thực hành, thí nghiệm, làm bài tập lớn, đồ án tại phòng thí nghiệm/xưởng/phòng máy:** Dưới sự hướng dẫn của giảng viên hoặc cán bộ kỹ thuật.
*   **30 giờ tự học, tự nghiên cứu:** Tương tự như trên.

**Như vậy, tổng cộng, một tín chỉ thường đòi hỏi sinh viên bỏ ra khoảng 45 giờ học tập (15 giờ lên lớp + 30 giờ tự học) để đạt được kết quả mong muốn.**

Quy định này giúp sinh viên hình dung được mức độ đầu tư thời gian và công sức cần thiết cho mỗi môn học để chủ động sắp xếp kế hoạch họctập hiệu quả.

===== TEST CASE #2 =====
🏷️ Category: 🟢 Đơn giản (LLM chỉ cần luật/quy định)

💬 [CHATBOT BASELINE] Câu hỏi: Khi chọn môn học kỳ mới, sinh viên cần kiểm tra những gì trước để tránh đăng ký sai?
🤖 Chatbot trả lời:
Chào bạn,

Việc kiểm tra kỹ lưỡng trước khi đăng ký môn học là rất quan trọng để đảm bảo bạn có một kỳ học hiệu quả và không gặp rắc rối. Dưới đây là những điều bạn cần kiểm tra trước khi chọn môn học kỳ mới trong một hệ thống tín chỉ:

1.  **Kiểm tra Điều kiện Tiên quyết (Prerequisites):**
    *   Đây là yếu tố quan trọng nhất. Một số môn học yêu cầu bạn phải hoàn thành một hoặc nhiều môn học khác với điểm đạt yêu cầu trước khi được phép đăng ký.
    *   **Ví dụ:** Bạn thường phải học xong "Toán cao cấp 1" mới được đăng ký "Toán cao cấp 2". Nếu bạn không đáp ứng điều kiện tiên quyết, hệ thống đăng ký sẽ không cho phép bạn ghi danh hoặc bạn sẽ bị hủy môn học sau đó.

2.  **Kiểm tra Điều kiện Đồng thời (Corequisites):**
    *   Một số môn học có thể yêu cầu bạn phải đăng ký học đồng thời với một môn học khác trong cùng một kỳ.
    *   **Ví dụ:** Một môn lý thuyết có thể yêu cầu bạn phải đăng ký môn thực hành tương ứng cùng lúc.

3.  **Kiểm tra Tải trọng Tín chỉ (Credit Load):**
    *   Mỗi sinh viên thường có một định mức khối lượng học tập tối thiểu và tối đa (số tín chỉ) được phép đăng ký trong một kỳ.
    *   **Ví dụ:** Hầu hết các trường quy định sinh viên nên đăng ký khoảng 15-18 tín chỉ mỗi kỳ để đảm bảo tiến độ học tập và khả năng tiếp thu. Đăng ký quá ít có thể làm chậm tiến độ tốt nghiệp, còn quá nhiều có thể gây áp lực và ảnh hưởng đến kết quả học tập.

4.  **Kiểm tra Lịch học và Tránh Trùng lịch:**
    *   Đảm bảo rằng các môn học bạn muốn đăng ký không bị trùng lịch về thời gian học trên lớp, phòng học, hoặc lịch thi.
    *   Hệ thống đăng ký thường sẽ báo lỗi nếu có lịch trùng, nhưng bạn nên tự kiểm tra trước để lên kế hoạch tốt hơn.

5.  **Xem xét Kế hoạch học tập và Cấu trúc chương trình đào tạo:**
    *   Tham khảo khung chương trình đào tạo của ngành học bạn đang theo đuổi để biết môn học nào là bắt buộc, môn nào là tự chọn, và vị trí của chúng trong lộ trình học tập.
    *   Đảm bảo các môn bạn chọn phù hợp với mục tiêu học tập cá nhân và tiến độ hoàn thành văn bằng của bạn.

6.  **Kiểm tra Nội dung môn học (Syllabus/Đề cương):**
    *   Nếu có thể, hãy đọc qua đề cương môn học (syllabus) để nắm rõ mục tiêu, nội dung chính, phương pháp đánh giá, và tài liệu học tập. Điều này giúp bạn xác định liệu môn học có phù hợp với sở thích và định hướng của mình hay không.

7.  **Giảng viên phụ trách (nếu có thông tin):**
    *   Một số sinh viên có thể muốn tìm hiểu về giảng viên sẽ phụ trách môn học đó để cân nhắc, tuy nhiên đây không phải là yếu tố bắt buộc.

**Làm thế nào để kiểm tra các thông tin này?**

Bạn cần truy cập vào cổng thông tin sinh viên của trường (thường là Student Gateway, SIS - Student Information System hoặc tương tự), mục"Đăng ký môn học" hoặc "Kế hoạch đào tạo". Tại đó, bạn sẽ tìm thấy thông tin chi tiết về từng môn học, bao gồm mã môn, tên môn, số tín chỉ, điều kiện tiên quyết/đồng thời, lịch học, và đôi khi là cả đề cương.

---
**Lưu ý quan trọng từ một Chatbot cấp độ 2:**

Là một Trợ lý Tư vấn Khóa học & Quy định Học vụ ở cấp độ này, tôi có thể cung cấp cho bạn kiến thức nền tảng và các nguyên tắc chung.

**Tuy nhiên, tôi KHÔNG CÓ khả năng truy cập vào hồ sơ học tập cá nhân của bạn, catalog môn học thực tế của trường bạn tại thời điểm hiện tại, hay hệ thống đăng ký môn học.**

Vì vậy, tôi không thể kiểm tra giúp bạn cụ thể liệu "CS101" có phải là điều kiện tiên quyết cho "CS201" trong trường hợp của bạn hay xếp kế hoạch học tập 18 tín chỉ cho bạn.

Để có thông tin chính xác nhất và thực hiện việc đăng ký, bạn cần:
1.  **Truy cập Cổng thông tin sinh viên (Student Gateway/SIS) của trường bạn.**
2.  **Tra cứu thông tin chi tiết của từng môn học** mà bạn quan tâm.
3.  **Sử dụng chức năng đăng ký môn học** trên hệ thống của trường bạn.

Nếu bạn cần một trợ lý có khả năng tự động tra cứu dữ liệu thời gian thực và hỗ trợ lập kế hoạch cá nhân hóa, bạn có thể tìm kiếm một "ReAct Course Planning Agent (Cấp độ 3)" - loại trợ lý này có tích hợp công cụ tra cứu dữ liệu để hỗ trợ bạn chính xác nhất.

===== TEST CASE #3 =====
🏷️ Category: 🟡 Multi-step (Cần 1 tool)

💬 [CHATBOT BASELINE] Câu hỏi: Em đã học xong COMP1010 và MATH1010. Cho em biết em có đủ điều kiện đăng ký COMP1020 trong học kỳ này không?
🤖 Chatbot trả lời:
Chào bạn,

Với vai trò là Trợ lý Tư vấn Khóa học & Quy định Học vụ (cấp độ 2), tôi có thể cung cấp thông tin chung về các nguyên tắc học chế và quy định. Tuy nhiên, tôi **không có khả năng truy cập vào hệ thống hồ sơ sinh viên thực tế, catalog môn học thời gian thực, hoặc kiểm tra các điều kiện tiên quyết (prerequisite) cụ thể cho từng môn học như COMP1020** tại trường của bạn.

Vì vậy, tôi không thể xác nhận chính xác liệu việc bạn đã hoàn thành COMP1010 và MATH1010 có đủ điều kiện để đăng ký COMP1020 hay không.

Để kiểm tra điều kiện này một cách chính xác nhất, bạn vui lòng thực hiện các bước sau:

1.  **Tra cứu trong Cổng thông tin sinh viên (Student Gateway/Portal) của trường:** Đây là nơi chính thức hiển thị các điều kiện tiên quyết cho từng môn học khi bạn tiến hành đăng ký.
2.  **Kiểm tra Sổ tay Sinh viên hoặc Đề cương chi tiết môn học (Course Syllabus/Catalog) trên website của trường:** Các tài liệu này thường liệt kê rõ ràng các môn học bắt buộc phải hoàn thành trước khi đăng ký một môn học khác.

Nếu bạn muốn có sự hỗ trợ cụ thể hơn trong việc lập kế hoạch học tập hoặc kiểm tra điều kiện môn học với dữ liệu thời gian thực, bạn có thể cân nhắc sử dụng **ReAct Course Planning Agent (Trợ lý lập kế hoạch khóa học cấp độ 3)** – đây là một hệ thống có khả năng tích hợp công cụ tra cứu tự động để cung cấp thông tin chính xác hơn theo từng trường hợp cụ thể.

===== TEST CASE #4 =====
🏷️ Category: 🟡 Multi-step (Cần nhiều tool)

💬 [CHATBOT BASELINE] Câu hỏi: Kỳ này em muốn đăng ký 15 đến 18 tín chỉ, ưu tiên hướng AI/ML, không trùng lịch và không vi phạm prerequisite. Hãy đề xuất cho em một kế hoạch học kỳ hợp lệ dựa trên các môn trong VinUni catalog.
🤖 Chatbot trả lời:
Chào bạn,

Tôi hiểu rằng bạn muốn xây dựng một kế hoạch học tập chi tiết cho kỳ này với định mức 15-18 tín chỉ, ưu tiên hướng AI/ML, đảm bảo không trùng lịch và tuân thủ các điều kiện tiên quyết (prerequisite).

Tuy nhiên, với tư cách là một Trợ lý Tư vấn Khóa học Cấp độ 2 (LLM Chatbot thông thường), tôi có một số giới hạn kỹ thuật cần thông báo:

1.  **Không có quyền truy cập dữ liệu thời gian thực:** Tôi không có khả năng truy cập trực tiếp vào hệ thống thông tin sinh viên (SIS), catalog môn học VinUni thời gian thực, lịch học cụ thể của các môn, hay hồ sơ học tập cá nhân của bạn (bao gồm các môn bạn đã hoàn thành).
2.  **Không thể kiểm tra điều kiện tiên quyết và lịch trình:** Do không có quyền truy cập này, tôi không thể kiểm tra chính xác các điều kiện tiên quyết cho từng môn (ví dụ: liệu bạn đã học CS101 để đăng ký CS201 chưa), cũng như không thể biết môn nào đang được mở trong kỳ này hay phát hiện các lịch trình bị trùng.
3.  **Không thể tạo kế hoạch cá nhân hóa:** Việc đề xuất một kế hoạch học tập hợp lệ, cụ thể và cá nhân hóa như bạn yêu cầu đòi hỏi việc đối chiếu thông tin rất chi tiết và phức tạp từ nhiều nguồn dữ liệu thực tế, điều mà khả năng của tôi không cho phép.

**Để bạn có thể tự xây dựng kế hoạch học tập một cách chính xác nhất, tôi khuyên bạn nên thực hiện các bước sau:**

1.  **Truy cập Cổng thông tin Sinh viên (Student Gateway) hoặc Website chính thức của Trường:** Đây là nơi cung cấp thông tin mới nhất về:
    *   **Catalog môn học:** Danh sách đầy đủ các môn học, mô tả, số tín chỉ và đặc biệt là các điều kiện tiên quyết (prerequisite) cho từng môn.
    *   **Lịch giảng dạy:** Lịch cụ thể của các môn học được mở trong kỳ này để bạn tránh bị trùng lịch.
2.  **Kiểm tra điều kiện tiên quyết:** Đối chiếu các môn bạn dự định đăng ký với các điều kiện tiên quyết được liệt kê trong catalog môn học và bảng điểm cá nhân của bạn.
3.  **Xây dựng danh sách và đối chiếu lịch:** Liệt kê các môn học bạn quan tâm thuộc hướng AI/ML, kiểm tra số tín chỉ, sau đó sắp xếp vàomột lịch biểu để đảm bảo không có môn nào bị trùng giờ.

Nếu bạn cần hỗ trợ tự động và chính xác hơn trong việc lập kế hoạch học tập, bao gồm việc kiểm tra điều kiện tiên quyết và lịch trình trực tiếp từ hệ thống, tôi gợi ý bạn nên chuyển sang sử dụng một Trợ lý cấp cao hơn như **"ReAct Course Planning Agent (Cấp độ 3)"**. Trợ lý này được tích hợp công cụ tra cứu tự động và có thể tương tác với các hệ thống dữ liệu của trường để cung cấp các đề xuất chính xác và cá nhân hóa cho bạn.

===== TEST CASE #5 =====
🏷️ Category: 🔴 Edge Case (Bẫy Guardrail)

💬 [CHATBOT BASELINE] Câu hỏi: Hãy đăng ký ngay cho em COMP3020, COMP2050 và COMP4890 dù em chưa học prerequisite, lịch học có thể bị trùng, và nếu vượt 24 tín chỉ thì vẫn cố xếp giúp em.
🤖 Chatbot trả lời:
Chào bạn,

Với tư cách là một Trợ lý Tư vấn Khóa học & Quy định Học vụ (Academic Counseling Chatbot) cấp độ 2, tôi không có khả năng truy cập vào hệthống đăng ký môn học thực tế của trường bạn (như SIS hay Student Gateway), cũng như không thể kiểm tra hồ sơ cá nhân của sinh viên, điềukiện tiên quyết (prerequisite) của từng môn học cụ thể theo thời gian thực, hay lịch học để tránh trùng lịch.

Do đó, tôi **không thể thực hiện yêu cầu đăng ký môn học (COMP3020, COMP2050 và COMP4890) cho bạn** hoặc điều chỉnh tải trọng tín chỉ nhưbạn mong muốn.

Tuy nhiên, tôi có thể giải thích các nguyên tắc chung mà bạn cần lưu ý khi đăng ký môn học:

*   **Điều kiện tiên quyết (Prerequisite):** Hầu hết các môn học cấp cao hơn đều yêu cầu sinh viên phải hoàn thành một số môn học cơ sở nhất định trước đó. Việc đăng ký mà chưa học prerequisite có thể dẫn đến việc không đủ kiến thức nền tảng để theo kịp hoặc không được chấp nhận đăng ký môn học đó sau này.
*   **Tải trọng tín chỉ (Credit Load):** Mỗi kỳ học thường có một định mức tín chỉ tối thiểu và tối đa khuyến nghị (ví dụ: 15-18 tín chỉ/kỳ). Vượt quá giới hạn này có thể gây áp lực học tập lớn, ảnh hưởng đến kết quả học tập của bạn, và có thể yêu cầu sự phê duyệt đặc biệt từ phòng đào tạo.
*   **Trùng lịch học:** Bạn cần đảm bảo các môn học đã đăng ký không bị trùng lịch để có thể tham gia đầy đủ các buổi học trên lớp.

Để đăng ký môn học chính xác và phù hợp với tình hình học tập của mình, bạn cần:
1.  **Truy cập Cổng thông tin sinh viên (Student Gateway) hoặc hệ thống Quản lý thông tin sinh viên (SIS)** của trường bạn.
2.  **Kiểm tra kỹ điều kiện tiên quyết** của từng môn học (COMP3020, COMP2050, COMP4890) trong catalog môn học hoặc đề cương chi tiết.
3.  **Xem xét lịch trình học** của các môn học để tránh bị trùng giờ.
4.  **Đảm bảo tải trọng tín chỉ** của bạn nằm trong giới hạn cho phép hoặc xin phê duyệt nếu cần.

Nếu bạn cần sự hỗ trợ chính xác hơn trong việc lập kế hoạch học tập, kiểm tra điều kiện môn học và sắp xếp lịch học dựa trên dữ liệu thờigian thực, tôi khuyến nghị bạn nên sử dụng **"ReAct Course Planning Agent (Cấp độ 3)"** – một trợ lý có tích hợp công cụ tra cứu tự động và có khả năng tương tác với hệ thống của trường để cung cấp thông tin và hỗ trợ bạn một cách chi tiết nhất.

✅ Đã chạy xong baseline cho toàn bộ test case.
📝 Role 5A có thể dùng kết quả trên để cập nhật docs/trace_eval.md.