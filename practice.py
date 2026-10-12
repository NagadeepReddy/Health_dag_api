python - <<'PY'
import ast
from pathlib import Path

base = Path("artifacts/v1.168-max/cta_max")
models = Path("artifacts/v1.168/utils/dependency-utils/models.py")

print("=== ORIGINAL NLP OPERATIONS ===")
lines = models.read_text().splitlines()
for i, line in enumerate(lines):
    if any(s in line for s in (
        "nlp_act0", "nlp_act1", "nlp_dense0",
        "nlp_dense1", "seq_dense"
    )):
        print(f"{i+1}: {line.strip()[:180]}")

print("\n=== EXISTING MAX BRANCH INTERFACES ===")
targets = {
    "nlp_bert_in_graph.py": ["nlp_bert_forward"],
    "sibling_context_max.py": ["sibling_context_forward"],
    "main_context_max.py": ["main_context_forward"],
    "grecbase_aux_branches_max.py": ["grecbase_aux_features"],
}

for filename, names in targets.items():
    p = base / filename
    print(f"\n{filename}:")
    if not p.exists():
        print("MISSING")
        continue
    tree = ast.parse(p.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name in names:
            print("ARGS:", ast.unparse(node.args)[:240])
            for child in ast.walk(node):
                if isinstance(child, ast.Return):
                    print("RETURN:", ast.unparse(child.value)[:240])

print("\n=== SEQUENCE GRAPH CONNECTIONS ===")
p = base / "parallel_transformer_graph_full_sequence.py"
if p.exists():
    tree = ast.parse(p.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            if "graph" in node.name or "sequence" in node.name:
                print("FUNCTION:", node.name, ast.unparse(node.args)[:180])
        if isinstance(node, ast.Call):
            name = ast.unparse(node.func)
            if name.endswith(".output"):
                print("OUTPUT:", ast.unparse(node)[:240])
else:
    print("SEQUENCE FILE MISSING")

print("\n=== CURRENT WORKING FUSION ===")
p = base / "grecbase_fusion_with_context_max.py"
print("FILE EXISTS:", p.exists())
if p.exists():
    tree = ast.parse(p.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name.startswith("build_"):
            print("BUILDER:", node.name)
            print("ARGS:", ast.unparse(node.args))

print("\nREAD ONLY — NO FILES MODIFIED")
PY
