python3 -B - <<'PY'
import subprocess, json

P = ["podman", "--root", "/application1/podman/storage",
     "--runroot", "/run/containers/storage"]

ids = subprocess.check_output(P + ["ps", "-q"], text=True).split()
target = "/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029"

matches = []
for cid in ids:
    info = json.loads(subprocess.check_output(
        P + ["inspect", cid], text=True))[0]
    for m in info.get("Mounts", []):
        if m.get("Source") == target and m.get("Destination") == "/batch2":
            matches.append(cid)

if len(matches) != 1:
    raise SystemExit(
        f"STOP: Expected one existing Batch-2 container; found {len(matches)}"
    )

code = '''
import importlib.util
from pathlib import Path

p = Path("/batch2/real_max_batch2_backend.py")
spec = importlib.util.spec_from_file_location("cta_batch2_test", p)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

assert callable(module.infer_max_batch)
print("BATCH-2 BACKEND IMPORT: PASS")

candidate = Path(
    "/application1/cta_max_true_batch_dev_20261028/"
    "batch2_candidate/cta_max/run_batch2_contract.py"
)
print("BATCH HELPER VISIBLE:", candidate.is_file())
'''

r = subprocess.run(
    P + ["exec", "-i", "-e", "PYTHONDONTWRITEBYTECODE=1",
         matches[0], "/opt/venv/bin/python", "-B", "-"],
    input=code, text=True, capture_output=True, timeout=30
)

print(r.stdout)
print(r.stderr[-2000:])
print("EXIT CODE:", r.returncode)
print("CONTAINERS RESTARTED: NONE")
PY
