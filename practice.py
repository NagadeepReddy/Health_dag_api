python3 -B - <<'PY'
import subprocess, json
from pathlib import Path

P = ["podman", "--root", "/application1/podman/storage",
     "--runroot", "/run/containers/storage"]

dev = "/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029"

mem = Path("/proc/meminfo").read_text()
available = int(next(
    x.split()[1] for x in mem.splitlines()
    if x.startswith("MemAvailable:")
)) // 1024

print("AVAILABLE RAM MB:", available, flush=True)
if available < 12000:
    raise SystemExit("STOP: Insufficient available memory")

matches = []
for cid in subprocess.check_output(P + ["ps", "-q"], text=True).split():
    info = json.loads(subprocess.check_output(
        P + ["inspect", cid], text=True))[0]
    if any(
        m.get("Source") == dev and m.get("Destination") == "/batch2"
        for m in info.get("Mounts", [])
    ):
        matches.append(cid)

if len(matches) != 1:
    raise SystemExit("STOP: Existing Batch-2 container unavailable")

code = r'''
import os, sys, json, inspect, ast, importlib.util
from pathlib import Path

sys.dont_write_bytecode = True

root = Path("/workspace")
core = root / "artifacts/v1.168/core-artifact"
maxroot = root / "artifacts/v1.168-max"

sys.path[:0] = [str(core), str(maxroot), "/batch2"]

ds = core / "pipeline.py"
bridge = maxroot / "cta_max/live_cta_pipeline_bridge.py"
adapter_file = Path("/batch2/native_batch2/cta_worker_adapter.py")

for p in (ds, bridge, adapter_file):
    if not p.is_file():
        raise SystemExit(f"STOP: Required integration file missing: {p}")

# Reuse environment defaults from the existing native spawn implementation.
spawn = maxroot / "maxserve_cta_extension/cta_spawn_worker.py"
if spawn.is_file():
    tree = ast.parse(spawn.read_text())
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fn = node.func
        if not (isinstance(fn, ast.Attribute) and fn.attr == "setdefault"):
            continue
        if len(node.args) < 2:
            continue
        try:
            key = ast.literal_eval(node.args[0])
            val = ast.literal_eval(node.args[1])
        except (ValueError, TypeError, SyntaxError):
            continue
        if key in ("modelId", "expThrottleLabel") and isinstance(val, str):
            os.environ.setdefault(key, val)

# Load the original CTA pipeline without modifying it.
spec = importlib.util.spec_from_file_location("cta_original_pipeline", ds)
original = importlib.util.module_from_spec(spec)
spec.loader.exec_module(original)

CTA = getattr(original, "CTA", None)
if not callable(CTA):
    raise SystemExit(
        "STOP: Original CTA class unavailable; found classes: " +
        str([n for n, v in vars(original).items()
             if inspect.isclass(v) and v.__module__ == original.__name__])
    )

import cta_max
repo_pkg = str(maxroot / "cta_max")
if repo_pkg not in cta_max.__path__:
    cta_max.__path__.append(repo_pkg)

from cta_max.live_cta_pipeline_bridge import attach_max
from native_batch2 import cta_worker_adapter as mod

classes = [
    c for _, c in inspect.getmembers(mod, inspect.isclass)
    if c.__module__ == mod.__name__
    and callable(getattr(c, "predict_batch", None))
]
if len(classes) != 1:
    raise SystemExit("STOP: Batch-2 adapter class not uniquely identified")

adapter = classes[0](CTA, attach_max)
print("CTA ADAPTER INITIALIZATION: PASS", flush=True)

fixtures = [
    maxroot / "test-results/cta_max_tiles_smoketest_input.json",
    maxroot / "cta_native_adjusted_sanity_input.json"
]
if not all(p.is_file() for p in fixtures):
    raise SystemExit("STOP: Known CTA fixtures unavailable")

bodies = [json.loads(p.read_text()) for p in fixtures]
if not all(isinstance(b, dict) for b in bodies):
    raise SystemExit("STOP: Fixtures are not JSON objects")

print("TWO CTA JSON REQUESTS: READY", flush=True)
print("REAL MAX BATCH-2 EXECUTION: START", flush=True)

responses = adapter.predict_batch(bodies)

assert isinstance(responses, (list, tuple))
assert len(responses) == 2

for i, response in enumerate(responses, 1):
    assert isinstance(response, dict)
    assert "error" not in response, response
    assert isinstance(response.get("jsonData"), dict)
    assert "prediction" in response["jsonData"]
    json.dumps(response, allow_nan=False)
    print(f"CTA RESPONSE {i}: PASS", flush=True)

print("REAL CTA JSON BATCH-2: PASS", flush=True)
'''

try:
    r = subprocess.run(
        P + [
            "exec", "-i", "-w", "/workspace",
            "-e", "PYTHONDONTWRITEBYTECODE=1",
            "-e", "TMPDIR=/tmp",
            matches[0], "/opt/venv/bin/python", "-B", "-"
        ],
        input=code, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        timeout=300
    )
    print(r.stdout[-7000:])
    print("JSON BATCH-2 EXIT CODE:", r.returncode)
except subprocess.TimeoutExpired as e:
    output = e.stdout or b""
    if isinstance(output, bytes):
        output = output.decode(errors="replace")
    print(output[-4000:])
    print("STOP: Test exceeded 300 seconds")

print("ORIGINAL DS/MAX: UNCHANGED")
print("CONTAINERS RESTARTED: NONE")
PY
