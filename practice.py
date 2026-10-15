python3 - <<'PY'
import ast
from pathlib import Path

root = Path("artifacts/v1.168-max")
start = [
    "cta_max/serve_max.py",
    "cta_max/live_cta_pipeline_bridge.py",
    "cta_max/run_live_max_inference.py",
    "cta_max/run_real_sanity_input_adapter.py",
    "cta_max/grecbase_fusion_full_head_72_max.py",
]

seen = set()
pending = [root / p for p in start]

while pending:
    p = pending.pop()
    if p in seen or not p.is_file():
        continue
    seen.add(p)
    tree = ast.parse(p.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            names = [node.module]
        elif isinstance(node, ast.Import):
            names = [x.name for x in node.names]
        else:
            continue
        for name in names:
            if name.startswith("cta_max."):
                candidate = root / (name.replace(".", "/") + ".py")
                if candidate.is_file():
                    pending.append(candidate)

print("RUNTIME PYTHON DEPENDENCIES:", len(seen))
for p in sorted(seen):
    print(p)
print("NO FILES MODIFIED")
PY
