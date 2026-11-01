"""Hardened container execution for running linters/tools against model-generated artifacts.

Model output is untrusted. It is never executed on the host: files are written to a temp dir that is
mounted read-only into a throwaway container with no network, no capabilities, a read-only root
filesystem, a non-root user and CPU/memory/pid limits.
"""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional


def docker_available() -> bool:
    try:
        return subprocess.run(["docker", "info"], capture_output=True, timeout=10).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


class SandboxExecutionEngine:
    def __init__(self, image: str, memory: str = "512m", cpus: str = "1", pids: int = 128, network: bool = False):
        """`image` should be pinned by digest (name@sha256:...) for reproducible scoring."""
        self.image = image
        self.memory = memory
        self.cpus = cpus
        self.pids = pids
        self.network = network

    def run(self, cmd: list[str], files: Optional[Dict[str, str]] = None, timeout: int = 60) -> Dict[str, Any]:
        """Run `cmd` in a fresh container. `files` ({relative path: content}) appear read-only under /work."""
        name = f"devops-bench-{next(tempfile._get_candidate_names())}"
        with tempfile.TemporaryDirectory() as tmp:
            for rel, content in (files or {}).items():
                p = Path(tmp, rel)
                if not p.resolve().is_relative_to(Path(tmp).resolve()):
                    raise ValueError(f"unsafe path: {rel}")
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(content)
            docker_cmd = [
                "docker", "run", "--rm", "--name", name,
                "--network", "bridge" if self.network else "none",
                "--read-only", "--tmpfs", "/tmp:rw,size=64m",
                "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
                "--user", "65534:65534",
                "--memory", self.memory, "--cpus", self.cpus, "--pids-limit", str(self.pids),
                "-v", f"{tmp}:/work:ro", "-w", "/work",
                self.image, *cmd,
            ]
            try:
                res = subprocess.run(docker_cmd, capture_output=True, text=True, timeout=timeout)
            except subprocess.TimeoutExpired as e:
                subprocess.run(["docker", "rm", "-f", name], capture_output=True)
                out = e.stdout.decode(errors="replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
                return {"exit_code": -1, "stdout": out, "stderr": "timed out", "timed_out": True}
            return {"exit_code": res.returncode, "stdout": res.stdout, "stderr": res.stderr, "timed_out": False}
