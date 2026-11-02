python3 - <<'PY'
from pathlib import Path

root = Path("/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension")
files = [
    root / "bplan_max_dev/grecbase_fusion_full_head_72_max.py",
    root / "bplan_max_dev/run_real_sanity_input_adapter.py",
    root / "bplan_max_dev/bplan_max_model_adapter.py",
    root / "bplan_native_serve_dev/bplan_native_worker_registration.py",
]

terms = (
    "def build_", "def build_real_inputs", "TensorType(",
    "Graph(", "reshape(", "broadcast(", "max_items_per_iteration",
    "batch_size", "batch_dim", "predict_batch",
    "shape == ", "shape =", "[1,", "(1,"
)

for path in files:
    print(f"\n=== {path.name} ===")
    if not path.is_file():
        print("FILE NOT FOUND")
        continue

    lines = path.read_text().splitlines()
    matches = [
        (i, line.strip())
        for i, line in enumerate(lines, 1)
        if any(term in line for term in terms)
    ]

    for number, line in matches[:90]:
        print(f"{number}: {line[:180]}")
    print("MATCHES:", len(matches))

print("\nBPLAN BATCH-2 GRAPH INSPECTION COMPLETE")
PY
