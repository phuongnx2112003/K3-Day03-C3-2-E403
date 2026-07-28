"""Tool registry cho trợ lý kiểm tra điều kiện đăng ký môn và lập kế hoạch học kỳ.

Dữ liệu catalog/schedule trong file này là fixture cục bộ để chạy lab offline.
Khi triển khai thật, các nguồn cần đồng bộ với Academic Catalog/SIS của VinUni.
"""

from functools import lru_cache
from pathlib import Path

try:
    from pypdf import PdfReader
except ImportError:  # Cho phép import module trước khi cài dependency.
    PdfReader = None

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_FILES = {
    "academic_regulations": PROJECT_ROOT / "docs/sources/vinuni-academic-regulations.pdf",
    "computer_science_curriculum": PROJECT_ROOT / "docs/sources/vinuni-computer-science-curriculum.pdf",
}
ONLINE_SOURCES = {
    "registrar": "https://registrar.vinuni.edu.vn/academics/policy-regulations/",
    "student_gateway": "https://vinuni.edu.vn/student-gateway/",
}

CATALOG = {
    "COMP1010": {"name": "Introduction to Programming", "credits": 4, "prerequisites": []},
    "MATH1010": {"name": "Calculus I", "credits": 4, "prerequisites": []},
    "STAT1010": {"name": "Probability and Statistics", "credits": 3, "prerequisites": []},
    "MATH2010": {"name": "Linear Algebra", "credits": 3, "prerequisites": []},
    "COMP1020": {"name": "Object-oriented Programming and Data Structures", "credits": 4, "prerequisites": ["COMP1010"]},
    "COMP2030": {"name": "Software Construction", "credits": 4, "prerequisites": ["COMP1020"]},
    "COMP2050": {"name": "Artificial Intelligence", "credits": 4, "prerequisites": ["COMP1010", "STAT1010"]},
    "COMP3010": {"name": "Algorithm Design", "credits": 4, "prerequisites": ["COMP1020"]},
    "COMP3020": {
        "name": "Machine Learning",
        "credits": 4,
        "prerequisites": ["MATH2010", "STAT1010", "COMP1020", "COMP2030"],
    },
    "COMP3030": {"name": "Databases and Database Systems", "credits": 3, "prerequisites": ["COMP1020", "COMP2030"]},
    "COMP4890": {"name": "Graduation Thesis/Capstone", "credits": 6, "prerequisites": ["COMP1020", "COMP2030", "COMP3010"]},
}

STUDENT_RECORDS = {
    "2A202601874": {
        "name": "Nguyễn Xuân Phượng",
        "completed_courses": ["COMP1010", "MATH1010"],
    },
}

COURSE_SCHEDULES = {
    "COMP1020": "Mon 08:00-10:00",
    "COMP2030": "Tue 08:00-10:00",
    "COMP2050": "Wed 08:00-10:00",
    "COMP3010": "Thu 08:00-10:00",
    "COMP3020": "Wed 08:00-10:00",
    "COMP3030": "Fri 08:00-10:00",
    "COMP4890": "Tue 08:00-10:00",
}


@lru_cache(maxsize=None)
def _read_source_pages(source_name: str):
    """Đọc PDF một lần và cache nội dung theo từng trang."""
    if PdfReader is None:
        raise RuntimeError("Thiếu thư viện pypdf. Hãy chạy: pip install -r requirements.txt")
    path = SOURCE_FILES.get(source_name)
    if path is None or not path.exists():
        raise FileNotFoundError(f"Không tìm thấy tài liệu nguồn: {source_name}")
    reader = PdfReader(str(path))
    return [page.extract_text() or "" for page in reader.pages]


