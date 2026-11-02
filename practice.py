python3 - <<'PY'
from pathlib import Path
import json

root = Path("/application1/sajjna8/rt-pzai-bplan-v1")
samples = root / "artifacts/v1.113/core-artifact/test_samples"

print("=== ORIGINAL BPLAN TEST FILES ===")
for p in sorted(samples.glob("*.json")):
    print(p.name)

print("\n=== AVAILABLE PROJECTION PARITY DATA ===")
for name in (
    "bplan_transfer_input.npy",
    "bplan_transfer_weight.npy",
    "bplan_transfer_reference.npy"
):
    p = Path("/bplan_out") / name
    print(name, "FOUND" if p.is_file() else "MISSING")

print("\n=== SAVED MAX HTTP RESPONSE ===")
p = Path("/tmp/bplan_verified_result.json")
if p.is_file():
    obj = json.loads(p.read_text())
    print("Type:", type(obj).__name__)
    print("Keys:", list(obj)[:15] if isinstance(obj, dict) else "not an object")
else:
    print("NOT FOUND")

print("\n=== POSSIBLE PYTORCH BASELINE OUTPUTS ===")
for p in sorted(samples.glob("*output*.json")):
    try:
        obj = json.loads(p.read_text())
        print(p.name, "| Keys:",
              list(obj)[:12] if isinstance(obj, dict) else type(obj).__name__)
    except Exception as e:
        print(p.name, "|", type(e).__name__)
PY
