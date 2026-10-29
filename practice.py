cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && bash <<'SH'
set -eu

DEV=/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029
STAGE="$DEV/native_batch2_live_stage"
CAND=/application1/cta_max_true_batch_dev_20261028/batch2_candidate
LOG="$DEV/native_batch2_kserve_http_test.log"

test -s "$STAGE/cta_native_launcher.py"
test -s "$STAGE/cta_router.py"
test -s "$STAGE/cta_worker_adapter.py"
test -s "$CAND/cta_max/grecbase_fusion_full_head_72_max.py"
test ! -e "$LOG" || { echo "STOP: Log already exists"; exit 1; }

MEM=$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)
DISK=$(df -Pk /application1 | awk 'NR==2 {print $4}')

test "$MEM" -ge 14680064 || { echo "STOP: RAM below 14 GiB"; exit 1; }
test "$DISK" -ge 20971520 || { echo "STOP: Disk below 20 GiB"; exit 1; }

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
import traceback
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

base = Path("/workspace/artifacts/v1.168-max")
url = "http://127.0.0.1:8000"
server_log = Path("/tmp/cta_kserve_server.log")

cmd = [
    sys.executable, "-u", "-B",
    str(base / "maxserve_cta_extension/cta_native_launcher.py"),
    "--model-path", str(base / "cta_native_model"),
    "--weight-path",
    str(base / "cta_native_model/cta_real_fp32.safetensors"),
    "--quantization-encoding", "float32",
    "--devices", "cpu",
    "--api-type", "kserve",
    "--port", "8000",
]

def call(path, body=None, timeout=5):
    request = urllib.request.Request(
        url + path,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Content-Type": "application/json"},
        method="POST" if body is not None else "GET"
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as error:
        return error.code, error.read(2000).decode(errors="replace")

with server_log.open("w") as output:
    server = subprocess.Popen(
        cmd, stdout=output, stderr=subprocess.STDOUT
    )

    try:
        print("BUILT-IN MAX KSERVE: START", flush=True)
        ready = False

        for _ in range(90):
            if server.poll() is not None:
                raise RuntimeError(
                    f"Server exited with {server.returncode}"
                )
            try:
                status, _ = call("/ready", timeout=2)
                if status == 200:
                    ready = True
                    break
            except Exception:
                pass
            time.sleep(2)

        assert ready, "STOP: MAX server not ready"
        print("NATIVE MAX HTTP READY: PASS", flush=True)

        status, probe = call("/v2/cta/probe", {})
        print("CTA PROBE STATUS:", status, flush=True)
        print("CTA PROBE RESPONSE:", probe, flush=True)

        assert status == 200, (
            "STOP: KServe CTA route not registered"
        )
        assert isinstance(probe, dict)
        print("NATIVE CTA ROUTE REGISTRATION: PASS", flush=True)

        fixture1 = base / "cta_native_adjusted_sanity_input.json"
        fixture2 = base / "test-results/cta_max_tiles_smoketest_input.json"

        body1 = json.loads(fixture1.read_text())
        body2 = json.loads(fixture2.read_text())

        gate = Barrier(2)

        def send(body):
            gate.wait(timeout=10)
            return call("/v2/cta/predict", body, timeout=160)

        print("CONCURRENT NATIVE CTA REQUESTS: START", flush=True)

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(send, body)
                for body in (body1, body2)
            ]
            results = [future.result() for future in futures]

        for i, (status, response) in enumerate(results, 1):
            print(f"HTTP RESPONSE {i}: {status}", flush=True)
            if isinstance(response, dict):
                print("RESPONSE KEYS:", sorted(response), flush=True)
            else:
                print("RESPONSE:", str(response)[:500], flush=True)

            assert status == 200, f"CTA request {i} failed"
            assert isinstance(response, dict)
            assert isinstance(response.get("jsonData"), dict)
            assert isinstance(
                response["jsonData"].get("prediction"), dict
            )
            print(f"NATIVE CTA RESPONSE {i}: PASS", flush=True)

        print("TWO NATIVE CTA HTTP RESPONSES: PASS", flush=True)

        # Allow buffered worker output to arrive.
        time.sleep(2)

        lines = server_log.read_text(errors="replace").splitlines()
        marker = "CTA TRUE MAX BATCH-2: TWO JSON RESPONSES PRODUCED"
        batch_count = sum(marker in line for line in lines)

        print("REAL MAX BATCH EXECUTIONS:", batch_count, flush=True)
        assert batch_count == 1, (
            "STOP: Exactly one real MAX batch not verified"
        )

        print("LIVE BUILT-IN MAX BATCH-2: PASS", flush=True)

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

        print("=== NATIVE SERVER LOG TAIL ===", flush=True)
        if server_log.exists():
            for line in server_log.read_text(
                errors="replace"
            ).splitlines()[-55:]:
                print(line, flush=True)

        print("TEMPORARY SERVER: STOPPED", flush=True)
PY

RC=$?
set -e

echo "=== RESULT ==="
echo "EXIT CODE: $RC"
echo "LOG: $LOG"

grep -E 'PASS|HTTP RESPONSE|PROBE|BATCH EXECUTIONS|STOP:|Traceback|Error|error|404|500|503|Server exited' "$LOG" | tail -35 || true
tail -12 "$LOG"

if [ "$RC" -eq 0 ] &&
   grep -q 'LIVE BUILT-IN MAX BATCH-2: PASS' "$LOG"; then
  echo "NATIVE MAX SERVE BATCH-2: PASS"
else
  echo "NATIVE MAX SERVE BATCH-2: NOT YET VERIFIED"
fi

echo "ORIGINAL DS: UNCHANGED"
echo "WORKING NATIVE RELEASE: UNCHANGED"
exit "$RC"
SH
