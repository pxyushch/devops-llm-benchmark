from dataclasses import dataclass, asdict
from typing import List, Dict, Any
import time
import json

@dataclass
class MetricPoint:
    timestamp: float
    task_id: str
    duration_ms: float
    status: str

class TelemetryExporter:
    """Collects benchmark evaluation telemetry and exports Prometheus/JSON metrics."""
    def __init__(self):
        self.metrics: List[MetricPoint] = []

    def record(self, task_id: str, duration_ms: float, status: str):
        self.metrics.append(
            MetricPoint(
                timestamp=time.time(),
                task_id=task_id,
                duration_ms=duration_ms,
                status=status
            )
        )

    def export_summary(self) -> Dict[str, Any]:
        if not self.metrics:
            return {"total_tasks": 0, "avg_duration_ms": 0.0}
        total = len(self.metrics)
        avg = sum(m.duration_ms for m in self.metrics) / total
        return {
            "total_tasks": total,
            "avg_duration_ms": round(avg, 2),
            "success_rate": round(sum(1 for m in self.metrics if m.status == "PASS") / total, 3)
        }
