bash <<'SH'
set -Eeuo pipefail

B=/application1
R=$B/sajjna8/rt-pzaas-cta-offers-v1
E=$B/cta_max_native_release_candidate_20261028
M=$R/artifacts/v1.168-max/cta_native_model
T=$R/artifacts/v1.168-max/test-results
NAME=cta-dual-queue-retest
LOG=$B/cta_dual_queue_retest_20261029.log
P=(podman --root "$B/podman/storage" --runroot /run/containers/storage)

test -s "$E/cta_native_launcher.py"
test -s "$M/cta_real_fp32.safetensors"
test -s "$T/cta_max_tiles_smoketest_input.json"
test -s "$T/cta_max_tiles_response.json"

grep -q '_CTA_EXTRA_RESPONSE_QUEUES' "$E/cta_http_pipeline.py"
grep -q '_CTA_EXTRA_RESPONSE_QUEUES.append(queue)' "$E/cta_router.py"

if "${P[@]}" container exists "$NAME"; then
  echo "STOP: Test container already exists"
  exit 1
fi

cleanup() {
  "${P[@]}" logs "$NAME" > "$LOG" 2>&1 || true
  "${P[@]}" stop -t 5 "$NAME" >/dev/null 2>&1 || true
  "${P[@]}" rm "$NAME" >/dev/null 2>&1 || true
  echo "=== RESPONSE DELIVERY EVENTS ==="
  grep -E 'CTA HTTP RESPONSE DELIVERED|CTA RESPONSE QUEUE SEND|CTA RESPONSE WITHOUT PENDING REQUEST|CTA RESPONSE WORKER LOOP: EXIT' "$LOG" | tail -15 || true
  echo "LOG: $LOG"
}
trap cleanup EXIT

echo "STARTING PATCHED NATIVE MAX SERVE"

"${P[@]}" run -d \
  --name "$NAME" --network bridge \
  -p 127.0.0.1:18084:8000 \
  --memory 12g --memory-swap 12g \
  --cpus 2 --pids-limit 128 --read-only \
  --tmpfs /tmp:rw,size=1g,mode=1777 \
  --tmpfs /opt/venv/lib/python3.12/site-packages/max/_core_mojo/__mojocache__:rw,size=2g,mode=1777 \
  -e HOME=/tmp -e XDG_CACHE_HOME=/tmp -e TMPDIR=/tmp \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -e 'API_TYPES=["openai","sagemaker","kserve"]' \
  -e 'MAX_SERVE_API_TYPES=["openai","sagemaker","kserve"]' \
  -e PYTHONPATH=/workspace/artifacts/v1.168-max:/workspace \
  -v "$R:/workspace:ro" \
  -v "$E:/workspace/artifacts/v1.168-max/maxserve_cta_extension:ro" \
  -w /workspace \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local \
  /workspace/artifacts/v1.168-max/maxserve_cta_extension/cta_native_launcher.py \
  --devices cpu \
  --model-path /workspace/artifacts/v1.168-max/cta_native_model \
  --weight-path /workspace/artifacts/v1.168-max/cta_native_model/cta_real_fp32.safetensors \
  --quantization-encoding float32 \
  --port 8000 >/dev/null

READY=0
for i in $(seq 1 120); do
  STATUS=$(curl --noproxy '*' -s -o /dev/null -w '%{http_code}' \
    --max-time 2 http://127.0.0.1:18084/health || true)
  if [ "$STATUS" = 200 ]; then READY=1; break; fi

  RUNNING=$("${P[@]}" inspect -f '{{.State.Running}}' "$NAME" 2>/dev/null || true)
  if [ "$RUNNING" != true ]; then
    echo "STOP: MAX server exited"
    exit 1
  fi
  sleep 2
done

test "$READY" = 1 || { echo "STOP: MAX server not ready"; exit 1; }

echo "SENDING TWO REAL CTA REQUESTS"

python3 -S -B - "$T" "$B" <<'PY'
import json, sys, time, threading
import urllib.request, urllib.error
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

tests, base = map(Path, sys.argv[1:])
body = (tests / "cta_max_tiles_smoketest_input.json").read_bytes()

baseline = json.loads((tests / "cta_max_tiles_response.json").read_text())
expected = baseline.get("jsonData", baseline)["prediction"]
barrier = threading.Barrier(2)

def send(n):
    barrier.wait()
    start = time.monotonic()
    req = urllib.request.Request(
        "http://127.0.0.1:18084/v2/cta/predict",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(req, timeout=335) as response:
            status, raw = response.status, response.read()
    except urllib.error.HTTPError as exc:
        status, raw = exc.code, exc.read()
    except Exception as exc:
        status, raw = 0, str(exc).encode()

    elapsed = round(time.monotonic() - start, 2)
    (base / f"cta_dual_queue_response_{n}.json").write_bytes(raw)

    try:
        data = json.loads(raw)
        prediction = data.get("jsonData", data)["prediction"]
        parity = prediction == expected
        offers = len(prediction["offerList"])
    except Exception:
        parity, offers = False, None

    return n, status, elapsed, offers, parity

start = time.monotonic()
with ThreadPoolExecutor(max_workers=2) as pool:
    results = list(pool.map(send, (1, 2)))

wall = time.monotonic() - start
print("\n=== DUAL-QUEUE NATIVE CONCURRENCY RESULTS ===")
for n, status, sec, offers, parity in results:
    print(f"REQUEST {n}: HTTP {status} | {sec}s | OFFERS {offers} | PARITY {parity}")

passed = all(s == 200 and p for _, s, _, _, p in results)
print("WALL SECONDS:", round(wall, 2))
print("THROUGHPUT RPS:", round(2 / wall, 4))
print("CONCURRENT-2:", "PASS" if passed else "FAIL")
print("ORIGINAL DS CODE: UNCHANGED BY TEST")

if not passed:
    raise SystemExit(1)
PY
SH
