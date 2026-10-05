from app.engine.gamification import award_badges


def test_badges():
    assert award_badges({}) == []
    got = award_badges({"labs_completed": 1, "providers_used": 3, "best_quiz_score": 95})
    assert got == ["First Lab", "Multi-Cloud Explorer", "Quiz Master"]
