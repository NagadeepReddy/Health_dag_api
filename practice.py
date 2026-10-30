PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
import json, os, re, shutil, subprocess, time, urllib.request
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

base = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029")
backend = base / "real_max_batch2_backend.py"
candidate = base / "batch2_candidate/cta_max/grecbase_fusion_full_head_72_max.py"
backup = base / "real_max_batch2_backend.py.before_graph_resolution_fix"
name = "cta-batch2-trace-8766-10g"
pod = ["podman", "--root", "/application1/podman/storage",
       "--runroot", "/run/containers/storage"]

def run(args, timeout=30):
    return subprocess.run(args, capture_output=True, text=True, timeout=timeout)

print("=== BATCH-2 FIX AND VALIDATION ===", flush=True)

assert backend.is_file(), "STOP: Isolated backend missing"
assert candidate.is_file(), "STOP: Corrected graph missing from mounted candidate"
assert "[2, 256]" in candidate.read_text(), "STOP: Batch-2 graph declaration missing"

r = run(pod + ["inspect", name])
assert r.returncode == 0, "STOP: Isolated container unavailable"
info = json.loads(r.stdout)[0]

assert any(
    m["Source"] == str(base / "batch2_candidate")
    and m["Destination"] == "/batch2"
    for m in info["Mounts"]
), "STOP: Candidate mount incorrect"

memory = info["HostConfig"].get("Memory", 0)
assert memory >= 10 * 1024**3, "STOP: 10GB memory limit not configured"

meminfo = Path("/proc/meminfo").read_text()
available = int(re.search(r"MemAvailable:\s+(\d+)", meminfo).group(1)) * 1024
assert available >= 12 * 1024**3, "STOP: Insufficient host memory"

fixture = Path(
    "/application1/sajjna8/rt-pzaas-cta-offers-v1/"
    "artifacts/v1.168-max/cta_native_adjusted_sanity_input.json"
)
assert fixture.is_file(), "STOP: Real CTA JSON fixture missing"
payload = fixture.read_bytes()
assert isinstance(json.loads(payload), dict), "STOP: Invalid CTA JSON"

source = backend.read_text()
pattern = re.compile(
    r"(?m)^([ \t]*)from cta_max\.grecbase_fusion_full_head_72_max "
    r"import build_grecbase_fusion_graph_order_correct[ \t]*$"
)
matches = list(pattern.finditer(source))
assert len(matches) == 1, "STOP: Expected exactly one graph import"

replacement = """
{indent}import importlib.util as _batch2_util
{indent}import cta_max as _batch2_package
{indent}_batch2_root = "/batch2/cta_max"
{indent}_batch2_package.__path__ = (
{indent}    [_batch2_root] +
{indent}    [p for p in _batch2_package.__path__ if p != _batch2_root]
{indent})
{indent}_batch2_spec = _batch2_util.spec_from_file_location(
{indent}    "cta_max._isolated_real_batch2_graph",
{indent}    _batch2_root + "/grecbase_fusion_full_head_72_max.py"
{indent})
{indent}assert _batch2_spec and _batch2_spec.loader
{indent}_batch2_graph = _batch2_util.module_from_spec(_batch2_spec)
{indent}_batch2_spec.loader.exec_module(_batch2_graph)
{indent}build_grecbase_fusion_graph_order_correct = (
{indent}    _batch2_graph.build_grecbase_fusion_graph_order_correct
{indent})
{indent}print("ISOLATED BATCH-2 GRAPH: LOADED", flush=True)
"""

indent = matches[0].group(1)
updated = pattern.sub(
    lambda _: replacement.format(indent=indent).strip("\n"),
    source,
    count=1
)
compile(updated, str(backend), "exec")

assert not backup.exists() or backup.read_text() == source, \
    "STOP: Existing backup differs; preserve it"

if not backup.exists():
    shutil.copy2(backend, backup)

backend.write_text(updated)
print("GRAPH IMPORT: PATCHED")
print("SYNTAX: PASS")
print("BACKUP: PRESERVED")
print("ORIGINAL DS: UNCHANGED")

print("RESTARTING ISOLATED CONTAINER ONLY", flush=True)
r = run(pod + ["restart", "--time", "15", name], timeout=60)
assert r.returncode == 0, "STOP: Isolated restart failed: " + r.stderr

health = "http://127.0.0.1:8766/health"
ready = False

for _ in range(60):
    state = json.loads(run(pod + ["inspect", name]).stdout)[0]["State"]
    if state["Status"] != "running":
        break
    try:
        with urllib.request.urlopen(health, timeout=3) as resp:
            if resp.status == 200:
                ready = True
                break
    except Exception:
        pass
    time.sleep(2)

assert ready, "STOP: Isolated server did not become healthy"

print("ISOLATED HEALTH: PASS")
print("NATIVE BATCH-2 HTTP: START", flush=True)

url = "http://127.0.0.1:8766/v2/cta/predict"

def request(n):
    started = time.monotonic()
    try:
        req = urllib.request.Request(
            url, data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=360) as resp:
            body = json.loads(resp.read())
            prediction = body.get("jsonData", {}).get("prediction", {})
            valid = isinstance(prediction.get("offerList"), list)
            return (n, resp.status, valid, round(time.monotonic()-started, 2))
    except Exception as exc:
        return (n, "FAILED", False, str(exc)[:180])

with ThreadPoolExecutor(max_workers=2) as pool:
    results = list(pool.map(request, (1, 2)))

for result in results:
    print("REQUEST:", result, flush=True)

logs = run(pod + ["logs", "--tail", "500", name]).stdout

markers = [
    "ISOLATED BATCH-2 GRAPH: LOADED",
    "CTA TRUE MAX BATCH-2: TWO JSON RESPONSES PRODUCED"
]
for marker in markers:
    print("MARKER:", marker, marker in logs)

passed = all(x[1] == 200 and x[2] for x in results)
proven = all(marker in logs for marker in markers)

print("NATIVE HTTP 2/2:", "PASS" if passed else "FAIL")
print("BATCH EXECUTION TRACE:", "PASS" if proven else "NOT VERIFIED")
print("ORIGINAL MAX: NOT RESTARTED")
print("ORIGINAL DS: UNCHANGED")

if not (passed and proven):
    print("NEXT ERROR LOGS:")
    print("\n".join(logs.splitlines()[-45:]))
    raise SystemExit("NATIVE BATCH-2 NOT YET VERIFIED")

print("NATIVE BATCH-2: PASS")
PY
