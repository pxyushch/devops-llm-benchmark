# Research notes: what credible benchmarks do (2026-11-01)

Sources are in the links. Items marked (bg) came from background knowledge and were not re-verified live.

## References
- SWE-bench Verified / Live: https://www.swebench.com , https://swe-bench-live.github.io (per-instance Docker, FAIL_TO_PASS plus PASS_TO_PASS, monthly fresh tasks)
- Terminal-Bench: https://github.com/harbor-framework/terminal-bench-2-1 (instruction + Docker env + test script, 5 attempts for leaderboard runs, HF leaderboard with PR bot)
- EvalPlus: https://github.com/evalplus/evalplus (extra tests found weak originals; unbiased pass@k, https://arxiv.org/abs/2107.03374)
- LiveCodeBench: https://arxiv.org/abs/2403.07974 (release-date tagging for contamination slices)
- BigCodeBench: https://arxiv.org/abs/2406.15877
- IaC-Eval (NeurIPS 2024): 458 Terraform scenarios with intent specs, GPT-4 at 19.36% pass@1
- Inspect AI: https://inspect.aisi.org.uk (task = dataset + solver + scorer; Docker sandbox; epochs; logs)
- Error bars: https://arxiv.org/pdf/2411.00640

## Adopt in the 1-month plan (priority order)
1. Multiple samples per task, unbiased pass@k, bootstrap/Wilson 95% CI, paired model comparisons.
2. Hermetic Docker sandbox: pinned digests, no network, resource limits, non-root, grader separate from the generation container.
3. Objective linters as scorers instead of regex.
4. Validate every task with an oracle solution (must score 100%), a null solution (must score 0), and a reward-hack attempt. Mutation-test the checks.
5. Contamination controls: creation date per task, about 30% private held-out split, canary string, rotation.
6. Pinned protocol (prompt, temperature, max tokens), versioned and recorded with every score.
7. Publish raw outputs, logs, cost, tokens, latency. Consider porting to Inspect AI.
8. Hugging Face dataset card, PR-based submissions with a schema and CI re-scoring.
9. Add pass^k (consistency) and a small multi-step repair set.

## Linters mapped to the rubric
| Tool | Artifact | Bucket |
|---|---|---|
| terraform validate/fmt, tflint | Terraform | correctness, best practice |
| kubeconform | K8s | correctness |
| kube-score | K8s | best practice, security context |
| hadolint | Dockerfile | best practice |
| trivy, checkov | images, IaC, CI | security |
| conftest/OPA | any config | task-specific policy |
| actionlint | GitHub Actions | correctness |
| shellcheck | shell | correctness, robustness |

Use errors as gates and a capped, severity-weighted deduction for warnings. Pin tool versions and record them in the protocol version.
