cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 -S -B - <<'PY'
from pathlib import Path
import ast

p = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029/run_distinct_batch2_live_max_inference.py")
assert p.is_file(), f"STOP: Missing {p}"

lines = p.read_text().splitlines()
tree = ast.parse("\n".join(lines))

print("=== EXISTING REAL MAX BATCH BACKEND ===")
print("FILE:", p)

functions = [
    n for n in ast.walk(tree)
    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
]

for fn in functions:
    if fn.name not in ("infer_max_live", "pack_two_requests"):
        continue

    print(f"\nFUNCTION: {fn.name} | LINES {fn.lineno}-{fn.end_lineno}")

    selected = set(range(fn.lineno, min(fn.lineno + 12, fn.end_lineno + 1)))

    for i in range(fn.lineno, fn.end_lineno + 1):
        s = lines[i-1]
        if any(x in s for x in (
            "pack_two_requests", "build_grecbase",
            "session.load", "model.execute",
            "runtime_inputs", "outputs", "results",
            "return ", "assert ", "reshape",
            "CTA_SECOND_MODEL_INPUT"
        )):
            selected.update(range(
                max(fn.lineno, i-2),
                min(fn.end_lineno, i+3)+1
            ))

    for i in sorted(selected):
        print(f"{i}: {lines[i-1][:180]}")

print("\n=== BATCH FUNCTION STATUS ===")
print("INFERENCE FUNCTION:", any(n.name == "infer_max_live" for n in functions))
print("FILES MODIFIED: NONE")
print("MAX STARTUP: NOT PERFORMED")
PY
