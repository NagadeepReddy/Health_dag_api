python - <<'PY'
from pathlib import Path

root = Path("artifacts/v1.168-max/cta_max")

print("=== FULL GRAPH EXECUTION CALLERS ===")
for p in sorted(root.rglob("*.py")):
    s = p.read_text()
    if "build_grecbase_fusion_graph_all8" in s or "grecbase_fusion_all8_max" in s:
        print("\nFILE:", p)
        for i, line in enumerate(s.splitlines(), 1):
            if any(x in line for x in (
                "import ", "build_grecbase_fusion_graph_all8(",
                "session.load(", ".execute(", "weights_registry="
            )):
                print(f"{i}: {line.strip()[:180]}")

print("\n=== SAVED REAL INPUTS AND WEIGHTS ===")
for pattern in (
    "*real*model*in*.pt",
    "*real*input*.npz",
    "*integration*weight*",
):
    for p in sorted(root.glob(pattern)):
        print(p)

print("READ ONLY — NO FILES MODIFIED")
PY
