import json
from pathlib import Path
import pytest
from app.engine.validator import state_from_dict, run_checks
from app.engine.routing import Route
from app.engine.firewall import Rule

LAB = Path(__file__).resolve().parents[2] / "labs" / "az104_lab07_web_unreachable.json"


def test_broken_lab_then_fixed():                  # UC-07 (routing + firewall challenge)
    lab = json.loads(LAB.read_text())
    state = state_from_dict(lab["broken_state"])
    assert len(run_checks(state, lab["goal_checks"])) == 2       # both problems found

    state["routes"][1] = Route("0.0.0.0/0", "internet")           # fix 1: default route
    state["rules"].append(Rule("allow-https", 90, "inbound", "tcp", 443, "*", "allow"))  # fix 2
    assert run_checks(state, lab["goal_checks"]) == []


def test_iam_checks():                             # IAM-04 (least privilege)
    state = state_from_dict({
        "network": {"name": "n", "provider": "azure", "address_space": "10.0.0.0/16"},
        "statements": [{"effect": "allow", "actions": ["*"], "resources": ["*"]}]})
    checks = [{"type": "iam_denies", "action": "storage:delete", "resource": "bucket/logs"}]
    assert len(run_checks(state, checks)) == 1                    # over-permissive: fails
    state["statements"][0].actions = ["storage:read"]             # learner applies least privilege
    assert run_checks(state, checks) == []


def test_unknown_check_type():
    state = state_from_dict({"network": {"name": "n", "provider": "azure",
                                         "address_space": "10.0.0.0/16"}})
    with pytest.raises(ValueError):
        run_checks(state, [{"type": "nope"}])


def test_min_running_instances_check():            # Stage 4 (AZ-140 style host pool)
    state = state_from_dict({
        "network": {"name": "n", "provider": "azure", "address_space": "10.0.0.0/16"},
        "instances": [{"name": "host1", "subnet": "s", "state": "running"},
                      {"name": "host2", "subnet": "s", "state": "stopped"}]})
    checks = [{"type": "min_running_instances", "count": 2}]
    assert run_checks(state, checks) == ["Only 1 of 2 required instances are running"]
    state["instances"][1].state = "running"
    assert run_checks(state, checks) == []


def test_host_pool_lab():                          # Stage 4 lab file
    lab = json.loads((LAB.parent / "az140_lab01_host_pool.json").read_text())
    state = state_from_dict(lab["broken_state"])
    assert len(run_checks(state, lab["goal_checks"])) == 1        # only 1 of 3 running
    for inst in state["instances"]:
        if inst.state == "stopped":
            inst.start()                                          # the learner's fix
    assert run_checks(state, lab["goal_checks"]) == []
