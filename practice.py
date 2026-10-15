python3 - <<'PY'
from pathlib import Path
import ast

root = Path("artifacts/v1.168-max")
manifest = root / "RELEASE_CANDIDATE.txt"
existing = manifest.read_text()

names = ["nlp_bert_max.py", "sequence_pooling_max.py"]

for name in names:
    p = root / "cta_max" / name
    if not p.is_file():
        print("MISSING:", name)
        continue
    if str(p) not in existing:
        with manifest.open("a") as f:
            f.write(str(p) + "\n")
        print("ADDED:", name)

    print("\nLOCAL IMPORTS IN", name)
    tree = ast.parse(p.read_text())
    for node in ast.walk(tree):
        modules = []
        if isinstance(node, ast.ImportFrom):
            modules = [node.module or ""]
        elif isinstance(node, ast.Import):
            modules = [x.name for x in node.names]

        for module in modules:
            short = module.removeprefix("cta_max.")
            candidate = root / "cta_max" / (short.replace(".", "/") + ".py")
            if candidate.is_file():
                print(" ", module)

print("\nRELEASE LIST UPDATED — NO FILES DELETED")
PY
