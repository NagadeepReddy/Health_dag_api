PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
import subprocess, json, shutil, textwrap, sys
from pathlib import Path

POD = [
    "podman",
    "--root", "/application1/podman/storage",
    "--runroot", "/run/containers/storage"
]
NAME = "cta-batch2-trace-8766-10g"
BASE = Path("/application1/cta_max_true_batch_dev_20261028/batch2_candidate")
GRAPH = BASE / "cta_max/grecbase_fusion_batch2_draft.py"
HELPER = BASE / "cta_max/grecbase_aux_features_max.py"

print("=== BATCH-2 SAFETY CHECK ===", flush=True)

assert GRAPH.is_file() and HELPER.is_file(), "STOP: Candidate missing"
src = GRAPH.read_text()
helper = HELPER.read_text()

assert "def grecbase_aux_features" in helper
assert "[2, 256]" in helper
assert "[2, 1, 128]" in helper

r = subprocess.run(
    POD + ["inspect", NAME],
    text=True, capture_output=True
)
assert r.returncode == 0, "STOP: Isolated container missing"
info = json.loads(r.stdout)[0]

assert info["State"]["Status"] == "running", "STOP: Container not running"
assert info["HostConfig"]["Memory"] >= 10_000_000_000, "STOP: Memory limit missing"
assert any(
    m["Destination"] == "/batch2"
    and Path(m["Source"]).resolve() == BASE.resolve()
    for m in info["Mounts"]
), "STOP: Batch-2 mount missing"

print("CONTAINER: VERIFIED")
print("MEMORY LIMIT: VERIFIED")
print("BATCH-2 MOUNT: VERIFIED")

old = "from cta_max.grecbase_aux_features_max import grecbase_aux_features"
marker = "_cta_batch2_aux_module"

replacement = """
from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path
_cta_batch2_aux_path = Path(__file__).with_name("grecbase_aux_features_max.py")
_cta_batch2_aux_spec = spec_from_file_location(
    "_cta_batch2_aux_module", str(_cta_batch2_aux_path)
)
_cta_batch2_aux_module = module_from_spec(_cta_batch2_aux_spec)
_cta_batch2_aux_spec.loader.exec_module(_cta_batch2_aux_module)
grecbase_aux_features = _cta_batch2_aux_module.grecbase_aux_features
"""

if old in src:
    assert src.count(old) == 1
    updated = src.replace(old, textwrap.dedent(replacement).strip())
    compile(updated, str(GRAPH), "exec")

    backup = GRAPH.with_name(GRAPH.name + ".before_aux_runtime_fix")
    if not backup.exists():
        shutil.copy2(GRAPH, backup)

    GRAPH.write_text(updated)
    print("ISOLATED HELPER RESOLUTION: FIXED")
    print("BACKUP: PRESERVED")
elif marker in src:
    print("ISOLATED HELPER RESOLUTION: ALREADY FIXED")
else:
    raise RuntimeError("STOP: Unexpected graph import")

compile(GRAPH.read_text(), str(GRAPH), "exec")
print("SYNTAX: PASS")

print("=== RESTART ISOLATED ONLY ===", flush=True)
r = subprocess.run(
    POD + ["restart", "--time", "15", NAME],
    text=True, capture_output=True, timeout=90
)
if r.returncode:
    print(r.stderr[-1500:])
    raise SystemExit("STOP: Isolated restart failed")

print("ISOLATED CONTAINER: RESTARTED")

test = r'''
import json, time, urllib.request, urllib.error
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

url = "http://127.0.0.1:8766"
deadline = time.monotonic() + 90

while time.monotonic() < deadline:
    try:
        with urllib.request.urlopen(url + "/health", timeout=3) as r:
            if r.status == 200:
                break
    except Exception:
        pass
    time.sleep(3)
else:
    raise RuntimeError("Native server not ready")

print("NATIVE HEALTH: PASS", flush=True)

p = Path("/workspace/artifacts/v1.168-max/cta_native_adjusted_sanity_input.json")
assert p.is_file(), "Real CTA fixture missing"
payload = p.read_bytes()
json.loads(payload)

def send(n):
    req = urllib.request.Request(
        url + "/v2/cta/predict",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=100) as r:
            status = r.status
            data = json.loads(r.read())
        offers = data.get("prediction", {}).get("offerList", [])
        ok = status == 200 and isinstance(offers, list)
        return n, ok, status, len(offers), ""
    except urllib.error.HTTPError as e:
        return n, False, e.code, 0, e.read(1200).decode(errors="replace")
    except Exception as e:
        return n, False, 0, 0, repr(e)

with ThreadPoolExecutor(max_workers=2) as pool:
    results = list(pool.map(send, (1, 2)))

for n, ok, status, offers, error in results:
    print(f"REQUEST {n}: HTTP {status} | OFFERS {offers} | {'PASS' if ok else 'FAIL'}")
    if error:
        print(error[:1200])

print("NATIVE HTTP 2/2:", "PASS" if all(x[1] for x in results) else "FAIL")
'''

r = subprocess.run(
    POD + ["exec", "-i", NAME, "/opt/venv/bin/python", "-B", "-"],
    input=test, text=True, capture_output=True, timeout=240
)

print(r.stdout[-6000:])
if r.stderr:
    print("ERROR:", r.stderr[-2000:])

print("=== FINAL ===")
print("ORIGINAL MAX: NOT RESTARTED")
print("ORIGINAL DS: UNCHANGED")
print("NATIVE HTTP EXIT:", r.returncode)

if r.returncode or "NATIVE HTTP 2/2: PASS" not in r.stdout:
    print("=== RECENT ISOLATED ERRORS ===")
    logs = subprocess.run(
        POD + ["logs", "--tail", "150", NAME],
        capture_output=True, text=True
    )
    lines = [
        x for x in (logs.stdout + logs.stderr).splitlines()
        if any(k in x.lower() for k in
               ("error", "reshape", "batch", "worker failed", "traceback"))
    ]
    print("\n".join(lines[-20:])[-4500:])
PY
