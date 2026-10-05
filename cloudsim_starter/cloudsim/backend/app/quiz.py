"""Stage 1: score a quiz. Quiz JSON: {"id", "questions": [{"q", "options", "answer": index}]}"""


def score_quiz(quiz: dict, answers: list) -> dict:
    questions = quiz["questions"]
    if len(answers) != len(questions):
        raise ValueError("Number of answers does not match number of questions")
    correct = sum(1 for q, a in zip(questions, answers) if a == q["answer"])
    return {"correct": correct, "total": len(questions),
            "percent": round(100 * correct / len(questions)) if questions else 0}
