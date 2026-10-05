"""Stage 3: export / import a multi-cloud lab as JSON or YAML (IT-06, IT-07, IT-08)."""
import json
from dataclasses import asdict
from typing import List
import yaml
from .models import Network, Subnet


def to_dict(networks: List[Network]) -> dict:
    return {"version": 1, "networks": [asdict(n) for n in networks]}


def from_dict(data: dict) -> List[Network]:
    if not isinstance(data, dict) or data.get("version") != 1 or "networks" not in data:
        raise ValueError("Unsupported or malformed lab file")
    return [Network(n["name"], n["provider"], n["address_space"],
                    [Subnet(**s) for s in n.get("subnets", [])])
            for n in data["networks"]]


def export_lab(networks: List[Network], fmt: str = "json") -> str:
    data = to_dict(networks)
    if fmt == "json":
        return json.dumps(data, indent=2)
    if fmt == "yaml":
        return yaml.safe_dump(data, sort_keys=False)
    raise ValueError("fmt must be 'json' or 'yaml'")


def import_lab(text: str, fmt: str = "json") -> List[Network]:
    try:
        data = json.loads(text) if fmt == "json" else yaml.safe_load(text)
    except (json.JSONDecodeError, yaml.YAMLError) as e:
        raise ValueError(f"Cannot parse {fmt}: {e}")
    return from_dict(data)
