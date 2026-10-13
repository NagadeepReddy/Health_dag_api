cd /application/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

python3 - <<'PY'
import ast
from pathlib import Path

p = Path("artifacts/v1.168-max/cta_max/grecbase_fusion_full_head_72_max.py")
tree = ast.parse(p.read_text())

for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.name == "build_grecbase_fusion_graph_order_correct":
        print("BUILDER:", node.name)

        for n in ast.walk(node):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute):
                if n.func.attr == "output":
                    print("GRAPH OUTPUT:", n.lineno, ast.unparse(n))
                elif n.func.attr == "execute":
                    print("EXECUTE:", n.lineno, ast.unparse(n))

            if isinstance(n, ast.Return):
                print("RETURN:", n.lineno, ast.unparse(n))

        print("HEAD CALLS:", [
            n.lineno for n in ast.walk(node)
            if isinstance(n, ast.Call)
            and isinstance(n.func, ast.Name)
            and n.func.id == "grecbase_get_path_max"
        ])
PY
