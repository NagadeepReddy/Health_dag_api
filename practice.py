python - <<'PY'
from pathlib import Path

base = Path("artifacts/v1.168-max/cta_max")

print("=== EXISTING REAL INPUT / REFERENCE ARTIFACTS ===")

terms = ("sanity", "real", "reference", "model_in", "input_bundle", "pytorch")

found = []
for p in base.rglob("*"):
    if p.is_file() and p.suffix in (".npz", ".pt", ".pth", ".npy"):
        if any(term in p.name.lower() for term in terms):
            found.append(p)

for p in sorted(found):
    print(p)

print("MATCHING FILES:", len(found))
print("READ ONLY — NOTHING MODIFIED")
PY
