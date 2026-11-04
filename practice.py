cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
import zipfile, re

print("=== PZAAS ORIGINAL TRAINED WEIGHT DISCOVERY ===")

roots = [
    Path("artifacts/v1.472"),
    Path("artifacts/v1.472-max"),
    Path("/models/pzaas_max"),
]

pattern = re.compile(
    rb'(?:ptransformer|ptramsformer|transformer)\.(\d+)\.'
)

found = set()
checkpoints = []

for root in roots:
    if not root.exists():
        continue
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix == ".npy":
            found.update(int(x) for x in pattern.findall(
                p.name.encode()
            ))
        elif p.suffix in (".pt", ".pth", ".ckpt"):
            checkpoints.append(p)

print("EXPORTED WEIGHT LAYERS:", sorted(found))
print("CHECKPOINTS FOUND:", len(checkpoints))

for p in checkpoints:
    layers = set()
    try:
        if zipfile.is_zipfile(p):
            with zipfile.ZipFile(p) as z:
                for name in z.namelist():
                    if name.endswith(".pkl"):
                        layers.update(
                            int(x) for x in pattern.findall(z.read(name))
                        )
        else:
            layers.update(
                int(x) for x in pattern.findall(p.read_bytes())
            )
        print("CHECKPOINT:", p)
        print("TRAINED LAYERS:", sorted(layers))
    except Exception as e:
        print("INSPECTION ERROR:", type(e).__name__, str(e)[:150])

print("=== FINAL ===")
print("EXPECTED LAYERS:", list(range(6)))
print("MISSING EXPORTED LAYERS:",
      sorted(set(range(6)) - found))
print("ORIGINAL DS: UNCHANGED")
print("CTA / BPLAN: UNCHANGED")
print("NEXT: EXTRACT MISSING TRAINED WEIGHTS OR VERIFY MODEL DEPTH")
PY
