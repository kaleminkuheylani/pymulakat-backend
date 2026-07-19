from services.achievements import (
    ACHIEVEMENTS,
    _ai_feedback_5,
    _category_n,
    _comeback,
    _first_perfect,
    _level_advanced_first_try,
    _level_n,
    _normalize_level,
    _persistent,
    _report_question,
    _share_first,
    evaluate,
)


def test_normalize_level():
    assert _normalize_level("başlangıç") == "beginner"
    assert _normalize_level("Beginner") == "beginner"
    assert _normalize_level("orta") == "intermediate"
    assert _normalize_level("ileri") == "advanced"
    assert _normalize_level("hard") == "advanced"
    assert _normalize_level("") == ""


def test_first_perfect_first_attempt_success():
    atts = [
        {
            "question_id": 1,
            "success": True,
            "passed_tests": 2,
            "total_tests": 2,
            "created_at": "2026-07-19T10:00:00",
        }
    ]
    assert _first_perfect(atts, []) is True


def test_first_perfect_fail_then_perfect_is_not_first_try():
    atts = [
        {
            "question_id": 1,
            "success": False,
            "passed_tests": 0,
            "total_tests": 2,
            "created_at": "2026-07-19T09:00:00",
        },
        {
            "question_id": 1,
            "success": True,
            "passed_tests": 2,
            "total_tests": 2,
            "created_at": "2026-07-19T10:00:00",
        },
    ]
    assert _first_perfect(atts, []) is False


def test_level_advanced_first_try_success_first():
    atts = [
        {
            "question_id": 2,
            "success": True,
            "level": "advanced",
            "created_at": "2026-07-19T10:00:00",
        }
    ]
    assert _level_advanced_first_try(atts, []) is True


def test_level_advanced_first_try_fail_then_success_is_not_first_try():
    atts = [
        {
            "question_id": 2,
            "success": False,
            "level": "advanced",
            "created_at": "2026-07-19T09:00:00",
        },
        {
            "question_id": 2,
            "success": True,
            "level": "advanced",
            "created_at": "2026-07-19T10:00:00",
        },
    ]
    assert _level_advanced_first_try(atts, []) is False


def test_comeback_seven_days_apart_success():
    atts = [
        {"success": True, "created_at": "2026-07-10T10:00:00"},
        {"success": True, "created_at": "2026-07-17T10:00:00"},
    ]
    assert _comeback(atts, []) is True


def test_comeback_failures_ignored():
    atts = [
        {"success": True, "created_at": "2026-07-10T10:00:00"},
        {"success": False, "created_at": "2026-07-20T10:00:00"},
    ]
    assert _comeback(atts, []) is False


def test_persistent_five_failures_before_success():
    qid = 10
    fails = [
        {
            "question_id": qid,
            "success": False,
            "created_at": f"2026-07-19T09:{i:02d}:00",
        }
        for i in range(5)
    ]
    success = [
        {
            "question_id": qid,
            "success": True,
            "created_at": "2026-07-19T10:00:00",
        }
    ]
    assert _persistent(fails + success, []) is True


def test_category_n_clamps_to_available_questions():
    atts = [
        {"question_id": 1, "success": True, "category": "x"},
        {"question_id": 2, "success": True, "category": "x"},
        {"question_id": 3, "success": True, "category": "x"},
    ]
    questions = [{"id": 1, "category": "x"}, {"id": 2, "category": "x"}]
    check = _category_n("x", 5)
    assert check(atts, questions, {}) is True  # 2 successes >= min(5, 2) = 2


def test_category_n_zero_questions_not_achievable():
    atts = [{"question_id": 1, "success": True, "category": "x"}]
    check = _category_n("x", 5)
    assert check(atts, [], {}) is False


def test_level_n_clamps_to_available_questions():
    atts = [{"question_id": 1, "success": True, "level": "advanced"}]
    questions = [{"id": 1, "level": "advanced"}]
    check = _level_n("advanced", 5)
    assert check(atts, questions, {}) is True  # 1 success >= min(5, 1) = 1


def test_context_achievements():
    assert _share_first([], [], {"shared": True}) is True
    assert _share_first([], [], {"shared": False}) is False
    assert _report_question([], [], {"reported": True}) is True
    assert _report_question([], [], {"reported": False}) is False
    assert _ai_feedback_5([], [], {"ai_feedback_count": 5}) is True
    assert _ai_feedback_5([], [], {"ai_feedback_count": 4}) is False


def test_evaluate_with_context():
    atts = []
    questions = []
    context = {"shared": True, "reported": True, "ai_feedback_count": 5}
    unlocked = evaluate(atts, questions, context)
    assert "share_first" in unlocked
    assert "report_question" in unlocked
    assert "ai_feedback_5" in unlocked
    assert all(a.id in unlocked for a in ACHIEVEMENTS if a.id in {"share_first", "report_question", "ai_feedback_5"})
