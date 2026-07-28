"""
🛠️ TOOL REGISTRY & SCHEMAS (Role 2: Tool & Spec Engineer)

Nơi khai báo tất cả các công cụ (Tools) mà ReAct Agent có thể sử dụng
để hỗ trợ sinh viên lập kế hoạch đăng ký môn học.
"""


def get_student_profile(student_id: str) -> str:
    """
    Lấy thông tin hồ sơ của sinh viên dựa trên mã số sinh viên.

    Bao gồm các thông tin như:
    - Ngành học
    - Năm học
    - GPA hiện tại
    - Danh sách môn đã hoàn thành
    - Tổng số tín chỉ đã tích lũy

    Args:
        student_id (str): Mã số sinh viên (Ví dụ: "A202601874").

    Returns:
        str: Thông tin chi tiết của sinh viên hoặc thông báo lỗi nếu không tìm thấy.
    """
    pass


def search_courses(keyword_or_area: str) -> str:
    """
    Tra cứu danh sách môn học trong Course Catalog theo từ khóa hoặc lĩnh vực.

    Có thể tìm kiếm theo:
    - Tên môn học
    - Mã môn học
    - Lĩnh vực (AI, Data Science, Programming,...)

    Args:
        keyword_or_area (str): Từ khóa hoặc lĩnh vực cần tìm.

    Returns:
        str: Danh sách các môn học phù hợp hoặc thông báo nếu không tìm thấy.
    """
    pass


def check_prerequisites(student_id: str, course_codes: list) -> str:
    """
    Kiểm tra sinh viên có đáp ứng điều kiện tiên quyết (Prerequisites)
    của các môn học dự định đăng ký hay không.

    Args:
        student_id (str): Mã số sinh viên.
        course_codes (list): Danh sách mã môn cần kiểm tra.

    Returns:
        str: Kết quả kiểm tra điều kiện tiên quyết của từng môn học.
    """
    pass


def check_schedule_conflicts(course_codes: list) -> str:
    """
    Kiểm tra xung đột lịch học hoặc lịch thi giữa các môn học đã chọn.

    Args:
        course_codes (list): Danh sách mã môn học.

    Returns:
        str: Kết quả cho biết có hoặc không có xung đột lịch học/lịch thi.
    """
    pass


def calculate_credit_load(student_id: str, planned_courses: list) -> str:
    """
    Tính tổng số tín chỉ của các môn học dự kiến đăng ký trong học kỳ.

    Đồng thời kiểm tra tổng số tín chỉ có nằm trong giới hạn cho phép
    theo quy định của nhà trường hay không.

    Args:
        student_id (str): Mã số sinh viên.
        planned_courses (list): Danh sách mã môn dự kiến đăng ký.

    Returns:
        str: Tổng số tín chỉ và kết quả đánh giá khối lượng học tập.
    """
    pass


def recommend_course_plan(student_id: str, goal: str) -> str:
    """
    Đề xuất kế hoạch học tập phù hợp với mục tiêu của sinh viên.

    Việc gợi ý có thể dựa trên:
    - Hồ sơ sinh viên
    - Các môn đã hoàn thành
    - Điều kiện tiên quyết
    - Khối lượng tín chỉ
    - Mục tiêu nghề nghiệp hoặc học tập

    Args:
        student_id (str): Mã số sinh viên.
        goal (str): Mục tiêu học tập hoặc nghề nghiệp
            (Ví dụ: "AI Engineer", "Data Scientist").

    Returns:
        str: Danh sách các môn học được đề xuất kèm giải thích.
    """
    pass


# ==========================
# Tool Registry
# ==========================

AVAILABLE_TOOLS = {
    "get_student_profile": get_student_profile,
    "search_courses": search_courses,
    "check_prerequisites": check_prerequisites,
    "check_schedule_conflicts": check_schedule_conflicts,
    "calculate_credit_load": calculate_credit_load,
    "recommend_course_plan": recommend_course_plan,
}