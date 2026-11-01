import pytest

from devops_bench.sandbox.engine import SandboxExecutionEngine, docker_available

pytestmark = pytest.mark.skipif(not docker_available(), reason="docker daemon not available")
IMAGE = "alpine:3.20"


@pytest.fixture(scope="module")
def sb():
    return SandboxExecutionEngine(IMAGE)


def test_files_are_visible_and_readonly(sb):
    r = sb.run(["sh", "-c", "cat /work/a.txt; touch /work/x 2>&1 || echo RO"], files={"a.txt": "hello"})
    assert "hello" in r["stdout"] and "RO" in r["stdout"]


def test_no_network(sb):
    r = sb.run(["sh", "-c", "wget -T 3 -q -O- http://1.1.1.1 >/dev/null 2>&1; echo rc=$?"])
    assert "rc=0" not in r["stdout"]


def test_runs_as_nobody(sb):
    assert sb.run(["id", "-u"])["stdout"].strip() == "65534"


def test_timeout_kills(sb):
    r = sb.run(["sleep", "30"], timeout=3)
    assert r["timed_out"]


def test_path_traversal_rejected(sb):
    with pytest.raises(ValueError):
        sb.run(["true"], files={"../evil": "x"})
