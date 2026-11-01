"""Rubric scoring: aggregates tagged checks into the 40/30/20/10 weighted score."""
from __future__ import annotations

from typing import Dict, List

from pydantic import BaseModel

from devops_bench.core.checks import WEIGHTS, Category, Check

PASS_THRESHOLD = 0.8


class EvaluationResult(BaseModel):
    task_id: str
    model_name: str
    passed: bool
    score: float
    rubric_scores: Dict[str, float]
    failure_patterns: List[str]
    failed_checks: List[str]


def score_checks(task_id: str, model_name: str, checks: List[Check]) -> EvaluationResult:
    """Per-category score = weighted fraction of passed checks. A category with no
    checks is excluded and the remaining weights are renormalised.
    A task passes iff every correctness check passes AND the overall score >= 0.8."""
    cat_scores: Dict[str, float] = {}
    for cat in Category:
        cs = [c for c in checks if c.category == cat]
        total = sum(c.weight for c in cs)
        if total:
            cat_scores[cat.value] = sum(c.weight for c in cs if c.passed) / total
    weight_sum = sum(WEIGHTS[Category(k)] for k in cat_scores)
    overall = sum(WEIGHTS[Category(k)] * v for k, v in cat_scores.items()) / weight_sum if weight_sum else 0.0
    correct = cat_scores.get(Category.CORRECTNESS.value, 0.0) == 1.0
    failed = [c for c in checks if not c.passed]
    return EvaluationResult(
        task_id=task_id,
        model_name=model_name,
        passed=correct and overall >= PASS_THRESHOLD,
        score=round(overall, 4),
        rubric_scores={k: round(v, 4) for k, v in cat_scores.items()},
        failure_patterns=sorted({c.failure_mode for c in failed if c.failure_mode}),
        failed_checks=[c.name for c in failed],
    )
