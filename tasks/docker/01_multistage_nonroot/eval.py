import re

def evaluate_dockerfile(content: str) -> dict:
    has_multistage = len(re.findall(r"^FROM ", content, re.M)) >= 2
    has_nonroot = bool(re.search(r"USER\s+(10001|appuser)", content))
    has_healthcheck = bool(re.search(r"HEALTHCHECK\s+", content))
    has_entrypoint = bool(re.search(r"(ENTRYPOINT|CMD)", content))

    score = 0.0
    if has_multistage: score += 0.3
    if has_nonroot: score += 0.3
    if has_healthcheck: score += 0.2
    if has_entrypoint: score += 0.2

    return {
        "score": score,
        "checks": {
            "multistage": has_multistage,
            "nonroot_security": has_nonroot,
            "healthcheck": has_healthcheck,
            "entrypoint": has_entrypoint
        }
    }
