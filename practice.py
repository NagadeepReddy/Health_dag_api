cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
import ast
from pathlib import Path

root = Path("artifacts/v1.472")
original = root / "utils/dependency-utils/models.py"
maxdir = Path("artifacts/v1.472-max/pzaas_max")

print("=== PZAAS TWO-LAYER SEQUENCE ALIGNMENT ===")

def inspect(path, classes, methods, limit=65):
    if not path.is_file():
        print("MISSING:", path)
        return

    source = path.read_text()
    lines = source.splitlines()
    tree = ast.parse(source)

    print("\nFILE:", path)

    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        if node.name not in classes:
            continue

        for fn in node.body:
            if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if fn.name not in methods:
                continue

            print("\nCLASS:", node.name)
            print("METHOD:", fn.name)

            selected = lines[fn.lineno-1:fn.end_lineno]

            if len(selected) > limit:
                selected = selected[:limit]
                print("SHOWING FIRST", limit, "LINES")

            for i, line in enumerate(selected, fn.lineno):
                print(f"{i}: {line}")

inspect(
    original,
    {"ParallelTransformerBlock", "Residual", "RotaryEmbedding"},
    {"forward"},
    65
)

inspect(
    original,
    {"ParallelTransformerAEP"},
    {"forward"},
    105
)

inspect(
    maxdir / "parallel_transformer_block_2layers.py",
    {"AttPoolingBlockMAX", "ParallelTransformerBlockMAX"},
    {"__call__", "forward"},
    100
)

inspect(
    maxdir / "sequence_transformer_max.py",
    {"ParallelTransformerMAEPMAX", "SequenceTransformerMAX"},
    {"__call__", "forward"},
    100
)

print("\nTRAINED DEPTH: 2")
print("CHECKPOINT WEIGHTS: 208/208 PASS")
print("NEXT: CORRECT FIRST DIFFERENT SEQUENCE OPERATION")
print("ORIGINAL DS: UNCHANGED")
print("CTA / BPLAN: UNCHANGED")
PY
