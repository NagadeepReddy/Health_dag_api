python - <<'PY'
import ast
from pathlib import Path

base = Path("artifacts/v1.168-max/cta_max")

for p in sorted(base.glob("*.py")):
    if not any(x in p.name for x in (
        "sequence", "grecbase", "nlp_bert_in_graph",
        "main_context_max", "sibling_context_max",
        "att_pooling_max"
    )):
        continue

    tree = ast.parse(p.read_text())
    print("\nFILE:", p.name)

    for n in tree.body:
        if isinstance(n, ast.FunctionDef):
            print("FUNCTION:", n.name, ast.unparse(n.args))
        elif isinstance(n, ast.ClassDef):
            for m in n.body:
                if isinstance(m, ast.FunctionDef) and m.name == "__call__":
                    print("CLASS CALL:", n.name, ast.unparse(m.args))

print("\nINTEGRATION INTERFACES IDENTIFIED")
print("NO FILES MODIFIED")
PY
