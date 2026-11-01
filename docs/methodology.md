# Methodology (protocol v0.1)

## Task
Each task lives in `tasks/<domain>/<id>/` with:
- `task.yaml`: `task_id`, `domain`, `difficulty`, `prompt`, `artifact_type`, `created` (ISO date), `split` (dev | heldout).
- `check.py`: `check(artifact: str) -> list[Check]`. Pure and deterministic.
- `solutions/{good,bad,null}.txt`: reference solutions used for task QA.

## Generation
One call per task per epoch to the model with a fixed system prompt (`devops_bench/runners/claude_cli.py`),
no tools, no conversation memory. The artifact is the fenced code block(s) of the response.

## Scoring
Every check carries one category: correctness (40%), security (30%), best practices (20%), idempotency (10%).
- Category score = weighted fraction of its checks that passed.
- A category with no checks is dropped and the remaining weights are renormalised.
- Overall score = weighted sum of category scores.
- **A task passes iff every correctness check passes and the overall score >= 0.8.**
- Explicit prompt requirements are correctness checks; extra hygiene belongs to the other buckets.
- An artifact that fails to parse scores 0 (a single failed `parses_as_*` check).

## Task QA (`devops-bench validate`)
For every task: `good` scores 1.0 and passes, `bad` does not pass, `null` (empty) scores 0.
This runs in the test suite, so a task cannot be merged if its checks are broken or can be passed vacuously.

## Known limitations (v0.1)
- Checks are static (parse + structural). Linters and sandboxed execution are being added.
- 4 tasks only. No confidence intervals yet (needs repeated epochs and more tasks).
- No held-out split yet.
