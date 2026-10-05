"""Final stage: simple badge rules based on progress numbers."""

BADGES = [
    ("First Lab", lambda p: p.get("labs_completed", 0) >= 1),
    ("Network Builder", lambda p: p.get("network_labs", 0) >= 3),
    ("Bug Hunter", lambda p: p.get("challenges_completed", 0) >= 3),
    ("Multi-Cloud Explorer", lambda p: p.get("providers_used", 0) >= 3),
    ("Quiz Master", lambda p: p.get("best_quiz_score", 0) >= 90),
]


def award_badges(progress: dict):
    return [name for name, rule in BADGES if rule(progress)]
