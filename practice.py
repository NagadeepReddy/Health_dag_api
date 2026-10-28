cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

BASE=/application1/cta_max_true_batch_dev_20261028
RUNNER="$BASE/native_concurrent2_realfile.py"
CANDIDATE=/application1/cta_max_native_release_candidate_20261028

test -f "$CANDIDATE/cta_native_e2e_test.py" || {
  echo "STOP: Native test source missing"
  exit 1
}

test ! -e "$RUNNER" || {
  echo "STOP: Benchmark launcher already exists"
  exit 1
}

mkdir -p "$BASE" || exit 1

cat > "$RUNNER" <<'PY'
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import copy
import time
import ast

SOURCE = Path(
    "/workspace/artifacts/v1.168-max/"
    "maxserve_cta_extension/cta_native_e2e_test.py"
)

ANCHOR = 'client.post("/v2/cta/predict", json=body)'

def benchmark_post(client, body):
    def send(number):
        started = time.monotonic()
        response = client.post(
            "/v2/cta/predict", json=copy.deepcopy(body)
        )
        elapsed = time.monotonic() - started
        print(
            f"REQUEST {number}: HTTP {response.status_code} "
            f"LATENCY {elapsed:.3f}s",
            flush=True,
        )
        return response, elapsed

    started = time.monotonic()
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(send, n) for n in (1, 2)]
        results = [f.result() for f in futures]

    seconds = time.monotonic() - started
    print("HTTP STATUSES:", [r.status_code for r, _ in results])
    print("WALL SECONDS:", round(seconds, 3))
    print("THROUGHPUT RPS:", round(2 / seconds, 3))
    print("MEAN LATENCY:", round(sum(t for _, t in results) / 2, 3))

    assert all(r.status_code == 200 for r, _ in results)
    print("NATIVE CONCURRENT-2: PASS", flush=True)
    return results[0][0]

if __name__ == "__main__":
    source = SOURCE.read_text()
    assert source.count(ANCHOR) == 1, "STOP: HTTP call differs"
    modified = source.replace(ANCHOR, "benchmark_post(client, body)")
    ast.parse(modified)
    exec(
        compile(modified, str(SOURCE), "exec"),
        {
            "__name__": "__main__",
            "__file__": str(SOURCE),
            "benchmark_post": benchmark_post,
        },
    )
PY

python3 -S -B -m py_compile "$RUNNER" && \
echo "REAL-FILE BENCHMARK LAUNCHER: READY" && \
echo "DS CODE: UNCHANGED" && \
echo "MAX: NOT STARTED"
