FAILURE_TAXONOMY = {
    "SYNTAX_ERROR": "Invalid YAML/HCL/Bash syntax causing immediate parser failure",
    "INSECURE_DEFAULTS": "Root containers, privileged mode, wildcard IAM permissions (0.0.0.0/0)",
    "HALLUCINATED_FLAG": "Invoking non-existent CLI flags or deprecated API versions (e.g., extensions/v1beta1)",
    "RESOURCE_OMISSION": "Missing CPU/memory limits or absent readiness probes leading to OOM-kills",
    "PROMPT_LEAK": "Echoing internal task instructions or formatting markers into final config"
}
