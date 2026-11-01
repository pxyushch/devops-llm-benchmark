"""Objective scoring via real linters, run inside the hardened sandbox.

Images are pinned by digest so scores are reproducible; bump them deliberately and bump
PROTOCOL_VERSION in cli.py when you do (linter updates change scores).
"""
from __future__ import annotations

import json
from typing import Callable, Dict, List

from devops_bench.core.checks import Category as C
from devops_bench.core.checks import Check
from devops_bench.sandbox.engine import SandboxExecutionEngine

IMAGES: Dict[str, str] = {
    "hadolint": "hadolint/hadolint@sha256:3c206a451cec6d486367e758645269fd7d696c5ccb6ff59d8b03b0e45268a199",  # v2.12.0
    "actionlint": "rhysd/actionlint@sha256:887a259a5a534f3c4f36cb02dca341673c6089431057242cdc931e9f133147e9",  # 1.7.7
    "kube-score": "zegl/kube-score@sha256:94137f32ce139dc9fbdbbd380249025e4d378c282ff151a100b981cdeeb923b6",  # v1.19.0
}

# kube-score check ids that are security relevant; everything else critical is best-practice.
_KS_SECURITY = ("container-security-context", "pod-networkpolicy", "container-image-tag", "container-image-pull-policy")


def _hadolint(artifact: str) -> List[Check]:
    r = SandboxExecutionEngine(IMAGES["hadolint"]).run(
        ["hadolint", "--no-color", "--ignore", "DL3008", "--format", "json", "/work/Dockerfile"],
        files={"Dockerfile": artifact})
    try:
        if r["exit_code"] not in (0, 1) or r["timed_out"]:
            raise json.JSONDecodeError("bad exit", "", 0)
        findings = json.loads(r["stdout"] or "[]")
    except json.JSONDecodeError:
        return [Check("lint_hadolint_ran", C.BEST_PRACTICES, False, detail=r["stderr"][:120])]
    errors = [f["code"] for f in findings if f["level"] == "error"]
    warns = [f["code"] for f in findings if f["level"] == "warning"]
    return [
        Check("lint_hadolint_no_errors", C.BEST_PRACTICES, not errors, detail=",".join(errors)),
        Check("lint_hadolint_no_warnings", C.BEST_PRACTICES, not warns, weight=0.5, detail=",".join(warns)),
    ]


def _actionlint(artifact: str) -> List[Check]:
    r = SandboxExecutionEngine(IMAGES["actionlint"]).run(
        ["actionlint", "-no-color", "-format", "{{json .}}", "/work/ci.yml"], files={"ci.yml": artifact})
    try:
        if r["exit_code"] not in (0, 1) or r["timed_out"]:
            raise json.JSONDecodeError("bad exit", "", 0)
        findings = json.loads(r["stdout"] or "[]") or []
    except json.JSONDecodeError:
        return [Check("lint_actionlint_ran", C.CORRECTNESS, False, detail=r["stderr"][:120])]
    return [Check("lint_actionlint_clean", C.CORRECTNESS, not findings,
                  detail="; ".join(f["message"][:60] for f in findings[:3]))]


# Opinionated kube-score checks unrelated to what the tasks ask for. Kept explicit and versioned.
_KS_IGNORED = (
    "container-resource-requests-equal-limits", "container-memory-requests-equal-limits",
    "container-cpu-requests-equal-limits", "container-image-pull-policy",
    "container-ephemeral-storage-request-and-limit", "deployment-has-poddisruptionbudget",
    "deployment-has-host-podantiaffinity",
)


def _kube_score(artifact: str) -> List[Check]:
    r = SandboxExecutionEngine(IMAGES["kube-score"]).run(
        ["/kube-score", "score", "--output-format", "json",
         *[a for t in _KS_IGNORED for a in ("--ignore-test", t)], "/work/manifests.yaml"],
        files={"manifests.yaml": artifact})
    try:
        if r["exit_code"] not in (0, 1) or r["timed_out"]:
            raise json.JSONDecodeError("bad exit", "", 0)
        objs = json.loads(r["stdout"] or "[]")
    except json.JSONDecodeError:
        return [Check("lint_kube_score_ran", C.BEST_PRACTICES, False, detail=r["stderr"][:120])]
    sec, other = [], []
    for o in objs:
        for c in o.get("checks", []):
            if c.get("grade", 10) == 1:  # CRITICAL (0 = skipped)
                cid = c["check"]["id"]
                (sec if cid.startswith(_KS_SECURITY) else other).append(cid)
    return [
        Check("lint_kube_score_no_critical_security", C.SECURITY, not sec, detail=",".join(sorted(set(sec)))),
        Check("lint_kube_score_no_critical_other", C.BEST_PRACTICES, not other, detail=",".join(sorted(set(other)))),
    ]


LINTERS: Dict[str, Callable[[str], List[Check]]] = {
    "hadolint": _hadolint, "actionlint": _actionlint, "kube-score": _kube_score,
}


def run_linters(names: List[str], artifact: str) -> List[Check]:
    out: List[Check] = []
    for n in names:
        out += LINTERS[n](artifact)
    return out
