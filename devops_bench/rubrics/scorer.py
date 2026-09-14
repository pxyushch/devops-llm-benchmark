from typing import Dict, Any, List
from pydantic import BaseModel

class EvaluationResult(BaseModel):
    task_id: str
    model_name: str
    passed: bool
    score: float
    rubric_scores: Dict[str, float]
    failure_patterns: List[str]

class RubricEngine:
    def score_response(self, task_id: str, model_output: str, eval_data: Dict[str, Any]) -> EvaluationResult:
        rubric = {
            "correctness": eval_data.get("score", 0.0),
            "security": 1.0 if "insecure" not in model_output.lower() else 0.2,
            "best_practices": 0.9 if "HEALTHCHECK" in model_output or "NetworkPolicy" in model_output else 0.5
        }
        final_score = sum(rubric.values()) / len(rubric)
        return EvaluationResult(
            task_id=task_id,
            model_name="Claude-3.5-Sonnet",
            passed=final_score >= 0.8,
            score=round(final_score, 3),
            rubric_scores=rubric,
            failure_patterns=[]
        )
