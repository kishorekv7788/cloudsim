from dataclasses import dataclass, field
from typing import Dict
from .network import ValidationError


@dataclass
class Bucket:
    name: str
    quota_bytes: int
    public_access: bool = False          # bucket says "objects are public"
    block_public_access: bool = False    # account/bucket-level guard (S3 / GCP style)
    objects: Dict[str, int] = field(default_factory=dict)

    @property
    def used(self):
        return sum(self.objects.values())


def upload(bucket: Bucket, key: str, size: int):
    """UT-14 / STO-01: quota is enforced."""
    if size < 0:
        raise ValidationError("Object size cannot be negative")
    old = bucket.objects.get(key, 0)
    if bucket.used - old + size > bucket.quota_bytes:
        raise ValidationError(
            f"Quota exceeded: {bucket.used - old + size} > {bucket.quota_bytes} bytes")
    bucket.objects[key] = size


def anonymous_read_allowed(bucket: Bucket) -> bool:
    """STO-03: public access is blocked when the guard is on."""
    return bucket.public_access and not bucket.block_public_access
