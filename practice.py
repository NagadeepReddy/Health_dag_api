cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && bash <<'SH'
set -eu

DEV=/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029
OVERLAY="$DEV/native_batch2_minimal_overlay"
CAND=/application1/cta_max_true_batch_dev_20261028/batch2_candidate
RUNNER="$DEV/native_http_batch2_healthfix_runner.py"
LOG="$DEV/native_http_batch2_healthfix.log"

test -f "$OVERLAY/cta_native_batch2_proven_server.py"
test -d "$CAND"

RAM=$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)
test "$RAM" -ge 16777216 || {
  echo "STOP: Available RAM below 16 GiB"
  exit 1
}

test ! -e "$RUNNER" || {
  echo "STOP: Development test runner already exists"
  exit 1
}

cat > "$RUNNER" <<'PY'
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
server_log = Path("/tmp/cta_native_server.log")
url = "http://127.0.0.1:8765"

def call(path, body=None, timeout=5):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        url + path,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST" if body is not None else "GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw = response.read()
            return response.status, json.loads(raw) if raw.strip() else {}
    except urllib.error.HTTPError as error:
        raw = error.read()
        try:
            detail = json.loads(raw) if raw.strip() else {}
        except ValueError:
            detail = raw.decode(errors="replace")
        return error.code, detail

inputs = [
    base / "cta_native_adjusted_sanity_input.json",
    base / "test-results/cta_max_tiles_smoketest_input.json",
]

assert all(p.is_file() for p in inputs), "STOP: CTA input JSON missing"

bodies = [json.loads(p.read_text()) for p in inputs]
assert bodies[0] != bodies[1], "STOP: Identical CTA requests"

with server_log.open("w") as stream:
    server = subprocess.Popen(
        [sys.executable, "-u", "-B", str(script)],
        stdout=stream,
        stderr=subprocess.STDOUT,
    )

try:
    print("NATIVE MAX SERVER: START", flush=True)

    deadline = time.monotonic() + 150

    while time.monotonic() < deadline:
        if server.poll() is not None:
            raise RuntimeError("STOP: Native server exited")

        try:
            status, _ = call("/health", timeout=2)
            if status == 200:
                print("NATIVE HTTP HEALTH: PASS", flush=True)
                break
        except Exception:
            pass

        time.sleep(2)
    else:
        raise RuntimeError("STOP: Server readiness not reached")

    status, result = call("/v2/cta/probe", {})
    assert status == 200, f"CTA route: {status} {result}"
    print("NATIVE CTA ROUTE: PASS", flush=True)

    gate = Barrier(2)

    def send(body):
        gate.wait(timeout=15)
        return call("/v2/cta/predict", body, timeout=120)

    print("TWO CONCURRENT CTA REQUESTS: START", flush=True)

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(send, body) for body in bodies]
        responses = [future.result() for future in futures]

    for i, (status, result) in enumerate(responses, 1):
        print(f"CTA HTTP STATUS {i}: {status}", flush=True)
        if status != 200:
            print(f"CTA ERROR {i}: {str(result)[:700]}", flush=True)
        assert status == 200
        assert isinstance(result, dict)
        assert isinstance(result.get("jsonData"), dict)
        assert isinstance(result["jsonData"].get("prediction"), dict)
        print(f"CTA JSON RESPONSE {i}: PASS", flush=True)

    text = server_log.read_text(errors="replace")
    marker = "CTA TRUE MAX BATCH-2: TWO JSON RESPONSES PRODUCED"
    count = text.count(marker)

    print("OBSERVED REAL MAX BATCH EXECUTIONS:", count, flush=True)

    assert count == 1, "STOP: One real batch not demonstrated"

    print("NATIVE HTTP REAL MAX BATCH-2: PASS", flush=True)

except Exception:
    traceback.print_exc()
    raise

finally:
    if server.poll() is None:
        server.terminate()
        try:
            server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait()

    lines = server_log.read_text(errors="replace").splitlines()

    print("=== SERVER STARTUP LOG ===", flush=True)
    for line in lines[:45]:
        print(line, flush=True)

    print("=== SERVER FINAL LOG ===", flush=True)
    for line in lines[-55:]:
        print(line, flush=True)

    print("TEMPORARY SERVER: STOPPED", flush=True)
PY

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
  -u -B /batch2/native_http_batch2_healthfix_runner.py \
  > "$LOG" 2>&1

RC=$?
set -e

echo "=== RESULT ==="
echo "EXIT CODE: $RC"
echo "LOG: $LOG"
grep -E 'PASS|STOP:|Traceback|Error|HTTP STATUS|BATCH EXECUTIONS|NATIVE MAX SERVER' "$LOG" | tail -35 || true

echo "ORIGINAL DS: UNCHANGED"
echo "WORKING NATIVE RELEASE: UNCHANGED"

if [ "$RC" -eq 0 ] &&
   grep -q 'NATIVE HTTP REAL MAX BATCH-2: PASS' "$LOG"; then
  echo "FINAL NATIVE BATCH-2: PASS"
else
  echo "FINAL NATIVE BATCH-2: NOT VERIFIED"
fi
SH
