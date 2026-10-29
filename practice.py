cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && bash <<'SH'
set -eu

DEV=/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029
STAGE="$DEV/native_batch2_live_stage"
CAND=/application1/cta_max_true_batch_dev_20261028/batch2_candidate
LOG="$DEV/native_batch2_bridge_final.log"

test -s "$STAGE/cta_native_launcher.py"
test -s "$STAGE/cta_worker_adapter.py"
test -s "$STAGE/cta_native_scheduler.py"
test -s "$STAGE/cta_router.py"
test -s "$CAND/cta_max/grecbase_fusion_full_head_72_max.py"
test ! -e "$LOG" || { echo "STOP: Log already exists"; exit 1; }

MEM=$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)
DISK=$(df -Pk /application1 | awk 'NR==2 {print $4}')
test "$MEM" -ge 14680064 || { echo "STOP: Low RAM"; exit 1; }
test "$DISK" -ge 20971520 || { echo "STOP: Low disk"; exit 1; }

set +e
TMPDIR="$DEV" timeout -k 15s 480s podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  run --rm -i --pull=never \
  --network bridge \
  -p 127.0.0.1:18084:8000 \
  --memory 12g --memory-swap 12g \
  --cpus 2 --pids-limit 256 \
  --read-only \
  --tmpfs /tmp:rw,size=1g \
  --tmpfs /root:rw,size=64m \
  --tmpfs /opt/venv/lib/python3.12/site-packages/max/_core_mojo/__mojocache__:rw,size=2g,mode=1777 \
  -e HOME=/tmp \
  -e TMPDIR=/tmp \
  -e XDG_CACHE_HOME=/tmp \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e PYTHONUNBUFFERED=1 \
  -e 'API_TYPES=["openai","sagemaker","kserve"]' \
  -e 'MAX_SERVE_API_TYPES=["openai","sagemaker","kserve"]' \
  -e modelId=rt-pzaas-cta-offers-v1 \
  -e expThrottleLabel=T \
  -e PYTHONPATH="$CAND:/workspace/artifacts/v1.168/core-artifact:/workspace/artifacts/v1.168-max:/batch2:/workspace" \
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
import traceback
import urllib.request
import urllib.error
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

base = Path("/workspace/artifacts/v1.168-max")
server_log = Path("/tmp/cta_batch2_server.log")
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
        method="POST" if body is not None else "GET"
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as res:
            return res.status, json.loads(res.read())
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read(1500).decode(errors="replace")

with server_log.open("w") as output:
    server = subprocess.Popen(
        cmd, stdout=output, stderr=subprocess.STDOUT
    )

    try:
        print("NATIVE BATCH-2 HTTP TEST: START", flush=True)
        ready = False
        deadline = time.monotonic() + 220

        while time.monotonic() < deadline:
            if server.poll() is not None:
                raise RuntimeError(
                    f"Native server exited: {server.returncode}"
                )
            try:
                status, _ = request("/health", timeout=2)
                if status == 200:
                    ready = True
                    break
            except Exception:
                pass
            time.sleep(2)

        assert ready, "STOP: Native MAX HTTP not ready"
        print("NATIVE MAX HTTP HEALTH: PASS", flush=True)

        status, probe = request("/v2/cta/probe", {})
        assert status == 200, f"CTA probe failed: {probe}"
        print("NATIVE CTA KSERVE ROUTE: PASS", flush=True)

        body1 = json.loads(
            (base / "cta_native_adjusted_sanity_input.json").read_text()
        )
        body2 = json.loads(
            (base / "test-results/cta_max_tiles_smoketest_input.json").read_text()
        )
        assert body1 != body2

        gate = Barrier(2)

        def send(body):
            gate.wait(timeout=15)
            return request("/v2/cta/predict", body, timeout=180)

        print("TWO CONCURRENT CTA HTTP REQUESTS: START", flush=True)

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [
                pool.submit(send, body)
                for body in (body1, body2)
            ]
            responses = [f.result() for f in futures]

        for i, (status, payload) in enumerate(responses, 1):
            print(f"CTA HTTP {i}: {status}", flush=True)
            assert status == 200, (
                f"CTA request {i}: {str(payload)[:600]}"
            )
            assert isinstance(payload, dict)
            assert isinstance(payload.get("jsonData"), dict)
            assert isinstance(
                payload["jsonData"].get("prediction"), dict
            )
            print(f"CTA JSON RESPONSE {i}: PASS", flush=True)

        time.sleep(2)
        lines = server_log.read_text(errors="replace").splitlines()
        marker = "CTA TRUE MAX BATCH-2: TWO JSON RESPONSES PRODUCED"
        count = sum(marker in line for line in lines)

        print("REAL MAX BATCH EXECUTIONS:", count, flush=True)
        assert count == 1, (
            "STOP: Exactly one real MAX batch not verified"
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

        print("=== NATIVE SERVER LOG TAIL ===", flush=True)
        for line in server_log.read_text(
            errors="replace"
        ).splitlines()[-40:]:
            print(line, flush=True)

        print("TEMPORARY SERVER: STOPPED", flush=True)
PY

RC=$?
set -e

echo "=== RESULT ==="
echo "EXIT CODE: $RC"
echo "LOG: $LOG"
grep -E 'PASS|HTTP|BATCH EXECUTIONS|STOP:|Traceback|Error|error' "$LOG" | tail -30 || true
tail -8 "$LOG"

if [ "$RC" -eq 0 ] &&
   grep -q 'LIVE NATIVE MAX TRUE BATCH-2: PASS' "$LOG"; then
  echo "NATIVE MAX TRUE BATCH-2: PASS"
else
  echo "NATIVE MAX TRUE BATCH-2: NOT VERIFIED"
fi

echo "ORIGINAL DS: UNCHANGED"
echo "WORKING NATIVE RELEASE: UNCHANGED"
exit "$RC"
SH
