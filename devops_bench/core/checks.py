"""Check primitives: every check is tagged with a rubric category."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Category(str, Enum):
    CORRECTNESS = "correctness"
    SECURITY = "security"
    BEST_PRACTICES = "best_practices"
    IDEMPOTENCY = "idempotency"


# Documented in docs/methodology.md
WEIGHTS = {
    Category.CORRECTNESS: 0.40,
    Category.SECURITY: 0.30,
    Category.BEST_PRACTICES: 0.20,
    Category.IDEMPOTENCY: 0.10,
}


@dataclass(frozen=True)
class Check:
    name: str
    category: Category
    passed: bool
    weight: float = 1.0
    detail: str = ""
    failure_mode: str | None = None  # key into FAILURE_TAXONOMY when failed
