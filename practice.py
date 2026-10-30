python3 - <<'PY'
from pathlib import Path
import subprocess, shutil, urllib.request

base = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029")
repo = Path("/application1/sajjna8/rt-pzaas-cta-offers-v1")
overlay = base / "native_batch2_cached_overlay"
candidate = Path("/application1/cta_max_true_batch_dev_20261028/batch2_candidate")
cache = base / "mojo_cache_8766"
name = "cta-batch2-trace-8766-v2"
image = "localhost/cta-max-faiss:local"

pod = [
    "podman", "--root", "/application1/podman/storage",
    "--runroot", "/run/containers/storage"
]

def run(args):
    return subprocess.run(
        pod + args, capture_output=True, text=True
    )

required = [
    repo,
    overlay / "cta_native_batch2_proven_server.py",
    overlay / "cta_native_scheduler.py",
    base / "real_max_batch2_backend.py",
    candidate / "cta_max"
]

for path in required:
    assert path.exists(), f"STOP: Missing {path}"

assert run(["image", "exists", image]).returncode == 0, \
    "STOP: Development image unavailable"

assert run(["container", "exists", name]).returncode != 0, \
    "STOP: Test container already exists"

ports = subprocess.run(
    ["ss", "-H", "-ltn", "( sport = :8766 )"],
    capture_output=True, text=True, check=True
)
assert not ports.stdout.strip(), "STOP: Port 8766 occupied"

with urllib.request.urlopen(
    "http://127.0.0.1:8765/health", timeout=10
) as response:
    assert response.status == 200, "STOP: Original MAX unhealthy"

assert shutil.disk_usage(base).free > 1024**3, \
    "STOP: Insufficient disk space"

mem = next(
    int(line.split()[1])
    for line in Path("/proc/meminfo").read_text().splitlines()
    if line.startswith("MemAvailable:")
)
assert mem >= 1200000, "STOP: Insufficient memory"

cache.mkdir(parents=True, exist_ok=True)

args = [
    "run", "-d", "--name", name,
    "--network", "host",
    "--read-only",
    "--memory", "1700m",
    "--memory-swap", "1700m",
    "--tmpfs", "/tmp:rw,exec,size=1024m",
    "--tmpfs", "/root:rw,size=16m",
    "--tmpfs", "/run:rw,size=64m",
    "-e", "PYTHONDONTWRITEBYTECODE=1",
    "-e", "PYTHONPATH=/workspace:/workspace/artifacts/v1.168-max:/batch2",
    "-v", f"{repo}:/workspace:ro",
    "-v", f"{overlay}:/workspace/artifacts/v1.168-max/maxserve_cta_extension:ro",
    "-v", f"{candidate}:/batch2:ro",
    "-v", f"{base}/real_max_batch2_backend.py:/batch2/real_max_batch2_backend.py:ro",
    "-v", f"{cache}:/opt/venv/lib/python3.12/site-packages/max/_core_mojo/__mojocache__:rw",
    "-w", "/workspace",
    "--entrypoint", "/opt/venv/bin/python",
    image,
    "-B",
    "/workspace/artifacts/v1.168-max/maxserve_cta_extension/cta_native_batch2_proven_server.py"
]

result = run(args)
assert result.returncode == 0, \
    f"STOP: Container launch failed: {result.stderr}"

print("ISOLATED CONTAINER: CREATED")
print("CONTAINER ID:", result.stdout.strip())
print("MOJO CACHE: APPLICATION1")
print("ORIGINAL MAX: UNCHANGED")
print("ORIGINAL DS: UNCHANGED")
print("HTTP READINESS: NOT YET VERIFIED")
PY
