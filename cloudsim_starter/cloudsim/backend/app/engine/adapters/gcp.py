NAMES = {"network": "VPC network", "firewall": "Firewall rule",
         "compute": "Compute Engine instance", "storage": "Cloud Storage bucket", "iam": "GCP IAM"}
FIREWALL_USES_PRIORITY = True


def validate_rule(rule):
    """VPC firewall rules can allow or deny and have a priority."""
    return None
