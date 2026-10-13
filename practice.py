python - <<'PY'
from pathlib import Path

base = Path("artifacts/v1.168-max/cta_max")

targets = [
    "grecbase_fusion_graph_all8_max.py",
    "grecbase_fusion_order_correct_max.py",
    "grecbase_fusion_graph_real_shapes_max.py",
    "grecbase_fusion_graph_with_context_max.py",
    "grecbase_fusion_graph_with_aux_max.py",
    "grecbase_max.py",
]

terms = (
    "context", "sequence", "sibling", "ihq",
    "jet", "task", "branch", "placeholder",
    "random", "zeros(", "ones(", "graph.output",
)

print("=== SIX-BRANCH INTEGRATION SOURCE AUDIT ===")

for name in targets:
    p = base / name
    if not p.is_file():
        continue

    lines = p.read_text(errors="replace").splitlines()
    matches = [
        i for i, line in enumerate(lines)
        if any(t in line.lower() for t in terms)
        and not line.strip().startswith("#")
    ]

    if not matches:
        continue

    print(f"\n=== {name} ===")
    shown = set()
    for i in matches[:22]:
        for j in range(max(0, i-1), min(len(lines), i+2)):
            if j not in shown:
                print(f"{j+1}: {lines[j][:190]}")
                shown.add(j)

    if len(matches) > 22:
        print(f"... {len(matches)-22} further matching lines")

print("\n=== SAVED BRANCH RESULTS PRODUCER ===")
found = False
for p in sorted(base.glob("*.py")):
    lines = p.read_text(errors="replace").splitlines()
    for i, line in enumerate(lines):
        if "real_sanity_max_branches" in line:
            found = True
            print(f"{p.name}:{i+1}: {line.strip()[:190]}")
if not found:
    print("No saved producer script found; may have been a terminal-only run")

print("\nREAD ONLY — NO TESTS OR FILES MODIFIED")
PY
