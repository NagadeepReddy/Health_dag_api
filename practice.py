ROOT=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension/bplan_max_dev
STAGE=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/bplan_batch2_graph_dev

ROOT="$ROOT" STAGE="$STAGE" python3 - <<'PY'
from pathlib import Path
import os, shutil, ast

src = Path(os.environ["ROOT"])
dst = Path(os.environ["STAGE"])
dst.mkdir(parents=True, exist_ok=True)

files = sorted(src.glob("*.py"))
for f in files:
    target = dst / f.name
    if target.exists():
        print("PRESERVED EXISTING:", f.name)
    else:
        shutil.copy2(f, target)

print("BPLAN BATCH-2 ISOLATED SOURCE:", dst)
print("PYTHON FILES:", len(list(dst.glob("*.py"))))

entry = dst / "grecbase_fusion_full_head_72_max.py"
if not entry.is_file():
    raise SystemExit("STOP: main graph file missing")

lines = entry.read_text().splitlines()
print("\n=== GRAPH INPUT AND SHAPE LOCATIONS ===")
for i, line in enumerate(lines, 1):
    if any(x in line for x in (
        "Graph(", "TensorType(", "input_types=",
        "ops.reshape(", "ops.constant(", "graph.output("
    )):
        print(f"{i}: {line.strip()[:160]}")

for f in dst.glob("*.py"):
    ast.parse(f.read_text(), filename=str(f))

print("\nISOLATED BATCH-2 SOURCE SYNTAX: PASS")
print("ORIGINAL MAX SOURCE: UNCHANGED")
PY
