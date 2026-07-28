"""Các công cụ cho trợ lý kiểm tra điều kiện đăng ký môn và lập kế hoạch học kỳ."""

CATALOG = {
    "CS101": {"name": "Introduction to Programming", "credits": 3, "prerequisites": []},
    "MATH101": {"name": "Calculus I", "credits": 3, "prerequisites": []},
    "CS201": {"name": "Data Structures", "credits": 3, "prerequisites": ["CS101"]},
    "AI301": {"name": "Machine Learning", "credits": 3, "prerequisites": ["CS201", "MATH101"]},
    "CAP401": {"name": "Capstone Project", "credits": 6, "prerequisites": ["CS201", "AI301"]},
}

STUDENT_RECORDS = {
    "2A202601874": {"name": "Nguyễn Xuân Phượng", "completed_courses": ["CS101", "MATH101"]},
}

COURSE_SCHEDULES = {
    "CS201": "Thứ 2, 08:00-10:00",
    "AI301": "Thứ 2, 09:00-11:00",
    "CAP401": "Thứ 4, 13:00-16:00",
}


def get_student_profile(student_id: str) -> str:
    """Tra cứu hồ sơ và các môn đã hoàn thành của sinh viên."""
    student = STUDENT_RECORDS.get(student_id)
    if not student:
        return f"LỖI [INVALID_ID]: Không tìm thấy sinh viên với mã '{student_id}'."
    return f"Sinh viên: {student['name']}\nMôn đã hoàn thành: {', '.join(student['completed_courses'])}"


def search_courses(keywords: str) -> str:
    """Tra cứu môn học theo mã môn hoặc tên môn."""
    query = keywords.lower().strip()
    matches = [
        f"{code}: {course['name']} ({course['credits']} tín chỉ)"
        for code, course in CATALOG.items()
        if query in code.lower() or query in course["name"].lower()
    ]
    if not matches:
        return f"LỖI [COURSE_NOT_FOUND]: Không tìm thấy môn phù hợp với '{keywords}'."
    return "\n".join(matches)


def check_prerequisites(student_id: str, course_codes: list[str]) -> str:
    """Kiểm tra sinh viên có đủ môn tiên quyết cho danh sách môn hay không."""
    student = STUDENT_RECORDS.get(student_id)
    if not student:
        return f"LỖI [INVALID_ID]: Không tìm thấy sinh viên với mã '{student_id}'."
    completed = set(student["completed_courses"])
    missing = {}
    unknown = []
    for code in course_codes:
        course = CATALOG.get(code.upper())
        if not course:
            unknown.append(code)
            continue
        unmet = [item for item in course["prerequisites"] if item not in completed]
        if unmet:
            missing[code.upper()] = unmet
    if unknown:
        return f"LỖI [COURSE_NOT_FOUND]: Không tồn tại môn {', '.join(unknown)}."
    if missing:
        details = "; ".join(f"{code} thiếu {', '.join(items)}" for code, items in missing.items())
        return f"CHƯA ĐỦ ĐIỀU KIỆN: {details}."
    return f"ĐỦ ĐIỀU KIỆN đăng ký: {', '.join(code.upper() for code in course_codes)}."


def check_schedule_conflicts(course_codes: list[str]) -> str:
    """Kiểm tra trùng lịch học trong danh sách môn dự kiến."""
    seen = {}
    conflicts = []
    for code in course_codes:
        schedule = COURSE_SCHEDULES.get(code.upper())
        if schedule and schedule in seen:
            conflicts.append(f"{seen[schedule]} và {code.upper()} ({schedule})")
        elif schedule:
            seen[schedule] = code.upper()
    if conflicts:
        return "LỖI [SCHEDULE_CONFLICT]: " + "; ".join(conflicts)
    return "Không phát hiện trùng lịch học."


def calculate_credit_load(student_id: str, planned_courses: list[str]) -> str:
    """Tính tổng tín chỉ và kiểm tra giới hạn 12-18 tín chỉ mỗi kỳ."""
    if student_id not in STUDENT_RECORDS:
        return f"LỖI [INVALID_ID]: Không tìm thấy sinh viên với mã '{student_id}'."
    unknown = [code for code in planned_courses if code.upper() not in CATALOG]
    if unknown:
        return f"LỖI [COURSE_NOT_FOUND]: Không tồn tại môn {', '.join(unknown)}."
    total = sum(CATALOG[code.upper()]["credits"] for code in planned_courses)
    if total > 18:
        return f"LỖI [CREDIT_LOAD_VIOLATION]: {total} tín chỉ vượt mức tối đa 18 tín chỉ/kỳ."
    if total < 12:
        return f"CẢNH BÁO [CREDIT_LOAD_VIOLATION]: {total} tín chỉ thấp hơn mức khuyến nghị tối thiểu 12 tín chỉ/kỳ."
    return f"Tải học kỳ hợp lệ: {total} tín chỉ."


def recommend_course_plan(student_id: str, goal: str) -> str:
    """Đề xuất kế hoạch mẫu dựa trên mục tiêu học tập sau khi kiểm tra điều kiện."""
    if student_id not in STUDENT_RECORDS:
        return f"LỖI [INVALID_ID]: Không tìm thấy sinh viên với mã '{student_id}'."
    plan = ["CS201", "AI301", "CAP401"] if "AI" in goal.upper() else ["CS201", "MATH101"]
    return (
        f"Kế hoạch đề xuất: {', '.join(plan)}\n"
        f"{check_prerequisites(student_id, plan)}\n"
        f"{check_schedule_conflicts(plan)}"
    )


AVAILABLE_TOOLS = {
    "get_student_profile": get_student_profile,
    "search_courses": search_courses,
    "check_prerequisites": check_prerequisites,
    "check_schedule_conflicts": check_schedule_conflicts,
    "calculate_credit_load": calculate_credit_load,
    "recommend_course_plan": recommend_course_plan,
}
