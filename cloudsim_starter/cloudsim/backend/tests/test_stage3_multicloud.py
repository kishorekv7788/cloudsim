import json
import yaml
import pytest
from app.engine.models import Network
from app.engine.network import add_subnet
from app.engine.routing import peer_networks, can_reach
from app.engine.iam import Statement, find_conflicts
from app.engine.topology import export_lab, import_lab
from app.engine.adapters import ADAPTERS


def _pair(cidr_b="10.1.0.0/16"):
    return (Network("azure-vnet", "azure", "10.0.0.0/16"),
            Network("aws-vpc", "aws", cidr_b))


def test_azure_aws_connectivity():                 # IT-01 / NET-03
    a, b = _pair()
    ra, rb = [], []
    assert peer_networks(a, b, ra, rb) == []
    assert can_reach(ra, "10.1.4.4") and can_reach(rb, "10.0.4.4")


def test_overlapping_cidr_refused():               # IT-02
    a, b = _pair(cidr_b="10.0.0.0/16")
    ra, rb = [], []
    errors = peer_networks(a, b, ra, rb)
    assert errors and "overlap" in errors[0] and ra == [] and rb == []


def test_missing_return_route():                   # IT-03
    a, b = _pair()
    ra, rb = [], []
    peer_networks(a, b, ra, rb)
    rb.clear()
    assert can_reach(ra, "10.1.4.4") is True
    assert can_reach(rb, "10.0.4.4") is False      # reply cannot return


def test_multicloud_role_conflict():               # IAM-03
    policies = {
        "azure": [Statement("allow", ["storage:read"], ["data/reports"])],
        "aws": [Statement("deny", ["storage:read"], ["data/reports"])],
    }
    conflicts = find_conflicts(policies)
    assert conflicts == ["storage:read on data/reports: allowed in azure, denied in aws"]


def test_export_import_roundtrip_json_and_yaml():  # IT-06 / IT-07 / IT-08
    a, b = _pair()
    add_subnet(a, "web", "10.0.1.0/24")
    add_subnet(b, "app", "10.1.1.0/24")
    for fmt in ("json", "yaml"):
        text = export_lab([a, b], fmt)
        assert import_lab(text, fmt) == [a, b]
    assert json.loads(export_lab([a, b], "json")) == yaml.safe_load(export_lab([a, b], "yaml"))


def test_import_rejects_bad_file():                # SP-02
    with pytest.raises(ValueError):
        import_lab('{"version": 99}', "json")


def test_adapters_use_provider_words():
    assert "VPC" in ADAPTERS["aws"].NAMES["network"]
    assert "VNet" in ADAPTERS["azure"].NAMES["network"]
    assert ADAPTERS["aws"].FIREWALL_USES_PRIORITY is False


def test_import_rejects_bad_yaml_and_wrong_shape():
    with pytest.raises(ValueError):
        import_lab("a: [unclosed", "yaml")
    with pytest.raises(ValueError):
        import_lab("just a string", "yaml")


def test_aws_security_group_rejects_deny_rule():
    from app.engine.firewall import Rule
    from app.engine.network import ValidationError
    deny = Rule("d", 1, "inbound", "tcp", 22, "*", "deny")
    allow = Rule("a", 1, "inbound", "tcp", 22, "*", "allow")
    with pytest.raises(ValidationError):
        ADAPTERS["aws"].validate_rule(deny)
    assert ADAPTERS["aws"].validate_rule(allow) is None
    assert ADAPTERS["azure"].validate_rule(deny) is None
    assert ADAPTERS["gcp"].validate_rule(deny) is None
