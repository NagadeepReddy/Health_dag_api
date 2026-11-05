
cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
import ast
from pathlib import Path

root = Path("artifacts/v1.472-max/maxserve_pzaas_extension")
native = root / "pzaas_native_serve_dev"
original = Path("artifacts/v1.472/core-artifact/pipeline.py")

print("=== PZAAS NATIVE WIRING CONTRACT ===")

targets = [
    ("FACTORY", native / "pzaas_spawn_worker.py"),
    ("WORKER", native / "pzaas_worker_adapter.py"),
    ("MODEL", native / "pzaas_max_model_adapter.py"),
    ("PIPELINE MODEL", native / "pzaas_pipeline_model.py"),
    ("REGISTRATION", native / "pzaas_architecture_registration.py"),
]

for label, path in targets:
    print(f"\n=== {label}: {path} ===")
    if not path.is_file():
        print("MISSING")
        continue

    source = path.read_text()
    tree = ast.parse(source)
    lines = source.splitlines()

    if label in ("FACTORY", "REGISTRATION"):
        for i, line in enumerate(lines[:100], 1):
            if line.strip():
                print(f"{i}: {line}")
    else:
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                print("CLASS:", node.name)
                for method in node.body:
                    if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        print("METHOD:", method.name,
                              "ARGS:", [a.arg for a in method.args.args])
        for i, line in enumerate(lines, 1):
            if any(x in line for x in (
                "attach_max", "max_factory", "pipeline_factory",
                "model_base", "def __call__", "def predict",
                "def initialize", "_pzaas_verified_pack",
                "PZAASMAXModel.pack", "return result",
                "return output"
            )):
                print(f"{i}: {line.strip()}")

print("\n=== ORIGINAL PIPELINE MODEL CALL ===")
if original.is_file():
    lines = original.read_text().splitlines()
    for i, line in enumerate(lines):
        if "self.model_base(" in line:
            for j in range(max(0, i-2), min(len(lines), i+23)):
                print(f"{j+1}: {lines[j]}")
else:
    print("ORIGINAL PIPELINE NOT FOUND")

print("\n=== NEXT ===")
print("WIRE REAL MAX FORWARD INTO NATIVE WORKER")
print("ORIGINAL DS: UNCHANGED")
print("CTA / BPLAN: UNCHANGED")
print("FILES MODIFIED: NONE")
PY
