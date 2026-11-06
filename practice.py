
cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
import hashlib
import json
import shutil

repo = Path.cwd()
stage = Path("/application1/sajjna8/PZAAS_MAX_CLEAN_STAGE_20261106")
model_root = repo / "artifacts/v1.472-max"

relative = Path(
    "artifacts/v1.472-max/validation/"
    "pzaas_forward_schema.json"
)
target = stage / relative

print("=== PZAAS RUNTIME SCHEMA RECOVERY ===")

if not stage.is_dir():
    raise SystemExit("STOP: Clean stage missing")

sources = sorted(
    p for p in model_root.rglob("pzaas_forward_schema.json")
    if p.is_file()
)

print("SOURCE MATCHES:", len(sources))
for path in sources:
    print(" ", path.relative_to(repo))

if not sources:
    print("\nSCHEMA NOT FOUND — NO FILES MODIFIED")
    print("=== SCHEMA REFERENCES ===")
    for path in sorted(model_root.rglob("*.py")):
        if "python_deps" in path.parts:
            continue
        for number, line in enumerate(
            path.read_text(errors="replace").splitlines(), 1
        ):
            if "pzaas_forward_schema" in line or "forward_schema" in line:
                print(
                    f"{path.relative_to(repo)}:{number}: "
                    f"{line.strip()[:200]}"
                )
    raise SystemExit(1)

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

hashes = {digest(path) for path in sources}

if len(hashes) != 1:
    raise SystemExit(
        "STOP: Multiple different schemas found. "
        "Manual source selection required."
    )

source = sources[0]

try:
    schema = json.loads(source.read_text())
except Exception as exc:
    raise SystemExit(f"STOP: Source JSON invalid: {exc}")

print("SOURCE JSON:", type(schema).__name__)

if target.exists():
    if digest(target) != digest(source):
        raise SystemExit("STOP: Existing staged schema differs")
    print("CLEAN SCHEMA: ALREADY CORRECT")
else:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    print("CLEAN SCHEMA: RESTORED")

if digest(target) != digest(source):
    raise SystemExit("STOP: Checksum mismatch")

print("SCHEMA SHA256: PASS")
print("CLEAN SCHEMA PATH:", target)
print("WORKING POC / ORIGINAL DS / CTA / BPLAN: UNCHANGED")
print("NEXT: CLEAN WORKER INITIALIZATION")
PY
