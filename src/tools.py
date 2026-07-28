"""Tool registry cho trợ lý kiểm tra điều kiện đăng ký môn và lập kế hoạch học kỳ.

Dữ liệu catalog/schedule trong file này là fixture cục bộ để chạy lab offline.
Khi triển khai thật, các nguồn cần đồng bộ với Academic Catalog/SIS của VinUni.
"""

import hashlib
import json
import os
import re
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
EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")
EMBEDDING_DIMENSIONS = int(os.getenv("GEMINI_EMBEDDING_DIMENSIONS", "768"))
CHROMA_DB_PATH = PROJECT_ROOT / ".chroma"
CHROMA_COLLECTION_NAME = "vinuni_official_documents"
EMBEDDING_CHUNK_WORDS = 180
EMBEDDING_CHUNK_OVERLAP = 40


class EmbeddingUnavailable(RuntimeError):
    """Gemini embedding chưa được cấu hình hoặc không thể gọi trong lúc này."""

CATALOG = {
    "COMP1010": {"name": "Introduction to Programming", "credits": 4, "prerequisites": [], "area": "Core CS"},
    "MATH1010": {"name": "Calculus I", "credits": 4, "prerequisites": [], "area": "Mathematics"},
    "STAT1010": {"name": "Probability and Statistics", "credits": 3, "prerequisites": [], "area": "Mathematics, AI/ML"},
    "MATH2010": {"name": "Linear Algebra", "credits": 3, "prerequisites": [], "area": "Mathematics, AI/ML"},
    "GENE1010": {"name": "Academic Writing", "credits": 3, "prerequisites": [], "area": "General Education"},
    "GENE1020": {"name": "Critical Thinking", "credits": 3, "prerequisites": [], "area": "General Education"},
    "COMP1020": {"name": "Object-oriented Programming and Data Structures", "credits": 4, "prerequisites": ["COMP1010"], "area": "Core CS, AI/ML foundation"},
    "COMP2030": {"name": "Software Construction", "credits": 4, "prerequisites": ["COMP1020"], "area": "Core CS"},
    "COMP2050": {"name": "Artificial Intelligence", "credits": 4, "prerequisites": ["COMP1010", "STAT1010"], "area": "AI/ML"},
    "COMP3010": {"name": "Algorithm Design", "credits": 4, "prerequisites": ["COMP1020"], "area": "Core CS"},
    "COMP3020": {
        "name": "Machine Learning",
        "credits": 4,
        "prerequisites": ["MATH2010", "STAT1010", "COMP1020", "COMP2030"],
        "area": "AI/ML",
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
    "MATH2010": "Mon 10:00-12:00",
    "STAT1010": "Tue 10:00-12:00",
    "GENE1010": "Wed 10:00-12:00",
    "GENE1020": "Thu 10:00-12:00",
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


def _source_fingerprints():
    """Fingerprint PDF để tự tạo lại index khi tài liệu nguồn thay đổi."""
    fingerprints = {}
    for source_name, path in SOURCE_FILES.items():
        if not path.exists():
            raise FileNotFoundError(f"Không tìm thấy tài liệu nguồn: {source_name}")
        fingerprints[source_name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return fingerprints


def _chunk_source_pages():
    """Chia PDF thành các đoạn ngắn có overlap, vẫn giữ nguồn và số trang."""
    chunks = []
    for source_name in SOURCE_FILES:
        for page_number, page_text in enumerate(_read_source_pages(source_name), start=1):
            words = page_text.split()
            for start in range(0, len(words), EMBEDDING_CHUNK_WORDS - EMBEDDING_CHUNK_OVERLAP):
                text = " ".join(words[start:start + EMBEDDING_CHUNK_WORDS])
                if text:
                    chunks.append({"source": source_name, "page": page_number, "text": text})
    return chunks


def _gemini_embed(texts, task_type):
    """Gọi Gemini Embedding API; không có key thì caller dùng lexical fallback."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise EmbeddingUnavailable("Chưa cấu hình GEMINI_API_KEY")
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        response = client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=texts,
            config=types.EmbedContentConfig(
                task_type=task_type,
                output_dimensionality=EMBEDDING_DIMENSIONS,
            ),
        )
        vectors = [embedding.values for embedding in response.embeddings]
        if len(vectors) != len(texts):
            raise EmbeddingUnavailable("Gemini trả về số vector không khớp dữ liệu đầu vào")
        return vectors
    except EmbeddingUnavailable:
        raise
    except Exception as exc:
        raise EmbeddingUnavailable(f"Không thể tạo Gemini embedding: {exc}") from exc


def _load_or_build_chroma_collection():
    """Mở ChromaDB persistent và index lại khi PDF nguồn thay đổi."""
    fingerprints = _source_fingerprints()
    try:
        import chromadb
    except ImportError as exc:
        raise EmbeddingUnavailable("Thiếu chromadb. Hãy chạy: pip install -r requirements.txt") from exc

    corpus_hash = hashlib.sha256(json.dumps(fingerprints, sort_keys=True).encode()).hexdigest()
    try:
        client = chromadb.PersistentClient(path=str(CHROMA_DB_PATH))
        collection = client.get_or_create_collection(
            name=CHROMA_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        existing = collection.get(include=["metadatas"])
    except Exception as exc:
        raise EmbeddingUnavailable(f"Không thể mở ChromaDB: {exc}") from exc

    chunks = _chunk_source_pages()
    if not chunks:
        raise EmbeddingUnavailable("Không trích xuất được nội dung từ PDF nguồn")

    existing_metadata = existing.get("metadatas") or []
    index_current = (
        len(existing.get("ids") or []) == len(chunks)
        and all(metadata and metadata.get("corpus_hash") == corpus_hash for metadata in existing_metadata)
    )
    if index_current:
        return collection

    if existing.get("ids"):
        collection.delete(ids=existing["ids"])
    for start in range(0, len(chunks), 32):
        batch = chunks[start:start + 32]
        vectors = _gemini_embed([chunk["text"] for chunk in batch], "RETRIEVAL_DOCUMENT")
        collection.upsert(
            ids=[f"{chunk['source']}-p{chunk['page']}-{start + index}" for index, chunk in enumerate(batch)],
            documents=[chunk["text"] for chunk in batch],
            embeddings=vectors,
            metadatas=[
                {
                    "source": chunk["source"],
                    "page": chunk["page"],
                    "corpus_hash": corpus_hash,
                    "embedding_model": EMBEDDING_MODEL,
                }
                for chunk in batch
            ],
        )
    return collection


def _semantic_search(query, max_results):
    """Semantic retrieval: Gemini tạo query vector, ChromaDB tìm nearest chunks."""
    collection = _load_or_build_chroma_collection()
    query_vector = _gemini_embed([query], "RETRIEVAL_QUERY")[0]
    results = collection.query(
        query_embeddings=[query_vector],
        n_results=max_results,
        include=["documents", "metadatas", "distances"],
    )
    documents = (results.get("documents") or [[]])[0]
    metadatas = (results.get("metadatas") or [[]])[0]
    distances = (results.get("distances") or [[]])[0]
    return [
        (distance, {"source": metadata["source"], "page": metadata["page"], "text": document})
        for distance, document, metadata in zip(distances, documents, metadatas)
        if document is not None and metadata is not None
    ]


def _lexical_search(query_text, max_results):
    """Fallback offline khi Gemini embedding chưa sẵn sàng."""
    terms = [term for term in query_text.split() if len(term) > 2]
    # PDF nguồn là tiếng Anh; map các cách hỏi phổ biến bằng tiếng Việt sang
    # thuật ngữ xuất hiện trong Academic Regulations để tránh kết quả nhiễu.
    if any(token in query_text for token in ("tải trọng", "tín chỉ", "học kỳ", "credit", "study load")):
        terms.extend(["study", "load", "credit", "semester"])
    terms = list(dict.fromkeys(terms))
    phrases = [query_text]
    if len(terms) > 1:
        phrases.extend(" ".join(terms[index:index + 2]) for index in range(len(terms) - 1))
    if not terms:
        return []

    results = []
    for source_name in SOURCE_FILES:
        pages = _read_source_pages(source_name)
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
            results.append((score, {"source": source_name, "page": page_number, "text": " ".join(text[start:start + 520].split())}))
    return sorted(results, key=lambda item: item[0], reverse=True)[:max_results]


def search_official_sources(query: str, max_results: int = 3) -> str:
    """Tìm đoạn trích liên quan trong PDF Academic Regulations/CS Curriculum.

    Kết quả luôn kèm nguồn và số trang để Agent có thể viện dẫn. Student Gateway
    và Registrar được trả dưới dạng liên kết chính thức vì cần truy cập online/SIS.
    """
    query_text = " ".join(str(query).lower().split())
    if not query_text:
        return "LỖI [EMPTY_QUERY]: Cần cung cấp từ khóa tra cứu tài liệu."
    try:
        results = _semantic_search(query_text, max_results)
        retrieval_method = "GEMINI EMBEDDING"
    except (EmbeddingUnavailable, FileNotFoundError, RuntimeError):
        try:
            results = _lexical_search(query_text, max_results)
            retrieval_method = "KEYWORD FALLBACK"
        except (FileNotFoundError, RuntimeError) as exc:
            return f"LỖI [SOURCE_UNAVAILABLE]: {exc}"
    if not results:
        online = "\n".join(f"- {name}: {url}" for name, url in ONLINE_SOURCES.items())
        return f"Không tìm thấy đoạn trích phù hợp trong PDF. Nguồn online cần kiểm tra:\n{online}"

    lines = [f"KẾT QUẢ TRA CỨU TÀI LIỆU CHÍNH THỨC ({retrieval_method}):"]
    for _, chunk in results:
        lines.append(f"[{chunk['source']}, trang {chunk['page']}] {chunk['text']}")
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
    """Tra cứu môn theo mã/tên; chấp nhận nhiều từ khóa ngăn cách bởi dấu phẩy."""
    query = str(keywords).lower().strip()
    terms = [term.strip() for term in re.split(r"[,;/]+", query) if term.strip()]
    if query in {"ai/ml", "ai", "ml"}:
        terms.extend(["artificial intelligence", "machine learning", "ai/ml"])
    if not terms:
        return "LỖI [EMPTY_QUERY]: Cần cung cấp từ khóa hoặc mã môn."
    matches = [
        f"{code}: {course['name']} ({course['credits']} tín chỉ; prerequisite: {', '.join(course['prerequisites']) or 'Không có'})"
        for code, course in CATALOG.items()
        if any(term in code.lower() or term in course["name"].lower() or term in course.get("area", "").lower() for term in terms)
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

    unavailable = [code for code in codes if code not in COURSE_SCHEDULES]
    if unavailable:
        return f"CẢNH BÁO [SCHEDULE_UNAVAILABLE]: Chưa có lịch fixture cho {', '.join(unavailable)}; không thể xác nhận kế hoạch không trùng lịch."

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
    candidates = [code for code in CATALOG if code not in STUDENT_RECORDS[str(student_id).strip()]["completed_courses"]]
    if "AI" not in str(goal).upper() and "ML" not in str(goal).upper():
        candidates = [code for code in candidates if "AI/ML" not in CATALOG[code].get("area", "")]
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
    # Ưu tiên các môn nền AI/ML; GenEd chỉ đóng vai trò bù đủ tải tối thiểu.
    eligible.sort(key=lambda code: ("AI/ML" not in CATALOG[code].get("area", ""), code))
    selected = []
    total = 0
    for code in eligible:
        credits = CATALOG[code]["credits"]
        if total + credits <= 18:
            selected.append(code)
            total += credits
    if total < 12:
        return (
            f"CHƯA CÓ KẾ HOẠCH FULL-TIME HỢP LỆ: các môn đủ điều kiện hiện có là {', '.join(selected)} "
            f"({total} tín chỉ), thấp hơn mức 12 tín chỉ. Không tự bịa thêm môn ngoài catalog.\n"
            + (f"Môn chưa thể đưa vào kế hoạch: {'; '.join(blocked)}" if blocked else "")
        )
    return (
        f"Kế hoạch sơ bộ: {', '.join(selected)}\n"
        f"{check_schedule_conflicts(selected)}\n"
        f"{calculate_credit_load(student_id, selected)}\n"
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
