from ..network import ValidationError

NAMES = {"network": "Virtual Private Cloud (VPC)", "firewall": "Security Group",
         "compute": "EC2 instance", "storage": "S3 bucket", "iam": "AWS IAM"}
FIREWALL_USES_PRIORITY = False   # Security Groups have no priority


def validate_rule(rule):
    """Security Groups are allow-only: a deny rule is a learner mistake."""
    if rule.action == "deny":
        raise ValidationError("AWS Security Groups only support allow rules. "
                              "Use a Network ACL if you need to deny traffic.")
