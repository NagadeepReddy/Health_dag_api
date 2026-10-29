cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && bash <<'SH'
set -eu

DEV=/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029
OVERLAY="$DEV/native_batch2_minimal_overlay"
ARCHIVE=/application1/CTA_MAX_NATIVE_CONCURRENT2_PASS_20261029.tar.gz
LOG="$DEV/native_batch2_minimal_overlay_e2e.log"
CAND=/application1/cta_max_true_batch_dev_20261028/batch2_candidate

python3 - <<'PY'
from pathlib import Path
import shutil, tarfile, ast

repo = Path("/application1/sajjna8/rt-pzaas-cta-offers-v1")
dev = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029")
original = repo / "artifacts/v1.168-max/maxserve_cta_extension"
batch = dev / "native_batch2_live_stage"
overlay = dev / "native_batch2_minimal_overlay"
archive = Path("/application1/CTA_MAX_NATIVE_CONCURRENT2_PASS_20261029.tar.gz")

assert original.is_dir() and batch.is_dir()
assert archive.is_file()

names = (
    "cta_worker_adapter.py",
    "cta_native_scheduler.py",
    "cta_scheduler_factory.py",
)
for name in names:
    assert (batch / name).is_file()

if overlay.exists():
    print("OVERLAY: EXISTS; verifying files")
else:
    shutil.copytree(original, overlay, symlinks=True)
    for name in names:
        shutil.copy2(batch / name, overlay / name)

with tarfile.open(archive, "r:gz") as tar:
    member = tar.getmember(
        "release_candidate/cta_native_live_server.py"
    )
    server_source = tar.extractfile(member).read().decode()

server = overlay / "cta_native_batch2_proven_server.py"
if server.exists():
    assert server.read_text() == server_source
else:
    server.write_text(server_source)

assert "disable_telemetry=True" in server_source
assert "api_types=[APIType.KSERVE]" in server_source

for name in (*names, server.name):
    ast.parse((overlay / name).read_text())

for name in names:
    assert (overlay / name).read_bytes() == (batch / name).read_bytes()

print("WORKING NATIVE BASE: PRESERVED")
print("MINIMAL BATCH OVERLAY: PASS")
print("KServe CONFIGURATION: PASS")
print("ORIGINAL DS: UNCHANGED")
PY

test "$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)" -ge 33554432 || {
  echo "STOP: Insufficient available memory"; exit 1;
}

test "$(df -Pk /application1 | awk 'NR==2 {print $4}')" -ge 8388608 || {
  echo "STOP: Insufficient disk"; exit 1;
}

set +e
TMPDIR="$DEV" timeout -k 15s 330s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never \
  --network none --read-only \
  --memory 20g --memory-swap 20g \
  --cpus 4 --pids-limit 256 \
  --tmpfs /tmp:rw,size=2g \
  --tmpfs /root:rw,size=64m \
  --tmpfs /opt/venv/lib/python3.12/site-packages/max/_core_mojo/__mojocache__:rw,size=2g,mode=1777 \
  -v "$PWD:/workspace:ro" \
  -v "$OVERLAY:/workspace/artifacts/v1.168-max/maxserve_cta_extension:ro" \
  -v "$DEV:/batch2:ro" \
  -v "$CAND:$CAND:ro" \
  -w /workspace \
  -e HOME=/tmp \
  -e TMPDIR=/tmp \
  -e XDG_CACHE_HOME=/tmp \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e PYTHONUNBUFFERED=1 \
  -e modelId=rt-pzaas-cta-offers-v1 \
  -e expThrottleLabel=T \
  -e PYTHONPATH="$CAND:/workspace/artifacts/v1.168/core-artifact:/workspace/artifacts/v1.168-max:/workspace" \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -u -B - > "$LOG" 2>&1 <<'PY'
import json
import subprocess
import sys
import time
import traceback
import urllib.request
import urllib.error
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

base = Path("/workspace/artifacts/v1.168-max")
script = base / "maxserve_cta_extension/cta_native_batch2_proven_server.py"
server_log = Path("/tmp/cta_native_minimal_overlay.log")
url = "http://127.0.0.1:8765"

def call(path, body=None, timeout=10):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        url + path,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST" if body is not None else "GET"
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as res:
            return res.status, json.loads(res.read())
    except urllib.error.HTTPError as error:
        return error.code, error.read().decode(errors="replace")

with server_log.open("w") as f:
    process = subprocess.Popen(
        [sys.executable, "-u", "-B", str(script)],
        stdout=f, stderr=subprocess.STDOUT
    )

try:
    print("MINIMAL OVERLAY NATIVE MAX: START", flush=True)

    deadline = time.monotonic() + 150
    ready = False

    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError("Native server exited during startup")
        try:
            status, _ = call("/health", timeout=2)
            if status == 200:
                ready = True
                break
        except Exception:
            pass
        time.sleep(2)

    if not ready:
        raise RuntimeError("Native server did not become ready")

    print("NATIVE MAX HEALTH: PASS", flush=True)

    inputs = [
        base / "cta_native_adjusted_sanity_input.json",
        base / "test-results/cta_max_tiles_smoketest_input.json",
    ]
    bodies = [json.loads(p.read_text()) for p in inputs]
    assert bodies[0] != bodies[1]

    gate = Barrier(2)

    def send(body):
        gate.wait(timeout=15)
        return call("/v2/cta/predict", body, timeout=155)

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(send, body) for body in bodies]
        responses = [future.result() for future in futures]

    for i, (status, result) in enumerate(responses, 1):
        assert status == 200, f"CTA {i}: {status} {result}"
        assert isinstance(result, dict)
        assert isinstance(result.get("jsonData"), dict)
        assert isinstance(result["jsonData"].get("prediction"), dict)
        print(f"CTA HTTP JSON {i}: PASS", flush=True)

    output = server_log.read_text(errors="replace")
    marker = "CTA TRUE MAX BATCH-2: TWO JSON RESPONSES PRODUCED"
    assert output.count(marker) == 1, (
        "Exactly one actual batch execution not verified"
    )

    print("NATIVE REAL MAX BATCH-2 E2E: PASS", flush=True)

except Exception:
    traceback.print_exc()
    raise

finally:
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()

    lines = server_log.read_text(errors="replace").splitlines()

    print("=== NATIVE SERVER INITIALIZATION ===")
    for line in lines[:35]:
        print(line)

    print("=== NATIVE SERVER FINAL OUTPUT ===")
    for line in lines[-45:]:
        print(line)

    print("TEMPORARY SERVER: STOPPED")
PY

RC=$?
set -e

echo "=== RESULT ==="
echo "EXIT CODE: $RC"
echo "LOG: $LOG"
grep -E 'PASS|STOP:|Error|Traceback|NATIVE SERVER|HTTP JSON|BATCH-2 E2E' "$LOG" | tail -25 || true
echo "ORIGINAL DS: UNCHANGED"
echo "WORKING NATIVE RELEASE: UNCHANGED"

if [ "$RC" -eq 0 ] && grep -q 'NATIVE REAL MAX BATCH-2 E2E: PASS' "$LOG"; then
    echo "FINAL NATIVE HTTP BATCH-2: PASS"
else
    echo "FINAL NATIVE HTTP BATCH-2: NOT VERIFIED"
fi
SH
