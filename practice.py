python3 - <<'PY'
from pathlib import Path

p = Path("/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/bplan_batch2_graph_dev/grecbase_fusion_full_head_72_batch2.py")

if not p.is_file():
    raise SystemExit(f"STOP: File not found: {p}")

lines = p.read_text().splitlines()

print("=== BPLAN BATCH-2 GRAPH CHANGE POINTS ===")
print("FILE:", p)

for i, line in enumerate(lines, 1):
    if any(x in line for x in (
        "def ", "TensorType(", "reshape(", "broadcast",
        "graph.output", "input_types=", "ops.concat", "ops.stack"
    )):
        print(f"{i}: {line.strip()}")

print("INSPECTION COMPLETE — NO FILES MODIFIED")
PY
