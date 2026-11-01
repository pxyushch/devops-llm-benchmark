"""Single entry point: task checks + (optional) sandboxed linters -> EvaluationResult."""
from __future__ import annotations

from devops_bench.core.checks import Check
from devops_bench.core.task import Task
from devops_bench.linters import run_linters
from devops_bench.rubrics.scorer import EvaluationResult, score_checks


def collect_checks(task: Task, artifact: str, lint: bool = True) -> list[Check]:
    checks = task.load_checker()(artifact)
    unparseable = any(c.name.startswith("parses_") and not c.passed for c in checks)
    if lint and task.linters and not unparseable:
        checks = checks + run_linters(task.linters, artifact)
    return checks


def evaluate(task: Task, artifact: str, model_name: str, lint: bool = True) -> EvaluationResult:
    return score_checks(task.task_id, model_name, collect_checks(task, artifact, lint))
