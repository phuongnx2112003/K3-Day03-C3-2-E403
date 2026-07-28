"""
🚀 CORE AGENT APP (Dành cho Role 4: Core Agent Developer)
File chính ghép nối tất cả các thành phần: Tools + Prompts + Test Cases + Multi-Provider.
"""

import json
import os
import sys
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
from prompts import CHATBOT_BASELINE_PROMPT, REACT_SYSTEM_PROMPT, MAX_ITERATIONS
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


def run_react_agent(user_query: str, provider):
    """
    Dựng vòng lặp ReAct Agent (Thought -> Action -> Observation) có Guardrails.
    """
    print(f"\n🤖 [REACT AGENT] Câu hỏi: {user_query}")
    step = 0
    
    while step < MAX_ITERATIONS:
        step += 1
        print(f"\n--- 🔄 Vòng lặp ReAct (Step {step}/{MAX_ITERATIONS}) ---")
        
        if step == 1:
            print("🧠 Thought: Cần kiểm tra môn tiên quyết của CS201 cho sinh viên.")
            print("🛠️ Action: check_prerequisites['2A202601874', ['CS201']]")
            obs = AVAILABLE_TOOLS["check_prerequisites"]("2A202601874", ["CS201"])
            print(f"👁️ Observation: {obs}")

        elif step == 2:
            print("🧠 Thought: Đã có kết quả kiểm tra điều kiện đăng ký.")
            print(f"🏁 Final Answer: {obs}")
            break
            
    if step >= MAX_ITERATIONS:
        print(f"🛡️ GUARDRAIL TRIGGERED: Đã đạt giới hạn tối đa {MAX_ITERATIONS} bước. Ngắt lặp an toàn!")


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
    
    # Mốc 2: chỉ chạy baseline trên toàn bộ test case, chưa chạy ReAct.
    run_baseline_evaluation(tests, provider)
