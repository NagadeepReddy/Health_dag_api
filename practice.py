cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

LOG=/application1/cta_native_concurrent2_benchmark.log
CANDIDATE=/application1/cta_max_native_release_candidate_20261028
TEST=artifacts/v1.168-max/maxserve_cta_extension/cta_native_e2e_test.py

echo "=== NATIVE MAX SERVE PERFORMANCE TEST ==="

if [ -e "$LOG" ]; then
  echo "STOP: Benchmark log already exists"
elif [ ! -f "$CANDIDATE/cta_router.py" ] || [ ! -f "$TEST" ]; then
  echo "STOP: Validated integration or test missing"
elif [ "$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)" -lt 16777216 ]; then
  echo "STOP: Available RAM below 16 GiB"
elif [ "$(df -Pk /application1 | awk 'NR==2 {print $4}')" -lt 10485760 ]; then
  echo "STOP: Less than 10 GiB free on /application1"
elif ps -eo stat=,args= | grep -E '[p]ython3 -B /workspace/artifacts/v1.168-max/maxserve_cta_extension/cta_native_e2e_test.py' | grep -v '^[[:space:]]*Z' | grep -q .; then
  echo "STOP: Another CTA test is running"
else
  timeout --signal=TERM --kill-after=10s 420s \
  podman \
    --root /application1/podman/storage \
    --runroot /run/containers/storage \
    run --rm -i --pull=never --init \
    --network=none --read-only --log-driver=none \
    --memory=8g --memory-swap=8g \
    --cpus=2 --pids-limit=256 \
    --tmpfs /tmp:rw,size=512m,mode=1777 \
    --tmpfs /root/.cache:rw,size=128m,mode=1777 \
    --tmpfs /opt/venv/lib/python3.12/site-packages/max/_core_mojo/__mojocache__:rw,size=256m,mode=1777 \
    -v "$PWD:/workspace:ro" \
    -v "$CANDIDATE:/workspace/artifacts/v1.168-max/maxserve_cta_extension:ro" \
    -w /workspace \
    -e HOME=/tmp \
    -e XDG_CACHE_HOME=/tmp \
    -e modelId=rt-pzaas-cta-offers-v1 \
    -e expThrottleLabel=T \
    -e PYTHONPATH=/workspace:/workspace/artifacts/v1.168-max \
    -e PYTHONDONTWRITEBYTECODE=1 \
    -e PYTHONUNBUFFERED=1 \
    -e OMP_NUM_THREADS=1 \
    -e MKL_NUM_THREADS=1 \
    -e OPENBLAS_NUM_THREADS=1 \
    --entrypoint /opt/venv/bin/python3 \
    localhost/cta-max-faiss:local -B - <<'PY' > "$LOG" 2>&1

from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import copy
import time

path = Path(
    "/workspace/artifacts/v1.168-max/"
    "maxserve_cta_extension/cta_native_e2e_test.py"
)

source = path.read_text()
anchor = 'client.post("/v2/cta/predict", json=body)'

assert source.count(anchor) == 1, (
    "STOP: Unexpected native test structure"
)

def benchmark_post(client, body):
    def request_one(number):
        start = time.monotonic()
        response = client.post(
            "/v2/cta/predict",
            json=copy.deepcopy(body)
        )
        elapsed = time.monotonic() - start
        print(
            f"REQUEST {number}: HTTP {response.status_code} "
            f"LATENCY {elapsed:.3f}s",
            flush=True
        )
        return response, elapsed

    start = time.monotonic()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [
            pool.submit(request_one, i)
            for i in (1, 2)
        ]
        results = [f.result() for f in futures]

    elapsed = time.monotonic() - start
    statuses = [r.status_code for r, _ in results]
    latencies = [t for _, t in results]

    print("HTTP STATUSES:", statuses, flush=True)
    print("TOTAL REQUESTS:", len(results), flush=True)
    print("WALL SECONDS:", round(elapsed, 3), flush=True)
    print("THROUGHPUT RPS:", round(2 / elapsed, 4), flush=True)
    print("MEAN LATENCY:", round(sum(latencies) / 2, 3), flush=True)

    assert statuses == [200, 200], (
        "STOP: Concurrent HTTP requests failed"
    )

    print("NATIVE CONCURRENT-2: PASS", flush=True)
    return results[0][0]

updated = source.replace(anchor, "benchmark_post(client, body)")
namespace = {
    "__name__": "__main__",
    "__file__": str(path),
    "benchmark_post": benchmark_post,
}
exec(compile(updated, str(path), "exec"), namespace)
PY

  RC=$?
  echo "BENCHMARK EXIT CODE: $RC"

  echo "=== PERFORMANCE RESULTS ==="
  grep -E \
    'REQUEST [12]:|HTTP STATUSES|TOTAL REQUESTS|WALL SECONDS|THROUGHPUT RPS|MEAN LATENCY|NATIVE CONCURRENT-2|CTA NATIVE HTTP STATUS|CTA NATIVE END-TO-END|Traceback|Error|Killed' \
    "$LOG" | tail -25 || true

  if [ "$RC" -ne 0 ]; then
    echo "BENCHMARK NOT PASSED — DO NOT RETRY AUTOMATICALLY"
    tail -10 "$LOG"
  fi
fi
