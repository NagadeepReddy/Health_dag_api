cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
import ast

roots = {
    "CTA": Path("/application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168-max/cta_native_batch2_release_candidate/maxserve_cta_extension"),
    "BPLAN": Path("/application1/BPLAN_MAX_FINAL_TEAM_HANDOFF_20261102/artifacts/v1.113-max/maxserve_bplan_extension/bplan_native_serve_dev")
}

for name, root in roots.items():
    print(f"\n=== {name} NATIVE MAX COMPONENTS ===")
    if not root.is_dir():
        print("PATH UNAVAILABLE:", root)
        continue
    for p in sorted(root.glob("*.py")):
        tree = ast.parse(p.read_text())
        classes = [n.name for n in tree.body if isinstance(n, ast.ClassDef)]
        functions = [n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        print(f"{p.name}: classes={classes[:5]}, functions={functions[:6]}")
PY
