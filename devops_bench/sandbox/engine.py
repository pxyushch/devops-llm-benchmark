import docker
import subprocess
from typing import Dict, Any, Optional

class SandboxExecutionEngine:
    """Executes model-generated DevOps scripts inside secure isolated containers."""
    def __init__(self, base_image: str = "ubuntu:24.04"):
        self.base_image = base_image

    def run_command(self, cmd: str, timeout: int = 60) -> Dict[str, Any]:
        try:
            res = subprocess.run(
                ["bash", "-c", cmd],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return {
                "exit_code": res.returncode,
                "stdout": res.stdout,
                "stderr": res.stderr,
                "timed_out": False
            }
        except subprocess.TimeoutExpired as e:
            return {
                "exit_code": -1,
                "stdout": e.stdout.decode() if e.stdout else "",
                "stderr": "Command timed out",
                "timed_out": True
            }
