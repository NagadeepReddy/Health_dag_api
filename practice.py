cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 -S -B - <<'PY'
from pathlib import Path
import ast

root = Path.cwd()
paths = [
    root / "artifacts/v1.168/core-artifact/pipeline.py",
    root / "artifacts/v1.168-max/maxserve_cta_extension/cta_worker_adapter.py",
    root / "artifacts/v1.168-max/cta_max/run_real_sanity_input_adapter.py",
]

print("=== ORIGINAL PREPROCESSING AND MODEL INPUT PATH ===")

for p in paths:
    print("\nFILE:", p)
    if not p.is_file():
        print("MISSING")
        continue

    lines = p.read_text().splitlines()
    tree = ast.parse("\n".join(lines), filename=str(p))

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if node.name not in (
            "predict_raw", "predict", "build_real_inputs",
            "initialize", "attach_max"
        ):
            continue

        print(f"FUNCTION: {node.name} | lines {node.lineno}-{node.end_lineno}")

        selected = set(range(
            node.lineno,
            min(node.lineno + 8, node.end_lineno + 1)
        ))

        for i in range(node.lineno, node.end_lineno + 1):
            s = lines[i - 1]
            if any(k in s for k in (
                "model_in", "model(", ".forward(",
                "predict(", "torch.save", "self.model",
                "attach_max", "preprocess"
            )):
                selected.update(range(
                    max(node.lineno, i - 2),
                    min(node.end_lineno, i + 2) + 1
                ))

        for i in sorted(selected)[:65]:
            print(f"{i}: {lines[i-1][:180]}")

print("\n=== EXISTING MODEL INPUT SAVE/CAPTURE CALLS ===")

found = 0
for base in (
    root / "artifacts/v1.168-max/cta_max",
    root / "artifacts/v1.168-max/maxserve_cta_extension",
):
    for p in base.rglob("*.py"):
        try:
            lines = p.read_text().splitlines()
            tree = ast.parse("\n".join(lines))
        except (OSError, SyntaxError, UnicodeError):
            continue

        for n in ast.walk(tree):
            if not isinstance(n, ast.Call):
                continue

            name = ast.unparse(n.func)
            if name not in (
                "torch.save", "register_forward_pre_hook",
                "register_forward_hook"
            ) and not name.endswith(".register_forward_pre_hook"):
                continue

            print(f"{p.relative_to(root)}:{n.lineno}: "
                  f"{lines[n.lineno-1].strip()[:150]}")
            found += 1
            if found >= 20:
                break

        if found >= 20:
            break

print("CAPTURE CALLS FOUND:", found)
print("FILES MODIFIED: NONE")
print("MAX STARTUP: NOT PERFORMED")
print("ORIGINAL DS CODE: UNCHANGED")
PY
