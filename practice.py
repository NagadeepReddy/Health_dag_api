
cd /application1/sajjna8 && python3 - <<'PY'
import json
from pathlib import Path

root = Path("/application1/sajjna8")
proof = root / "max_shared_infra/analysis/shared_pzaas_e2e_20261106_205213.json"

print("=== PREVIOUSLY VERIFIED SHARED MAX REQUEST ===")

if not proof.is_file():
    print("STOP: Previous E2E evidence not found")
    raise SystemExit(1)

data = json.loads(proof.read_text())
print("PROOF:", proof)

def inspect(value, prefix="", depth=0):
    if depth > 5:
        return
    if isinstance(value, dict):
        for key, child in value.items():
            location = f"{prefix}.{key}" if prefix else key
            if isinstance(child, str) and any(
                term in key.lower()
                for term in ("request", "input", "fixture", "sample", "path")
            ):
                print(location, "=", child[:250])
            elif isinstance(child, (dict, list)):
                inspect(child, location, depth + 1)
    elif isinstance(value, list):
        for i, child in enumerate(value[:5]):
            inspect(child, f"{prefix}[{i}]", depth + 1)

print("EVIDENCE FIELDS:", list(data) if isinstance(data, dict) else type(data).__name__)
inspect(data)

print("\nORIGINAL SAMPLE FILES:")
samples = root / "PZAAS_MAX_CLEAN_HANDOFF_20261106/model/artifacts/v1.472/samples"
if samples.is_dir():
    for path in sorted(samples.glob("*.json")):
        print(path.name)
else:
    print("Samples not present in packaged model")

print("\nNO FILES MODIFIED")
print("NEXT: USE VERIFIED INPUT FOR SHARED MAX E2E")
PY
