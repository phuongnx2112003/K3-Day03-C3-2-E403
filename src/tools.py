"""
🛠️ TOOL REGISTRY & SCHEMAS (Dành cho Role 2: Tool & Spec Engineer)
Nơi khai báo tất cả các "món đồ nghề" mà ReAct Agent có thể gọi.
"""
def get_student_profile(student_id: str) -> str:
    """
    Tra cứu thông tin sinh viên dựa trên mã số sinh viên.
    
    Args:
        student_id (str): Mã số sinh viên (Ví dụ: 'A202601874')
        
    Returns:
        str: Thông tin chi tiết về sinh viên
    """
    if student_id == "A202601874":
        return "Thông tin sinh viên:\n- Họ tên: "
    else:
        return f"LỖI: Không tìm thấy thông tin sinh viên với mã '{student_id}'."

def search_courses(keywords: str) -> str:
    """
    Tra cứu thông tin khóa học dựa trên từ khóa.
    
    Args:
        keywords (str): Từ khóa liên quan đến khóa học (Ví dụ: 'Python', 'Data Science')
        
    Returns:
        str: Danh sách các khóa học phù hợp
    """
    if "python" in keywords.lower():
        return "Khóa học Python:\n1. Python Cơ Bản\n2. Python Nâng Cao"
    elif "data science" in keywords.lower():
        return "Khóa học Data Science:\n1. Data Science Cơ Bản\n2. Machine Learning"
    else:
        return f"LỖI: Không tìm thấy khóa học phù hợp với từ khóa '{keywords}'."

def check_prerequisites(student_id, course_codes):
    pass

def check_schedule_conflicts(course_codes):
    pass

def calculate_credit_load(student_id, planned_courses):
    pass

def recommend_course_plan(student_id, goal):
    pass

# Danh sách các tool được đăng ký để Agent sử dụng
AVAILABLE_TOOLS = {
    "get_student_profile": get_student_profile,
    "search_courses": search_courses,
    "check_prerequisites": check_prerequisites,
    "check_schedule_conflicts": check_schedule_conflicts,
    "calculate_credit_load": calculate_credit_load,
    "recommend_course_plan": recommend_course_plan,
}
