python3 -B - <<'PY'
from pathlib import Path
import subprocess, json

P = [
    "podman",
    "--root", "/application1/podman/storage",
    "--runroot", "/run/containers/storage"
]
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
        P + ["inspect", cid], text=True
    ))[0]
    if any(
        m.get("Source") == dev and m.get("Destination") == "/batch2"
        for m in info.get("Mounts", [])
    ):
        matches.append(cid)

if len(matches) != 1:
    raise SystemExit("STOP: Expected one existing Batch-2 container")

code = r'''
import sys, os, json, ast, inspect
from pathlib import Path

sys.dont_write_bytecode = True

root = Path("/workspace")
core = root / "artifacts/v1.168/core-artifact"
maxroot = root / "artifacts/v1.168-max"

sys.path[:0] = [str(core), str(maxroot), "/batch2"]

required = [
    core / "pipeline.py",
    maxroot / "cta_max/live_cta_pipeline_bridge.py",
    Path("/batch2/native_batch2/cta_worker_adapter.py"),
    Path("/batch2/real_max_batch2_backend.py")
]

if not all(p.is_file() for p in required):
    raise SystemExit("STOP: Required integration files missing")

# Reuse environment defaults from the existing native worker.
spawn = maxroot / "maxserve_cta_extension/cta_spawn_worker.py"

if spawn.is_file():
    for node in ast.walk(ast.parse(spawn.read_text())):
        if not isinstance(node, ast.Call):
            continue
        if not (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "setdefault"
            and len(node.args) >= 2
        ):
            continue
        try:
            key = ast.literal_eval(node.args[0])
            value = ast.literal_eval(node.args[1])
        except (ValueError, TypeError, SyntaxError):
            continue

        if key in ("modelId", "expThrottleLabel") and isinstance(value, str):
            os.environ.setdefault(key, value)

# Use the actual original DS class, confirmed by previous output.
import pipeline as original

if Path(original.__file__).resolve() != (core / "pipeline.py").resolve():
    raise SystemExit("STOP: Wrong original pipeline imported")

CTA = original.pipeline

if not inspect.isclass(CTA):
    raise SystemExit("STOP: Original pipeline class invalid")

import cta_max

repo_package = str(maxroot / "cta_max")
if repo_package not in cta_max.__path__:
    cta_max.__path__.append(repo_package)

from cta_max.live_cta_pipeline_bridge import attach_max
from native_batch2 import cta_worker_adapter as mod

classes = [
    cls for _, cls in inspect.getmembers(mod, inspect.isclass)
    if cls.__module__ == mod.__name__
    and callable(getattr(cls, "predict_batch", None))
]

if len(classes) != 1:
    raise SystemExit("STOP: Batch-2 adapter not uniquely identified")

adapter = classes[0](CTA, attach_max)

fixtures = [
    maxroot / "test-results/cta_max_tiles_smoketest_input.json",
    maxroot / "cta_native_adjusted_sanity_input.json"
]

if not all(p.is_file() for p in fixtures):
    raise SystemExit("STOP: Known CTA fixtures missing")

bodies = [json.loads(p.read_text()) for p in fixtures]

if not all(isinstance(b, dict) for b in bodies):
    raise SystemExit("STOP: Invalid JSON fixtures")

print("ORIGINAL CTA PIPELINE: PASS", flush=True)
print("BATCH-2 ADAPTER INITIALIZATION: PASS", flush=True)
print("TWO CTA JSON REQUESTS: READY", flush=True)
print("REAL MAX BATCH-2: START", flush=True)

responses = adapter.predict_batch(bodies)

if not isinstance(responses, (list, tuple)) or len(responses) != 2:
    raise RuntimeError("Expected exactly two CTA responses")

for i, response in enumerate(responses, 1):
    if not isinstance(response, dict):
        raise RuntimeError(f"Response {i} is not a dictionary")
    if "error" in response:
        raise RuntimeError(f"Response {i}: {response['error']}")
    if not isinstance(response.get("jsonData"), dict):
        raise RuntimeError(f"Response {i} missing jsonData")
    if "prediction" not in response["jsonData"]:
        raise RuntimeError(f"Response {i} missing prediction")

    json.dumps(response, allow_nan=False)
    print(f"CTA JSON RESPONSE {i}: PASS", flush=True)

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
        input=code,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=300
    )

    print(r.stdout[-7000:])
    print("JSON BATCH-2 EXIT CODE:", r.returncode)

except subprocess.TimeoutExpired as e:
    output = e.stdout or b""
    if isinstance(output, bytes):
        output = output.decode(errors="replace")
    print(output[-4000:])
    print("STOP: Execution exceeded 300 seconds")

print("ORIGINAL DS/MAX: UNCHANGED")
print("CONTAINERS RESTARTED: NONE")
PY
