import pytest

from devops_bench.core.checks import Category, Check
from devops_bench.core.extract import extract_artifact
from devops_bench.core.task import load_tasks
from devops_bench.rubrics.scorer import score_checks
from devops_bench.rubrics.taxonomy import FAILURE_TAXONOMY

TASKS = load_tasks()


def test_failure_taxonomy_exists():
    assert "INSECURE_DEFAULTS" in FAILURE_TAXONOMY


def test_weights_sum_to_one():
    from devops_bench.core.checks import WEIGHTS
    assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9


def test_scorer_weighting():
    checks = [
        Check("a", Category.CORRECTNESS, True),
        Check("b", Category.SECURITY, False),
        Check("c", Category.BEST_PRACTICES, True),
        Check("d", Category.IDEMPOTENCY, True),
    ]
    r = score_checks("t", "m", checks)
    assert r.score == pytest.approx(0.7)  # 0.4 + 0 + 0.2 + 0.1
    assert r.passed is False


def test_failed_correctness_blocks_pass():
    r = score_checks("t", "m", [Check("a", Category.CORRECTNESS, False), Check("b", Category.SECURITY, True)])
    assert not r.passed


def test_extract_artifact():
    assert extract_artifact("hi\n```dockerfile\nFROM x\n```\nbye") == "FROM x"
    assert extract_artifact("FROM x") == "FROM x"


def test_tasks_loaded():
    assert len(TASKS) >= 4


@pytest.mark.parametrize("task", TASKS, ids=lambda t: t.task_id)
def test_task_validation(task):
    """Every task: good scores 1.0 and passes, bad fails, null scores 0."""
    chk = task.load_checker()
    good, bad, null = (score_checks(task.task_id, n, chk(task.solution(n))) for n in ("good", "bad", "null"))
    assert good.passed and good.score == 1.0, good.failed_checks
    assert not bad.passed
    assert null.score == 0.0


def test_dockerfile_arg_expansion_regression():
    """USER ${APP_UID}:${APP_UID} must resolve via ARG defaults (false negative found 2026-11-01)."""
    from devops_bench.checks.parsers import parse_dockerfile
    stages = parse_dockerfile("ARG APP_UID=10001\nFROM python:3.11-slim\nUSER ${APP_UID}:${APP_UID}\n")
    assert ("USER", "10001:10001") in stages[0].instructions
