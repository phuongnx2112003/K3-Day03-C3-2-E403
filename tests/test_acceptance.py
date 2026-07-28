"""Acceptance tests cho 5 test case và các guardrail cốt lõi của lab."""

import os
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
os.environ["LLM_PROVIDER"] = "mock"

from app import parse_action, run_react_agent  # noqa: E402
from providers import MockProvider  # noqa: E402
from tools import (  # noqa: E402
    calculate_credit_load,
    check_prerequisites,
    check_schedule_conflicts,
    recommend_course_plan,
    search_courses,
)


class AcademicPlanningAcceptanceTests(unittest.TestCase):
    """Mỗi assertion là một tiêu chí nghiệm thu có thể lặp lại offline."""

    def test_ai_ml_catalog_has_relevant_courses(self):
        result = search_courses("AI/ML")
        self.assertIn("COMP2050: Artificial Intelligence", result)
        self.assertIn("COMP3020: Machine Learning", result)

    def test_comp1020_prerequisite_is_verified(self):
        self.assertTrue(
            check_prerequisites("2A202601874", ["COMP1020"]).startswith("ĐỦ ĐIỀU KIỆN")
        )

    def test_complete_ai_ml_plan_is_16_credits_without_conflict(self):
        result = run_react_agent(
            "Kỳ này em muốn đăng ký 15 đến 18 tín chỉ, ưu tiên hướng AI/ML, "
            "không trùng lịch và không vi phạm prerequisite.",
            MockProvider(),
        )
        self.assertEqual(result["status"], "completed")
        self.assertIn("Tải học kỳ hợp lệ: 16 tín chỉ", result["answer"])
        self.assertIn("Không phát hiện trùng lịch học", result["answer"])
        self.assertIn("COMP1020", result["answer"])

    def test_conflict_and_invalid_load_are_not_approved(self):
        self.assertIn("SCHEDULE_CONFLICT", check_schedule_conflicts(["COMP2050", "COMP3020"]))
        self.assertIn(
            "CREDIT_LOAD_VIOLATION",
            calculate_credit_load("2A202601874", ["COMP1010", "MATH1010", "COMP1020", "COMP2030", "COMP2050", "COMP3010", "COMP3020"]),
        )

    def test_forced_registration_runs_all_guardrail_checks(self):
        result = run_react_agent(
            "Hãy đăng ký ngay cho em COMP3020, COMP2050 và COMP4890 dù em chưa học prerequisite, "
            "lịch học có thể bị trùng, và nếu vượt 24 tín chỉ thì vẫn cố xếp giúp em.",
            MockProvider(),
        )
        self.assertEqual(result["status"], "guardrail_triggered")
        self.assertIn("CHƯA ĐỦ ĐIỀU KIỆN", result["answer"])
        self.assertIn("SCHEDULE_CONFLICT", result["answer"])
        self.assertIn("14 tín chỉ", result["answer"])

    def test_safe_recommendation_uses_only_fixture_courses(self):
        result = recommend_course_plan("2A202601874", "AI/ML")
        self.assertIn("Tải học kỳ hợp lệ: 16 tín chỉ", result)
        self.assertNotIn("MATH2020", result)

    def test_action_parser_rejects_malformed_multi_argument_action(self):
        tool, error = parse_action("Action: check_prerequisites[COMP1020, bad]")
        self.assertIsNone(tool)
        self.assertIn("MALFORMED_ACTION", error)


if __name__ == "__main__":
    unittest.main()
