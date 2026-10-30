python3 -B - <<'PY'
from pathlib import Path
import subprocess, json

P = ["podman", "--root", "/application1/podman/storage",
     "--runroot", "/run/containers/storage"]
dev = "/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029"

mem = int(next(
    x.split()[1] for x in Path("/proc/meminfo").read_text().splitlines()
    if x.startswith("MemAvailable:")
)) // 1024

print("AVAILABLE RAM MB:", mem, flush=True)
if mem < 12000:
    raise SystemExit("STOP: Insufficient available RAM")

ids = []
for cid in subprocess.check_output(P + ["ps", "-q"], text=True).split():
    info = json.loads(subprocess.check_output(
        P + ["inspect", cid], text=True))[0]
    if any(m.get("Source") == dev and m.get("Destination") == "/batch2"
           for m in info.get("Mounts", [])):
        ids.append(cid)

if len(ids) != 1:
    raise SystemExit("STOP: Existing Batch-2 container unavailable")

code = r'''
import os, sys, ast, json, inspect
from pathlib import Path

root = Path("/workspace")
core = root / "artifacts/v1.168/core-artifact"
mx = root / "artifacts/v1.168-max"

sys.dont_write_bytecode = True
sys.path[:0] = [str(core), str(mx), "/batch2"]

spawn = mx / "maxserve_cta_extension/cta_spawn_worker.py"
if spawn.is_file():
    for n in ast.walk(ast.parse(spawn.read_text())):
        if not (isinstance(n, ast.Call)
                and isinstance(n.func, ast.Attribute)
                and n.func.attr == "setdefault"
                and len(n.args) >= 2):
            continue
        try:
            k = ast.literal_eval(n.args[0])
            v = ast.literal_eval(n.args[1])
        except (ValueError, TypeError, SyntaxError):
            continue
        if k in ("modelId", "expThrottleLabel") and isinstance(v, str):
            os.environ.setdefault(k, v)

import pipeline
assert Path(pipeline.__file__).resolve() == (core / "pipeline.py").resolve()

import cta_max
repo_pkg = str(mx / "cta_max")
if repo_pkg not in cta_max.__path__:
    cta_max.__path__.append(repo_pkg)

from cta_max.live_cta_pipeline_bridge import attach_max
from native_batch2 import cta_worker_adapter

classes = [
    c for _, c in inspect.getmembers(cta_worker_adapter, inspect.isclass)
    if c.__module__ == cta_worker_adapter.__name__
    and callable(getattr(c, "predict_batch", None))
]
assert len(classes) == 1, "Batch adapter unavailable"

fixtures = [
    mx / "test-results/cta_max_tiles_smoketest_input.json",
    mx / "cta_native_adjusted_sanity_input.json"
]
assert all(p.is_file() for p in fixtures), "Known fixtures unavailable"

bodies = [json.loads(p.read_text()) for p in fixtures]
assert all(isinstance(x, dict) for x in bodies)

adapter = classes[0](pipeline.pipeline, attach_max)

print("TWO REAL CTA JSON REQUESTS: READY", flush=True)
print("REAL MAX BATCH-2: START", flush=True)

responses = adapter.predict_batch(bodies)

assert isinstance(responses, (list, tuple))
assert len(responses) == 2, "Response count mismatch"

for i, response in enumerate(responses, 1):
    assert isinstance(response, dict), "Invalid response object"
    assert "error" not in response, str(response.get("error"))
    assert isinstance(response.get("jsonData"), dict)
    assert "prediction" in response["jsonData"]
    json.dumps(response, allow_nan=False)
    print(f"CTA RESPONSE {i}: PASS", flush=True)

print("REAL CTA JSON BATCH-2: PASS", flush=True)
'''

try:
    r = subprocess.run(
        P + ["exec", "-i", "-w", "/workspace",
             "-e", "PYTHONDONTWRITEBYTECODE=1",
             "-e", "TMPDIR=/tmp",
             "-e", "PYTHONPATH=/batch2:/workspace/artifacts/v1.168-max",
             ids[0], "/opt/venv/bin/python", "-B", "-"],
        input=code, text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=300
    )
    print(r.stdout[-8000:])
    print("JSON BATCH-2 EXIT CODE:", r.returncode)
except subprocess.TimeoutExpired as e:
    out = e.stdout or b""
    if isinstance(out, bytes):
        out = out.decode(errors="replace")
    print(out[-4000:])
    print("STOP: Test exceeded 300 seconds")

print("ORIGINAL DS/MAX: UNCHANGED")
print("CONTAINERS RESTARTED: NONE")
PY
