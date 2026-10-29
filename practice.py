cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && bash <<'SH'
set -eu

DEV=/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029
OVERLAY="$DEV/native_batch2_minimal_overlay"
CAND=/application1/cta_max_true_batch_dev_20261028/batch2_candidate
LOG="$DEV/native_batch2_memory_safe_e2e.log"

RAM=$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)
DISK=$(df -Pk /application1 | awk 'NR==2 {print $4}')

test "$RAM" -ge 16777216 || {
  echo "STOP: Available RAM below 16 GiB"; exit 1;
}
test "$DISK" -ge 6291456 || {
  echo "STOP: Available disk below 6 GiB"; exit 1;
}

test -f "$OVERLAY/cta_native_batch2_proven_server.py"
test -f "$OVERLAY/cta_worker_adapter.py"
test -f "$OVERLAY/cta_native_scheduler.py"
test -d "$CAND"

echo "MEMORY SAFETY: PASS"
echo "MINIMAL BATCH OVERLAY: PRESENT"
echo "STARTING NATIVE MAX HTTP TEST"

set +e
TMPDIR="$DEV" timeout -k 15s 330s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never \
  --network none --read-only \
  --memory 14g --memory-swap 14g \
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
import urllib.request
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

base = Path("/workspace/artifacts/v1.168-max")
script = base / "maxserve_cta_extension/cta_native_batch2_proven_server.py"
log = Path("/tmp/native_server.log")

inputs = [
    base / "cta_native_adjusted_sanity_input.json",
    base / "test-results/cta_max_tiles_smoketest_input.json",
]

assert all(p.is_file() for p in inputs), "STOP: Test JSON missing"
bodies = [json.loads(p.read_text()) for p in inputs]
assert bodies[0] != bodies[1], "STOP: Test requests identical"

def call(path, body=None, timeout=5):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        "http://127.0.0.1:8765" + path,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST" if body is not None else "GET"
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.status, json.loads(response.read())

with log.open("w") as stream:
    server = subprocess.Popen(
        [sys.executable, "-u", "-B", str(script)],
        stdout=stream,
        stderr=subprocess.STDOUT,
    )

try:
    print("NATIVE MAX SERVER: STARTING", flush=True)
    deadline = time.monotonic() + 180

    while time.monotonic() < deadline:
        if server.poll() is not None:
            raise RuntimeError("STOP: Server exited")
        try:
            status, _ = call("/health")
            if status == 200:
                break
        except Exception:
            pass
        time.sleep(2)
    else:
        raise RuntimeError("STOP: HTTP readiness not reached")

    print("NATIVE MAX HTTP HEALTH: PASS", flush=True)

    gate = Barrier(2)

    def send(body):
        gate.wait(timeout=15)
        return call("/v2/cta/predict", body, timeout=110)

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(send, b) for b in bodies]
        responses = [f.result() for f in futures]

    for i, (status, result) in enumerate(responses, 1):
        assert status == 200
        assert isinstance(result, dict)
        assert isinstance(result.get("jsonData"), dict)
        assert isinstance(result["jsonData"].get("prediction"), dict)
        print(f"CTA HTTP JSON {i}: PASS", flush=True)

    marker = "CTA TRUE MAX BATCH-2: TWO JSON RESPONSES PRODUCED"
    count = log.read_text(errors="replace").count(marker)

    print("REAL MAX BATCH EXECUTIONS:", count, flush=True)
    assert count == 1, "STOP: One real batch not verified"

    print("NATIVE HTTP TRUE MAX BATCH-2: PASS", flush=True)

finally:
    if server.poll() is None:
        server.terminate()
        try:
            server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait()

    lines = log.read_text(errors="replace").splitlines()
    print("=== SERVER LOG LAST 35 LINES ===", flush=True)
    for line in lines[-35:]:
        print(line, flush=True)
    print("TEMPORARY SERVER: STOPPED", flush=True)
PY

RC=$?
set -e

echo "=== FINAL RESULT ==="
echo "EXIT CODE: $RC"
echo "LOG: $LOG"
grep -E 'PASS|STOP:|Error|Traceback|EXECUTIONS|HEALTH' "$LOG" | tail -25 || true
echo "ORIGINAL DS: UNCHANGED"
echo "WORKING NATIVE RELEASE: UNCHANGED"

if [ "$RC" -eq 0 ] &&
   grep -q 'NATIVE HTTP TRUE MAX BATCH-2: PASS' "$LOG"; then
  echo "FINAL NATIVE BATCH-2: PASS"
else
  echo "FINAL NATIVE BATCH-2: NOT VERIFIED"
fi
SH
