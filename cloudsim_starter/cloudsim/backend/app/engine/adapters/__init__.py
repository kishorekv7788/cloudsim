"""Stage 3: provider adapters. Each maps provider words to the common model."""
from . import azure, aws, gcp

ADAPTERS = {"azure": azure, "aws": aws, "gcp": gcp}
