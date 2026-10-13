cd /application/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

python - <<'PY'
import ast
from pathlib import Path

roots = [
    Path("artifacts/v1.168/utils"),
    Path("artifacts/v1.168-max/cta_max"),
]
names = {"ParallelTransformerMAEP", "ParallelTransformerMAEPMAX"}
terms = (
    "item_pre", "v1_in", "embedding", "concat",
    "transformer", "pool", "valid_len", "seq_dense"
)

found = set()

for root in roots:
    for path in root.rglob("*.py"):
        try:
            source = path.read_text()
            tree = ast.parse(source)
        except (SyntaxError, UnicodeError, OSError):
            continue

        lines = source.splitlines()

        for cls in ast.walk(tree):
            if not isinstance(cls, ast.ClassDef):
                continue
            if cls.name not in names:
                continue

            found.add(cls.name)
            print(f"\n=== {cls.name} ===")
            print("FILE:", path)

            for method in cls.body:
                if not isinstance(method, ast.FunctionDef):
                    continue
                if method.name not in ("forward", "__call__"):
                    continue

                print("METHOD:", method.name)
                print(
                    "SIGNATURE:",
                    ast.unparse(method.args)
                )

                selected = set()
                for n in range(method.lineno, method.end_lineno + 1):
                    if any(t in lines[n - 1] for t in terms):
                        selected.update(
                            range(max(method.lineno, n - 1),
                                  min(method.end_lineno, n + 1) + 1)
                        )

                for n in sorted(selected):
                    print(f"{n}: {lines[n - 1]}")

print("\nCLASSES FOUND:", ", ".join(sorted(found)) or "NONE")
print("READ ONLY — ORIGINAL CODE AND WEIGHTS UNCHANGED")
PY
