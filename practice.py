cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 -S -B - <<'PY'
from pathlib import Path
import ast

bridge = Path("artifacts/v1.168-max/cta_max/live_cta_pipeline_bridge.py")
ds = Path("artifacts/v1.168/core-artifact/pipeline.py")

for path in (bridge, ds):
    assert path.is_file(), f"STOP: Missing {path}"

    source = path.read_text()
    lines = source.splitlines()
    tree = ast.parse(source)

    print("\n=== ", path.name, "===")

    if path == bridge:
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name == "MaxCTAInference":
                print("CLASS:", node.name)
                for i in range(node.lineno, node.end_lineno + 1):
                    print(f"{i}: {lines[i-1]}")
    else:
        fn = next(
            n for n in ast.walk(tree)
            if isinstance(n, ast.FunctionDef) and n.name == "inference"
        )
        print("ORIGINAL DS INFERENCE CONTRACT:")
        for i in range(fn.lineno, fn.end_lineno + 1):
            print(f"{i}: {lines[i-1]}")

print("\nCPU MAX BATCH-2: ALREADY PASS")
print("SCHEDULER DISPATCH MOCK: ALREADY PASS")
print("BATCH ADAPTER: MISSING")
print("FILES MODIFIED: NONE")
print("MAX STARTUP: NOT PERFORMED")
PY
