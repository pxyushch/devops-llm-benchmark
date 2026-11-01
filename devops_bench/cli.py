"""devops-bench CLI: list | validate | run"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from devops_bench.core.extract import extract_artifact
from devops_bench.core.task import DEFAULT_TASK_ROOT, load_tasks
from devops_bench.evaluate import evaluate
from devops_bench.sandbox.engine import docker_available

PROTOCOL_VERSION = "0.2"  # 0.2: sandboxed linters (pinned digests) added to scoring


def cmd_list(args) -> int:
    for t in load_tasks(Path(args.tasks)):
        print(f"{t.task_id:32} {t.domain:11} {t.difficulty:7} {t.split:8} {t.created}")
    return 0


def _lint_enabled(args, tasks) -> bool:
    if args.no_lint:
        return False
    if any(t.linters for t in tasks) and not docker_available():
        sys.exit("error: docker daemon not available but tasks require linters (use --no-lint to skip; "
                 "results will not be comparable)")
    return True


def cmd_validate(args) -> int:
    """Task QA: good solution must pass, bad must fail, null must score 0."""
    bad_tasks = 0
    lint = _lint_enabled(args, load_tasks(Path(args.tasks)))
    for t in load_tasks(Path(args.tasks)):
        res = {n: evaluate(t, t.solution(n), n, lint) for n in ("good", "bad", "null")}
        ok = res["good"].passed and res["good"].score == 1.0 and not res["bad"].passed and res["null"].score == 0.0
        bad_tasks += not ok
        scores = f"good={res['good'].score} bad={res['bad'].score} null={res['null'].score}"
        print(f"{'OK  ' if ok else 'FAIL'} {t.task_id:32} {scores}")
    return 1 if bad_tasks else 0


def cmd_run(args) -> int:
    from devops_bench.runners.claude_cli import ClaudeCLIRunner

    runner = ClaudeCLIRunner(model=args.model)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tasks = [t for t in load_tasks(Path(args.tasks)) if not args.task or t.task_id in args.task]
    lint = _lint_enabled(args, tasks)
    with out_path.open("a") as f:
        for t in tasks:
            for epoch in range(args.epochs):
                gen = runner.generate(t.prompt)
                artifact = extract_artifact(gen.text)
                res = evaluate(t, artifact, args.model, lint)
                rec = {
                    "protocol": PROTOCOL_VERSION, "linted": lint, "ts": time.time(), "epoch": epoch,
                    "task_id": t.task_id, "model": args.model, "error": gen.error,
                    "passed": res.passed, "score": res.score, "rubric": res.rubric_scores,
                    "failed_checks": res.failed_checks, "failure_patterns": res.failure_patterns,
                    "input_tokens": gen.input_tokens, "output_tokens": gen.output_tokens,
                    "cost_usd": gen.cost_usd, "latency_ms": gen.duration_ms,
                    "raw_response": gen.text, "artifact": artifact,
                }
                f.write(json.dumps(rec) + "\n")
                f.flush()
                print(f"{t.task_id:32} {args.model:7} epoch={epoch} pass={res.passed} "
                      f"score={res.score} failed={res.failed_checks}")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="devops-bench")
    p.add_argument("--tasks", default=str(DEFAULT_TASK_ROOT))
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list").set_defaults(fn=cmd_list)
    v = sub.add_parser("validate")
    v.add_argument("--no-lint", action="store_true")
    v.set_defaults(fn=cmd_validate)
    r = sub.add_parser("run")
    r.add_argument("--model", default="sonnet")
    r.add_argument("--epochs", type=int, default=1)
    r.add_argument("--task", action="append")
    r.add_argument("--no-lint", action="store_true")
    r.add_argument("--out", default="results/runs.jsonl")
    r.set_defaults(fn=cmd_run)
    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
