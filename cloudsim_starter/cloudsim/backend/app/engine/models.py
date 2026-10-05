from dataclasses import dataclass, field
from typing import List


@dataclass
class Subnet:
    name: str
    cidr: str


@dataclass
class Network:
    name: str
    provider: str            # "azure" | "aws" | "gcp"
    address_space: str       # e.g. "10.0.0.0/16"
    subnets: List[Subnet] = field(default_factory=list)
