python - <<'PY'
import ast
from pathlib import Path

base = Path("artifacts/v1.168-max/cta_max")

for filename in (
    "parallel_transformer_graph_full_sequence.py",
    "sibling_context_max.py",
):
    p = base / filename
    src = p.read_text()
    tree = ast.parse(src)

    print("\n===", filename, "===")
    print("IMPORTS:")
    for n in tree.body:
        if isinstance(n, (ast.Import, ast.ImportFrom)):
            print(ast.unparse(n))

    if "parallel_transformer" in filename:
        print("SEQUENCE CONSTRUCTION:")
        for n in ast.walk(tree):
            if isinstance(n, ast.Assign):
                names = [
                    t.id for t in n.targets
                    if isinstance(t, ast.Name)
                ]
                if any(x in names for x in (
                    "features", "block0", "block1",
                    "postprocess", "x", "x1", "x2"
                )):
                    print(ast.unparse(n)[:500])
    else:
        print("SIBLING CONSTANTS AND FORWARD:")
        for n in tree.body:
            if isinstance(n, ast.Assign):
                print(ast.unparse(n)[:300])
            elif isinstance(n, ast.FunctionDef) and n.name == "sibling_context_forward":
                print("ARGUMENTS:", ast.unparse(n.args))
                for child in ast.walk(n):
                    if isinstance(child, ast.Assign):
                        s = ast.unparse(child)
                        if any(t in s for t in (
                            "deep_ids", "wide_input",
                            "embeddings =", "reshape"
                        )):
                            print(s[:350])
                print("FINAL RETURN:",
                      ast.unparse([
                          n for n in ast.walk(n)
                          if isinstance(n, ast.Return)
                      ][0].value)[:300])

print("\nREAD ONLY — NO FILES MODIFIED")
PY
