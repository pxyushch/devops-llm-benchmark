"""Run generations through the headless Claude Code CLI (uses the user's subscription)."""
from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass

SYSTEM_PROMPT = (
    "You are an expert DevOps engineer. Respond with the complete requested artifact "
    "in a single fenced code block and nothing else. No explanations."
)


@dataclass
class Generation:
    text: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    duration_ms: int
    error: str | None = None


class ClaudeCLIRunner:
    def __init__(self, model: str = "sonnet", timeout: int = 300):
        self.model = model
        self.timeout = timeout

    def generate(self, prompt: str) -> Generation:
        cmd = [
            "claude", "-p", "--model", self.model, "--tools", "",
            "--system-prompt", SYSTEM_PROMPT,
            "--no-session-persistence", "--disable-slash-commands",
            "--output-format", "json",
        ]
        try:
            res = subprocess.run(cmd, input=prompt, capture_output=True, text=True, timeout=self.timeout)
        except subprocess.TimeoutExpired:
            return Generation("", self.model, 0, 0, 0.0, 0, error="timeout")
        if res.returncode != 0:
            return Generation("", self.model, 0, 0, 0.0, 0, error=res.stderr.strip()[:500])
        data = json.loads(res.stdout)
        usage = data.get("usage", {})
        return Generation(
            text=data.get("result", ""),
            model=self.model,
            input_tokens=usage.get("input_tokens", 0) + usage.get("cache_creation_input_tokens", 0)
            + usage.get("cache_read_input_tokens", 0),
            output_tokens=usage.get("output_tokens", 0),
            cost_usd=data.get("total_cost_usd", 0.0),
            duration_ms=data.get("duration_ms", 0),
            error=data.get("result") if data.get("is_error") else None,
        )
