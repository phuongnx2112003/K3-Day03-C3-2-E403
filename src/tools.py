"""
🛠️ TOOL REGISTRY & SCHEMAS (Role 2: Tool & Spec Engineer)

Các công cụ (Tools) dành cho ReAct Agent hỗ trợ sinh viên
kiểm tra điều kiện đăng ký môn học và lập kế hoạch học kỳ.

Yêu cầu:
- Không raise Exception khi gặp lỗi.
- Luôn trả về chuỗi (str).
- Có thông báo lỗi rõ ràng để Agent có thể tiếp tục suy luận.
"""

CATALOG = {
    "CS101": {
        "name": "Introduction to Programming",
        "credits": 3,
        "prerequisites": [],
    },
    "MATH101": {
        "name": "Calculus I",
        "credits": 3,
        "prerequisites": [],
    },
    "CS201": {
        "name": "Data Structures",
        "credits": 3,
        "prerequisites": ["CS101"],
    },
    "AI301": {
        "name": "Machine Learning",
        "credits": 3,
        "prerequisites": ["CS201", "MATH101"],
    },
    "CAP401": {
        "name": "Capstone Project",
        "credits": 6,
        "prerequisites": ["CS201", "AI301"],
    },
}

STUDENT_RECORDS = {
    "2A202601874": {
        "name": "Nguyễn Xuân Phượng",
        "major": "Computer Science",
        "year": 2,
        "gpa": 3.45,
        "completed_courses": ["CS101", "MATH101"],
        "current_credits": 6,
    }
}

COURSE_SCHEDULES = {
    "CS201": "Thứ 2, 08:00-10:00",
    "AI301": "Thứ 2, 09:00-11:00",
    "CAP401": "Thứ 4, 13:00-16:00",
}


# ==========================================================
# Tool 1
# ==========================================================

def get_student_profile(student_id: str) -> str:
    """
    Lấy thông tin hồ sơ sinh viên.

    Bao gồm:
    - Họ tên
    - Ngành học
    - Năm học
    - GPA
    - Danh sách môn đã hoàn thành
    - Tổng số tín chỉ đã tích lũy

    Args:
        student_id (str): Mã số sinh viên.

    Returns:
        str: Thông tin sinh viên hoặc thông báo lỗi.
    """
    try:
        if not isinstance(student_id, str):
            return "LỖI [INVALID_INPUT]: student_id phải là chuỗi."

        student = STUDENT_RECORDS.get(student_id)

        if student is None:
            return (
                f"LỖI [INVALID_ID]: "
                f"Không tìm thấy sinh viên với mã '{student_id}'."
            )

        return (
            f"Họ tên: {student['name']}\n"
            f"Ngành: {student['major']}\n"
            f"Năm học: {student['year']}\n"
            f"GPA: {student['gpa']}\n"
            f"Tín chỉ hiện tại: {student['current_credits']}\n"
            f"Môn đã hoàn thành: "
            f"{', '.join(student['completed_courses'])}"
        )

    except Exception as e:
        return f"LỖI [SYSTEM_ERROR]: {str(e)}"


# ==========================================================
# Tool 2
# ==========================================================

def search_courses(keyword_or_area: str) -> str:
    """
    Tra cứu môn học theo mã hoặc tên môn.

    Args:
        keyword_or_area (str): Từ khóa tìm kiếm.

    Returns:
        str: Danh sách môn học hoặc thông báo lỗi.
    """
    try:
        if not isinstance(keyword_or_area, str):
            return (
                "LỖI [INVALID_INPUT]: "
                "keyword_or_area phải là chuỗi."
            )

        query = keyword_or_area.lower().strip()

        if query == "":
            return "LỖI [INVALID_INPUT]: Từ khóa không được để trống."

        results = []

        for code, course in CATALOG.items():

            if (
                query in code.lower()
                or query in course["name"].lower()
            ):
                results.append(
                    f"{code} - "
                    f"{course['name']} "
                    f"({course['credits']} tín chỉ)"
                )

        if not results:
            return (
                f"LỖI [COURSE_NOT_FOUND]: "
                f"Không tìm thấy môn phù hợp với '{keyword_or_area}'."
            )

        return "\n".join(results)

    except Exception as e:
        return f"LỖI [SYSTEM_ERROR]: {str(e)}"


# ==========================================================
# Tool 3
# ==========================================================

def check_prerequisites(
    student_id: str,
    course_codes: list
) -> str:
    """
    Kiểm tra điều kiện tiên quyết của các môn học.

    Args:
        student_id (str): Mã sinh viên.
        course_codes (list): Danh sách mã môn.

    Returns:
        str: Kết quả kiểm tra prerequisite.
    """
    try:
        if not isinstance(student_id, str):
            return "LỖI [INVALID_INPUT]: student_id phải là chuỗi."

        if not isinstance(course_codes, list):
            return (
                "LỖI [INVALID_INPUT]: "
                "course_codes phải là danh sách."
            )

        student = STUDENT_RECORDS.get(student_id)

        if student is None:
            return (
                f"LỖI [INVALID_ID]: "
                f"Không tìm thấy sinh viên '{student_id}'."
            )

        completed = set(student["completed_courses"])

        missing = []
        unknown = []

        for code in course_codes:

            code = code.upper()

            if code not in CATALOG:
                unknown.append(code)
                continue

            prereqs = CATALOG[code]["prerequisites"]

            unmet = [
                item
                for item in prereqs
                if item not in completed
            ]

            if unmet:
                missing.append(
                    f"{code} thiếu {', '.join(unmet)}"
                )

        if unknown:
            return (
                "LỖI [COURSE_NOT_FOUND]: "
                + ", ".join(unknown)
            )

        if missing:
            return (
                "CHƯA ĐỦ ĐIỀU KIỆN: "
                + "; ".join(missing)
            )

        return (
            "ĐỦ ĐIỀU KIỆN đăng ký: "
            + ", ".join(course_codes)
        )

    except Exception as e:
        return f"LỖI [SYSTEM_ERROR]: {str(e)}"


