python3 -B - <<'PY'
import subprocess, json

P = ["podman", "--root", "/application1/podman/storage",
     "--runroot", "/run/containers/storage"]

target = "/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029"
matches = []

for cid in subprocess.check_output(P + ["ps", "-q"], text=True).split():
    info = json.loads(subprocess.check_output(
        P + ["inspect", cid], text=True))[0]

    for m in info.get("Mounts", []):
        if m.get("Source") == target and m.get("Destination") == "/batch2":
            matches.append(cid)

if len(matches) != 1:
    raise SystemExit(f"STOP: Expected one Batch-2 container; found {len(matches)}")

code = '''
from pathlib import Path
import importlib.util

p = Path("/batch2/real_max_batch2_backend.py")
print("BACKEND:", p.is_file(), flush=True)

paths = [
    Path("/batch2/cta_max/parallel_transformer_block_2layers.py"),
    Path("/application1/cta_max_true_batch_dev_20261028/batch2_candidate/cta_max/parallel_transformer_block_2layers.py")
]
for path in paths:
    print("TRANSFORMER:", path, path.is_file(), flush=True)

spec = importlib.util.spec_from_file_location("cta_batch2_test", p)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

assert callable(module.infer_max_batch)
print("BATCH-2 BACKEND IMPORT: PASS")
'''

r = subprocess.run(
    P + ["exec", "-i", "-e", "PYTHONDONTWRITEBYTECODE=1",
         matches[0], "/opt/venv/bin/python", "-B", "-"],
    input=code, text=True, capture_output=True, timeout=30
)

print(r.stdout)
if r.returncode:
    print(r.stderr[-2500:])
print("EXIT CODE:", r.returncode)
print("CONTAINERS RESTARTED: NONE")
PY
