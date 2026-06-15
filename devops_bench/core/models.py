from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from enum import Enum

class TaskDomain(str, Enum):
    DOCKER = "docker"
    KUBERNETES = "kubernetes"
    TERRAFORM = "terraform"
    CICD = "cicd"
    SYSADMIN = "sysadmin"

@dataclass
class BenchmarkTask:
    task_id: str
    domain: TaskDomain
    title: str
    difficulty: str
    timeout_seconds: int
    rubric_id: str
    test_harness_path: str
