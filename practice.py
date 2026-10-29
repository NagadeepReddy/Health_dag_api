cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && bash <<'SH'
set -eu

DEV=/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029
STAGE="$DEV/native_batch2_live_stage"
ARCHIVE=/application1/CTA_MAX_NATIVE_CONCURRENT2_PASS_20261029.tar.gz
LOG="$DEV/native_batch2_proven_server_e2e.log"
CAND=/application1/cta_max_true_batch_dev_20261028/batch2_candidate

python3 - <<'PY'
from pathlib import Path
import tarfile, shutil, ast

repo = Path("/application1/sajjna8/rt-pzaas-cta-offers-v1")
dev = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029")
stage = dev / "native_batch2_live_stage"
original = repo / "artifacts/v1.168-max/maxserve_cta_extension"
archive = Path("/application1/CTA_MAX_NATIVE_CONCURRENT2_PASS_20261029.tar.gz")

assert stage.is_dir() and original.is_dir()
assert archive.is_file()

for name in (
    "cta_worker_adapter.py",
    "cta_native_scheduler.py",
    "cta_scheduler_factory.py",
):
    assert (stage / name).is_file(), f"STOP: {name} missing"

# Fill missing supporting modules only in the isolated stage.
for src in original.glob("*.py"):
    dest = stage / src.name
    if not dest.exists():
        shutil.copy2(src, dest)

# Restore the exact previously successful server entry point.
with tarfile.open(archive, "r:gz") as tar:
    member = tar.getmember(
        "release_candidate/cta_native_live_server.py"
    )
    source = tar.extractfile(member).read().decode()

assert "disable_telemetry=True" in source
assert "api_types=[APIType.KSERVE]" in source
assert "CTANativeHTTPPipeline" in source

dest = stage / "cta_native_batch2_proven_server.py"

if dest.exists():
    assert dest.read_text() == source, "STOP: Existing staged server differs"
else:
    dest.write_text(source)

ast.parse(dest.read_text())

print("PROVEN NATIVE SERVER: STAGED")
print("KServe API: PASS")
print("TELEMETRY DISABLED: PASS")
print("STAGED SERVER SYNTAX: PASS")
print("ORIGINAL DS: UNCHANGED")
print("WORKING NATIVE RELEASE: UNCHANGED")
PY

FREE_RAM=$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)
FREE_DISK=$(df -Pk /application1 | awk 'NR==2 {print $4}')

test "$FREE_RAM" -ge 14680064 || {
  echo "STOP: Insufficient available RAM"; exit 1;
}
test "$FREE_DISK" -ge 8388608 || {
  echo "STOP: Insufficient disk"; exit 1;
}

set +e
TMPDIR="$DEV" timeout -k 15s 420s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never \
  --network none \
  --read-only \
  --memory 12g --memory-swap 12g \
  --cpus 2 --pids-limit 256 \
  --tmpfs /tmp:rw,size=1g \
  --tmpfs /root:rw,size=64m \
  --tmpfs /opt/venv/lib/python3.12/site-packages/max/_core_mojo/__mojocache__:rw,size=2g,mode=1777 \
  -v "$PWD:/workspace:ro" \
  -v "$STAGE:/workspace/artifacts/v1.168-max/maxserve_cta_extension:ro" \
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
import urllib.error
import traceback
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

base = Path("/workspace/artifacts/v1.168-max")
script = base / "maxserve_cta_extension/cta_native_batch2_proven_server.py"
server_log = Path("/tmp/cta_proven_server.log")
url = "http://127.0.0.1:8765"

def request(path, body=None, timeout=10):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(
        url + path,
        data=data,
        headers={"Content-Type": "application/json"},
        method="GET" if body is None else "POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read(1500).decode(errors="replace")

with server_log.open("w") as stream:
    server = subprocess.Popen(
        [sys.executable, "-u", "-B", str(script)],
        stdout=stream,
        stderr=subprocess.STDOUT
    )

try:
    print("PROVEN NATIVE MAX SERVER: START", flush=True)

    deadline = time.monotonic() + 200
    ready = False

    while time.monotonic() < deadline:
        if server.poll() is not None:
            raise RuntimeError("Native server exited before readiness")
        try:
            status, _ = request("/health", timeout=2)
            if status == 200:
                ready = True
                break
        except Exception:
            pass
        time.sleep(2)

    assert ready, "STOP: Native server not ready"
    print("NATIVE MAX HTTP HEALTH: PASS", flush=True)

    status, payload = request("/v2/cta/probe", {})
    assert status == 200, f"CTA probe: {status} {payload}"
    print("NATIVE CTA ROUTE: PASS", flush=True)

    inputs = [
        base / "cta_native_adjusted_sanity_input.json",
        base / "test-results/cta_max_tiles_smoketest_input.json",
    ]

    bodies = [json.loads(p.read_text()) for p in inputs]
    assert bodies[0] != bodies[1]

    gate = Barrier(2)

    def send(body):
        gate.wait(timeout=15)
        return request("/v2/cta/predict", body, timeout=175)

    print("CONCURRENT CTA REQUESTS: START", flush=True)

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(send, b) for b in bodies]
        responses = [f.result() for f in futures]

    for i, (status, result) in enumerate(responses, 1):
        print(f"CTA HTTP RESPONSE {i}: {status}", flush=True)
        assert status == 200, str(result)[:800]
        assert isinstance(result, dict)
        assert isinstance(result.get("jsonData"), dict)
        assert isinstance(result["jsonData"].get("prediction"), dict)
        print(f"CTA JSON RESPONSE {i}: PASS", flush=True)

    time.sleep(2)

    text = server_log.read_text(errors="replace")
    marker = "CTA TRUE MAX BATCH-2: TWO JSON RESPONSES PRODUCED"
    count = text.count(marker)

    print("REAL MAX BATCH-2 CALL COUNT:", count, flush=True)

    assert count == 1, (
        "STOP: Exactly one real MAX batch not demonstrated"
    )

    print("LIVE NATIVE MAX TRUE BATCH-2: PASS", flush=True)

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
    print("\n=== SERVER STARTUP ===", flush=True)
    for line in lines[:30]:
        print(line, flush=True)

    print("\n=== SERVER LOG END ===", flush=True)
    for line in lines[-35:]:
        print(line, flush=True)

    print("TEMPORARY SERVER: STOPPED", flush=True)
PY

RC=$?
set -e

echo "=== FINAL RESULT ==="
echo "EXIT CODE: $RC"
echo "LOG: $LOG"
grep -E 'PASS|STOP:|Traceback|Error|RESPONSE|BATCH-2 CALL COUNT' "$LOG" | tail -25 || true
echo "ORIGINAL DS: UNCHANGED"
echo "WORKING NATIVE RELEASE: UNCHANGED"

if [ "$RC" -eq 0 ] &&
   grep -q 'LIVE NATIVE MAX TRUE BATCH-2: PASS' "$LOG"; then
    echo "NATIVE TRUE BATCH-2: PASS"
else
    echo "NATIVE TRUE BATCH-2: NOT VERIFIED"
fi

exit "$RC"
SH
