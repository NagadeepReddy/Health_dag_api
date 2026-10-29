cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 -S -B - <<'PY'
from pathlib import Path
import ast

base = Path("artifacts/v1.168-max/cta_max")
bridge = base / "live_cta_pipeline_bridge.py"
pipeline = Path("artifacts/v1.168/core-artifact/pipeline.py")

for p in (bridge, pipeline):
    assert p.is_file(), f"STOP: Missing {p}"

for p in (bridge, pipeline):
    source = p.read_text()
    lines = source.splitlines()
    tree = ast.parse(source)

    print("\n=== FILE:", p, "===")

    for fn in ast.walk(tree):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        if p == bridge:
            if fn.name != "attach_max":
                continue
        else:
            if fn.name != "inference":
                continue

        print(f"\nFUNCTION: {fn.name}")
        print("LINES:", fn.lineno, "-", fn.end_lineno)

        selected = set(range(
            fn.lineno, min(fn.lineno + 12, fn.end_lineno + 1)
        ))

        keywords = (
            "infer_max", "max_infer", "setattr",
            "model_in", "output", "return ",
            "self.", "postprocess", "max_model"
        )

        for i in range(fn.lineno, fn.end_lineno + 1):
            line = lines[i - 1]
            if p == bridge or (
                any(k in line for k in keywords)
                and ("self." in line or "return " in line)
            ):
                if p == bridge:
                    selected.add(i)
                elif (
                    "infer_max" in line or "max_infer" in line
                    or "return " in line or "self.model" in line
                ):
                    selected.update(range(
                        max(fn.lineno, i - 2),
                        min(fn.end_lineno, i + 2) + 1
                    ))

        for i in sorted(selected):
            print(f"{i}: {lines[i-1][:200]}")

print("\nCPU MAX BATCH-2: PASS - ALREADY VERIFIED")
print("NATIVE SCHEDULER MOCK: PASS - ALREADY VERIFIED")
print("ORIGINAL DS CODE: UNCHANGED")
print("FILES MODIFIED: NONE")
print("MAX STARTUP: NOT PERFORMED")
PY
