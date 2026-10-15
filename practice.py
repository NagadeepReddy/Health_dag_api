python3 - <<'PY'
import ast
from pathlib import Path

root = Path("artifacts/v1.168-max")
names = {
    "context_head", "graph", "model",
    "nlp_bert_max", "sequence_pooling_max"
}

runtime = [
    Path(line.strip())
    for line in (root / "RELEASE_CANDIDATE.txt").read_text().splitlines()
    if line.strip() and not line.startswith("#")
]

print("ACTUAL IMPORT REFERENCES:")
count = 0

for p in runtime:
    tree = ast.parse(p.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            modules = [node.module or ""]
        elif isinstance(node, ast.Import):
            modules = [x.name for x in node.names]
        else:
            continue

        for module in modules:
            if module.split(".")[-1] in names:
                print(f"{p.name}:{node.lineno} -> {module}")
                count += 1

print("MATCHES:", count)
print("NO FILES CHANGED")
PY
