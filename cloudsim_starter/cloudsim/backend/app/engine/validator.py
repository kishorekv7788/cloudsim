"""Stage 2: generic lab checker. A lab lists 'checks'; each check calls one engine function."""
from .models import Network, Subnet
from .network import find_issues
from .routing import Route, can_reach
from .firewall import Rule, evaluate as fw_eval
from .iam import Statement, evaluate as iam_eval
from .compute import Instance


def state_from_dict(d: dict) -> dict:
    """Turn the JSON in a lab file (or a learner's canvas) into engine objects."""
    n = d["network"]
    return {
        "network": Network(n["name"], n["provider"], n["address_space"],
                           [Subnet(**s) for s in n.get("subnets", [])]),
        "routes": [Route(**r) for r in d.get("routes", [])],
        "rules": [Rule(**r) for r in d.get("rules", [])],
        "statements": [Statement(**s) for s in d.get("statements", [])],
        "instances": [Instance(**i) for i in d.get("instances", [])],
    }


def run_checks(state: dict, checks: list) -> list:
    """Return a list of failure messages. Empty list = lab passed."""
    failures = []
    for c in checks:
        t = c["type"]
        if t == "no_subnet_issues":
            failures += find_issues(state["network"])
        elif t == "can_reach":
            if not can_reach(state["routes"], c["dest_ip"]):
                failures.append(f"No usable route to {c['dest_ip']}")
        elif t == "firewall_allows":
            action, rule = fw_eval(state["rules"], c["direction"], c["protocol"],
                                   c["port"], c["src_ip"])
            if action != "allow":
                failures.append(f"Port {c['port']} from {c['src_ip']} is blocked by '{rule}'")
        elif t in ("iam_allows", "iam_denies"):
            allowed = iam_eval(state["statements"], c["action"], c["resource"]).allowed
            if allowed != (t == "iam_allows"):
                failures.append(f"{c['action']} on {c['resource']} should be "
                                f"{'allowed' if t == 'iam_allows' else 'denied'}")
        elif t == "min_running_instances":                       # Stage 4 (AZ-140 host pool)
            running = sum(1 for i in state.get("instances", []) if i.state == "running")
            if running < c["count"]:
                failures.append(f"Only {running} of {c['count']} required instances are running")
        else:
            raise ValueError(f"Unknown check type '{t}'")
    return failures
