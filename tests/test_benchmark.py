import pytest
from devops_bench.rubrics.scorer import RubricEngine

def test_rubric_engine_scoring():
    engine = RubricEngine()
    result = engine.score_response(
        task_id="docker-01",
        model_output="FROM python:3.11-slim\nUSER appuser\nHEALTHCHECK CMD curl -f http://localhost:8000/health",
        eval_data={"score": 1.0}
    )
    assert result.passed is True
    assert result.score >= 0.85
    assert "correctness" in result.rubric_scores

def test_failure_taxonomy_exists():
    from devops_bench.rubrics.taxonomy import FAILURE_TAXONOMY
    assert "INSECURE_DEFAULTS" in FAILURE_TAXONOMY
