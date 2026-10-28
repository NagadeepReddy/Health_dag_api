cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 -S -B - <<'PY'
from pathlib import Path
import ast

base = Path("/application1/cta_max_true_batch_dev_20261028")
source = Path("/application1/cta_max_native_release_candidate_20261028/cta_native_e2e_test.py")
runner = base / "native_concurrent2_static.py"
helper = base / "cta_native_benchmark_helper.py"

anchor = 'client.post("/v2/cta/predict", json=body)'

assert source.is_file(), "STOP: Native source missing"
assert not runner.exists() and not helper.exists(), "STOP: Benchmark files already exist"

original = source.read_text()
assert original.count(anchor) == 1, "STOP: HTTP call structure differs"

updated = original.replace(
    anchor,
    '__import__("cta_native_benchmark_helper").benchmark_post(client, body)'
)

helper_code = '''
from concurrent.futures import ThreadPoolExecutor
import copy
import time

def benchmark_post(client, body):
    def send(number):
        start = time.monotonic()
        response = client.post(
            "/v2/cta/predict",
            json=copy.deepcopy(body)
        )
        elapsed = time.monotonic() - start
        print(f"REQUEST {number}: HTTP {response.status_code} LATENCY {elapsed:.3f}s", flush=True)
        return response, elapsed

    start = time.monotonic()
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(send, n) for n in (1, 2)]
        results = [f.result() for f in futures]

    elapsed = time.monotonic() - start
    print("HTTP STATUSES:", [r.status_code for r, _ in results], flush=True)
    print("WALL SECONDS:", round(elapsed, 3), flush=True)
    print("THROUGHPUT RPS:", round(2 / elapsed, 3), flush=True)
    print("MEAN LATENCY:", round(sum(t for _, t in results) / 2, 3), flush=True)

    assert all(r.status_code == 200 for r, _ in results)
    print("NATIVE CONCURRENT-2: PASS", flush=True)
    return results[0][0]
'''

ast.parse(updated)
ast.parse(helper_code)

runner.write_text(updated)
helper.write_text(helper_code)

print("STATIC BENCHMARK LAUNCHER: CREATED")
print("PYTHON SYNTAX: PASS")
print("DS CODE: UNCHANGED")
print("MAX STARTUP: NOT PERFORMED")
print("DYNAMIC EXEC: REMOVED")
PY
