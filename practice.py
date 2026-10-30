PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
import ast, json, subprocess
from pathlib import Path

base = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029")
backend = base / "real_max_batch2_backend.py"
graph = Path(
    "/application1/cta_max_true_batch_dev_20261028/"
    "batch2_candidate/cta_max/grecbase_fusion_batch2_draft.py"
)

assert backend.is_file(), "STOP: Backend missing"
assert graph.is_file(), "STOP: Batch-2 graph missing"

print("=== ACTUAL GRAPH SELECTION ===")
tree = ast.parse(backend.read_text())

found = False
for node in ast.walk(tree):
    if isinstance(node, ast.ImportFrom):
        for alias in node.names:
            if alias.name == "build_grecbase_fusion_graph_order_correct":
                print("BACKEND IMPORTS:", node.module)
                found = True

print("GRAPH IMPORT FOUND:", found)
print("BATCH-2 GRAPH:", graph)
print("BATCH-2 DECLARATION:",
      "[2, 256]" in graph.read_text())

print("\n=== ACTIVE ISOLATED MOUNTS ===")
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
for env in info["Config"].get("Env", []):
    if env.startswith("PYTHONPATH="):
        print(env)

for m in info["Mounts"]:
    if any(x in m["Source"] for x in (
        "CTA_MAX_TRUE_BATCH2_DEV",
        "cta_max_true_batch_dev"
    )):
        print("MOUNT:", m["Source"], "=>", m["Destination"])

print("\nGRAPH RESOLUTION CHECK: COMPLETE")
print("FILES MODIFIED: NONE")
print("ORIGINAL MAX: UNTOUCHED")
print("ORIGINAL DS: UNCHANGED")
PY
