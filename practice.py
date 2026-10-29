bash <<'SH'
set -Eeuo pipefail

B=/application1
R=$B/sajjna8/rt-pzaas-cta-offers-v1
E=$B/cta_max_native_release_candidate_20261028
M=$R/artifacts/v1.168-max/cta_native_model
T=$R/artifacts/v1.168-max/test-results
NAME=cta-native-concurrency-final
LOG=$B/cta_native_concurrency_final.log
P=(podman --root /application1/podman/storage --runroot /run/containers/storage)

test -s "$T/cta_max_tiles_smoketest_input.json"
test -s "$T/cta_max_tiles_response.json"
test -s "$M/cta_real_fp32.safetensors"
test -s "$E/cta_native_launcher.py"

if "${P[@]}" container exists "$NAME"; then
  echo "STOP: Test container already exists"
  exit 1
fi

cleanup() {
  "${P[@]}" logs "$NAME" > "$LOG" 2>&1 || true
  "${P[@]}" stop -t 5 "$NAME" >/dev/null 2>&1 || true
  "${P[@]}" rm "$NAME" >/dev/null 2>&1 || true
  echo "LOG: $LOG"
  grep -E 'CTA PREDICT_RAW: ELAPSED|CTA RESPONSE QUEUE SEND|ERROR|Traceback' "$LOG" | tail -12 || true
}
trap cleanup EXIT

echo "STARTING NATIVE MAX CPU CONCURRENCY TEST"

"${P[@]}" run -d \
  --name "$NAME" --network bridge \
  -p 127.0.0.1:18082:8000 \
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
  STATUS=$(curl -s -o /dev/null -w '%{http_code}' \
    --max-time 2 http://127.0.0.1:18082/health || true)

  if [ "$STATUS" = 200 ]; then
    READY=1
    break
  fi

  RUNNING=$("${P[@]}" inspect -f '{{.State.Running}}' "$NAME" 2>/dev/null || true)
  if [ "$RUNNING" != true ]; then
    echo "STOP: Server exited during startup"
    exit 1
  fi
  sleep 2
done

test "$READY" = 1 || { echo "STOP: Server not ready"; exit 1; }

echo "NATIVE SERVER: READY"
echo "SENDING TWO SIMULTANEOUS REAL CTA REQUESTS"

python3 -S -B - "$T" "$B" <<'PY'
import sys, json, time, threading
import urllib.request, urllib.error
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

tests, base = map(Path, sys.argv[1:3])
body = (tests / "cta_max_tiles_smoketest_input.json").read_bytes()

def prediction(data):
    return data.get("jsonData", data)["prediction"]

expected = prediction(json.loads(
    (tests / "cta_max_tiles_response.json").read_text()
))

barrier = threading.Barrier(2)

def send(number):
    barrier.wait()
    start = time.monotonic()
    request = urllib.request.Request(
        "http://127.0.0.1:18082/v2/cta/predict",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        opener = urllib.request.build_opener(
            urllib.request.ProxyHandler({})
        )
        with opener.open(request, timeout=335) as response:
            status = response.status
            raw = response.read()
    except urllib.error.HTTPError as exc:
        status, raw = exc.code, exc.read()
    except Exception as exc:
        status, raw = 0, str(exc).encode()

    elapsed = time.monotonic() - start
    path = base / f"cta_native_concurrency_response_{number}.json"
    path.write_bytes(raw)

    try:
        value = prediction(json.loads(raw))
        parity = value == expected
        offers = len(value["offerList"])
    except Exception:
        parity, offers = False, None

    return number, status, elapsed, offers, parity

start = time.monotonic()
with ThreadPoolExecutor(max_workers=2) as executor:
    futures = [executor.submit(send, i) for i in (1, 2)]
    results = [f.result() for f in futures]

wall = time.monotonic() - start

print("\n=== NATIVE CPU CONCURRENCY RESULTS ===")
for number, status, elapsed, offers, parity in results:
    print(
        f"REQUEST {number}: HTTP {status} | "
        f"{elapsed:.2f}s | OFFERS {offers} | "
        f"BUSINESS PARITY {'PASS' if parity else 'FAIL'}"
    )

print("WALL SECONDS:", round(wall, 2))
print("THROUGHPUT RPS:", round(2 / wall, 4))

passed = all(
    status == 200 and parity
    for _, status, _, _, parity in results
)
print("NATIVE CONCURRENT-2:", "PASS" if passed else "FAIL")
print("ORIGINAL DS CODE: NOT MODIFIED BY TEST")

if not passed:
    raise SystemExit(1)
PY
SH
