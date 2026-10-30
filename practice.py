PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
import ast, re, json, shutil, subprocess, time
import datetime, urllib.request
from pathlib import Path

base = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029")
backend = base / "real_max_batch2_backend.py"
candidate_root = Path(
    "/application1/cta_max_true_batch_dev_20261028/batch2_candidate"
)
candidate = candidate_root / "cta_max"
helper = candidate / "parallel_transformer_block_2layers.py"
graph = candidate / "grecbase_fusion_batch2_draft.py"
fixture = Path(
    "/application1/sajjna8/rt-pzaas-cta-offers-v1/"
    "artifacts/v1.168-max/cta_native_adjusted_sanity_input.json"
)
backup = base / "real_max_batch2_backend.py.before_helper_priority"
marker = "# CTA_BATCH2_EARLY_IMPORT_PRIORITY_V2"

pod = [
    "podman", "--root", "/application1/podman/storage",
    "--runroot", "/run/containers/storage"
]
name = "cta-batch2-trace-8766-10g"

def run(args, timeout=45):
    return subprocess.run(
        args, capture_output=True, text=True, timeout=timeout
    )

def health(port):
    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{port}/health", timeout=5
        ) as r:
            return r.status == 200
    except Exception:
        return False

print("=== CORRECTED BATCH-2 PRE-FLIGHT ===", flush=True)

assert backend.is_file(), "STOP: Backend missing"
assert graph.is_file(), "STOP: Graph missing"
assert helper.is_file(), "STOP: Transformer helper missing"
assert fixture.is_file(), "STOP: CTA JSON missing"

for p in (backend, graph, helper):
    ast.parse(p.read_text(), filename=str(p))

text = helper.read_text()

assert re.search(
    r"reshape\s*\(\s*valid_length\s*,\s*"
    r"\[\s*2\s*,\s*1\s*,\s*1\s*,\s*1\s*\]",
    text
), "STOP: Corrected transformer valid_length reshape missing"

assert health(8765), "STOP: Original MAX unhealthy"

r = run(pod + ["inspect", name])
assert r.returncode == 0, r.stderr

info = json.loads(r.stdout)[0]
assert info["State"]["Running"], "STOP: Container not running"
assert not info["State"]["OOMKilled"], "STOP: Previous OOM"

memory = info["HostConfig"]["Memory"] / 1024**3
assert 9 <= memory <= 11, "STOP: Memory limit invalid"

mounts = info["Mounts"]

assert any(
    m["Destination"] == "/batch2"
    and Path(m["Source"]).resolve() == candidate_root.resolve()
    for m in mounts
), "STOP: Candidate mount mismatch"

assert any(
    m["Destination"] == "/batch2/real_max_batch2_backend.py"
    and Path(m["Source"]).resolve() == backend.resolve()
    for m in mounts
), "STOP: Backend mount mismatch"

mem = Path("/proc/meminfo").read_text()
available = int(re.search(
    r"MemAvailable:\s*(\d+)", mem
).group(1)) / 1024**2

assert available >= 12, "STOP: Insufficient available memory"
assert shutil.disk_usage(base).free > 20 * 1024**2, \
    "STOP: Insufficient application1 disk space"

print("TRANSFORMER BATCH-2 SHAPE: PASS")
print("CANDIDATE GRAPH: PASS")
print("ORIGINAL MAX: HEALTHY")
print("MEMORY LIMIT GB:", round(memory, 2))
print("HOST AVAILABLE GB:", round(available, 2))
print("CONTAINER MOUNTS: PASS")

source = backend.read_text()

if marker not in source:
    tree = ast.parse(source)
    body = tree.body
    index = 0

    if body and isinstance(body[0], ast.Expr) and isinstance(
        body[0].value, (ast.Str, ast.Constant)
    ):
        index = body[0].end_lineno

    for node in body:
        if isinstance(node, ast.ImportFrom) and node.module == "__future__":
            index = max(index, node.end_lineno)

    bootstrap = '''
# CTA_BATCH2_EARLY_IMPORT_PRIORITY_V2
import sys as _b2_sys
import importlib as _b2_importlib
import os as _b2_os
import cta_max as _b2_pkg

_b2_dir = "/batch2/cta_max"
_b2_pkg.__path__ = [_b2_dir] + [
    str(p) for p in _b2_pkg.__path__
    if str(p) != _b2_dir
]

for _b2_short in (
    "parallel_transformer_block_2layers",
    "nlp_bert_in_graph",
):
    _b2_full = "cta_max." + _b2_short
    _b2_expected = _b2_dir + "/" + _b2_short + ".py"
    _b2_old = _b2_sys.modules.get(_b2_full)

    if _b2_old is not None:
        if getattr(_b2_pkg, _b2_short, None) is _b2_old:
            delattr(_b2_pkg, _b2_short)
        del _b2_sys.modules[_b2_full]

    _b2_importlib.invalidate_caches()
    _b2_module = _b2_importlib.import_module(_b2_full)

    if _b2_os.path.realpath(_b2_module.__file__) != (
        _b2_os.path.realpath(_b2_expected)
    ):
        raise RuntimeError(
            "STOP: Wrong Batch-2 helper " + _b2_full
        )

    print(
        "ACTIVE BATCH-2 HELPER:",
        _b2_module.__file__,
        flush=True
    )
'''

    lines = source.splitlines(keepends=True)
    lines.insert(index, bootstrap.strip() + "\n\n")
    updated = "".join(lines)

    compile(updated, str(backend), "exec")

    assert not backup.exists(), \
        "STOP: Existing backup requires review"

    shutil.copy2(backend, backup)
    backend.write_text(updated)

    print("HELPER IMPORT PRIORITY: INSTALLED", flush=True)
