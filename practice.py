python3 - <<'PY'
import subprocess, json
from pathlib import Path

P = ["podman", "--root", "/application1/podman/storage",
     "--runroot", "/run/containers/storage"]

src = Path("/application1/cta_max_true_batch_dev_20261028/batch2_candidate")
target = src / "cta_max/grecbase_fusion_batch2_draft.py"

if not target.is_file() or "CTA_BATCH2_BRANCH_SHAPES" not in target.read_text():
    raise SystemExit("STOP: Installed trace not found")

ids = subprocess.check_output(P + ["ps", "-q"], text=True).split()
matches = []

for cid in ids:
    data = json.loads(subprocess.check_output(P + ["inspect", cid], text=True))[0]
    for mount in data.get("Mounts", []):
        if (mount.get("Destination") == "/batch2" and
            Path(mount.get("Source", "/")).resolve() == src.resolve()):
            matches.append(cid)

if len(matches) != 1:
    raise SystemExit(f"STOP: Expected one running isolated Batch-2 container; found {len(matches)}")

code = """
import sys
sys.dont_write_bytecode = True
sys.path[:0] = ["/batch2", "/workspace/artifacts/v1.168-max"]
import cta_max
cta_max.__path__.insert(0, "/batch2/cta_max")
from max.graph import DeviceRef
from cta_max.grecbase_fusion_batch2_draft import build_grecbase_fusion_graph_order_correct

print("BUILDING ISOLATED BATCH-2 GRAPH", flush=True)
graph = build_grecbase_fusion_graph_order_correct(DeviceRef.CPU())
print("GRAPH BUILD: PASS", len(graph.inputs), flush=True)
"""

try:
    r = subprocess.run(
        P + ["exec", "-i", "-e", "PYTHONDONTWRITEBYTECODE=1",
             "-e", "PYTHONPATH=/batch2:/workspace/artifacts/v1.168-max",
             matches[0], "/opt/venv/bin/python", "-"],
        input=code, text=True, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, timeout=90
    )
    print(r.stdout[-12000:])
    print("EXIT CODE:", r.returncode)
except subprocess.TimeoutExpired:
    print("STOP: Graph build exceeded 90 seconds")

print("ORIGINAL DS/MAX: UNCHANGED")
print("CONTAINERS RESTARTED: NONE")
PY
