python3 - <<'PY'
from pathlib import Path

root = Path("artifacts/v1.168/core-artifact")

print("ORIGINAL CTA MODEL ASSETS:")
for p in sorted(root.glob("model_0_*.pt")):
    print(f"{p.name}: {p.stat().st_size / 1048576:.1f} MB")
    config = root / "model_0_" / "config.json"
    print("  Associated config:", config.exists())

print("\nOTHER REQUIRED SOURCE ASSETS:")
for name in ["pipeline.py", "config.py", "tokenizer.json"]:
    matches = list(root.rglob(name))
    print(name, ":", len(matches), "found")

print("\nNO FILES CHANGED OR COPIED")
PY
