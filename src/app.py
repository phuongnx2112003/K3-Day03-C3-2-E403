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
from tools import AVAILABLE_TOOLS
from prompts import CHATBOT_BASELINE_PROMPT, REACT_SYSTEM_PROMPT, MAX_ITERATIONS, TIMEOUT_SECONDS
from providers import get_llm_provider

load_dotenv()

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
    """Parse Action: tool[args] bằng AST, không dùng eval không an toàn."""
    match = re.search(r"Action:\s*([A-Za-z_]\w*)\s*(\[.*\])", response, re.DOTALL)
    if not match:
        return None, None
    tool_name, args_text = match.group(1), match.group(2)[1:-1]
    try:
        call = ast.parse(f"f({args_text})", mode="eval").body
        if not isinstance(call, ast.Call) or call.keywords:
            raise ValueError("chỉ hỗ trợ positional arguments")
        args = [ast.literal_eval(argument) for argument in call.args]
        return tool_name, args
    except (SyntaxError, ValueError, TypeError) as exc:
        return None, f"LỖI [MALFORMED_ACTION]: {exc}"


def call_tool_with_timeout(tool_name: str, args: list):
    """Gọi tool đã đăng ký với timeout và không để exception làm crash agent."""
    tool = AVAILABLE_TOOLS.get(tool_name)
    if tool is None:
        return f"LỖI [UNKNOWN_TOOL]: '{tool_name}' không nằm trong AVAILABLE_TOOLS."

    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(tool, *args)
    try:
        return future.result(timeout=TIMEOUT_SECONDS)
    except TimeoutError:
        future.cancel()
        return f"LỖI [TOOL_TIMEOUT]: Tool '{tool_name}' vượt quá {TIMEOUT_SECONDS} giây."
    except Exception as exc:
        return f"LỖI [TOOL_EXCEPTION]: Tool '{tool_name}' thất bại: {exc}"
    finally:
        executor.shutdown(wait=False, cancel_futures=True)


def run_react_agent(user_query: str, provider):
    """Chạy ReAct động: LLM → Action → tool → Observation → LLM."""
    print(f"\n🤖 [REACT AGENT] Câu hỏi: {user_query}")
    conversation = f"User: {user_query}"
    trace = []

    for step in range(1, MAX_ITERATIONS + 1):
        print(f"\n--- 🔄 Vòng lặp ReAct (Step {step}/{MAX_ITERATIONS}) ---")
        response = provider.generate(conversation, system_prompt=REACT_SYSTEM_PROMPT)
        print(response)
        trace.append({"step": step, "assistant": response})

        if "Final Answer:" in response:
            answer = response.split("Final Answer:", 1)[1].strip()
            print(f"🏁 Final Answer: {answer}")
            return {"answer": answer, "trace": trace, "status": "completed"}

        tool_name, args = parse_action(response)
        if tool_name is None:
            observation = args or "LỖI [NO_ACTION]: Agent không sinh Action hợp lệ."
        else:
            print(f"🛠️ Action parsed: {tool_name}{args}")
            observation = call_tool_with_timeout(tool_name, args)
        print(f"👁️ Observation: {observation}")
        trace.append({"step": step, "observation": observation})
        conversation += f"\nAssistant: {response}\nObservation: {observation}"

    fallback = "Không thể hoàn tất tư vấn trong giới hạn số vòng lặp an toàn."
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
