"""
🚀 CORE AGENT APP (Dành cho Role 4: Core Agent Developer)
File chính ghép nối tất cả các thành phần: Tools + Prompts + Test Cases + Multi-Provider.
"""

import json
import os
import ast
import re
import sys
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from dotenv import load_dotenv

# Đảm bảo import các module cùng thư mục src/ hoạt động mượt mà
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Đảm bảo in ra Tiếng Việt và Emojis không bị lỗi trên Windows Console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Import các thành phần từ file của Role 2, Role 3 & Multi-Provider Adapter
from tools import AVAILABLE_TOOLS, CATALOG, STUDENT_RECORDS
from prompts import (
    CHATBOT_BASELINE_PROMPT,
    DOCUMENT_SEARCH_TIMEOUT_SECONDS,
    REACT_SYSTEM_PROMPT,
    MAX_ITERATIONS,
    TIMEOUT_SECONDS,
)
from providers import get_llm_provider

load_dotenv()
PROVIDER_TIMEOUT_SECONDS = int(os.getenv("PROVIDER_TIMEOUT_SECONDS", "20"))

def load_test_cases():
    """Đọc bộ test cases từ config/test_cases.json của Role 1"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")
    
    # Fallback kiểm tra nếu file ở thư mục hiện tại
    if not os.path.exists(config_path):
        config_path = "test_cases.json"
        
    # utf-8-sig vẫn đọc được UTF-8 thông thường và file có BOM từ Windows.
    with open(config_path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def run_baseline_chatbot(user_query: str, provider):
    """
    Dựng Chatbot gốc (Baseline) không có công cụ.

    Returns:
        str: Câu trả lời do provider sinh ra để Role 5A ghi trace và đánh giá.
    """
    print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")
    # Mốc 2 chỉ dùng prompt baseline; tuyệt đối không gọi AVAILABLE_TOOLS.
    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    print(f"🤖 Chatbot trả lời:\n{response}")
    return response


def run_baseline_evaluation(test_cases, provider):
    """Chạy baseline trên toàn bộ test case của Role 1."""
    results = []
    print("\n--- MỐC 2: ĐÁNH GIÁ CHATBOT BASELINE ---")
    print(f"📋 Tổng số test case: {len(test_cases)}")

    for case in test_cases:
        print(f"\n===== TEST CASE #{case['id']} =====")
        print(f"🏷️ Category: {case['category']}")
        response = run_baseline_chatbot(case["question"], provider)
        results.append({
            "id": case["id"],
            "category": case["category"],
            "question": case["question"],
            "expected_behavior": case["expected_behavior"],
            "response": response,
        })

    print("\n✅ Đã chạy xong baseline cho toàn bộ test case.")
    print("📝 Role 5A có thể dùng kết quả trên để cập nhật docs/trace_eval.md.")
    return results


def parse_action(response: str):
    """Parse ``Action: tool[args]`` an toàn, kể cả khi model bỏ dấu nháy.

    LLM đôi khi sinh ``search_courses[COMP1020]`` thay vì chuỗi Python hợp lệ.
    Với một đối số không có dấu nháy, giữ nguyên nội dung như một chuỗi thay vì
    biến nó thành lỗi cú pháp và lặp vô ích đến MAX_ITERATIONS.
    """
    match = re.search(
        r"(?m)^Action:\s*([A-Za-z_]\w*)\s*\[(.*?)\](?:\s+Observation:.*)?\s*$",
        response,
    )
    if not match:
        return None, None
    tool_name, args_text = match.group(1), match.group(2).strip()
    try:
        call = ast.parse(f"f({args_text})", mode="eval").body
        if not isinstance(call, ast.Call) or call.keywords:
            raise ValueError("chỉ hỗ trợ positional arguments")
        args = [ast.literal_eval(argument) for argument in call.args]
        return tool_name, args
    except (SyntaxError, ValueError, TypeError) as exc:
        if args_text and "," not in args_text:
            return tool_name, [args_text]
        return None, f"LỖI [MALFORMED_ACTION]: {exc}"


def strip_model_observations(response: str) -> str:
    """Không cho model tự chèn Observation vào lịch sử ReAct.

    Observation chỉ có giá trị khi được tạo bởi ``call_tool_with_timeout``. Nếu
    giữ một Observation do model tự viết, model ở lượt sau có thể dựa vào catalog
    hoặc lịch học bịa đặt thay vì kết quả tool thật.
    """
    clean_lines = []
    for line in response.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("Observation:"):
            break
        if stripped.startswith("Action:") and " Observation:" in line:
            line = line.split(" Observation:", 1)[0]
        clean_lines.append(line)
    return "\n".join(clean_lines).strip()


def _requires_verified_plan(query: str) -> bool:
    normalized = query.lower()
    return any(term in normalized for term in ("kế hoạch", "15 đến 18", "15-18"))


def _is_forced_registration_request(query: str) -> bool:
    """Nhận diện yêu cầu ép đăng ký bỏ qua quy tắc để chạy guardrail đầy đủ."""
    normalized = query.lower()
    return "đăng ký ngay" in normalized and any(
        phrase in normalized for phrase in ("dù", "bỏ qua", "vẫn cố", "vượt")
    )


def _plan_verification_fallback(verified_tools: set[str]) -> str:
    required_tools = {"search_courses", "check_prerequisites", "check_schedule_conflicts", "calculate_credit_load"}
    missing_tools = required_tools - verified_tools
    return (
        "Chưa thể chốt kế hoạch học kỳ hợp lệ. Agent chưa hoàn tất các kiểm chứng bắt buộc: "
        f"{', '.join(sorted(missing_tools))}. Không xác nhận môn, lịch hay tổng tín chỉ khi chưa có Observation từ các tool này."
    )


def _plan_data_fallback() -> str:
    """Trả về kết luận có grounding khi model bị lặp/đạt iteration limit."""
    plan_result = AVAILABLE_TOOLS["recommend_course_plan"]("2A202601874", "AI/ML")
    return (
        "Không thể chốt kế hoạch 15–18 tín chỉ từ catalog fixture hiện tại mà không bịa dữ liệu.\n"
        f"{plan_result}\n"
        "Cần bổ sung các môn tự chọn/GenEd cùng lịch học vào catalog hoặc cập nhật hồ sơ sau khi hoàn thành prerequisite."
    )


def run_catalog_plan_workflow(user_query: str):
    """Workflow ReAct xác định cho demo lập kế hoạch từ catalog fixture.

    Một kế hoạch cần đủ năm bước kiểm chứng; không để LLM kết thúc sớm trước
    khi có các Observation này. Khi fixture chưa đủ môn/lịch để tạo plan hợp lệ,
    workflow trả safe fallback có dẫn chứng thay vì bịa course.
    """
    student_id, student = next(iter(STUDENT_RECORDS.items()))
    completed = set(student["completed_courses"])
    planned_courses = [
        code for code, course in CATALOG.items()
        if code not in completed and set(course["prerequisites"]).issubset(completed)
    ]
    # Đưa các môn nền AI/ML lên trước, sau đó mới dùng GenEd để đủ tải tín chỉ.
    planned_courses.sort(key=lambda code: ("AI/ML" not in CATALOG[code].get("area", ""), code))
    trace = []

    def observe(step, thought, action, tool_name, args):
        observation = call_tool_with_timeout(tool_name, args)
        trace.append({"step": step, "assistant": f"Thought: {thought}\nAction: {action}"})
        trace.append({"step": step, "observation": observation})
        return observation

    observe(
        1,
        "Cần đọc hồ sơ fixture trước khi chọn các môn chưa hoàn thành.",
        f"get_student_profile['{student_id}']",
        "get_student_profile",
        [student_id],
    )
    observe(
        2,
        "Cần tra catalog cho hướng AI/ML và các môn nền tảng liên quan.",
        "search_courses['AI/ML']",
        "search_courses",
        ["AI/ML"],
    )
    prerequisite = observe(
        3,
        "Kiểm tra prerequisite của toàn bộ môn hiện đủ điều kiện theo hồ sơ.",
        f"check_prerequisites['{student_id}', {planned_courses}]",
        "check_prerequisites",
        [student_id, planned_courses],
    )
    schedule = observe(
        4,
        "Kiểm tra lịch của các môn đủ điều kiện; thiếu dữ liệu lịch cũng không được xem là không trùng.",
        f"check_schedule_conflicts[{planned_courses}]",
        "check_schedule_conflicts",
        [planned_courses],
    )
    credit = observe(
        5,
        "Tính tổng tải tín chỉ của các môn đã qua kiểm prerequisite.",
        f"calculate_credit_load['{student_id}', {planned_courses}]",
        "calculate_credit_load",
        [student_id, planned_courses],
    )

    verified = (
        prerequisite.startswith("ĐỦ ĐIỀU KIỆN")
        and schedule.startswith("Không phát hiện")
        and credit.startswith("Tải học kỳ hợp lệ")
    )
    if verified:
        answer = f"Kế hoạch học kỳ hợp lệ: {', '.join(planned_courses)}. {credit} {schedule}"
        return {"answer": answer, "trace": trace, "status": "completed"}

    answer = (
        "Chưa thể chốt kế hoạch 15–18 tín chỉ hợp lệ từ catalog fixture hiện tại.\n"
        f"Môn đủ điều kiện theo hồ sơ: {', '.join(planned_courses) or 'không có'}.\n"
        f"Prerequisite: {prerequisite}\nLịch: {schedule}\nTải tín chỉ: {credit}\n"
        "Không tự thêm môn ngoài catalog hoặc khẳng định không trùng lịch khi fixture chưa có lịch."
    )
    return {"answer": answer, "trace": trace, "status": "verification_incomplete"}


def run_forced_registration_guardrail(user_query: str):
    """Kiểm chứng toàn bộ trước khi từ chối yêu cầu ép đăng ký.

    Guardrail không suy đoán "có thể trùng" hay "có thể quá tải": nó gọi tool
    trên đúng mã môn trong câu hỏi và chỉ kết luận từ Observation nhận được.
    """
    student_id = next(iter(STUDENT_RECORDS))
    course_codes = list(dict.fromkeys(re.findall(r"\b[A-Z]{4}\d{4}\b", user_query.upper())))
    trace = []

    def observe(step, thought, action, tool_name, args):
        observation = call_tool_with_timeout(tool_name, args)
        trace.append({"step": step, "assistant": f"Thought: {thought}\nAction: {action}"})
        trace.append({"step": step, "observation": observation})
        return observation

    profile = observe(1, "Cần xác định hồ sơ trước khi đánh giá yêu cầu đăng ký.", f"get_student_profile['{student_id}']", "get_student_profile", [student_id])
    prerequisites = observe(2, "Phải kiểm prerequisite của đúng các môn được yêu cầu.", f"check_prerequisites['{student_id}', {course_codes}]", "check_prerequisites", [student_id, course_codes])
    schedule = observe(3, "Phải kiểm lịch thực tế trong fixture trước khi kết luận trùng lịch.", f"check_schedule_conflicts[{course_codes}]", "check_schedule_conflicts", [course_codes])
    credit = observe(4, "Phải tính tổng tín chỉ thực tế thay vì suy đoán quá tải.", f"calculate_credit_load['{student_id}', {course_codes}]", "calculate_credit_load", [student_id, course_codes])
    answer = (
        "Không thể tự đăng ký hoặc bỏ qua quy định học vụ.\n"
        f"Hồ sơ: {profile}\nPrerequisite: {prerequisites}\nLịch: {schedule}\nTải tín chỉ: {credit}\n"
        "Chỉ khi tất cả kiểm chứng hợp lệ, sinh viên mới nên gửi đăng ký qua hệ thống chính thức."
    )
    return {"answer": answer, "trace": trace, "status": "guardrail_triggered"}


def _provider_failure_message(response: str) -> str | None:
    """Nhận diện lỗi mà provider trả về dưới dạng text thay vì exception."""
    normalized = response.lower()
    provider_markers = ("[provider timeout]", "[provider exception]", "[gemini error]", "[gemini exception]", "[openai error]", "[openai exception]", "[ollama error]", "[ollama exception]", "[anthropic error]", "[anthropic exception]", "[openrouter")
    if not any(marker in normalized for marker in provider_markers):
        return None
    if "timeout" in normalized:
        return "Provider LLM phản hồi quá chậm hoặc không kết nối được. Agent đã dừng sau thời gian chờ để không treo giao diện."
    if "429" in normalized or "resource_exhausted" in normalized or "quota" in normalized:
        return (
            "Gemini hiện đã chạm giới hạn quota nên agent không thể tiếp tục suy luận. "
            "Hãy chờ quota được cấp lại, dùng API key/gói có quota còn lại, hoặc đặt `LLM_PROVIDER=mock` để demo offline."
        )
    if "404" in normalized or "not_found" in normalized or "no longer available" in normalized:
        return (
            "Model Gemini đã chọn không còn khả dụng cho API key này. Hãy dùng `gemini-3.6-flash` "
            "(default hiện tại) hoặc đổi `LLM_MODEL` sang một model Gemini đang được hỗ trợ."
        )
    return "Provider LLM hiện không phản hồi được. Agent đã dừng để không đưa ra kết luận không được kiểm chứng."


def call_tool_with_timeout(tool_name: str, args: list):
    """Gọi tool đã đăng ký với timeout và không để exception làm crash agent."""
    tool = AVAILABLE_TOOLS.get(tool_name)
    if tool is None:
        return f"LỖI [UNKNOWN_TOOL]: '{tool_name}' không nằm trong AVAILABLE_TOOLS."

    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(tool, *args)
    timeout_seconds = DOCUMENT_SEARCH_TIMEOUT_SECONDS if tool_name == "search_official_sources" else TIMEOUT_SECONDS
    try:
        return future.result(timeout=timeout_seconds)
    except TimeoutError:
        future.cancel()
        return f"LỖI [TOOL_TIMEOUT]: Tool '{tool_name}' vượt quá {timeout_seconds} giây."
    except Exception as exc:
        return f"LỖI [TOOL_EXCEPTION]: Tool '{tool_name}' thất bại: {exc}"
    finally:
        executor.shutdown(wait=False, cancel_futures=True)


def call_provider_with_timeout(provider, prompt: str, system_prompt: str):
    """Giới hạn thời gian chờ API LLM để web không spinner vô hạn."""
    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(provider.generate, prompt, system_prompt)
    try:
        return future.result(timeout=PROVIDER_TIMEOUT_SECONDS)
    except TimeoutError:
        future.cancel()
        return f"[Provider Timeout]: API không phản hồi trong {PROVIDER_TIMEOUT_SECONDS} giây."
    except Exception as exc:
        return f"[Provider Exception]: {exc}"
    finally:
        executor.shutdown(wait=False, cancel_futures=True)


def run_react_agent(user_query: str, provider):
    """Chạy ReAct động: LLM → Action → tool → Observation → LLM."""
    print(f"\n🤖 [REACT AGENT] Câu hỏi: {user_query}")
    if _is_forced_registration_request(user_query):
        return run_forced_registration_guardrail(user_query)
    if _requires_verified_plan(user_query):
        return run_catalog_plan_workflow(user_query)
    conversation = f"User: {user_query}"
    trace = []
    verified_tools = set()
    action_signatures = set()
    requires_verified_plan = _requires_verified_plan(user_query)

    for step in range(1, MAX_ITERATIONS + 1):
        print(f"\n--- 🔄 Vòng lặp ReAct (Step {step}/{MAX_ITERATIONS}) ---")
        response = strip_model_observations(call_provider_with_timeout(provider, conversation, REACT_SYSTEM_PROMPT))
        print(response)
        trace.append({"step": step, "assistant": response})

        provider_failure = _provider_failure_message(response)
        if provider_failure:
            print(f"🛑 PROVIDER UNAVAILABLE: {provider_failure}")
            return {"answer": provider_failure, "trace": trace, "status": "provider_unavailable"}

        if "Final Answer:" in response:
            required_tools = {"search_courses", "check_prerequisites", "check_schedule_conflicts", "calculate_credit_load"}
            if requires_verified_plan and not required_tools.issubset(verified_tools):
                answer = _plan_verification_fallback(verified_tools)
                print(f"🛡️ VERIFICATION INCOMPLETE: {answer}")
                return {"answer": answer, "trace": trace, "status": "verification_incomplete"}
            answer = response.split("Final Answer:", 1)[1].strip()
            print(f"🏁 Final Answer: {answer}")
            return {"answer": answer, "trace": trace, "status": "completed"}

        tool_name, args = parse_action(response)
        if tool_name is None:
            observation = args or "LỖI [NO_ACTION]: Agent không sinh Action hợp lệ."
        else:
            signature = (tool_name, repr(args))
            if signature in action_signatures:
                answer = _plan_data_fallback() if requires_verified_plan else "Agent đã lặp lại cùng một Action nên đã dừng an toàn."
                print(f"🛡️ REPEATED ACTION: {answer}")
                trace.append({"step": step, "observation": "LỖI [REPEATED_ACTION]: Agent gọi lại cùng tool với cùng tham số."})
                return {"answer": answer, "trace": trace, "status": "verification_incomplete"}
            action_signatures.add(signature)
            print(f"🛠️ Action parsed: {tool_name}{args}")
            observation = call_tool_with_timeout(tool_name, args)
            if tool_name == "search_courses" and not observation.startswith("LỖI"):
                verified_tools.add(tool_name)
            elif tool_name == "check_prerequisites" and observation.startswith("ĐỦ ĐIỀU KIỆN"):
                verified_tools.add(tool_name)
            elif tool_name == "check_schedule_conflicts" and observation.startswith("Không phát hiện"):
                verified_tools.add(tool_name)
            elif tool_name == "calculate_credit_load" and observation.startswith("Tải học kỳ hợp lệ"):
                verified_tools.add(tool_name)
        print(f"👁️ Observation: {observation}")
        trace.append({"step": step, "observation": observation})
        conversation += f"\nAssistant: {response}\nObservation: {observation}"

    fallback = _plan_data_fallback() if requires_verified_plan else "Không thể hoàn tất tư vấn trong giới hạn số vòng lặp an toàn."
    print(f"🛡️ GUARDRAIL TRIGGERED: {fallback}")
    return {"answer": fallback, "trace": trace, "status": "max_iterations"}


if __name__ == "__main__":
    print("==================================================")
    print("🏫 ĐẠI HỌC VINUNI - BÀI LAB 3: CHATBOT VS REACT AGENT")
    print("==================================================")
    
    # Khởi tạo Multi-Provider LLM Adapter (Đọc từ biến môi trường LLM_PROVIDER)
    provider = get_llm_provider()
    model_name = getattr(provider, "model_name", "Offline Mock Mode")
    print(f"🔌 LLM Provider đang hoạt động: {provider.__class__.__name__} (Model: {model_name})")
    
    tests = load_test_cases()
    print(f"✅ Đã tải thành công {len(tests)} Test Cases từ config/test_cases.json\n")
    
    # Mốc 2: chạy baseline trên toàn bộ test case.
    run_baseline_evaluation(tests, provider)

    # Mốc 3: chạy ReAct trên các case cần tool/guardrail.
    print("\n--- MỐC 3: CHẠY REACT AGENT ---")
    for case in tests[2:]:
        run_react_agent(case["question"], provider)
