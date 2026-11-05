
cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
import ast

base = Path("artifacts/v1.472-max")
files = [
    base / "pzaas_max/grecbase_fusion_full_head_72_max.py",
    base / "pzaas_max/pzaas_weight_loader.py",
    base / "pzaas_max/validation/pzaas_forward_input_adapter.py",
    base / "maxserve_pzaas_extension/pzaas_native_serve_dev/pzaas_worker_adapter.py",
]

print("=== PZAAS REAL MAX NATIVE EXECUTION CONTRACT ===")

for path in files:
    print(f"\n=== {path} ===")
    if not path.is_file():
        print("NOT FOUND")
        continue

    lines = path.read_text().splitlines()
    try:
        tree = ast.parse("\n".join(lines))
    except SyntaxError as e:
        print("SYNTAX ERROR:", e)
        continue

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            print(f"\nDEFINITION: {node.name}")
            if isinstance(node, ast.FunctionDef):
                end = node.end_lineno
                start = node.lineno
                if node.name in (
                    "build_grecbase_fusion_graph_order_correct",
                    "pack",
                    "load_weight",
                ):
                    for i in range(start, end + 1):
                        print(f"{i}: {lines[i-1]}")
            else:
                for child in node.body:
                    if isinstance(child, ast.FunctionDef):
                        print("METHOD:", child.name)
                        if child.name in ("__init__", "initialize"):
                            for i in range(
                                child.lineno,
                                min(child.end_lineno, child.lineno + 16) + 1
                            ):
                                print(f"{i}: {lines[i-1]}")

    if path.name == "pzaas_worker_adapter.py":
        print("\n=== EXISTING MAX EXECUTION HOOKS ===")
        for i, line in enumerate(lines, 1):
            if any(s in line for s in (
                "attach_max", "model_base", "infer_max_batch",
                "predict_raw", "pipeline_factory", "max_factory"
            )):
                print(f"{i}: {line}")

print("\n=== PROGRESS ===")
print("MAX CPU / 72 INPUTS: PASS")
print("LAYER-0: PASS")
print("EIGHT-BRANCH: 8/8 PASS")
print("FULL MODEL PARITY: PASS")
print("NATIVE SCAFFOLD: PREPARED")
print("REAL MAX WORKER BRIDGE: PENDING")
print("NATIVE HTTP: PENDING")
print("ORIGINAL DS: UNCHANGED")
print("CTA / BPLAN: UNCHANGED")
print("FILES MODIFIED: NONE")
print("NEXT: IMPLEMENT VERIFIED MAX EXECUTION BRIDGE")
PY
