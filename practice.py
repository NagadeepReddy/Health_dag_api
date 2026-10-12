python - <<'PY'
import ast
from pathlib import Path

base = Path("artifacts/v1.168-max/cta_max")
p = base / "nlp_bert_in_graph.py"
source = p.read_text()
lines = source.splitlines()
tree = ast.parse(source)

print("=== EXISTING NLP FORWARD CONTRACT ===")

for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.name == "nlp_bert_forward":
        print("ARGS:", ast.unparse(node.args))
        print("FIRST 25 LINES:")
        for n in range(node.lineno, min(node.end_lineno, node.lineno+24)+1):
            print(f"{n}: {lines[n-1]}")

        print("LAST 12 LINES:")
        for n in range(max(node.lineno, node.end_lineno-11), node.end_lineno+1):
            print(f"{n}: {lines[n-1]}")

p = Path("artifacts/v1.168/utils/dependency-utils/models.py")
lines = p.read_text().splitlines()

print("\n=== ORIGINAL NLP ACTIVATIONS ===")
for i, line in enumerate(lines):
    if "self.nlp_act0 =" in line or "self.nlp_act1 =" in line:
        print(f"{i+1}: {line.strip()}")

print("\nREAD ONLY — NO FILES MODIFIED")
PY