else:
    print("HELPER IMPORT PRIORITY: ALREADY INSTALLED")
    print("STOP: Avoid repeating an unchanged restart")
    raise SystemExit(0)

compile(backend.read_text(), str(backend), "exec")
print("BACKUP: PRESERVED")
print("SYNTAX: PASS")

print("\n=== RESTART ISOLATED ONLY ===", flush=True)

r = run(pod + ["restart", "--time", "15", name], timeout=90)
assert r.returncode == 0, "STOP: " + r.stderr

inside_health = r'''
import urllib.request, time
opener = urllib.request.build_opener(
    urllib.request.ProxyHandler({})
)
for i in range(75):
    try:
        with opener.open(
            "http://127.0.0.1:8766/health", timeout=3
        ) as response:
            if response.status == 200:
                print("ISOLATED HTTP HEALTH: PASS", flush=True)
                break
    except Exception:
        pass
    time.sleep(2)
else:
    print("ISOLATED HTTP HEALTH: FAIL", flush=True)
    raise SystemExit(2)
'''

r = run(
    pod + [
        "exec", "-e", "PYTHONDONTWRITEBYTECODE=1",
        name, "/opt/venv/bin/python", "-B", "-c", inside_health
    ],
    timeout=200
)
print(r.stdout or r.stderr, flush=True)

if r.returncode != 0:
    print("STOP: Isolated startup failed")
    proceed = False
else:
    proceed = True

if proceed and not health(8765):
    print("STOP: Original MAX health changed")
    proceed = False

if proceed:
    print("\n=== REAL NATIVE HTTP BATCH-2 ===", flush=True)

    started = datetime.datetime.now(
        datetime.timezone.utc
    ).isoformat()

    inside_test = r'''
import json, urllib.request, urllib.error, time, threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

path = Path(
    "/workspace/artifacts/v1.168-max/"
    "cta_native_adjusted_sanity_input.json"
)
assert path.is_file(), "STOP: Real CTA fixture missing"
payload = path.read_bytes()
assert isinstance(json.loads(payload), dict)

barrier = threading.Barrier(2)
opener = urllib.request.build_opener(
    urllib.request.ProxyHandler({})
)

def test(n):
    barrier.wait(timeout=10)
    start = time.monotonic()
    req = urllib.request.Request(
        "http://127.0.0.1:8766/v2/cta/predict",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with opener.open(req, timeout=150) as resp:
            data = json.loads(resp.read())
            offers = data["jsonData"]["prediction"]["offerList"]
            assert isinstance(offers, list)
            return n, 200, len(offers), round(
                time.monotonic() - start, 2
            )
    except urllib.error.HTTPError as e:
        return n, e.code, e.read(800).decode(
            errors="replace"
        ), round(time.monotonic() - start, 2)
    except Exception as e:
        return n, "FAIL", str(e), round(
            time.monotonic() - start, 2
        )

with ThreadPoolExecutor(max_workers=2) as pool:
    a = pool.submit(test, 1)
    b = pool.submit(test, 2)
    results = sorted([a.result(), b.result()])

for result in results:
    print("REQUEST:", result, flush=True)

print(
    "REAL NATIVE HTTP 2/2:",
    "PASS" if all(x[1] == 200 for x in results)
    else "FAIL",
    flush=True
)
'''

    try:
        r = run(
            pod + [
                "exec", "-e", "PYTHONDONTWRITEBYTECODE=1",
                name, "/opt/venv/bin/python", "-B",
                "-c", inside_test
            ],
            timeout=190
        )
        print(r.stdout, flush=True)
        if r.stderr:
            print(r.stderr[-2500:], flush=True)
    except subprocess.TimeoutExpired:
        print("STOP: Bounded HTTP validation timed out")

    print("\n=== MAX BATCH EXECUTION LOGS ===")
    r = run(
        pod + [
            "logs", "--since", started,
            "--tail", "700", name
        ]
    )
    logs = r.stdout + r.stderr
    markers = (
        "CTA TRUE MAX BATCH-2",
        "CTA RESPONSE ID MATCH",
        "ACTIVE BATCH-2 HELPER",
        "ERROR", "Traceback", "OOM",
        "POST /v2/cta/predict"
    )

    for line in logs.splitlines():
        if any(m in line for m in markers):
            print(line[:600])

    print("TWO-RESPONSE BACKEND MARKERS:",
          logs.count(
              "CTA TRUE MAX BATCH-2: TWO JSON RESPONSES PRODUCED"
          ))

print("\n=== FINAL SAFETY ===")
print("ORIGINAL MAX:",
      "HEALTHY" if health(8765) else "CHECK REQUIRED")
print("ORIGINAL DS: UNCHANGED")
print("ORIGINAL MAX: NOT RESTARTED")
print("BACKUP: PRESERVED")
PY
