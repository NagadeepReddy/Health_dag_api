python3 - <<'PY'
import subprocess, json, urllib.request
from pathlib import Path

pod = [
    "podman", "--root", "/application1/podman/storage",
    "--runroot", "/run/containers/storage"
]
name = "cta-batch2-trace-8766-v2"
overlay = "/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029/native_batch2_cached_overlay"

def run(args):
    r = subprocess.run(
        pod + args, capture_output=True, text=True
    )
    if r.returncode:
        raise SystemExit("STOP: " + (r.stderr or r.stdout))
    return r.stdout.strip()

info = json.loads(run(["inspect", name]))[0]
state = info["State"]

assert state["Status"] == "exited", "STOP: Container not stopped"
assert state.get("OOMKilled") is True, "STOP: OOM not confirmed"
assert any(
    m.get("Source") == overlay for m in info["Mounts"]
), "STOP: Container identity mismatch"

available = next(
    int(x.split()[1])
    for x in Path("/proc/meminfo").read_text().splitlines()
    if x.startswith("MemAvailable:")
)

assert available >= 10 * 1024 * 1024, "STOP: Insufficient available memory"

with urllib.request.urlopen(
    "http://127.0.0.1:8765/health", timeout=10
) as r:
    assert r.status == 200, "STOP: Original MAX unhealthy"

ports = subprocess.run(
    ["ss", "-H", "-ltn", "( sport = :8766 )"],
    capture_output=True, text=True, check=True
)
assert not ports.stdout.strip(), "STOP: Port 8766 occupied"

print("MEMORY FIX: APPLYING", flush=True)

run([
    "update",
    "--memory", "6g",
    "--memory-swap", "6g",
    name
])

print("MEMORY LIMIT: 6 GB")
print("RESTARTING ISOLATED MAX", flush=True)

run(["start", name])

print("ISOLATED MAX: START REQUESTED")
print("ORIGINAL MAX: UNCHANGED")
print("ORIGINAL DS: UNCHANGED")
print("HTTP READINESS: PENDING")
PY
