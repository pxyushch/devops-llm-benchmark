import yaml

from devops_bench.checks.parsers import load_yaml_docs
from devops_bench.core.checks import Category as C, Check


def _find(docs, kind):
    return [d for d in docs if d.get("kind") == kind]


def check(artifact: str) -> list[Check]:
    try:
        docs = load_yaml_docs(artifact)
    except yaml.YAMLError as e:
        return [Check("parses_as_yaml", C.CORRECTNESS, False, detail=str(e)[:120], failure_mode="SYNTAX_ERROR")]
    if not docs:
        return [Check("parses_as_yaml", C.CORRECTNESS, False, failure_mode="SYNTAX_ERROR")]

    out: list[Check] = []
    deps, hpas, nps = _find(docs, "Deployment"), _find(docs, "HorizontalPodAutoscaler"), _find(docs, "NetworkPolicy")
    out += [
        Check("has_deployment", C.CORRECTNESS, bool(deps)),
        Check("has_hpa", C.CORRECTNESS, bool(hpas)),
        Check("has_networkpolicy", C.CORRECTNESS, bool(nps)),
    ]

    # --- Deployment
    dep = deps[0] if deps else {}
    pod = dep.get("spec", {}).get("template", {}).get("spec", {})
    ctrs = pod.get("containers", []) or []
    out.append(Check("deployment_has_containers", C.CORRECTNESS, bool(ctrs)))
    out.append(Check("resources_requests_limits", C.BEST_PRACTICES, bool(ctrs) and all(
        {"cpu", "memory"} <= set((c.get("resources", {}).get("requests") or {}))
        and {"cpu", "memory"} <= set((c.get("resources", {}).get("limits") or {})) for c in ctrs),
        failure_mode="RESOURCE_OMISSION"))
    out.append(Check("readiness_and_liveness_probes", C.BEST_PRACTICES, bool(ctrs) and all(
        c.get("readinessProbe") and c.get("livenessProbe") for c in ctrs), failure_mode="RESOURCE_OMISSION"))
    has_sc = bool(pod.get("securityContext")) or any(c.get("securityContext") for c in ctrs)
    out.append(Check("security_context_present", C.CORRECTNESS, has_sc))
    out.append(Check("runs_as_nonroot", C.SECURITY, any(
        (s or {}).get("runAsNonRoot") is True for s in [pod.get("securityContext")] + [c.get("securityContext") for c in ctrs]),
        failure_mode="INSECURE_DEFAULTS"))
    out.append(Check("no_privileged_no_privesc", C.SECURITY, bool(ctrs) and all(
        not (c.get("securityContext") or {}).get("privileged")
        and (c.get("securityContext") or {}).get("allowPrivilegeEscalation") is False for c in ctrs),
        failure_mode="INSECURE_DEFAULTS"))
    out.append(Check("image_not_latest", C.SECURITY, bool(ctrs) and all(
        ":" in str(c.get("image", "")) and not str(c.get("image", "")).endswith(":latest") for c in ctrs)))

    # --- HPA
    hpa = hpas[0] if hpas else {}
    spec = hpa.get("spec", {})
    out.append(Check("hpa_api_v2", C.CORRECTNESS, str(hpa.get("apiVersion", "")).startswith("autoscaling/v2"),
                     failure_mode="HALLUCINATED_FLAG"))
    out.append(Check("hpa_replicas_3_15", C.CORRECTNESS, spec.get("minReplicas") == 3 and spec.get("maxReplicas") == 15))
    targets = {}
    for m in spec.get("metrics", []) or []:
        r = m.get("resource", {})
        targets[r.get("name")] = (r.get("target") or {}).get("averageUtilization")
    out.append(Check("hpa_cpu_70", C.CORRECTNESS, targets.get("cpu") == 70))
    out.append(Check("hpa_memory_80", C.CORRECTNESS, targets.get("memory") == 80))
    ref = spec.get("scaleTargetRef", {})
    out.append(Check("hpa_targets_deployment", C.CORRECTNESS,
                     ref.get("kind") == "Deployment" and ref.get("name") == dep.get("metadata", {}).get("name")))

    # --- NetworkPolicy
    np_ = nps[0] if nps else {}
    nspec = np_.get("spec", {})
    out.append(Check("netpol_ingress_policy_type", C.CORRECTNESS, "Ingress" in (nspec.get("policyTypes") or [])))
    rules = nspec.get("ingress") or []
    frm = [f for r in rules for f in (r.get("from") or [])]
    ns_ok = any(
        ((f.get("namespaceSelector") or {}).get("matchLabels") or {}).get("kubernetes.io/metadata.name") == "frontend"
        or ((f.get("namespaceSelector") or {}).get("matchLabels") or {}).get("name") == "frontend" for f in frm)
    out.append(Check("netpol_allows_frontend_ns", C.CORRECTNESS, ns_ok))
    ports = [p for r in rules for p in (r.get("ports") or [])]
    out.append(Check("netpol_tcp_8080_only", C.CORRECTNESS, bool(ports) and all(
        p.get("port") == 8080 and p.get("protocol", "TCP") == "TCP" for p in ports)))
    out.append(Check("netpol_no_open_cidr", C.SECURITY, not any(
        (f.get("ipBlock") or {}).get("cidr") in ("0.0.0.0/0", "::/0") for f in frm), failure_mode="INSECURE_DEFAULTS"))
    out.append(Check("netpol_no_empty_from", C.SECURITY, all(r.get("from") for r in rules) if rules else False,
                     failure_mode="INSECURE_DEFAULTS"))
    return out
