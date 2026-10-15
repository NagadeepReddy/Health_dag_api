python3 - <<'PY'
from pathlib import Path

files = {
    "WORKING": Path("artifacts/v1.168-max/cta_max/serve_max.py"),
    "CLEAN": Path("../cta-max-release-review/cta_max/serve_max.py"),
}

for label, file in files.items():
    root = file.resolve().parents[3]
    checkpoint = root / "artifacts/v1.168/core-artifact/model_0_base.pt"
    weights = root / "artifacts/v1.168-max/cta_max/grecbase_integration_weights"

    print(f"\n{label} PACKAGE")
    print("ROOT:", root)
    print("CHECKPOINT:", checkpoint.exists())
    print("EXPORTED WEIGHTS:", weights.exists())

print("\nNO FILES CHANGED")
PY
