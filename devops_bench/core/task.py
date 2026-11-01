"""Task schema and loader."""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Callable

import yaml
from pydantic import BaseModel, Field

from devops_bench.core.checks import Check

DEFAULT_TASK_ROOT = Path(__file__).resolve().parents[2] / "tasks"


class Task(BaseModel):
    task_id: str
    domain: str
    difficulty: str
    timeout_seconds: int = 120
    prompt: str
    artifact_type: str = "text"  # dockerfile | yaml | hcl | text
    created: str | None = None  # ISO date, used for contamination slicing
    split: str = "dev"  # dev | heldout
    task_dir: Path = Field(exclude=True)

    def load_checker(self) -> Callable[[str], list[Check]]:
        path = self.task_dir / "check.py"
        spec = importlib.util.spec_from_file_location(f"check_{self.task_id.replace('-', '_')}", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.check

    def solution(self, name: str) -> str:
        """Reference solutions live in <task_dir>/solutions/<name>.txt (good|bad|null)."""
        return (self.task_dir / "solutions" / f"{name}.txt").read_text()


def load_tasks(root: Path = DEFAULT_TASK_ROOT) -> list[Task]:
    tasks = []
    for yaml_path in sorted(root.glob("*/*/task.yaml")):
        data = yaml.safe_load(yaml_path.read_text())
        tasks.append(Task(task_dir=yaml_path.parent, **data))
    return tasks
