from dataclasses import dataclass
from fnmatch import fnmatchcase
from typing import Dict, List


@dataclass
class Statement:
    effect: str                   # "allow" | "deny"
    actions: List[str]            # e.g. "storage:read", "storage:*", "*"
    resources: List[str]          # e.g. "bucket/logs", "bucket/*", "*"


@dataclass
class Decision:
    allowed: bool
    reason: str


def _any_match(patterns, value):
    return any(fnmatchcase(value, p) for p in patterns)


def evaluate(statements: List[Statement], action: str, resource: str) -> Decision:
    """UT-07/08/09: explicit deny beats allow; no match means implicit deny."""
    allowed = False
    for s in statements:
        if _any_match(s.actions, action) and _any_match(s.resources, resource):
            if s.effect == "deny":
                return Decision(False, "explicit deny")
            allowed = True
    return Decision(allowed, "allow" if allowed else "implicit deny")


def find_conflicts(policies: Dict[str, List[Statement]]):
    """IAM-03: the same action+resource allowed in one cloud but denied in another."""
    conflicts = []
    clouds = list(policies)
    for i, c1 in enumerate(clouds):
        for c2 in clouds[i + 1:]:
            for s1 in policies[c1]:
                for s2 in policies[c2]:
                    if s1.effect == s2.effect:
                        continue
                    shared_actions = set(s1.actions) & set(s2.actions)
                    shared_res = set(s1.resources) & set(s2.resources)
                    for a in sorted(shared_actions):
                        for r in sorted(shared_res):
                            allow_cloud = c1 if s1.effect == "allow" else c2
                            deny_cloud = c2 if s1.effect == "allow" else c1
                            conflicts.append(
                                f"{a} on {r}: allowed in {allow_cloud}, denied in {deny_cloud}")
    return conflicts
