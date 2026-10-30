python3 -B - <<'PY'
from pathlib import Path
import subprocess, json

P = ["podman", "--root", "/application1/podman/storage",
     "--runroot", "/run/containers/storage"]
dev = "/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029"

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
import sys, os, ast, json, inspect, hashlib
import numpy as np
from pathlib import Path

root = Path("/workspace")
core = root / "artifacts/v1.168/core-artifact"
mx = root / "artifacts/v1.168-max"
sys.path[:0] = [str(core), str(mx), "/batch2"]

spawn = mx / "maxserve_cta_extension/cta_spawn_worker.py"
if spawn.is_file():
    for n in ast.walk(ast.parse(spawn.read_text())):
        if not (isinstance(n, ast.Call) and
                isinstance(n.func, ast.Attribute) and
                n.func.attr == "setdefault" and len(n.args) >= 2):
            continue
        try:
            k, v = ast.literal_eval(n.args[0]), ast.literal_eval(n.args[1])
        except (TypeError, ValueError, SyntaxError):
            continue
        if k in ("modelId", "expThrottleLabel") and isinstance(v, str):
            os.environ.setdefault(k, v)

import pipeline
from native_batch2 import cta_worker_adapter as mod

classes = [
    c for _, c in inspect.getmembers(mod, inspect.isclass)
    if c.__module__ == mod.__name__
    and callable(getattr(c, "predict_batch", None))
]
assert len(classes) == 1

# Preprocessing only — no model execution.
adapter = classes[0](pipeline.pipeline, lambda x: x)
instance = adapter.initialize()

fixtures = [
    mx / "test-results/cta_max_tiles_smoketest_input.json",
    mx / "cta_native_adjusted_sanity_input.json",
    root / "artifacts/v1.168/samples/sanity_input.json"
]

def fingerprint(value):
    if hasattr(value, "detach"):
        value = value.detach().cpu().numpy()
    try:
        arr = np.asarray(value)
        if arr.dtype.kind not in "OUSV":
            return (
                str(arr.dtype), tuple(arr.shape),
                hashlib.sha256(
                    np.ascontiguousarray(arr).tobytes()
                ).hexdigest()
            )
    except (TypeError, ValueError):
        pass
    return ("other", repr(value))

prepared = []
for path in fixtures:
    if not path.is_file():
        print("SKIP MISSING:", path.name, flush=True)
        continue
    try:
        body = json.loads(path.read_text())
        result = instance.preprocess(body)
        inputs = result[0]
        assert isinstance(inputs, dict)
        prepared.append((path.name, {
            k: fingerprint(v) for k, v in inputs.items()
        }))
        print("PREPROCESS PASS:", path.name,
              "INPUTS:", len(inputs), flush=True)
    except Exception as exc:
        print("SKIP INVALID:", path.name,
              type(exc).__name__, str(exc)[:200], flush=True)

found = False
for i in range(len(prepared)):
    for j in range(i + 1, len(prepared)):
        name1, a = prepared[i]
        name2, b = prepared[j]
        different = sum(
            a.get(k) != b.get(k)
            for k in a.keys() | b.keys()
        )
        print("PAIR:", name1, "+", name2,
              "DIFFERENT INPUTS:", different, flush=True)
        if different > 0:
            found = True

print("DISTINCT MODEL INPUT PAIR:", "FOUND" if found else "NOT FOUND")
print("MAX EXECUTIONS: ZERO")
print("ORIGINAL DS/MAX: UNCHANGED")
'''

try:
    r = subprocess.run(
        P + ["exec", "-i", "-w", "/workspace",
             "-e", "PYTHONDONTWRITEBYTECODE=1",
             ids[0], "/opt/venv/bin/python", "-B", "-"],
        input=code, text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=90
    )
    print(r.stdout[-4500:])
    print("EXIT CODE:", r.returncode)
except subprocess.TimeoutExpired:
    print("STOP: Preprocessing check exceeded 90 seconds")

print("CONTAINERS RESTARTED: NONE")
PY
