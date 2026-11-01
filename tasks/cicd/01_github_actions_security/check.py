import re

import yaml

from devops_bench.core.checks import Category as C, Check


def _steps(wf):
    for job in (wf.get("jobs") or {}).values():
        for s in (job or {}).get("steps", []) or []:
            yield s


def check(artifact: str) -> list[Check]:
    try:
        wf = yaml.safe_load(artifact)
    except yaml.YAMLError as e:
        return [Check("parses_as_yaml", C.CORRECTNESS, False, detail=str(e)[:120], failure_mode="SYNTAX_ERROR")]
    if not isinstance(wf, dict) or not isinstance(wf.get("jobs"), dict):
        return [Check("parses_as_workflow", C.CORRECTNESS, False, failure_mode="SYNTAX_ERROR")]

    out: list[Check] = []
    text = artifact.lower()
    on = wf.get("on", wf.get(True))  # PyYAML parses bare `on` as boolean True
    jobs = wf["jobs"]

    versions = None
    for job in jobs.values():
        m = ((job or {}).get("strategy") or {}).get("matrix") or {}
        if "python-version" in m:
            versions = [str(v) for v in m["python-version"]]
    out.append(Check("matrix_python_versions", C.CORRECTNESS, versions is not None and set(versions) >= {"3.10", "3.11", "3.12"},
                     detail=f"matrix={versions} (unquoted 3.10 parses as 3.1)"))
    out.append(Check("uses_bandit", C.CORRECTNESS, "bandit" in text))
    out.append(Check("uses_trivy", C.CORRECTNESS, "trivy" in text))

    tag_trigger = isinstance(on, dict) and bool((on.get("push") or {}).get("tags"))
    tag_if = any(re.search(r"refs/tags/", str((j or {}).get("if", ""))) for j in jobs.values())
    out.append(Check("release_on_version_tags_only", C.CORRECTNESS, tag_trigger or tag_if))
    out.append(Check("release_packages_artifact", C.CORRECTNESS, any(
        "upload-artifact" in str(s.get("uses", "")) or "action-gh-release" in str(s.get("uses", ""))
        or "release" in str(s.get("run", "")).lower() for s in _steps(wf))))

    perms = wf.get("permissions")
    out.append(Check("top_level_permissions_contents_read", C.CORRECTNESS,
                     isinstance(perms, dict) and perms.get("contents") == "read"))
    out.append(Check("no_write_all", C.SECURITY, perms != "write-all" and "write-all" not in text,
                     failure_mode="INSECURE_DEFAULTS"))
    uses = [str(s["uses"]) for s in _steps(wf) if "uses" in s]
    out.append(Check("actions_not_on_mutable_branch", C.SECURITY, all(
        not re.search(r"@(main|master)$", u) for u in uses), failure_mode="INSECURE_DEFAULTS"))
    out.append(Check("actions_pinned_to_sha", C.SECURITY, bool(uses) and all(
        re.search(r"@[0-9a-f]{40}", u) or u.startswith("./") for u in uses),
        detail="stricter than the prompt requires; reserved for the security bucket"))
    out.append(Check("no_pull_request_target", C.SECURITY, not (isinstance(on, dict) and "pull_request_target" in on)))
    out.append(Check("no_secret_echo", C.SECURITY, not re.search(r"echo\s+.*\$\{\{\s*secrets\.", artifact)))

    out.append(Check("job_timeouts", C.BEST_PRACTICES, all("timeout-minutes" in (j or {}) for j in jobs.values())))
    out.append(Check("uses_cache_or_concurrency", C.BEST_PRACTICES, "cache" in text or "concurrency" in wf))
    out.append(Check("explicit_runner_version", C.IDEMPOTENCY, all(
        not str((j or {}).get("runs-on", "")).endswith("-latest") for j in jobs.values())))
    return out
