"""Flask UI cho trợ lý học vụ.

API trong file này chỉ chuyển đổi dữ liệu sang giao diện; mọi suy luận và dữ liệu
học vụ đều dùng lại các hàm ReAct/tool registry chính thức trong ``src``.
"""

import os
import sys

from flask import Flask, jsonify, render_template, request

SRC_DIR = os.path.dirname(os.path.abspath(__file__))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from app import load_test_cases, run_baseline_chatbot, run_react_agent
from providers import get_llm_provider
from tools import CATALOG, COURSE_SCHEDULES, STUDENT_RECORDS

app = Flask(__name__, template_folder="../templates", static_folder="../static")


def _trace_to_steps(trace):
    """Chuyển trace ReAct thành cấu trúc mà frontend hiển thị được."""
    steps = []
    pending = {}
    for item in trace:
        step = item["step"]
        if "assistant" in item:
            pending[step] = item["assistant"]
        elif "observation" in item:
            response = pending.get(step, "")
            thought = response.split("Thought:", 1)[-1].split("Action:", 1)[0].strip()
            action = response.split("Action:", 1)[-1].strip() if "Action:" in response else "Không có action"
            steps.append({
                "step": step,
                "thought": thought or "Agent đang đánh giá yêu cầu.",
                "action": action,
                "observation": item["observation"],
            })
    return steps


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/test-cases")
def get_test_cases():
    return jsonify({"status": "success", "data": load_test_cases()})


@app.get("/api/student-profile")
def get_profile_api():
    student_id, record = next(iter(STUDENT_RECORDS.items()))
    return jsonify({
        "status": "success",
        "data": {
            "id": student_id,
            "name": record["name"],
            "completed_courses": record["completed_courses"],
        },
    })


@app.get("/api/catalog")
def get_catalog_api():
    courses = [
        {
            "code": code,
            "name": details["name"],
            "credits": details["credits"],
            "prerequisites": details["prerequisites"],
            "schedule": COURSE_SCHEDULES.get(code, "Chưa có lịch fixture"),
        }
        for code, details in CATALOG.items()
    ]
    return jsonify({"status": "success", "data": courses})


@app.get("/api/status")
def get_status_api():
    provider = get_llm_provider()
    return jsonify({
        "status": "success",
        "provider": provider.__class__.__name__.removesuffix("Provider"),
        "model": getattr(provider, "model_name", "Offline Mock Mode"),
    })


@app.post("/api/chat")
def chat():
    data = request.get_json(silent=True) or {}
    query = str(data.get("query", "")).strip()
    mode = data.get("mode", "react")
    provider_name = data.get("provider")
    if not query:
        return jsonify({"status": "error", "message": "Vui lòng nhập câu hỏi."}), 400
    if mode not in {"baseline", "react"}:
        return jsonify({"status": "error", "message": "Chế độ không hợp lệ."}), 400

    provider = get_llm_provider(provider_name)
    if mode == "baseline":
        return jsonify({
            "status": "success",
            "mode": mode,
            "steps": [],
            "final_answer": run_baseline_chatbot(query, provider),
            "guardrail_triggered": False,
        })

    # UI hiện chỉ hiển thị fixture một sinh viên; cung cấp rõ ngữ cảnh này để
    # provider có thể gọi tool hồ sơ thay vì hỏi lại ID đã có trên màn hình.
    student_id = next(iter(STUDENT_RECORDS))
    agent_query = f"{query}\n\nNgữ cảnh UI fixture: student_id hiện tại là {student_id}."
    result = run_react_agent(agent_query, provider)
    return jsonify({
        "status": "success",
        "mode": mode,
        "steps": _trace_to_steps(result["trace"]),
        "final_answer": result["answer"],
        "guardrail_triggered": False,
        "agent_status": result["status"],
    })


if __name__ == "__main__":
    app.run(debug=True)
