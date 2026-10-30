PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
from pathlib import Path
import ast, json, subprocess

base = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029")
repo = Path("/application1/sajjna8/rt-pzaas-cta-offers-v1")
candidate = Path("/application1/cta_max_true_batch_dev_20261028/batch2_candidate")
backend = base / "real_max_batch2_backend.py"

print("=== ACTUAL BACKEND GRAPH IMPORT ===")
assert backend.is_file(), "STOP: Backend missing"
source = backend.read_text()
tree = ast.parse(source)
modules = set()

for node in ast.walk(tree):
    if isinstance(node, ast.ImportFrom):
        names = [a.name for a in node.names]
        if any("graph" in n.lower() or "grecbase" in n.lower()
               for n in names):
            print(f"FROM {node.module}: {names}")
            if node.module:
                modules.add(node.module)

print("\n=== GRAPH SOURCE DECLARATIONS ===")
paths = [candidate / "cta_max/grecbase_fusion_batch2_draft.py"]

for module in sorted(modules):
    rel = Path(*module.split(".")).with_suffix(".py")
    paths += [
        candidate / rel,
        repo / "artifacts/v1.168-max" / rel,
        repo / rel,
    ]

seen = set()
for path in paths:
    if path in seen or not path.is_file():
        continue
    seen.add(path)
    print("FILE:", path)
    lines = path.read_text().splitlines()
    for i, line in enumerate(lines, 1):
        if "input_types=" in line or "graph = Graph(" in line:
            print(f"LINE {i}: {line.strip()[:380]}")

print("\n=== ISOLATED CONTAINER CONFIG ===")
pod = [
    "podman", "--root", "/application1/podman/storage",
    "--runroot", "/run/containers/storage"
]
r = subprocess.run(
    pod + ["inspect", "cta-batch2-trace-8766-10g"],
    capture_output=True, text=True
)
assert r.returncode == 0, r.stderr
info = json.loads(r.stdout)[0]
print("STATUS:", info["State"]["Status"])
print("WORKDIR:", info["Config"].get("WorkingDir"))
for env in info["Config"].get("Env", []):
    if env.startswith("PYTHONPATH="):
        print(env)
for m in info["Mounts"]:
    if any(s in m["Source"].lower()
           for s in ("batch", "cta", "workspace")):
        print("MOUNT:", m["Source"], "=>", m["Destination"])

print("\nTARGETED GRAPH CHECK: COMPLETE")
print("ORIGINAL MAX / DS: UNCHANGED")
print("FILES MODIFIED: 0")
PY
