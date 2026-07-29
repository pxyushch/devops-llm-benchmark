import yaml

def evaluate_k8s_manifests(manifest_str: str) -> dict:
    docs = list(yaml.safe_load_all(manifest_str))
    kinds = {d.get("kind"): d for d in docs if isinstance(d, dict)}

    has_deploy = "Deployment" in kinds
    has_hpa = "HorizontalPodAutoscaler" in kinds
    has_netpol = "NetworkPolicy" in kinds

    return {
        "score": (has_deploy * 0.4) + (has_hpa * 0.3) + (has_netpol * 0.3),
        "kinds_found": list(kinds.keys())
    }
