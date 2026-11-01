import re

from devops_bench.checks.parsers import parse_dockerfile
from devops_bench.core.checks import Category as C, Check

BUILD_TOOLS = re.compile(r"\b(build-essential|gcc|g\+\+|make|cmake|python3?-dev|libc6-dev)\b")


def check(artifact: str) -> list[Check]:
    stages = parse_dockerfile(artifact)
    if not stages:
        return [Check("parses_as_dockerfile", C.CORRECTNESS, False, failure_mode="SYNTAX_ERROR")]
    out: list[Check] = []
    final = stages[-1] if stages else None
    ins = final.instructions if final else []

    out.append(Check("multi_stage", C.CORRECTNESS, len(stages) >= 2, detail=f"{len(stages)} stage(s)"))
    out.append(Check("bases_python311_slim", C.CORRECTNESS,
                     bool(stages) and all(s.base == "python:3.11-slim" for s in stages)))
    out.append(Check("copies_from_builder", C.CORRECTNESS,
                     any(i == "COPY" and "--from=" in a for i, a in ins)))
    out.append(Check("expose_8000", C.CORRECTNESS,
                     any(i == "EXPOSE" and re.search(r"\b8000\b", a) for i, a in ins)))
    out.append(Check("healthcheck", C.CORRECTNESS, any(i == "HEALTHCHECK" and "NONE" not in a.upper() for i, a in ins)))
    pid1 = [a for i, a in ins if i in ("ENTRYPOINT", "CMD")]
    out.append(Check("pid1_supervisor", C.CORRECTNESS,
                     any("dumb-init" in a or "gunicorn" in a for a in pid1)))
    final_installs = " ".join(a for i, a in ins if i == "RUN" and re.search(r"(apt-get|apk|yum)\s+install", a))
    out.append(Check("no_build_tools_in_final", C.CORRECTNESS, not BUILD_TOOLS.search(final_installs),
                     failure_mode="RESOURCE_OMISSION"))

    users = [a.split(":")[0].strip() for i, a in ins if i == "USER"]
    out.append(Check("final_user_nonroot", C.CORRECTNESS,
                     bool(users) and users[-1] not in ("root", "0") and users[-1] in ("appuser", "10001"),
                     failure_mode="INSECURE_DEFAULTS"))
    all_runs = " ".join(a for s in stages for i, a in s.instructions if i == "RUN")
    out.append(Check("appuser_uid_10001", C.CORRECTNESS,
                     bool(re.search(r"(-u|--uid)[ =]10001", all_runs)) and "appuser" in all_runs,
                     failure_mode="INSECURE_DEFAULTS"))
    out.append(Check("no_latest_tag", C.SECURITY, all(not s.base.endswith(":latest") and ":" in s.base for s in stages)))
    out.append(Check("no_curl_pipe_sh", C.SECURITY, not re.search(r"(curl|wget)[^|]*\|\s*(sh|bash)", artifact),
                     failure_mode="INSECURE_DEFAULTS"))

    out.append(Check("no_secrets_in_env", C.SECURITY, not re.search(
        r"^\s*(ENV|ARG)\s+\S*(PASSWORD|SECRET|TOKEN|API_?KEY)\S*\s*=", artifact, re.I | re.M),
        failure_mode="INSECURE_DEFAULTS"))
    out.append(Check("no_remote_add", C.SECURITY, not any(i == "ADD" and a.startswith("http") for i, a in ins)))

    apt_used = "apt-get install" in all_runs
    out.append(Check("apt_cache_cleaned", C.BEST_PRACTICES,
                     (not apt_used) or "rm -rf /var/lib/apt/lists" in all_runs))
    out.append(Check("pip_no_cache", C.BEST_PRACTICES,
                     "pip install" not in all_runs or "--no-cache-dir" in all_runs or "PIP_NO_CACHE_DIR" in artifact))
    out.append(Check("workdir_set", C.BEST_PRACTICES, any(i == "WORKDIR" for i, _ in ins)))

    out.append(Check("pinned_base_tags", C.IDEMPOTENCY, all(re.search(r":\d", s.base) for s in stages)))
    return out
