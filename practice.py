python - <<'PY'
import ast
from pathlib import Path

p = Path("artifacts/v1.168/utils/dependency-utils/models.py")
source = p.read_text()
tree = ast.parse(source)

cls = next(
    n for n in ast.walk(tree)
    if isinstance(n, ast.ClassDef) and n.name == "GRecBase"
)

for method_name in ("__init__", "forward"):
    method = next(
        n for n in cls.body
        if isinstance(n, ast.FunctionDef) and n.name == method_name
    )

    print(f"\n===== {method_name} NLP DETAILS =====")

    for node in ast.walk(method):
        segment = ast.get_source_segment(source, node)

        if isinstance(node, ast.Call):
            fn = ast.unparse(node.func)
            if "nlp_encoder" in fn or "AutoModel.from_config" in fn:
                print("CALL:", segment)

        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = (
                node.targets if isinstance(node, ast.Assign)
                else [node.target]
            )
            names = [ast.unparse(t) for t in targets]
            if any(
                "config" in n.lower() or
                "search_out" in n or
                "nlp_dim" in n
                for n in names
            ):
                print("ASSIGN:", segment[:500])

print("\nREAD-ONLY — NO FILES MODIFIED")
PY
