cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
import re, zipfile

base = Path("artifacts/v1.472")
maxdir = Path("artifacts/v1.472-max/pzaas_max")

print("=== PZAAS ACTUAL MODEL DEPTH ===")

for name in ["model_0_base.pt", "model_0_sku.pt"]:
    p = base / "core-artifact" / name
    if not p.exists():
        print(name, "NOT FOUND")
        continue
    with zipfile.ZipFile(p) as z:
        data = b" ".join(
            z.read(n) for n in z.namelist()
            if n.endswith(".pkl")
        )
    layers = sorted(set(
        int(x) for x in re.findall(
            rb'ptransformer\.(\d+)\.', data
        )
    ))
    print(name, "TRAINED LAYERS:", layers)
    print("INFERRED DEPTH:", max(layers)+1 if layers else "UNKNOWN")

print("\n=== ORIGINAL DS DEPTH CONFIGURATION ===")
for p in [
    base / "core-artifact/pipeline.py",
    base / "utils/dependency-utils/models.py",
]:
    if not p.exists():
        continue
    lines = p.read_text(errors="replace").splitlines()
    for i, line in enumerate(lines):
        if re.search(r'num_layers|ptransformer\s*=|model_base\s*=', line):
            print(f"{p.name}:{i+1}: {line.strip()[:180]}")

print("\n=== ISOLATED MAX GRAPH DEPTH ===")
for p in maxdir.rglob("*.py") if maxdir.exists() else []:
    lines = p.read_text(errors="replace").splitlines()
    for i, line in enumerate(lines):
        if re.search(r'range\(6\)|num_layers\s*=\s*6|ptransformer\.[2-5]\.', line):
            print(f"{p.name}:{i+1}: {line.strip()[:180]}")

print("\nORIGINAL DS: UNCHANGED")
print("CTA / BPLAN: UNCHANGED")
print("FILES MODIFIED: 0")
print("NEXT: ALIGN MAX WITH VERIFIED PYTORCH DEPTH")
PY
