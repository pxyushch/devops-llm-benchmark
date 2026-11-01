from devops_bench.checks.parsers import blocks, parse_hcl_resources
from devops_bench.core.checks import Category as C, Check

OPEN = {"0.0.0.0/0", "::/0"}


def _of(res, rtype):
    return [(n, b) for t, n, b in res if t == rtype]


def check(artifact: str) -> list[Check]:
    try:
        res = parse_hcl_resources(artifact)
    except Exception as e:  # hcl2 raises several parser exception types
        return [Check("parses_as_hcl", C.CORRECTNESS, False, detail=str(e)[:120], failure_mode="SYNTAX_ERROR")]
    if not res:
        return [Check("parses_as_hcl", C.CORRECTNESS, False, failure_mode="SYNTAX_ERROR")]

    out: list[Check] = []
    nets = _of(res, "google_compute_network")
    vpc = next((b for _, b in nets if b.get("name") == "prod-vpc"), None)
    out.append(Check("vpc_prod_vpc", C.CORRECTNESS, vpc is not None))
    out.append(Check("vpc_no_auto_subnets", C.CORRECTNESS, vpc is not None and vpc.get("auto_create_subnetworks") is False))

    subs = [b for _, b in _of(res, "google_compute_subnetwork")]
    regions = {b.get("region") for b in subs}
    out.append(Check("two_subnets_two_regions", C.CORRECTNESS, {"us-central1", "us-east1"} <= regions))
    out.append(Check("private_google_access", C.CORRECTNESS, bool(subs) and all(
        b.get("private_ip_google_access") is True for b in subs)))
    out.append(Check("subnet_ranges_defined", C.BEST_PRACTICES, bool(subs) and all(b.get("ip_cidr_range") for b in subs)))

    out.append(Check("has_cloud_router", C.CORRECTNESS, bool(_of(res, "google_compute_router"))))
    nats = [b for _, b in _of(res, "google_compute_router_nat")]
    out.append(Check("has_cloud_nat", C.CORRECTNESS, bool(nats)))
    out.append(Check("nat_auto_ip_no_static_public", C.CORRECTNESS, bool(nats) and all(
        b.get("nat_ip_allocate_option") == "AUTO_ONLY" for b in nats)))
    out.append(Check("nat_logging_enabled", C.BEST_PRACTICES, bool(nats) and all(b.get("log_config") for b in nats)))

    fws = [b for _, b in _of(res, "google_compute_firewall")]
    ssh_allow = [b for b in fws if any(
        a.get("protocol") == "tcp" and "22" in [str(p) for p in a.get("ports", [])] for a in blocks(b, "allow"))]
    out.append(Check("ssh_allow_rule", C.CORRECTNESS, bool(ssh_allow)))
    out.append(Check("ssh_source_restricted", C.SECURITY, bool(ssh_allow) and all(
        b.get("source_ranges") and not (set(b["source_ranges"]) & OPEN) for b in ssh_allow),
        failure_mode="INSECURE_DEFAULTS"))
    deny_all = [b for b in fws if str(b.get("direction", "INGRESS")) == "INGRESS" and any(
        d.get("protocol") == "all" for d in blocks(b, "deny"))]
    out.append(Check("deny_all_ingress_rule", C.CORRECTNESS, bool(deny_all)))
    ssh_prio = min((int(b.get("priority", 1000)) for b in ssh_allow), default=None)
    deny_prio = max((int(b.get("priority", 1000)) for b in deny_all), default=None)
    out.append(Check("ssh_allow_overrides_deny", C.CORRECTNESS,
                     ssh_prio is not None and deny_prio is not None and ssh_prio < deny_prio,
                     detail="allow rule needs a lower priority number than deny-all"))
    out.append(Check("no_allow_from_anywhere", C.SECURITY, not any(
        set(b.get("source_ranges", [])) & OPEN for b in fws if blocks(b, "allow")), failure_mode="INSECURE_DEFAULTS"))

    inst = [b for _, b in _of(res, "google_compute_instance")]
    out.append(Check("instances_no_public_ip", C.SECURITY, all(not blocks(b, "access_config") for b in inst),
                     failure_mode="INSECURE_DEFAULTS"))
    out.append(Check("firewall_attached_to_vpc", C.CORRECTNESS, bool(fws) and all(b.get("network") for b in fws)))
    out.append(Check("resources_reference_not_hardcode", C.IDEMPOTENCY, any(
        "google_compute_network." in str(b.get("network", "")) for b in subs + fws)))
    return out
