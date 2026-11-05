
cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
import ast
import shutil
import subprocess
from pathlib import Path

base = Path("artifacts/v1.472-max")
native = base / "maxserve_pzaas_extension/pzaas_native_serve_dev"

print("=== PZAAS NATIVE WORKER CONTRACT ===")

files = [
    "pzaas_spawn_worker.py",
    "pzaas_worker_adapter.py",
    "pzaas_native_worker_adapter.py",
    "pzaas_max_model_adapter.py",
]

for filename in files:
    path = native / filename
    if not path.is_file():
        print(filename, "NOT PRESENT")
        continue

    tree = ast.parse(path.read_text())
    print("\nFILE:", filename)

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module and (
                "pzaas" in node.module or
                node.module == "pipeline"
            ):
                print("IMPORT:", node.module,
                      [x.name for x in node.names])

        if isinstance(node, ast.ClassDef):
            for method in node.body:
                if not isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                if method.name in (
                    "__init__", "initialize", "attach_max",
                    "predict", "predict_batch", "__call__"
                ):
                    args = [a.arg for a in method.args.args]
                    print("METHOD:", node.name + "." + method.name,
                          "ARGS:", args)

        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if "WorkerAdapter" in node.func.id or "MAXModel" in node.func.id:
                print("CALL:", node.func.id,
                      "KEYWORDS:", [x.arg for x in node.keywords])

print("\n=== AVAILABLE NATIVE RUNTIME ===")
if shutil.which("podman"):
    p = subprocess.run(
        ["podman", "ps", "--format",
         "{{.Names}} | {{.Image}} | {{.Status}}"],
        capture_output=True, text=True
    )
    print(p.stdout.strip() or p.stderr.strip() or "No running containers")
else:
    print("Podman not available in this shell")

print("\n=== PROGRESS ===")
print("MAX CPU: PASS")
print("LAYER-0: PASS")
print("EIGHT BRANCHES: 8/8 PASS")
print("FULL MODEL PARITY: PASS")
print("FACTORY IMPORT PATH: CORRECTED")
print("NATIVE WORKER: PENDING RUNTIME VERIFICATION")
print("NATIVE HTTP 200: PENDING")
print("SOURCE MODIFICATIONS: NONE FROM THIS CHECK")
print("NEXT: RESOLVE WORKER INTERFACE AND RUN NATIVE HTTP")
PY
