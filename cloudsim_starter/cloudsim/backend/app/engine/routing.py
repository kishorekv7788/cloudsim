import ipaddress
from dataclasses import dataclass
from typing import List, Optional
from .network import ValidationError, parse_cidr, check_peering
from .models import Network


@dataclass
class Route:
    destination: str      # CIDR
    next_hop: str         # "local" | "internet" | "peering:<name>" | "appliance:<ip>" | "none"


def lookup(routes: List[Route], dest_ip: str) -> Optional[Route]:
    """UT-05 / UT-06: longest-prefix match. Returns None when nothing matches."""
    try:
        ip = ipaddress.ip_address(dest_ip)
    except ValueError:
        raise ValidationError(f"Invalid IP address '{dest_ip}'")
    best_net, best_route = None, None
    for r in routes:
        net = parse_cidr(r.destination)
        if net.version == ip.version and ip in net:
            if best_net is None or net.prefixlen > best_net.prefixlen:
                best_net, best_route = net, r
    return best_route


def can_reach(routes: List[Route], dest_ip: str) -> bool:
    r = lookup(routes, dest_ip)
    return r is not None and r.next_hop != "none"


def peer_networks(a: Network, b: Network, routes_a: List[Route], routes_b: List[Route]):
    """NET-03 / IT-01: refuse on overlap, otherwise add a route on BOTH sides."""
    errors = check_peering(a, b)
    if errors:
        return errors
    name = f"{a.name}-{b.name}"
    routes_a.append(Route(b.address_space, f"peering:{name}"))
    routes_b.append(Route(a.address_space, f"peering:{name}"))
    return []
