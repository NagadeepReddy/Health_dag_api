python - <<'PY'
import ast
from pathlib import Path

p = Path("artifacts/v1.168/utils/dependency-utils/models.py")
tree = ast.parse(p.read_text())
classes = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)}

print("=== ORIGINAL GRecBase SEQUENCE INITIALIZATION ===")
grec = classes["GRecBase"]
for fn in grec.body:
    if isinstance(fn, ast.FunctionDef) and fn.name == "__init__":
        for n in ast.walk(fn):
            if isinstance(n, (ast.Assign, ast.AnnAssign)):
                targets = n.targets if isinstance(n, ast.Assign) else [n.target]
                if any("self.sequence_transformer" in ast.unparse(t) for t in targets):
                    print("LINE", n.lineno, ast.unparse(n)[:1200])

print("\n=== ORIGINAL TRANSFORMER CLASSES ===")
for cls in classes.values():
    for fn in cls.body:
        if not isinstance(fn, ast.FunctionDef) or fn.name != "forward":
            continue
        args = ast.unparse(fn.args)
        if "vl_in" in args or (
            "Transformer" in cls.name and
            any(x in args for x in ("page_in", "item_in"))
        ):
            print("\nCLASS:", cls.name, "LINE:", fn.lineno)
            print("ARGS:", args)
            for stmt in fn.body:
                print(" ", ast.unparse(stmt).replace("\n", " ")[:300])

print("\n=== ACTUAL MAX SEQUENCE CONNECTION ===")
p = Path("artifacts/v1.168-max/cta_max/grecbase_fusion_real_shapes_max.py")
t = ast.parse(p.read_text())
for n in ast.walk(t):
    if isinstance(n, ast.Assign):
        s = ast.unparse(n)
        if any(k in s for k in ("features(", "block0(", "block1(", "postprocess(", "seq_w", "seq_b")):
            print("LINE", n.lineno, s[:400])

print("\nREAD ONLY — NO FILES MODIFIED")
PY
