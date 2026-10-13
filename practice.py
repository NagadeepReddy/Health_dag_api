python - <<'PY'
import ast
from pathlib import Path

original = Path("artifacts/v1.168/utils/dependency-utils/models.py")
base = Path("artifacts/v1.168-max/cta_max")

def functions(path):
    tree = ast.parse(path.read_text())
    return tree, [
        n for n in ast.walk(tree)
        if isinstance(n, ast.FunctionDef)
    ]

tree, fns = functions(original)

print("=== ORIGINAL PYTORCH GRecBase ===")
cls = next(
    n for n in ast.walk(tree)
    if isinstance(n, ast.ClassDef) and n.name == "GRecBase"
)
forward = next(
    n for n in cls.body
    if isinstance(n, ast.FunctionDef) and n.name == "forward"
)

for node in ast.walk(forward):
    if isinstance(node, ast.Assign):
        if any(
            isinstance(t, ast.Name) and t.id == "outs"
            for t in node.targets
        ):
            print("OUTS =", ast.unparse(node.value))

print("\n=== MAX FUSION ===")
p = base / "grecbase_fusion_parity_max.py"
_, fns = functions(p)
fn = next(n for n in fns if n.name ==
          "build_grecbase_fusion_graph_parity")

for node in ast.walk(fn):
    if isinstance(node, ast.Assign):
        if any(
            isinstance(t, ast.Name) and t.id in
            ("outs", "task", "ihq", "jet")
            for t in node.targets
        ):
            print(ast.unparse(node)[:500])

print("\n=== MAX AUXILIARY RETURN ===")
for p in sorted(base.glob("*aux*max.py")):
    _, fns = functions(p)
    for fn in fns:
        if "aux" in fn.name:
            print("FILE:", p.name)
            print("FUNCTION:", fn.name)
            for node in ast.walk(fn):
                if isinstance(node, ast.Return):
                    print("RETURN:", ast.unparse(node.value))

print("\nREAD ONLY — NO FILES MODIFIED")
PY
