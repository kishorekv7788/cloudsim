from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List
from .models import Network
from .network import ValidationError

TRANSITIONS = {
    "creating": {"running"},
    "running": {"stopped", "deleted"},
    "stopped": {"running", "deleted"},
    "deleted": set(),
}


@dataclass
class Instance:
    name: str
    subnet: str
    state: str = "creating"
    log: List[str] = field(default_factory=list)

    def _log(self, message):
        self.log.append(f"{datetime.now(timezone.utc).isoformat()} {self.name}: {message}")

    def _move(self, new_state):
        if new_state not in TRANSITIONS[self.state]:
            raise ValidationError(f"Cannot go from '{self.state}' to '{new_state}'")
        self._log(f"{self.state} -> {new_state}")
        self.state = new_state

    def start(self):
        self._move("running")

    def stop(self):
        self._move("stopped")

    def delete(self):
        self._move("deleted")


def create_instance(network: Network, name: str, subnet_name: str) -> Instance:
    """UT-10 / UT-11 / CMP-01: needs a valid subnet; ends in state 'running'."""
    if not any(s.name == subnet_name for s in network.subnets):
        raise ValidationError(f"Subnet '{subnet_name}' not found in {network.name}")
    inst = Instance(name, subnet_name)
    inst._log("created")
    inst._move("running")
    return inst
