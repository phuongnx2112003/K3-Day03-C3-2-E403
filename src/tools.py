"""
🛠️ TOOL REGISTRY & SCHEMAS (Role 2: Tool & Spec Engineer)

Nơi khai báo tất cả các công cụ (Tools) mà ReAct Agent có thể sử dụng
để hỗ trợ sinh viên lập kế hoạch đăng ký môn học.

NGUYÊN TẮC AN TOÀN (Guardrail-friendly):
Mọi tool bên dưới đều CAM KẾT trả về str trong MỌI trường hợp — kể cả khi:
  - Input sai định dạng (None, sai kiểu, thiếu trường...)
  - Dữ liệu không tồn tại (student_id / course_code không có trong hệ thống)
  - Có lỗi runtime không lường trước (IndexError, KeyError, TypeError...)
Không có exception nào được phép "văng" ra khỏi các hàm này, vì Agent
sẽ ghép trực tiếp giá trị trả về vào chuỗi Observation -> nếu hàm trả về
None hoặc raise Exception, cả vòng lặp ReAct sẽ sập.
"""

import functools
from typing import List, Union

# ============================================================
# 0. SAFETY DECORATOR — lưới an toàn cuối cùng cho mọi tool
# ============================================================

def safe_tool(func):
    """
    Decorator bọc quanh mọi tool: bắt MỌI Exception phát sinh trong quá trình
    thực thi (kể cả lỗi không lường trước như sai kiểu dữ liệu do LLM tự sinh
    Action Input sai định dạng) và chuyển thành chuỗi lỗi thay vì để crash
    lan ra ngoài, làm sập vòng lặp ReAct của Agent.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            # Guardrail phụ: nếu logic bên trong lỡ quên return (như "pass"),
            # vẫn ép về string thay vì để None lọt ra ngoài.
            if result is None:
                return f"LỖI: Tool '{func.__name__}' chưa trả về kết quả hợp lệ."
            return str(result)
        except Exception as e:
            return f"LỖI: Tool '{func.__name__}' gặp sự cố khi thực thi ({type(e).__name__}: {e})."
    return wrapper

# ============================================================
# 2. HELPERS (không expose cho Agent, nhưng vẫn phòng thủ đầu vào)
# ============================================================

def _normalize_course_list(course_codes) -> List[str]:
    """
    Chuẩn hoá input về list mã môn viết hoa. Chấp nhận:
    - list/tuple: ['CS101', 'CS201']
    - string: 'CS101,CS201' (LLM hay sinh dạng này dù docstring khai báo list)
    - None hoặc kiểu lạ -> trả về list rỗng, KHÔNG raise lỗi.
    """
    if course_codes is None:
        return []
    if isinstance(course_codes, str):
        raw = course_codes.split(",")
    elif isinstance(course_codes, (list, tuple)):
        raw = course_codes
    else:
        # Kiểu dữ liệu lạ (int, dict...) -> không crash, coi như không hợp lệ
        return []
    return [str(c).strip().upper() for c in raw if str(c).strip()]


def _time_to_minutes(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def _schedules_overlap(sched_a: dict, sched_b: dict) -> bool:
    shared_days = set(sched_a["days"]) & set(sched_b["days"])
    if not shared_days:
        return False
    a_start, a_end = [_time_to_minutes(t) for t in sched_a["time"].split("-")]
    b_start, b_end = [_time_to_minutes(t) for t in sched_b["time"].split("-")]
    return a_start < b_end and b_start < a_end


# ============================================================
# 3. TOOLS
# ============================================================

@safe_tool
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
    if not student_id or not isinstance(student_id, str):
        return "LỖI: student_id không hợp lệ hoặc bị bỏ trống."

    student = STUDENTS_DB.get(student_id.strip().upper())
    if not student:
        return f"LỖI: Không tìm thấy sinh viên với mã '{student_id}'."

    completed = ", ".join(student["completed_courses"]) or "Chưa có môn nào"
    return (
        f"Hồ sơ sinh viên {student_id}:\n"
        f"- Họ tên: {student['name']}\n"
        f"- Ngành: {student['major']}\n"
        f"- Năm học: {student['year']}\n"
        f"- GPA: {student['gpa']}\n"
        f"- Tổng tín chỉ đã tích luỹ: {student['total_credits_completed']}\n"
        f"- Các môn đã hoàn thành: {completed}"
    )


@safe_tool
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
    if not keyword_or_area or not isinstance(keyword_or_area, str):
        return "LỖI: Từ khoá tìm kiếm trống hoặc không hợp lệ."

    keyword = keyword_or_area.strip().lower()
    matches = []
    for code, info in COURSE_CATALOG.items():
        haystack = f"{code} {info['name']} {info['area']}".lower()
        if keyword in haystack:
            seats_left = info["capacity"] - info["enrolled"]
            prereq = ", ".join(info["prerequisites"]) or "Không yêu cầu"
            matches.append(
                f"- {code}: {info['name']} ({info['credits']} tín chỉ)\n"
                f"    Prerequisite: {prereq}\n"
                f"    Lịch: {'/'.join(info['schedule']['days'])} {info['schedule']['time']}\n"
                f"    Chỗ còn trống: {seats_left}/{info['capacity']}"
            )

    if not matches:
        return f"LỖI: Không tìm thấy môn học nào khớp với từ khoá '{keyword_or_area}'."

    return f"Tìm thấy {len(matches)} môn phù hợp với '{keyword_or_area}':\n" + "\n".join(matches)


@safe_tool
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
    if not student_id or not isinstance(student_id, str):
        return "LỖI: student_id không hợp lệ hoặc bị bỏ trống."

    student = STUDENTS_DB.get(student_id.strip().upper())
    if not student:
        return f"LỖI: Không tìm thấy sinh viên với mã '{student_id}'."

    codes = _normalize_course_list(course_codes)
    if not codes:
        return "LỖI: Danh sách mã môn trống hoặc sai định dạng."

    results = []
    completed = set(student["completed_courses"])
    for code in codes:
        course = COURSE_CATALOG.get(code)
        if not course:
            results.append(f"- {code}: LỖI - Mã môn không tồn tại trong catalog.")
            continue
        missing = set(course["prerequisites"]) - completed
        if code in completed:
            results.append(f"- {code}: Sinh viên đã hoàn thành môn này trước đó.")
        elif not missing:
            results.append(f"- {code}: ĐỦ điều kiện đăng ký (đã hoàn thành hết prerequisite).")
        else:
            results.append(f"- {code}: THIẾU điều kiện. Cần hoàn thành trước: {', '.join(sorted(missing))}")

    return f"Kết quả kiểm tra prerequisite cho sinh viên {student_id}:\n" + "\n".join(results)


@safe_tool
def check_schedule_conflicts(course_codes: list) -> str:
    """
    Kiểm tra xung đột lịch học hoặc lịch thi giữa các môn học đã chọn.

    Args:
        course_codes (list): Danh sách mã môn học.

    Returns:
        str: Kết quả cho biết có hoặc không có xung đột lịch học/lịch thi.
    """
    codes = _normalize_course_list(course_codes)
    if len(codes) < 2:
        return "LỖI: Cần ít nhất 2 mã môn hợp lệ để kiểm tra trùng lịch."

    invalid = [c for c in codes if c not in COURSE_CATALOG]
    if invalid:
        return f"LỖI: Các mã môn sau không tồn tại trong catalog: {', '.join(invalid)}"

    conflicts = []
    for i in range(len(codes)):
        for j in range(i + 1, len(codes)):
            c1, c2 = codes[i], codes[j]
            sched1 = COURSE_CATALOG[c1]["schedule"]
            sched2 = COURSE_CATALOG[c2]["schedule"]
            if _schedules_overlap(sched1, sched2):
                conflicts.append(
                    f"- {c1} ({'/'.join(sched1['days'])} {sched1['time']}) "
                    f"TRÙNG LỊCH với {c2} ({'/'.join(sched2['days'])} {sched2['time']})"
                )

    if not conflicts:
        return f"Không có xung đột lịch học giữa các môn: {', '.join(codes)}."
    return "Phát hiện xung đột lịch học:\n" + "\n".join(conflicts)


@safe_tool
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
    if not student_id or not isinstance(student_id, str):
        return "LỖI: student_id không hợp lệ hoặc bị bỏ trống."

    student = STUDENTS_DB.get(student_id.strip().upper())
    if not student:
        return f"LỖI: Không tìm thấy sinh viên với mã '{student_id}'."

    codes = _normalize_course_list(planned_courses)
    if not codes:
        return "LỖI: Danh sách môn dự định đăng ký trống hoặc sai định dạng."

    invalid = [c for c in codes if c not in COURSE_CATALOG]
    if invalid:
        return f"LỖI: Các mã môn sau không tồn tại trong catalog: {', '.join(invalid)}"

    total_credits = sum(COURSE_CATALOG[c]["credits"] for c in codes)
    detail = ", ".join(f"{c} ({COURSE_CATALOG[c]['credits']} tc)" for c in codes)

    warning = ""
    if total_credits > MAX_CREDITS_PER_SEMESTER:
        warning = f"\nCẢNH BÁO: Vượt quá tải tối đa cho phép ({MAX_CREDITS_PER_SEMESTER} tín chỉ/học kỳ)."
    elif total_credits < MIN_CREDITS_FULL_TIME:
        warning = f"\nLƯU Ý: Dưới mức tối thiểu full-time ({MIN_CREDITS_FULL_TIME} tín chỉ/học kỳ)."

    return (
        f"Tổng tín chỉ dự kiến của sinh viên {student_id}: {total_credits} tín chỉ\n"
        f"Chi tiết: {detail}{warning}"
    )


@safe_tool
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
    if not student_id or not isinstance(student_id, str):
        return "LỖI: student_id không hợp lệ hoặc bị bỏ trống."

    student = STUDENTS_DB.get(student_id.strip().upper())
    if not student:
        return f"LỖI: Không tìm thấy sinh viên với mã '{student_id}'."

    goal_kw = (goal or "").strip().lower()
    completed = set(student["completed_courses"])

    eligible = []
    for code, info in COURSE_CATALOG.items():
        if code in completed:
            continue
        if set(info["prerequisites"]) - completed:
            continue
        if info["capacity"] - info["enrolled"] <= 0:
            continue
        eligible.append((code, info))

    if not eligible:
        return (f"Không tìm thấy môn nào sinh viên {student_id} đủ điều kiện đăng ký "
                f"ở thời điểm hiện tại (có thể do thiếu prerequisite hoặc lớp đã đầy).")

    matched = [(c, i) for c, i in eligible if goal_kw and goal_kw in f"{i['name']} {i['area']}".lower()]
    chosen = (matched if matched else eligible)[:4]

    lines = []
    for code, info in chosen:
        reason = "khớp với mục tiêu đã nêu" if (code, info) in matched else "đủ điều kiện, mở rộng kiến thức nền tảng"
        lines.append(f"- {code}: {info['name']} ({info['credits']} tín chỉ) — {reason}")

    total = sum(i["credits"] for _, i in chosen)
    note = f"\nLƯU Ý: Tổng {total} tín chỉ vượt mức tối đa {MAX_CREDITS_PER_SEMESTER}, cân nhắc bớt môn." \
        if total > MAX_CREDITS_PER_SEMESTER else ""

    return (
        f"Gợi ý kế hoạch học kỳ cho sinh viên {student_id} (mục tiêu: '{goal}'):\n"
        + "\n".join(lines) + f"\nTổng tín chỉ gợi ý: {total}{note}"
    )


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


# ==========================
# SELF-TEST: cố tình gửi input "bẩn" để chứng minh KHÔNG CRASH
# ==========================
if __name__ == "__main__":
    dirty_inputs = [
        ("get_student_profile", (None,), {}),
        ("get_student_profile", (12345,), {}),
        ("search_courses", ("",), {}),
        ("check_prerequisites", ("A202601874", None), {}),
        ("check_prerequisites", ("A202601874", "CS999"), {}),
        ("check_schedule_conflicts", (["CS201"],), {}),          # thiếu, chỉ 1 môn
        ("check_schedule_conflicts", (["CS201", "ZZZ99"]), {}),  # sai kiểu cố ý (thiếu dấu phẩy)
        ("calculate_credit_load", ("XXXX", ["CS301"]), {}),
        ("recommend_course_plan", ("A202601874", None), {}),
    ]
    all_safe = True
    for name, args, kwargs in dirty_inputs:
        func = AVAILABLE_TOOLS[name]
        try:
            result = func(*args, **kwargs)
            ok = isinstance(result, str)
            all_safe = all_safe and ok
            print(f"[{'OK ' if ok else 'FAIL'}] {name}{args} -> {result[:80]}...")
        except Exception as e:
            all_safe = False
            print(f"[CRASH] {name}{args} -> {type(e).__name__}: {e}")

    print("\n" + ("✅ TẤT CẢ INPUT BẨN ĐỀU TRẢ VỀ STRING, KHÔNG CRASH." if all_safe
                  else "❌ VẪN CÒN TRƯỜNG HỢP CRASH HOẶC TRẢ SAI KIỂU."))