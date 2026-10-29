cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && bash <<'SH'
set -eu

DEV=/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029
STAGE="$DEV/native_batch2_live_stage"
CAND=/application1/cta_max_true_batch_dev_20261028/batch2_candidate
LOG="$DEV/native_batch2_live_http_test.log"

test -s "$STAGE/cta_native_launcher.py"
test -s "$STAGE/cta_worker_adapter.py"
test -s "$STAGE/cta_native_scheduler.py"
test -s "$CAND/cta_max/grecbase_fusion_full_head_72_max.py"
test -s artifacts/v1.168-max/cta_native_model/cta_real_fp32.safetensors
test ! -e "$LOG" || { echo "STOP: Log exists"; exit 1; }

MEM=$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)
DISK=$(df -Pk /application1 | awk 'NR==2 {print $4}')

test "$MEM" -ge 14680064 || { echo "STOP: Low RAM"; exit 1; }
test "$DISK" -ge 20971520 || { echo "STOP: Low disk"; exit 1; }

set +e
TMPDIR="$DEV" timeout -k 15s 420s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --network none \
  --memory 12g --cpus 4 --pids-limit 256 \
  --tmpfs /tmp:rw,size=512m \
  --tmpfs /root:rw,size=64m \
  -e HOME=/tmp \
  -e XDG_CACHE_HOME=/tmp \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e PYTHONUNBUFFERED=1 \
  -e modelId=rt-pzaas-cta-offers-v1 \
  -e expThrottleLabel=T \
  -e PYTHONPATH="$CAND:/workspace/artifacts/v1.168/core-artifact:/workspace/artifacts/v1.168-max:/batch2" \
  -v "$PWD:/workspace:ro" \
  -v "$STAGE:/workspace/artifacts/v1.168-max/maxserve_cta_extension:ro" \
  -v "$DEV:/batch2:ro" \
  -v "$CAND:$CAND:ro" \
  -w /workspace \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  -u -B - > "$LOG" 2>&1 <<'PY'
import json
import subprocess
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

base = Path("/workspace/artifacts/v1.168-max")
server_log = Path("/tmp/cta_native_server.log")

cmd = [
    sys.executable, "-u", "-B",
    str(base / "maxserve_cta_extension/cta_native_launcher.py"),
    "--model-path", str(base / "cta_native_model"),
    "--weight-path", str(base / "cta_native_model/cta_real_fp32.safetensors"),
    "--quantization-encoding", "float32",
    "--devices", "cpu",
    "--port", "8000",
]

print("BUILT-IN MAX SERVE: STARTING", flush=True)
print("ISOLATED NETWORK: YES", flush=True)

with server_log.open("w") as output:
    process = subprocess.Popen(
        cmd, stdout=output, stderr=subprocess.STDOUT
    )

    try:
        ready = False
        start = time.monotonic()

        while time.monotonic() - start < 180:
            if process.poll() is not None:
                raise RuntimeError(
                    f"MAX server exited: {process.returncode}"
                )

            for endpoint in ("/ready", "/health"):
                try:
                    with urllib.request.urlopen(
                        "http://127.0.0.1:8000" + endpoint,
                        timeout=2
                    ) as response:
                        if response.status == 200:
                            ready = True
                            break
                except Exception:
                    pass

            if ready:
                break
            time.sleep(2)

        assert ready, "STOP: Native MAX server not ready"
        print("NATIVE MAX HTTP READY: PASS", flush=True)

        routes = []
        try:
            with urllib.request.urlopen(
                "http://127.0.0.1:8000/openapi.json",
                timeout=5
            ) as response:
                schema = json.load(response)
                routes = [
                    p for p in schema.get("paths", {})
                    if p.endswith("/cta/predict")
                    or p.endswith("/cta/infer")
                ]
        except Exception:
            pass

        route = routes[0] if routes else "/v2/cta/predict"
        print("CTA HTTP ROUTE:", route, flush=True)

        body1 = json.loads(
            (base / "cta_native_adjusted_sanity_input.json").read_text()
        )
        body2 = json.loads(
            (base / "test-results/cta_max_tiles_smoketest_input.json").read_text()
        )

        gate = Barrier(2)

        def send(body):
            gate.wait(timeout=10)
            request = urllib.request.Request(
                "http://127.0.0.1:8000" + route,
                data=json.dumps(body).encode(),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            try:
                with urllib.request.urlopen(request, timeout=145) as res:
                    return res.status, json.loads(res.read())
            except urllib.error.HTTPError as error:
                return error.code, {
                    "error": error.read(2000).decode(errors="replace")
                }

        print("TWO CONCURRENT CTA REQUESTS: START", flush=True)

        with ThreadPoolExecutor(max_workers=2) as pool:
            jobs = [pool.submit(send, body) for body in (body1, body2)]
            responses = [job.result() for job in jobs]

        for i, (status, response) in enumerate(responses, 1):
            print(f"HTTP RESPONSE {i}: {status}", flush=True)
            print(f"RESPONSE {i} KEYS:", sorted(response), flush=True)
            assert status == 200, f"Request {i} failed"
            assert isinstance(response.get("jsonData"), dict)
            assert isinstance(
                response["jsonData"].get("prediction"), dict
            )

        print("TWO NATIVE CTA HTTP RESPONSES: PASS", flush=True)

    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()

print("=== NATIVE SERVER LOG TAIL ===", flush=True)
lines = server_log.read_text(errors="replace").splitlines()
for line in lines[-65:]:
    print(line, flush=True)

batch_count = sum(
    "CTA TRUE MAX BATCH-2: TWO JSON RESPONSES PRODUCED" in line
    for line in lines
)
print("REAL MAX BATCH EXECUTION MARKERS:", batch_count, flush=True)

assert batch_count == 1, "STOP: Exactly one batch execution not verified"
print("LIVE BUILT-IN MAX SERVE BATCH-2: PASS", flush=True)
PY

RC=$?
set -e

echo "=== RESULT ==="
echo "EXIT CODE: $RC"
echo "LOG: $LOG"
tail -65 "$LOG"

if [ "$RC" -eq 0 ] &&
   grep -q 'LIVE BUILT-IN MAX SERVE BATCH-2: PASS' "$LOG"; then
  echo "NATIVE HTTP BATCH-2: PASS"
else
  echo "NATIVE HTTP BATCH-2: NOT VALIDATED"
fi

echo "ORIGINAL DS: UNCHANGED"
echo "WORKING NATIVE RELEASE: UNCHANGED"
exit "$RC"
SH
