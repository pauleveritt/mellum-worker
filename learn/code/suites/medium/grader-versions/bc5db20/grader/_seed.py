"""The seed snapshot, imported only by phases that need models.

`_contract` is imported FIRST and for effect: the snapshot must be taken
after `client.__enter__()` has run the FastAPI lifespan, or seeding via a
startup hook -- a valid reading of the roadmap's "module-level list" --
looks identical to an empty store. This ordering is load-bearing; it is
the reason the source module interleaved these two statements.

pytest imports every selected module during collection, before any test
runs, so this snapshot is still taken before phase 3's POST tests mutate
`models.complaints`.
"""

from dataclasses import MISSING, fields

import models
from models import Complaint

from grader_tests import _contract  # noqa: F401  -- imported for lifespan order

SEED_COMPLAINTS = tuple(models.complaints)

__all__ = ["Complaint", "MISSING", "SEED_COMPLAINTS", "fields"]
