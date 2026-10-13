python - <<'PY'
from pathlib import Path

checks = [
    (
        "ORIGINAL v1.168 MODEL / POOLING",
        Path("artifacts/v1.168"),
        (
            "class GRecBase",
            "class AttPooling",
            "ihq_pooling",
            "jet_pooling",
            "att_pooling",
            "sibling_context_head",
        ),
    ),
    (
        "ACTIVE MAX FUSION CALLERS",
        Path("artifacts/v1.168-max"),
        (
            "build_grecbase_fusion_graph_order_correct(",
            "real_sanity_max_branches.npz",
            "real_sanity_max_output.npy",
        ),
    ),
]

for title, root, terms in checks:
    print("\n===", title, "===")
    total = 0
    for p in sorted(root.rglob("*.py")):
        if ".before_" in p.name or "backup" in p.name.lower():
            continue
        for i, line in enumerate(p.read_text(errors="replace").splitlines(), 1):
            if any(term in line for term in terms):
                print(f"{p}:{i}: {line.strip()[:170]}")
                total += 1
                if total >= 65:
                    break
        if total >= 65:
            print("OUTPUT LIMITED TO 65 MATCHES")
            break
    if not total:
        print("NO MATCHES FOUND")

print("\nREAD ONLY — NOTHING MODIFIED")
PY
