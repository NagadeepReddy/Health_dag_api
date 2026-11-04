cd /application1/sajjna8/rt-pzaas-v1.0 || exit 1

python3 - <<'PY'
from pathlib import Path
import ast

print("=== PZAAS ORIGINAL SEQUENCE SOURCE ===")

roots = [
    Path("artifacts/v1.472"),
    Path("/workspace/artifacts/v1.472"),
]

seen = set()
found = 0

for root in roots:
    if not root.is_dir():
        print("PATH UNAVAILABLE:", root)
        continue

    for p in root.rglob("*.py"):
        path = str(p.resolve())
        if path in seen:
            continue
        seen.add(path)

        try:
            source = p.read_text(errors="replace")
        except OSError:
            continue

        if not any(x in source for x in (
            "class ParallelTransformerMAEP",
            "page_full_out",
            "item_full_out",
        )):
            continue

        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue

        lines = source.splitlines()

        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            if "ParallelTransformer" not in node.name:
                continue

            found += 1
            print("\nFILE:", p)
            print("CLASS:", node.name)

            methods = [
                n for n in node.body
                if isinstance(n, ast.FunctionDef)
                and n.name in ("__init__", "forward")
            ]

            for method in methods:
                print("\nMETHOD:", method.name)
                print("LINES:", method.lineno, "-", method.end_lineno)

                if method.name == "__init__":
                    keywords = (
                        "num_layers", "transformer",
                        "embedding", "seq_dense",
                        "pooling", "page_meta",
                    )
                else:
                    keywords = (
                        "page_", "item_", "wide_",
                        "torch.cat", "transformer",
                        "pooling", "seq_dense",
                        "return", "norm",
                    )

                selected = [
                    i for i in range(
                        method.lineno,
                        method.end_lineno + 1
                    )
                    if any(
                        k in lines[i-1].lower()
                        for k in keywords
                    )
                ]

                for i in selected[:65]:
                    print(f"{i}: {lines[i-1].strip()[:170]}")

                if len(selected) > 65:
                    print("MORE MATCHING LINES:", len(selected)-65)

print("\nMATCHING CLASSES:", found)

if found:
    print("ORIGINAL SEQUENCE SOURCE: LOCATED")
    print("NEXT: ALIGN FIRST DIVERGENT MAX OPERATION")
else:
    print("ORIGINAL SEQUENCE SOURCE: NOT LOCATED")
    print("NEXT: RESOLVE ORIGINAL SOURCE PATH")

print("FILES MODIFIED: 0")
print("CTA / BPLAN: UNCHANGED")
PY
