import pytest
from app.engine.models import Network
from app.engine.network import ValidationError, add_subnet
from app.engine.routing import Route, lookup, can_reach
from app.engine.firewall import Rule, evaluate
from app.engine.iam import Statement, evaluate as iam_eval
from app.engine.compute import create_instance
from app.engine.storage import Bucket, upload, anonymous_read_allowed


def test_longest_prefix_match():                   # UT-05
    routes = [Route("10.0.0.0/16", "local"), Route("10.0.1.0/24", "appliance:10.0.9.4")]
    assert lookup(routes, "10.0.1.5").next_hop == "appliance:10.0.9.4"
    assert lookup(routes, "10.0.2.5").next_hop == "local"


def test_no_matching_route():                      # UT-06
    assert lookup([Route("10.0.0.0/16", "local")], "8.8.8.8") is None
    assert can_reach([Route("10.0.0.0/16", "local")], "8.8.8.8") is False


def test_firewall_priority_and_default():          # UT-13 / NET-02
    rules = [Rule("allow-ssh", 200, "inbound", "tcp", 22, "*", "allow"),
             Rule("deny-ssh", 100, "inbound", "tcp", 22, "*", "deny")]
    assert evaluate(rules, "inbound", "tcp", 22, "1.2.3.4") == ("deny", "deny-ssh")
    assert evaluate(rules, "inbound", "tcp", 443, "1.2.3.4") == ("deny", "default")


def test_firewall_source_cidr():
    rules = [Rule("office", 100, "inbound", "tcp", 443, "203.0.113.0/24", "allow")]
    assert evaluate(rules, "inbound", "tcp", 443, "203.0.113.7")[0] == "allow"
    assert evaluate(rules, "inbound", "tcp", 443, "198.51.100.7")[0] == "deny"


def test_iam_allow_deny_implicit():                # UT-07 / UT-08 / UT-09
    allow = Statement("allow", ["storage:read"], ["bucket/*"])
    deny = Statement("deny", ["storage:read"], ["bucket/secret"])
    assert iam_eval([allow], "storage:read", "bucket/logs").allowed is True
    d = iam_eval([allow, deny], "storage:read", "bucket/secret")
    assert d.allowed is False and d.reason == "explicit deny"
    d = iam_eval([], "storage:read", "bucket/logs")
    assert d.allowed is False and d.reason == "implicit deny"


def test_instance_lifecycle_and_log():             # UT-10 / UT-12 / CMP-01 / CMP-02
    net = Network("vnet", "azure", "10.0.0.0/16")
    add_subnet(net, "web", "10.0.1.0/24")
    vm = create_instance(net, "vm1", "web")
    assert vm.state == "running"
    vm.stop(); vm.start()
    assert vm.state == "running" and len(vm.log) == 4


def test_instance_needs_subnet():                  # UT-11
    with pytest.raises(ValidationError):
        create_instance(Network("vnet", "azure", "10.0.0.0/16"), "vm1", "missing")


def test_stop_twice_is_error():                    # CMP-04
    net = Network("vnet", "aws", "10.0.0.0/16")
    add_subnet(net, "a", "10.0.1.0/24")
    vm = create_instance(net, "i-1", "a")
    vm.stop()
    with pytest.raises(ValidationError):
        vm.stop()


def test_storage_quota():                          # UT-14 / STO-01
    b = Bucket("logs", quota_bytes=100)
    upload(b, "a.txt", 60)
    with pytest.raises(ValidationError):
        upload(b, "b.txt", 60)


def test_public_access_blocked():                  # STO-03
    b = Bucket("site", 1000, public_access=True, block_public_access=True)
    assert anonymous_read_allowed(b) is False


def test_bad_ip_is_validation_error():
    with pytest.raises(ValidationError):
        lookup([Route("10.0.0.0/16", "local")], "not-an-ip")
    rules = [Rule("r", 1, "inbound", "tcp", 22, "10.0.0.0/8", "allow")]
    with pytest.raises(ValidationError):
        evaluate(rules, "inbound", "tcp", 22, "bad")


def test_azure_vnet_peering_updates_routes():      # NET-03
    from app.engine.routing import peer_networks
    a = Network("vnet-a", "azure", "10.0.0.0/16")
    b = Network("vnet-b", "azure", "10.1.0.0/16")
    ra, rb = [Route("10.0.0.0/16", "local")], [Route("10.1.0.0/16", "local")]
    assert peer_networks(a, b, ra, rb) == []
    assert ra[-1] == Route("10.1.0.0/16", "peering:vnet-a-vnet-b")
    assert rb[-1] == Route("10.0.0.0/16", "peering:vnet-a-vnet-b")


def test_delete_running_instance():                # CMP-05
    net = Network("vnet", "azure", "10.0.0.0/16")
    add_subnet(net, "web", "10.0.1.0/24")
    vm = create_instance(net, "vm1", "web")
    vm.delete()
    assert vm.state == "deleted" and "running -> deleted" in vm.log[-1]
    with pytest.raises(ValidationError):
        vm.start()
