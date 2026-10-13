python - <<'PY'
import ast
from pathlib import Path

root = Path("artifacts/v1.168")
base = Path("artifacts/v1.168-max/cta_max")
p = root / "utils/dependency-utils/models.py"
tree = ast.parse(p.read_text())

print("=== ORIGINAL TRANSFORMER BLOCK VL HANDLING ===")
for cls in ast.walk(tree):
    if not isinstance(cls, ast.ClassDef):
        continue
    for fn in cls.body:
        if not isinstance(fn, ast.FunctionDef):
            continue
        if fn.name != "forward":
            continue
        args = ast.unparse(fn.args)
        if "vl_in" not in args:
            continue
        if "ParallelTransformerMAEP" in cls.name:
            continue
        print("\nCLASS:", cls.name, "LINE:", fn.lineno)
        print("ARGS:", args)
        for stmt in fn.body:
            print(ast.unparse(stmt).replace("\n"," ")[:500])

print("\n=== MAX TRANSFORMER POSITION HANDLING ===")
for name in (
    "parallel_transformer_block_2layers.py",
    "parallel_transformer_graph_full_sequence.py",
    "grecbase_fusion_real_shapes_max.py"
):
    f = base/name
    if not f.exists():
        continue
    print("\nFILE:", name)
    t = ast.parse(f.read_text())
    for node in ast.walk(t):
        if isinstance(node, ast.Call):
            call = ast.unparse(node)
            if any(x in call for x in (
                "block0(", "block1(", "rotary",
                "attention_mask", "pos,"
            )):
                print("LINE",node.lineno,call[:400])

print("\nREAD ONLY — NO FILES MODIFIED")
PY
