cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && bash <<'SH'
set -eu

DEV=/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029
STAGE="$DEV/native_batch2_live_stage"
CAND=/application1/cta_max_true_batch_dev_20261028/batch2_candidate
LOG="$DEV/native_true_batch2_kserve_verified.log"

test -s "$STAGE/cta_native_launcher.py"
test -s "$STAGE/cta_router.py"
test -s "$STAGE/cta_worker_adapter.py"
test -s "$STAGE/cta_native_scheduler.py"
test -s "$STAGE/cta_http_pipeline.py"
test -s "$CAND/cta_max/grecbase_fusion_full_head_72_max.py"
test -s artifacts/v1.168-max/cta_native_model/cta_real_fp32.safetensors
test ! -e "$LOG" || { echo "STOP: Log already exists"; exit 1; }

MEM=$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)
DISK=$(df -Pk /application1 | awk 'NR==2 {print $4}')

test "$MEM" -ge 14680064 || { echo "STOP: Insufficient RAM"; exit 1; }
test "$DISK" -ge 20971520 || { echo "STOP: Insufficient disk"; exit 1; }

set +e
TMPDIR="$DEV" timeout -k 15s 420s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never --network none \
  --memory 12g --cpus 4 --pids-limit 256 \
  --tmpfs /tmp:rw,size=512m \
  --tmpfs /root:rw,size=64m \
  -e HOME=/tmp \
  -e XDG_CACHE_HOME=/tmp \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e PYTHONUNBUFFERED=1 \
  -e 'API_TYPES=["openai","sagemaker","kserve"]' \
  -e 'MAX_SERVE_API_TYPES=["openai","sagemaker","kserve"]' \
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
server_log = Path("/tmp/cta_true_batch2_server.log")
url = "http://127.0.0.1:8000"

cmd = [
    sys.executable, "-u", "-B",
    str(base / "maxserve_cta_extension/cta_native_launcher.py"),
    "--model-path", str(base / "cta_native_model"),
    "--weight-path",
    str(base / "cta_native_model/cta_real_fp32.safetensors"),
    "--quantization-encoding", "float32",
    "--devices", "cpu",
    "--port", "8000",
]

def request(path, body=None, timeout=5):
    req = urllib.request.Request(
        url + path,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Content-Type": "application/json"},
        method="POST" if body is not None else "GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as res:
            return res.status, json.loads(res.read())
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read(3000).decode(errors="replace")

with server_log.open("w") as output:
    server = subprocess.Popen(
        cmd, stdout=output, stderr=subprocess.STDOUT
    )

    try:
        print("NATIVE MAX SERVE: STARTING", flush=True)

        ready = False
        for _ in range(90):
            if server.poll() is not None:
                raise RuntimeError(
                    f"MAX server exited: {server.returncode}"
                )
            try:
                status, _ = request("/ready", timeout=2)
                if status == 200:
                    ready = True
                    break
            except Exception:
                pass
            time.sleep(2)

        assert ready, "STOP: Native MAX not ready"
        print("NATIVE MAX READY: PASS", flush=True)

        status, probe = request("/v2/cta/probe", {})
        print("CTA PROBE STATUS:", status, flush=True)
        assert status == 200, "STOP: CTA KServe route unavailable"
        print("NATIVE KSERVE ROUTE: PASS", flush=True)

        body1 = json.loads(
            (base / "cta_native_adjusted_sanity_input.json").read_text()
        )
        body2 = json.loads(
            (base / "test-results/cta_max_tiles_smoketest_input.json").read_text()
        )

        assert body1 != body2
        barrier = Barrier(2)

        def send(body):
            barrier.wait(timeout=15)
            return request("/v2/cta/predict", body, timeout=170)

        print("TWO CONCURRENT CTA REQUESTS: START", flush=True)

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(send, body)
                for body in (body1, body2)
            ]
            responses = [f.result() for f in futures]

        for i, (status, response) in enumerate(responses, 1):
            print(f"HTTP RESPONSE {i}: {status}", flush=True)
            assert status == 200, (
                f"CTA response {i} failed: {str(response)[:500]}"
            )
            assert isinstance(response, dict)
            assert isinstance(response.get("jsonData"), dict)
            prediction = response["jsonData"].get("prediction")
            assert isinstance(prediction, dict)

            offers = prediction.get("offerList")
            print(
                f"CTA RESPONSE {i}: PASS; "
                f"offers={len(offers) if isinstance(offers,list) else 'N/A'}",
                flush=True
            )

        print("TWO REAL NATIVE HTTP RESPONSES: PASS", flush=True)
        time.sleep(2)

        lines = server_log.read_text(errors="replace").splitlines()
        marker = "CTA TRUE MAX BATCH-2: TWO JSON RESPONSES PRODUCED"
        count = sum(marker in line for line in lines)

        print("REAL MAX BATCH-2 EXECUTIONS:", count, flush=True)

        assert count == 1, (
            "STOP: One real batch-2 execution not verified"
        )

        print("BUILT-IN MAX SERVE TRUE BATCH-2 E2E: PASS", flush=True)

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

        print("=== SERVER LOG TAIL ===", flush=True)
        if server_log.exists():
            for line in server_log.read_text(
                errors="replace"
            ).splitlines()[-45:]:
                print(line, flush=True)

        print("TEMPORARY SERVER: STOPPED", flush=True)
PY

RC=$?
set -e

echo "=== RESULT ==="
echo "EXIT CODE: $RC"
echo "LOG: $LOG"

grep -E 'PASS|HTTP RESPONSE|BATCH-2 EXECUTIONS|STOP:|Error|Traceback|404|500|503' "$LOG" | tail -30 || true
tail -8 "$LOG"

if [ "$RC" -eq 0 ] &&
   grep -q 'BUILT-IN MAX SERVE TRUE BATCH-2 E2E: PASS' "$LOG"; then
  echo "NATIVE REAL MAX BATCH-2: PASS"
else
  echo "NATIVE REAL MAX BATCH-2: NOT VERIFIED"
fi

echo "ORIGINAL DS: UNCHANGED"
echo "WORKING NATIVE RELEASE: UNCHANGED"
exit "$RC"
SH