def search_official_sources(query: str, max_results: int = 3) -> str:
    """Tìm đoạn trích liên quan trong PDF Academic Regulations/CS Curriculum.

    Kết quả luôn kèm nguồn và số trang để Agent có thể viện dẫn. Student Gateway
    và Registrar được trả dưới dạng liên kết chính thức vì cần truy cập online/SIS.
    """
    query_text = " ".join(str(query).lower().split())
    terms = [term for term in query_text.split() if len(term) > 2]
    phrases = [query_text]
    if len(terms) > 1:
        phrases.extend(" ".join(terms[index:index + 2]) for index in range(len(terms) - 1))
    if not terms:
        return "LỖI [EMPTY_QUERY]: Cần cung cấp từ khóa tra cứu tài liệu."

    results = []
    for source_name in SOURCE_FILES:
        try:
            pages = _read_source_pages(source_name)
        except (FileNotFoundError, RuntimeError) as exc:
            return f"LỖI [SOURCE_UNAVAILABLE]: {exc}"
        for page_number, text in enumerate(pages, start=1):
            lowered = text.lower()
            score = sum(lowered.count(term) for term in terms)
            score += 2 * sum(lowered.count(phrase) for phrase in phrases if " " in phrase)
            if score == 0:
                continue
            first_term_position = min(
                (lowered.find(phrase) for phrase in sorted(phrases, key=len, reverse=True) if lowered.find(phrase) >= 0),
                default=0,
            )
            start = max(0, first_term_position - 180)
            snippet = " ".join(text[start:start + 520].split())
            results.append((score, source_name, page_number, snippet))

    results.sort(key=lambda item: item[0], reverse=True)
    if not results:
        online = "\n".join(f"- {name}: {url}" for name, url in ONLINE_SOURCES.items())
        return f"Không tìm thấy đoạn trích phù hợp trong PDF. Nguồn online cần kiểm tra:\n{online}"

    lines = ["KẾT QUẢ TRA CỨU TÀI LIỆU CHÍNH THỨC:"]
    for _, source_name, page_number, snippet in results[:max_results]:
        lines.append(f"[{source_name}, trang {page_number}] {snippet}")
    return "\n".join(lines)


def _normalise_codes(course_codes):
    """Chuẩn hóa mã môn và chấp nhận cả một mã đơn lẻ."""
    if isinstance(course_codes, str):
        course_codes = [course_codes]
    return [str(code).strip().upper() for code in course_codes]


def get_student_profile(student_id: str) -> str:
    """Tra cứu hồ sơ và các môn đã hoàn thành của sinh viên."""
    student = STUDENT_RECORDS.get(str(student_id).strip())
    if not student:
        return f"LỖI [INVALID_ID]: Không tìm thấy sinh viên với mã '{student_id}'."
    completed = ", ".join(student["completed_courses"])
    return f"Sinh viên: {student['name']} ({student_id})\nMôn đã hoàn thành: {completed}"


def search_courses(keywords: str) -> str:
    """Tra cứu môn học theo mã môn hoặc tên môn trong catalog fixture."""
    query = str(keywords).lower().strip()
    matches = [
        f"{code}: {course['name']} ({course['credits']} tín chỉ; prerequisite: {', '.join(course['prerequisites']) or 'Không có'})"
        for code, course in CATALOG.items()
        if query in code.lower() or query in course["name"].lower()
    ]
    if not matches:
        return f"LỖI [COURSE_NOT_FOUND]: Không tìm thấy môn phù hợp với '{keywords}'."
    return "\n".join(matches)


def check_prerequisites(student_id: str, course_codes: list[str]) -> str:
    """Kiểm tra prerequisite của các môn đối với hồ sơ sinh viên."""
    student = STUDENT_RECORDS.get(str(student_id).strip())
    if not student:
        return f"LỖI [INVALID_ID]: Không tìm thấy sinh viên với mã '{student_id}'."

    codes = _normalise_codes(course_codes)
    completed = set(student["completed_courses"])
    missing = {}
    unknown = []
    for code in codes:
        course = CATALOG.get(code)
        if not course:
            unknown.append(code)
            continue
        unmet = [item for item in course["prerequisites"] if item not in completed]
        if unmet:
            missing[code] = unmet

    if unknown:
        return f"LỖI [COURSE_NOT_FOUND]: Không tồn tại môn {', '.join(unknown)}."
    if missing:
        details = "; ".join(f"{code} thiếu {', '.join(items)}" for code, items in missing.items())
        return f"CHƯA ĐỦ ĐIỀU KIỆN: {details}."
    return f"ĐỦ ĐIỀU KIỆN đăng ký: {', '.join(codes)}."


