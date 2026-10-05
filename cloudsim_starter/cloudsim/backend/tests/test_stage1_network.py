import json
from pathlib import Path
import pytest
from app.engine.models import Network, Subnet
from app.engine.network import (ValidationError, check_cidr_overlap, subnet_within,
                                add_subnet, find_issues)

LAB = Path(__file__).resolve().parents[2] / "labs" / "az900_lab02_fix_subnet_overlap.json"


def test_overlap_detected():                       # UT-01
    assert check_cidr_overlap("10.0.1.0/24", "10.0.1.0/25") is True


def test_no_overlap():                             # UT-02
    assert check_cidr_overlap("10.0.1.0/24", "10.0.2.0/24") is False


@pytest.mark.parametrize("bad", ["10.0.0.0/33", "300.1.1.1/24", "", "10.0.0.5/24"])
def test_invalid_cidr_rejected(bad):               # UT-03
    with pytest.raises(ValidationError):
        check_cidr_overlap(bad, "10.0.0.0/24")


def test_subnet_outside_network():                 # UT-04
    assert subnet_within("10.0.0.0/16", "192.168.1.0/24") is False
    assert subnet_within("10.0.0.0/16", "10.0.5.0/24") is True


def test_add_subnet_overlap_error_message():       # NET-01
    net = Network("vnet1", "azure", "10.0.0.0/16")
    add_subnet(net, "web", "10.0.1.0/24")
    with pytest.raises(ValidationError) as e:
        add_subnet(net, "app", "10.0.1.0/25")
    assert "overlaps web" in str(e.value)


def test_add_subnet_outside_range():
    net = Network("vnet1", "azure", "10.0.0.0/16")
    with pytest.raises(ValidationError):
        add_subnet(net, "x", "192.168.0.0/24")


def test_challenge_lab_broken_then_fixed():        # UC-07 (challenge)
    lab = json.loads(LAB.read_text())
    s = lab["broken_state"]
    net = Network(s["name"], s["provider"], s["address_space"],
                  [Subnet(**x) for x in s["subnets"]])
    assert len(find_issues(net)) == 1              # broken: one overlap
    net.subnets[1].cidr = "10.0.2.0/24"            # the learner's fix
    assert len(find_issues(net)) <= lab["goal_spec"]["max_issues"]


def test_quiz_scoring():                           # UC-02 / IT-10
    from app.quiz import score_quiz
    quiz = {"id": "az900-q1", "questions": [
        {"q": "What does IaaS stand for?", "options": ["A", "B"], "answer": 0},
        {"q": "Who owns the physical datacenter in public cloud?", "options": ["A", "B"], "answer": 1}]}
    assert score_quiz(quiz, [0, 1]) == {"correct": 2, "total": 2, "percent": 100}
    assert score_quiz(quiz, [0, 0])["percent"] == 50
    with pytest.raises(ValueError):
        score_quiz(quiz, [0])


def test_content_files_are_valid():                # Stage 1 content
    from app.quiz import score_quiz
    root = Path(__file__).resolve().parents[2] / "content"
    quiz = json.loads((root / "quizzes" / "az900-q1.json").read_text())
    assert score_quiz(quiz, [0, 0, 1])["percent"] == 100
    lessons = json.loads((root / "az-900" / "lessons.json").read_text())
    assert [l["id"] for l in lessons] == [1, 2, 3]
    assert json.loads((root / "modules.json").read_text())[0]["code"] == "AZ-900"
