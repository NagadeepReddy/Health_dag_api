python - <<'PY'
import ast
from pathlib import Path

orig = Path("artifacts/v1.168/utils/dependency-utils/models.py")
base = Path("artifacts/v1.168-max/cta_max")

print("=== ORIGINAL PYTORCH PADDING MASK ===")
tree = ast.parse(orig.read_text())

for cls in ast.walk(tree):
    if not isinstance(cls, ast.ClassDef):
        continue
    for fn in cls.body:
        if not isinstance(fn, ast.FunctionDef):
            continue
        if fn.name == "create_key_padding_mask":
            print("CLASS:", cls.name)
            print(ast.unparse(fn)[:3000])
        elif (
            cls.name == "ParallelTransformerBlock"
            and fn.name == "forward"
        ):
            for stmt in fn.body:
                s = ast.unparse(stmt)
                if any(k in s for k in (
                    "mask", "valid_length", "masked_fill", "softmax"
                )):
                    print("ORIGINAL:", s[:650])

print("\n=== MAX ATTENTION MASK IMPLEMENTATION ===")
p = base / "parallel_transformer_block_2layers.py"
assert p.is_file(), p
lines = p.read_text().splitlines()

keywords = (
    "mask", "valid_length", "seq_len",
    "softmax", "causal", "block0", "block1"
)
selected = set()

for i, line in enumerate(lines):
    if any(k in line.lower() for k in keywords):
        selected.update(range(
            max(0, i-2),
            min(len(lines), i+3)
        ))

for i in sorted(selected):
    print(f"{i+1}: {lines[i]}")

print("\n=== REAL FUSION MASK / BLOCK CONNECTIONS ===")
p = base / "grecbase_fusion_real_shapes_max.py"
assert p.is_file(), p

for i, line in enumerate(p.read_text().splitlines(), 1):
    if any(k in line.lower() for k in (
        "mask", "valid", "vl_in", "block0(",
        "block1(", "seq_raw", "pos ="
    )):
        print(f"{i}: {line.strip()}")

print("\nREAD ONLY — NO FILES MODIFIED")
PY
