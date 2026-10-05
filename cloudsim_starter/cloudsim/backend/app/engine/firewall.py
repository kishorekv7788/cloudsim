import ipaddress
from dataclasses import dataclass
from typing import List, Optional, Tuple
from .network import ValidationError


@dataclass
class Rule:
    name: str
    priority: int                 # lower number = evaluated first (Azure NSG / GCP style)
    direction: str                # "inbound" | "outbound"
    protocol: str                 # "tcp" | "udp" | "icmp" | "*"
    port: Optional[int]           # None = any port
    source: str                   # CIDR or "*"
    action: str                   # "allow" | "deny"


def _matches(rule: Rule, direction, protocol, port, src_ip) -> bool:
    if rule.direction != direction:
        return False
    if rule.protocol not in ("*", protocol):
        return False
    if rule.port is not None and rule.port != port:
        return False
    if rule.source != "*":
        try:
            if ipaddress.ip_address(src_ip) not in ipaddress.ip_network(rule.source):
                return False
        except ValueError as e:
            raise ValidationError(str(e))
    return True


def evaluate(rules: List[Rule], direction, protocol, port, src_ip,
             default: str = "deny") -> Tuple[str, str]:
    """UT-13 / NET-02: first matching rule (by priority) wins.
    Returns (action, rule_name). Falls back to the provider default."""
    for rule in sorted(rules, key=lambda r: r.priority):
        if _matches(rule, direction, protocol, port, src_ip):
            return rule.action, rule.name
    return default, "default"