# ==========================================================
# Tool 4
# ==========================================================

def check_schedule_conflicts(course_codes: list) -> str:
    """
    Kiểm tra trùng lịch học.

    Args:
        course_codes (list): Danh sách mã môn.

    Returns:
        str: Kết quả kiểm tra lịch học.
    """
    try:

        if not isinstance(course_codes, list):
            return (
                "LỖI [INVALID_INPUT]: "
                "course_codes phải là danh sách."
            )

        seen = {}

        conflicts = []

        for code in course_codes:

            schedule = COURSE_SCHEDULES.get(code.upper())

            if schedule is None:
                continue

            if schedule in seen:

                conflicts.append(
                    f"{seen[schedule]} ↔ {code.upper()} "
                    f"({schedule})"
                )

            else:
                seen[schedule] = code.upper()

        if conflicts:

            return (
                "LỖI [SCHEDULE_CONFLICT]: "
                + "; ".join(conflicts)
            )

        return "Không phát hiện trùng lịch học."

    except Exception as e:
        return f"LỖI [SYSTEM_ERROR]: {str(e)}"


# ==========================================================
# Tool 5
# ==========================================================

def calculate_credit_load(
    student_id: str,
    planned_courses: list
) -> str:
    """
    Tính tổng số tín chỉ của học kỳ.

    Args:
        student_id (str): Mã sinh viên.
        planned_courses (list): Danh sách môn.

    Returns:
        str: Kết quả đánh giá số tín chỉ.
    """
    try:

        if not isinstance(student_id, str):
            return "LỖI [INVALID_INPUT]: student_id phải là chuỗi."

        if not isinstance(planned_courses, list):
            return (
                "LỖI [INVALID_INPUT]: "
                "planned_courses phải là danh sách."
            )

        if student_id not in STUDENT_RECORDS:
            return (
                f"LỖI [INVALID_ID]: "
                f"Không tìm thấy sinh viên '{student_id}'."
            )

        unknown = []

        total = 0

        for code in planned_courses:

            code = code.upper()

            if code not in CATALOG:
                unknown.append(code)
                continue

            total += CATALOG[code]["credits"]

        if unknown:

            return (
                "LỖI [COURSE_NOT_FOUND]: "
                + ", ".join(unknown)
            )

        if total > 18:
            return (
                f"LỖI [CREDIT_LOAD_VIOLATION]: "
                f"{total} tín chỉ vượt giới hạn 18."
            )

        if total < 12:
            return (
                f"CẢNH BÁO [LOW_CREDIT_LOAD]: "
                f"{total} tín chỉ dưới mức khuyến nghị 12."
            )

        return (
            f"Tải học kỳ hợp lệ: {total} tín chỉ."
        )

    except Exception as e:
        return f"LỖI [SYSTEM_ERROR]: {str(e)}"


# ==========================================================
# Tool 6
# ==========================================================

def recommend_course_plan(
    student_id: str,
    goal: str
) -> str:
    """
    Gợi ý kế hoạch học tập.

    Args:
        student_id (str): Mã sinh viên.
        goal (str): Mục tiêu học tập.

    Returns:
        str: Kế hoạch môn học đề xuất.
    """
    try:

        if not isinstance(student_id, str):
            return "LỖI [INVALID_INPUT]: student_id phải là chuỗi."

        if not isinstance(goal, str):
            return "LỖI [INVALID_INPUT]: goal phải là chuỗi."

        if student_id not in STUDENT_RECORDS:
            return (
                f"LỖI [INVALID_ID]: "
                f"Không tìm thấy sinh viên '{student_id}'."
            )

        if "AI" in goal.upper():
            plan = [
                "CS201",
                "AI301",
                "CAP401",
            ]
        else:
            plan = [
                "CS201",
                "MATH101",
            ]

        prerequisite_result = check_prerequisites(
            student_id,
            plan,
        )

        schedule_result = check_schedule_conflicts(
            plan
        )

        credit_result = calculate_credit_load(
            student_id,
            plan,
        )

        return (
            "KẾ HOẠCH ĐỀ XUẤT\n"
            "-------------------------\n"
            f"Môn học: {', '.join(plan)}\n\n"
            f"{prerequisite_result}\n"
            f"{schedule_result}\n"
            f"{credit_result}"
        )

    except Exception as e:
        return f"LỖI [SYSTEM_ERROR]: {str(e)}"


# ==========================================================
# Tool Registry
# ==========================================================

AVAILABLE_TOOLS = {
    "get_student_profile": get_student_profile,
    "search_courses": search_courses,
    "check_prerequisites": check_prerequisites,
    "check_schedule_conflicts": check_schedule_conflicts,
    "calculate_credit_load": calculate_credit_load,
    "recommend_course_plan": recommend_course_plan,
}