"""
Test verification script for BIS Quiz Application
Verifies:
1. Question bank integrity (at least 30 questions, proper formatting)
2. Grading logic and speed bonus calculation
3. Flask app routes and JSON APIs
4. Automatic CSV export generation
"""

import sys
import os
import json

from questions import BIS_QUESTIONS, get_quiz_questions, grade_answers
from app import app, export_csv, generate_host_summary

def run_tests():
    print(">>> 1. Verifying Question Bank...")
    assert len(BIS_QUESTIONS) >= 30, f"Expected at least 30 questions, got {len(BIS_QUESTIONS)}"
    for idx, q in enumerate(BIS_QUESTIONS):
        assert "id" in q, f"Question {idx} missing id"
        assert "question" in q and len(q["question"]) > 5, f"Question {idx} has invalid text"
        assert len(q["options"]) == 4, f"Question {idx} must have 4 options"
        assert 0 <= q["answer"] <= 3, f"Question {idx} answer index out of bounds"
    print(f"[OK] All {len(BIS_QUESTIONS)} BIS questions validated successfully!")

    print("\n>>> 2. Verifying Quiz Generator...")
    sanitized, q_ids = get_quiz_questions(30)
    assert len(sanitized) == 30, f"Expected 30 questions, got {len(sanitized)}"
    assert len(q_ids) == 30, f"Expected 30 IDs, got {len(q_ids)}"
    for q in sanitized:
        assert "answer" not in q, "Security error: Answer key leaked to participant!"
    print("[OK] Quiz sanitization and randomization working cleanly without leaking answers!")

    print("\n>>> 3. Verifying Scoring & Speed Bonus...")
    # Test perfect score in fast time (e.g. 600s / 10 mins)
    fast_answers = {str(q_id): next(item["answer"] for item in BIS_QUESTIONS if item["id"] == q_id) for q_id in q_ids}
    result_fast = grade_answers(q_ids, fast_answers, time_spent_seconds=600, max_time_seconds=1200)
    
    # Test perfect score in slow time (e.g. 1100s / 18 mins 20s)
    result_slow = grade_answers(q_ids, fast_answers, time_spent_seconds=1100, max_time_seconds=1200)
    
    print(f"Fast student (10 min): Correct={result_fast['correct_count']}/30, Base={result_fast['base_points']}, Speed Bonus={result_fast['speed_bonus']}, Total={result_fast['total_points']}")
    print(f"Slow student (18.3 min): Correct={result_slow['correct_count']}/30, Base={result_slow['base_points']}, Speed Bonus={result_slow['speed_bonus']}, Total={result_slow['total_points']}")
    
    assert result_fast["total_points"] > result_slow["total_points"], "Faster student must get more points!"
    assert result_fast["speed_bonus"] > result_slow["speed_bonus"], "Speed bonus for faster student must be higher!"
    print("[OK] Speed bonus logic verified: Faster students accurately awarded extra points!")

    print("\n>>> 4. Verifying Flask API Endpoints...")
    client = app.test_client()
    
    # Check landing page
    res = client.get("/")
    assert res.status_code == 200, f"Expected 200 on /, got {res.status_code}"

    # Check registration
    reg_payload = {
        "name": "Aarav Sharma",
        "phone": "9876543210",
        "college_id": "COLLEGE-2026-001"
    }
    res_reg = client.post("/api/register", json=reg_payload)
    assert res_reg.status_code == 200, f"Registration failed: {res_reg.data}"
    reg_data = json.loads(res_reg.data)
    participant_id = reg_data["participant_id"]
    print(f"[OK] Registered participant: {participant_id}")

    # Check quiz questions delivery
    res_q = client.get(f"/api/quiz-data/{participant_id}")
    assert res_q.status_code == 200
    q_data = json.loads(res_q.data)
    assert len(q_data["questions"]) == 30
    print("[OK] Received 30 quiz questions via API")

    # Map correct answers for this participant's specific questions
    part_q_ids = [q["id"] for q in q_data["questions"]]
    part_answers = {str(q_id): next(item["answer"] for item in BIS_QUESTIONS if item["id"] == q_id) for q_id in part_q_ids}

    # Check exam submission
    submit_payload = {
        "participant_id": participant_id,
        "answers": part_answers,
        "time_spent_seconds": 450
    }
    res_sub = client.post("/api/submit-quiz", json=submit_payload)
    assert res_sub.status_code == 200
    sub_data = json.loads(res_sub.data)
    assert sub_data["result"]["correct_count"] == 30
    print(f"[OK] Submitted exam: Score={sub_data['result']['total_points']} pts, Time={sub_data['result']['time_taken']}")

    # Check Leaderboard API
    res_lb = client.get("/api/leaderboard")
    assert res_lb.status_code == 200
    lb_data = json.loads(res_lb.data)
    assert lb_data["total_completed"] >= 1
    assert lb_data["leaderboard"][0]["name"] == "Aarav Sharma"
    print("[OK] Leaderboard API verified with rank 1 participant!")

    # Check Host Data API
    res_host = client.get("/api/host-data")
    assert res_host.status_code == 200
    host_data = json.loads(res_host.data)
    assert host_data["stats"]["total_completed"] >= 1
    print("[OK] Host Data API verified!")

    # Check CSV export endpoint
    res_csv = client.get("/api/export-csv")
    assert res_csv.status_code == 200
    assert "Aarav Sharma" in res_csv.data.decode("utf-8")
    assert "COLLEGE-2026-001" in res_csv.data.decode("utf-8")
    print("[OK] CSV export contains complete participant data!")

    print("\n==========================================")
    print(" ALL TESTS PASSED SUCCESSFULLY! ")
    print("==========================================")

if __name__ == "__main__":
    run_tests()
