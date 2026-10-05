import ipaddress
from .models import Network, Subnet


class ValidationError(Exception):
    """Raised when a user action breaks a simulation rule."""


def parse_cidr(cidr):
    try:
        return ipaddress.ip_network(cidr, strict=True)
    except ValueError as e:
        raise ValidationError(f"Invalid CIDR '{cidr}': {e}")


def check_cidr_overlap(cidr1, cidr2):
    a, b = parse_cidr(cidr1), parse_cidr(cidr2)
    if a.version != b.version:
        return False
    return a.overlaps(b)


def subnet_within(network_cidr, subnet_cidr):
    net, sub = parse_cidr(network_cidr), parse_cidr(subnet_cidr)
    return net.version == sub.version and sub.subnet_of(net)


def add_subnet(network: Network, name: str, cidr: str) -> Subnet:
    """UT-01 / UT-04 / NET-01: validate, then add."""
    if any(s.name == name for s in network.subnets):
        raise ValidationError(f"Subnet name '{name}' already exists")
    if not subnet_within(network.address_space, cidr):
        raise ValidationError(
            f"Subnet {cidr} is not within address space {network.address_space}")
    for s in network.subnets:
        if check_cidr_overlap(s.cidr, cidr):
            raise ValidationError(f"Subnet {cidr} overlaps {s.name} ({s.cidr})")
    subnet = Subnet(name, cidr)
    network.subnets.append(subnet)
    return subnet


def check_peering(a: Network, b: Network):
    """IT-02: return a list of errors; empty list means peering is allowed."""
    if check_cidr_overlap(a.address_space, b.address_space):
        return [f"Address spaces overlap: {a.name} {a.address_space} "
                f"and {b.name} {b.address_space}"]
    return []


def find_issues(network: Network):
    """Used by challenge labs: list every problem in a network."""
    issues = []
    for i, s1 in enumerate(network.subnets):
        try:
            if not subnet_within(network.address_space, s1.cidr):
                issues.append(f"{s1.name} ({s1.cidr}) is outside {network.address_space}")
        except ValidationError as e:
            issues.append(str(e))
            continue
        for s2 in network.subnets[i + 1:]:
            try:
                if check_cidr_overlap(s1.cidr, s2.cidr):
                    issues.append(f"{s1.name} ({s1.cidr}) overlaps {s2.name} ({s2.cidr})")
            except ValidationError as e:
                issues.append(str(e))
    return issues
