# Baseline audit (2026-11-01)

Snapshot of the repo at commit 8ba0415, before the v1 upgrade work.

## Findings

| # | Finding | Severity |
|---|---------|----------|
| 1 | `pip install -e .` failed (setuptools found two top-level packages). Fixed in this branch. | High (fixed) |
| 2 | Only 6 files under `tasks/`, forming 4 task definitions (docker, kubernetes, terraform, cicd). Terraform and CI/CD have no `eval.py`. | High |
| 3 | `benchmarks/` and `eval_data/` hold about 150 empty `pass` stub functions. They are not tasks and no code reads them. | High |
| 4 | `RubricEngine.score_response` hardcodes `model_name="Claude-3.5-Sonnet"`, scores security by looking for the word "insecure" in the output, and uses a bare substring check for best practices. It does not implement the documented 40/30/20/10 weights. | High |
| 5 | `SandboxExecutionEngine.run_command` runs `bash -c` on the host with `subprocess`. It does not use Docker, despite the docs and the `docker` import. | High (safety) |
| 6 | `devops_bench.cli` does not exist, though `pyproject.toml` declares the `devops-bench` script. There is no model-runner code and no code that calls any LLM. | High |
| 7 | The README leaderboard (Claude 3.5 Sonnet 78.4%, GPT-4o 71.2%, and others) is not produced by any code in the repo. | High (credibility) |
| 8 | `docker/eval.py` uses regex only (e.g. any `USER appuser` line passes), and `telemetry.py` and `reporter.json` are placeholders. | Medium |
| 9 | Only 2 tests, covering the scorer and the taxonomy. No CI. | Medium |
| 10 | Git author email (`piyush.chauhan@ethara.ai`) differs from `pyproject.toml` (`peeyushrajput321@gmail.com`). | Low |

## Implication

The repo is a skeleton with a published leaderboard that nothing backs. Before launch, either generate real results with the real harness or remove the leaderboard. Week 1 changes the plan: build the working harness first, then scale up the tasks.

## Done in this branch so far

- Fixed package discovery in `pyproject.toml`; tests pass (2/2).
- Added `.gitignore`.
