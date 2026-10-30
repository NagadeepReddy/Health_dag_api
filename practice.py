python3 -B - <<'PY'
from pathlib import Path
import subprocess, json

dev = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029")
P = ["podman", "--root", "/application1/podman/storage",
     "--runroot", "/run/containers/storage"]

# Check memory before real MAX compilation.
mem = Path("/proc/meminfo").read_text()
available = int(next(
    x.split()[1] for x in mem.splitlines()
    if x.startswith("MemAvailable:")
)) // 1024

print("AVAILABLE RAM MB:", available, flush=True)
if available < 10240:
    raise SystemExit("STOP: Less than 10 GB available; unsafe to compile MAX")

if not (dev / "native_batch2/cta_worker_adapter.py").is_file():
    raise SystemExit("STOP: Development adapter missing")

matches = []
for cid in subprocess.check_output(P + ["ps", "-q"], text=True).split():
    info = json.loads(subprocess.check_output(
        P + ["inspect", cid], text=True))[0]
    mounts = info.get("Mounts", [])
    if any(m.get("Source") == str(dev)
           and m.get("Destination") == "/batch2" for m in mounts):
        matches.append(cid)

if len(matches) != 1:
    raise SystemExit("STOP: Expected one existing Batch-2 container")

code = r'''
import sys, json, inspect
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, "/batch2")
sys.path.insert(0, "/workspace/artifacts/v1.168-max")

from native_batch2 import cta_worker_adapter as mod

classes = [
    obj for _, obj in inspect.getmembers(mod, inspect.isclass)
    if obj.__module__ == mod.__name__
    and callable(getattr(obj, "predict_batch", None))
]
if len(classes) != 1:
    raise SystemExit("STOP: Expected one Batch-2 adapter class")

cls = classes[0]
signature = inspect.signature(cls)
required = [
    p for p in signature.parameters.values()
    if p.default is inspect.Parameter.empty
    and p.kind not in (
        inspect.Parameter.VAR_POSITIONAL,
        inspect.Parameter.VAR_KEYWORD
    )
]
if required:
    raise SystemExit(f"STOP: Adapter requires initialization: {signature}")

paths = [
    Path("/workspace/artifacts/v1.168-max/test-results/cta_max_tiles_smoketest_input.json"),
    Path("/workspace/artifacts/v1.168-max/cta_native_adjusted_sanity_input.json")
]
if not all(p.is_file() for p in paths):
    raise SystemExit("STOP: Validated CTA fixtures not both accessible")

bodies = [json.loads(p.read_text()) for p in paths]
if not all(isinstance(b, dict) for b in bodies):
    raise SystemExit("STOP: Expected JSON objects")

print("TWO CTA FIXTURES: READY", flush=True)
print("EXECUTING REAL MAX BATCH-2 JSON...", flush=True)

adapter = cls()
responses = adapter.predict_batch(bodies)

if not isinstance(responses, (list, tuple)) or len(responses) != 2:
    raise RuntimeError("Batch must return exactly two responses")

for i, response in enumerate(responses, 1):
    if not isinstance(response, dict):
        raise RuntimeError(f"Response {i} is not JSON-compatible dict")
    if "error" in response:
        raise RuntimeError(f"Response {i} returned error: {response['error']}")
    json.dumps(response, allow_nan=False)
    print(f"CTA RESPONSE {i}: VALID JSON", flush=True)

print("REAL TWO-REQUEST CTA JSON BATCH-2: PASS", flush=True)
'''

r = subprocess.run(
    P + [
        "exec", "-i", "-w", "/workspace",
        "-e", "PYTHONDONTWRITEBYTECODE=1",
        "-e", "PYTHONPATH=/batch2:/workspace/artifacts/v1.168-max",
        matches[0], "/opt/venv/bin/python", "-B", "-"
    ],
    input=code, text=True, stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT, timeout=300
)

print(r.stdout[-6000:])
print("JSON BATCH-2 EXIT CODE:", r.returncode)
print("ORIGINAL DS/MAX: UNCHANGED")
print("CONTAINERS RESTARTED: NONE")
PY
