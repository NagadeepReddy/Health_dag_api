
cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
import ast

root = Path.cwd()
ext = root / "artifacts/v1.472-max/maxserve_pzaas_extension"
native = ext / "pzaas_native_serve_dev"

print("=== PZAAS NATIVE MODEL BRIDGE CONTRACT ===")

def show(path, limit):
    print("\nFILE:", path)
    if not path.is_file():
        print("NOT FOUND")
        return
    for i, line in enumerate(path.read_text().splitlines()[:limit], 1):
        print(f"{i}: {line}")

show(native / "pzaas_spawn_worker.py", 115)
show(native / "pzaas_architecture_registration.py", 100)

print("\n=== EXISTING CTA MODEL BRIDGE REFERENCE ===")

candidates = list(ext.rglob("cta_pipeline_model.py"))

cta_repo = Path(
    "/application1/sajjna8/rt-pzaas-cta-offers-v1"
)

if cta_repo.is_dir() and not candidates:
    candidates = list(
        (cta_repo / "artifacts/v1.168-max")
        .rglob("cta_pipeline_model.py")
    )

if candidates:
    show(candidates[0], 180)
else:
    print("CTA MODEL BRIDGE SOURCE: NOT LOCATED")

print("\n=== PZAAS MODEL CLASS AVAILABILITY ===")

found = []
for p in native.glob("*.py"):
    try:
        tree = ast.parse(p.read_text())
    except (SyntaxError, UnicodeError):
        continue
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            if node.name == "PZAASMAXModel":
                found.append(str(p))

print("PZAASMAXModel:", found or "NOT IMPLEMENTED IN NATIVE PACKAGE")

print("\n=== CURRENT PROGRESS ===")
print("MAX CPU: PASS")
print("LAYER-0 PARITY: PASS")
print("EIGHT-BRANCH PARITY: 8/8 PASS")
print("FULL-MODEL PARITY: PASS")
print("NATIVE SCAFFOLD: PREPARED")
print("PZAAS MODEL BRIDGE: PENDING")
print("NATIVE HTTP: NOT VERIFIED")
print("FILES MODIFIED: NONE")
print("ORIGINAL DS: UNCHANGED")
print("CTA / BPLAN: UNCHANGED")
print("NEXT: IMPLEMENT PZAAS-SPECIFIC MODEL BRIDGE")
PY
