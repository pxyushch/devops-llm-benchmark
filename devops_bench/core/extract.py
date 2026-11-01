"""Pull the artifact out of a model response."""
import re

_FENCE = re.compile(r"```[a-zA-Z0-9_+-]*\n(.*?)```", re.S)


def extract_artifact(response: str) -> str:
    """Join all fenced code blocks; fall back to the raw response if none."""
    blocks = _FENCE.findall(response)
    if not blocks:
        return response.strip()
    return "\n---\n".join(b.strip("\n") for b in blocks) if len(blocks) > 1 else blocks[0].strip("\n")
