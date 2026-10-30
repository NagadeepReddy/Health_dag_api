python3 -B - <<'PY'
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
    raise SystemExit("STOP: Expected one existing development container")

code = r'''
import sys, os, ast, json, hashlib, inspect, io, contextlib
from pathlib import Path
import numpy as np

root = Path("/workspace")
core = root / "artifacts/v1.168/core-artifact"
mx = root / "artifacts/v1.168-max"

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
        except (TypeError, ValueError, SyntaxError):
            continue
        if k in ("modelId", "expThrottleLabel") and isinstance(v, str):
            os.environ.setdefault(k, v)

import pipeline
from native_batch2 import cta_worker_adapter

classes = [
    c for _, c in inspect.getmembers(cta_worker_adapter, inspect.isclass)
    if c.__module__ == cta_worker_adapter.__name__
    and callable(getattr(c, "predict_batch", None))
]

assert len(classes) == 1

with contextlib.redirect_stdout(io.StringIO()):
    adapter = classes[0](pipeline.pipeline, lambda x: x)
    original = adapter.initialize()

def fingerprint(v):
    if hasattr(v, "detach"):
        v = v.detach().cpu().numpy()
    try:
        a = np.asarray(v)
        if a.dtype.kind not in "OUSV":
            return (str(a.dtype), tuple(a.shape),
                    hashlib.sha256(
                        np.ascontiguousarray(a).tobytes()
                    ).hexdigest())
    except (ValueError, TypeError):
        pass
    return ("other", hashlib.sha256(
        repr(v).encode()).hexdigest())

def preprocess(path):
    body = json.loads(path.read_text())
    if not isinstance(body, dict):
        return None
    with contextlib.redirect_stdout(io.StringIO()):
        result = original.preprocess(body)
    inputs = result[0]
    if not isinstance(inputs, dict) or len(inputs) != 17:
        return None
    return {k: fingerprint(v) for k, v in inputs.items()}

baseline = mx / "test-results/cta_max_tiles_smoketest_input.json"
if not baseline.is_file():
    raise SystemExit("STOP: Verified baseline unavailable")

reference = preprocess(baseline)
if reference is None:
    raise SystemExit("STOP: Baseline preprocessing changed")

# Exclude the three already-tested fixtures.
excluded = {
    baseline.resolve(),
    (mx / "cta_native_adjusted_sanity_input.json").resolve(),
    (root / "artifacts/v1.168/samples/sanity_input.json").resolve()
}

folders = [
    root / "artifacts/v1.168/samples",
    mx / "test-results",
    mx
]

files = set()
for folder in folders:
    if folder.is_dir():
        for p in folder.rglob("*.json"):
            if (p.is_file() and not p.is_symlink()
                and p.resolve() not in excluded
                and p.stat().st_size < 2_000_000
                and any(word in p.name.lower() for word in
                    ("input", "request", "sample",
                     "fixture", "payload", "smoke"))):
                files.add(p)

candidates = sorted(files)[:60]
print("NEW REQUEST FIXTURES FOUND:", len(candidates), flush=True)

tested = 0
found = None

for p in candidates:
    try:
        signature = preprocess(p)
        if signature is None:
            continue
        tested += 1

        if signature.keys() != reference.keys():
            continue

        # Require matching tensor types and shapes.
        compatible = all(
            a[:-1] == signature[k][:-1]
            for k, a in reference.items()
        )
        if not compatible:
            continue

        different = sum(
            reference[k] != signature[k]
            for k in reference
        )

        if different:
            found = (p, different)
            break

    except Exception:
        continue

print("ADDITIONAL VALID FIXTURES:", tested)

if found:
    print("DISTINCT MODEL INPUT PAIR: FOUND")
    print("REQUEST 1:", baseline)
    print("REQUEST 2:", found[0])
    print("DIFFERENT MODEL INPUTS:", found[1])
else:
    print("DISTINCT MODEL INPUT PAIR: NOT FOUND IN EXISTING FIXTURES")

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
        timeout=120
    )
    print(r.stdout[-4000:])
    print("EXIT CODE:", r.returncode)
except subprocess.TimeoutExpired:
    print("STOP: Fixture scan exceeded 120 seconds")

print("CONTAINERS RESTARTED: NONE")
PY
