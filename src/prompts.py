"""
🧠 PROMPTS & SAFEGUARDS (Dành cho Role 3: Prompt & Safeguard Engineer)
Nơi cấu hình System Prompt và Phanh An Toàn (Guardrails) cho AI.
Chủ đề: #7. Trợ Lý Lập Kế Hoạch Học Kỳ & Đăng Ký Môn (Student Course Planning Agent)
"""

# ==============================================================================
# 🛡️ FAILURE MODES & GUARDRAIL STRATEGIES (MỐC 1: ĐỊNH HÌNH & XÁC ĐỊNH LỖI TOOL)
# ==============================================================================
"""
Trong bài toán Trợ lý Lập Kế Hoạch Học Kỳ & Đăng Ký Môn (Academic Planning Agent),
hệ thống AI có nguy cơ gặp phải 6 trường hợp lỗi công cụ (Failure Modes) phổ biến.
Dưới đây là bảng phân tích nguyên nhân và chiến lược phanh Guardrails / Prompting để xử lý:

1. [COURSE_NOT_FOUND] Môn học không tồn tại trong Catalog
   - Nguyên nhân: Sinh viên nhập sai mã môn (VD: CS999, AI1000) hoặc tên môn không đúng từ khóa.
   - Phản ứng của Tool: Trả về lỗi "[LỖI] Môn học 'CS999' không tồn tại trong Academic Catalog."
   - Chiến lược Guardrail: LLM tuyệt đối KHÔNG được tự ý bịa thông tin môn học (hallucination). Khi nhận lỗi, Agent phải thông báo rõ môn không tồn tại và đề xuất tra cứu lại danh sách môn hợp lệ trong catalog.

2. [PREREQUISITES_NOT_MET] Thiếu môn tiên quyết (Chưa đủ điều kiện học)
   - Nguyên nhân: Sinh viên muốn đăng ký môn chuyên ngành nâng cao (VD: Machine Learning, Data Structures) nhưng chưa đạt/chưa học môn tiên quyết (VD: Intro to Programming, Calculus).
   - Phản ứng của Tool: check_prerequisites trả về status thất bại kèm danh sách môn tiên quyết còn thiếu.
   - Chiến lược Guardrail: Agent tuyệt đối KHÔNG được lập kế hoạch hay khuyên đăng ký bừa. Phải giải thích rõ quy định học vụ (VinUni Academic Regulations), từ chối đưa môn này vào kế hoạch học kỳ và khuyên sinh viên học môn tiên quyết trước.

3. [SCHEDULE_CONFLICT] Trùng lịch học hoặc lịch thi
   - Nguyên nhân: Các môn được chọn có khung giờ giảng dạy hoặc lịch thi cuối kỳ bị chồng chéo.
   - Phản ứng của Tool: check_schedule_conflicts trả về lỗi chi tiết các khung giờ bị trùng.
   - Chiến lược Guardrail: Agent không được chốt kế hoạch bị trùng lịch. Phải tự động thử tìm section/lớp khác hoặc gợi ý môn học thay thế cùng nhóm ngành.

4. [CREDIT_LOAD_VIOLATION] Vi phạm định mức tải trọng tín chỉ (Quá tải / Thiếu tải)
   - Nguyên nhân: Sinh viên tham lam đăng ký quá số tín chỉ tối đa (VD: đòi học 25 - 30 tín chỉ trong 1 kỳ trong khi quy định tối đa là 18 tín chỉ/kỳ) hoặc đăng ký dưới mức tối thiểu full-time (< 12 tín chỉ).
   - Phản ứng của Tool: calculate_credit_load cảnh báo vi phạm chính sách tải trọng học kỳ.
   - Chiến lược Guardrail: Agent cương quyết cảnh báo vi phạm quy định đào tạo, từ chối chốt lịch 30 tín chỉ, yêu cầu sinh viên rút bớt môn để đảm bảo sức khỏe và chất lượng học tập (khuyến nghị 15-18 tín chỉ).

5. [SYSTEM_ERROR / INVALID_ID] Lỗi truy vấn hồ sơ sinh viên hoặc kết nối API
   - Nguyên nhân: Mã sinh viên không hợp lệ hoặc hệ thống Student Gateway bị timeout.
   - Phản ứng của Tool: Trả về chuỗi thông báo lỗi kỹ thuật thay vì crash code (Exception Handling).
   - Chiến lược Guardrail: Agent lịch sự thông báo lỗi kỹ thuật hoặc yêu cầu người dùng kiểm tra lại mã sinh viên.

6. [INFINITE_LOOP] Rơi vào vòng lặp suy luận vô tận (ReAct Looping)
   - Nguyên nhân: LLM gọi đi gọi lại cùng một tool với một tham số do không tìm thấy thỏa hiệp phù hợp.
   - Chiến lược Guardrail: Đặt phanh cứng MAX_ITERATIONS (mặc định = 3 đến 5 bước) và TIMEOUT_SECONDS. Khi chạm ngưỡng, hệ thống tự động ngắt vòng lặp và xuất câu trả lời tổng kết tốt nhất hiện có.
"""

# ==============================================================================
# 📋 PROMPT DEFINITIONS (MỐC 2 & MỐC 3)
# ==============================================================================

# Baseline Chatbot Prompt (Chỉ dùng LLM thông thường, không có Tool - Mốc 2)
CHATBOT_BASELINE_PROMPT = """Bạn là một Chatbot tư vấn thông thường.
Hãy trả lời câu hỏi của người dùng một cách thân thiện dựa trên kiến thức có sẵn của bạn.
Nếu không biết thông tin thực tế thời gian thực, hãy lịch sự thông báo cho người dùng.
"""

# ReAct Agent Prompt (Ép LLM suy luận theo chuỗi Thought -> Action - Mốc 3)
REACT_SYSTEM_PROMPT = """Bạn là một ReAct Agent thông minh có khả năng sử dụng công cụ (Tools).

Danh sách các công cụ bạn có thể sử dụng:
1. get_weather[location]: Tra cứu thời tiết hiện tại của một thành phố.
2. search_flights[origin, destination]: Tra cứu chuyến bay giữa 2 địa điểm.

QUY TẮC BẮT BUỘC: Khi trả lời, bạn PHẢI tuân theo định dạng từng dòng như sau:

Thought: Suy luận của bạn về bước tiếp theo cần làm.
Action: tên_công_cụ[tham_số]
(Sau đó dừng lại chờ hệ thống trả về kết quả Observation)

Khi đã có đủ thông tin để trả lời người dùng, hãy dùng định dạng:
Thought: Tôi đã có đủ thông tin để trả lời.
Final Answer: Câu trả lời hoàn chỉnh cuối cùng gửi cho người dùng.

BẮT ĐẦU:
"""

# 🛡️ GUARDRAILS CONFIGURATION (PHANH AN TOÀN)
MAX_ITERATIONS = 3  # Giới hạn tối đa 3 vòng lặp Thought-Action để tránh lặp vô tận
TIMEOUT_SECONDS = 10  # Timeout cho mỗi lần gọi tool