def check_schedule_conflicts(course_codes: list[str]) -> str:
    """Kiểm tra trùng khung giờ trong danh sách môn dự kiến."""
    codes = _normalise_codes(course_codes)
    unknown = [code for code in codes if code not in CATALOG]
    if unknown:
        return f"LỖI [COURSE_NOT_FOUND]: Không tồn tại môn {', '.join(unknown)}."

    seen = {}
    conflicts = []
    for code in codes:
        schedule = COURSE_SCHEDULES.get(code)
        if schedule and schedule in seen:
            conflicts.append(f"{seen[schedule]} và {code} ({schedule})")
        elif schedule:
            seen[schedule] = code
    if conflicts:
        return "LỖI [SCHEDULE_CONFLICT]: " + "; ".join(conflicts)
    return "Không phát hiện trùng lịch học."


def calculate_credit_load(student_id: str, planned_courses: list[str]) -> str:
    """Tính tải tín chỉ theo quy định fixture 12 credits tối thiểu, 18 credits chuẩn."""
    if str(student_id).strip() not in STUDENT_RECORDS:
        return f"LỖI [INVALID_ID]: Không tìm thấy sinh viên với mã '{student_id}'."
    codes = _normalise_codes(planned_courses)
    unknown = [code for code in codes if code not in CATALOG]
    if unknown:
        return f"LỖI [COURSE_NOT_FOUND]: Không tồn tại môn {', '.join(unknown)}."
    total = sum(CATALOG[code]["credits"] for code in codes)
    if total > 18:
        return f"CẢNH BÁO [CREDIT_LOAD_VIOLATION]: {total} tín chỉ vượt mức chuẩn 18; cần phê duyệt overload."
    if total < 12:
        return f"CẢNH BÁO [CREDIT_LOAD_VIOLATION]: {total} tín chỉ thấp hơn mức full-time tối thiểu 12."
    return f"Tải học kỳ hợp lệ: {total} tín chỉ."


def recommend_course_plan(student_id: str, goal: str) -> str:
    """Đề xuất kế hoạch an toàn và báo rõ các điều kiện chưa đáp ứng."""
    if str(student_id).strip() not in STUDENT_RECORDS:
        return f"LỖI [INVALID_ID]: Không tìm thấy sinh viên với mã '{student_id}'."
    candidates = ["COMP1020", "COMP2030", "COMP2050", "COMP3010", "COMP3030"]
    if "AI" not in str(goal).upper() and "ML" not in str(goal).upper():
        candidates = ["COMP1020", "COMP2030", "COMP3030"]
    eligible = []
    blocked = []
    completed = set(STUDENT_RECORDS[str(student_id).strip()]["completed_courses"])
    for code in candidates:
        unmet = [item for item in CATALOG[code]["prerequisites"] if item not in completed]
        if unmet:
            blocked.append(f"{code} thiếu {', '.join(unmet)}")
        else:
            eligible.append(code)
    if not eligible:
        return "KHÔNG CÓ KẾ HOẠCH HỢP LỆ: " + "; ".join(blocked)
    return (
        f"Kế hoạch sơ bộ: {', '.join(eligible)}\n"
        f"{check_schedule_conflicts(eligible)}\n"
        f"{calculate_credit_load(student_id, eligible)}\n"
        + (f"Môn chưa thể đưa vào kế hoạch: {'; '.join(blocked)}" if blocked else "")
    )


AVAILABLE_TOOLS = {
    "search_official_sources": search_official_sources,
    "get_student_profile": get_student_profile,
    "search_courses": search_courses,
    "check_prerequisites": check_prerequisites,
    "check_schedule_conflicts": check_schedule_conflicts,
    "calculate_credit_load": calculate_credit_load,
    "recommend_course_plan": recommend_course_plan,
}
