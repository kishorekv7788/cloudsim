NAMES = {"network": "Virtual Network (VNet)", "firewall": "Network Security Group (NSG)",
         "compute": "Virtual Machine", "storage": "Blob container", "iam": "Azure RBAC"}
FIREWALL_USES_PRIORITY = True


def validate_rule(rule):
    """NSG rules can allow or deny and always have a priority."""
    return None
