"""Lightweight, dependency-free-ish parsers shared by task checkers."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List

import yaml


@dataclass
class Stage:
    base: str
    alias: str | None
    instructions: List[tuple[str, str]] = field(default_factory=list)


def _collect_vars(text: str) -> Dict[str, str]:
    """Defaults of ARG/ENV declarations (NAME=value or ENV NAME value), quotes stripped."""
    out: Dict[str, str] = {}
    for m in re.finditer(r"^\s*(?:ARG|ENV)\s+(.+)$", text, re.M | re.I):
        for pair in re.findall(r"([A-Za-z_][A-Za-z0-9_]*)=(\"[^\"]*\"|\S+)", m.group(1)):
            out[pair[0]] = _expand(pair[1].strip('"'), out)
    return out


def _expand(s: str, variables: Dict[str, str]) -> str:
    def sub(m):
        name = m.group(1) or m.group(2)
        return variables.get(name, m.group(0))
    return re.sub(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}|\$([A-Za-z_][A-Za-z0-9_]*)", sub, s)


def parse_dockerfile(text: str) -> List[Stage]:
    """Split a Dockerfile into build stages with (INSTRUCTION, args) pairs.
    Handles line continuations and comments."""
    joined = re.sub(r"\\\s*\n", " ", text)
    variables = _collect_vars(joined)
    stages: List[Stage] = []
    for raw in joined.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        instr, _, args = line.partition(" ")
        instr = instr.upper()
        args = _expand(args, variables)
        if instr == "FROM":
            m = re.match(r"(?:--platform=\S+\s+)?(\S+)(?:\s+[Aa][Ss]\s+(\S+))?", args.strip())
            stages.append(Stage(base=m.group(1), alias=m.group(2)))
        elif stages:
            stages[-1].instructions.append((instr, args.strip()))
    return stages


def load_yaml_docs(text: str) -> List[Dict[str, Any]]:
    """Parse multi-document YAML; raises yaml.YAMLError on invalid syntax."""
    return [d for d in yaml.safe_load_all(text) if isinstance(d, dict)]


def _clean_hcl(v: Any) -> Any:
    if isinstance(v, str):
        return v[1:-1] if len(v) >= 2 and v[0] == v[-1] == '"' else v
    if isinstance(v, list):
        return [_clean_hcl(x) for x in v]
    if isinstance(v, dict):
        return {_clean_hcl(k): _clean_hcl(x) for k, x in v.items() if k != "__is_block__"}
    return v


def parse_hcl_resources(text: str) -> List[tuple[str, str, Dict[str, Any]]]:
    """Return [(resource_type, name, body)] from Terraform HCL. Raises on syntax errors."""
    import hcl2

    doc = _clean_hcl(hcl2.loads(text))
    out = []
    for block in doc.get("resource", []):
        for rtype, named in block.items():
            for name, body in named.items():
                out.append((rtype, name, body))
    return out


def blocks(body: Dict[str, Any], key: str) -> List[Dict[str, Any]]:
    """Nested blocks (e.g. 'allow') as a list of dicts."""
    v = body.get(key, [])
    return v if isinstance(v, list) else [v]
