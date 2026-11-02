P=(podman --root /application1/podman/storage --runroot /run/containers/storage)

echo "=== BPLAN CONTAINER STATUS ==="
"${P[@]}" ps -a --filter name=bplan-debug

echo "=== LATEST BPLAN WORKER LOGS ==="
"${P[@]}" logs --tail 600 bplan-debug 2>&1 |
  grep -v -iE 'telemetry.modular.com|failed to send telemetry|/v1/metrics' |
  tail -160

echo "=== MYPLAN INPUT STRUCTURE ==="
python3 - <<'PY'
import json
from pathlib import Path

p = Path("/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113/core-artifact/test_samples")

for name in ("test_sample_1.json", "test_sample_myplan_bundle.json"):
    obj = json.loads((p / name).read_text())
    print(name)
    print("Top-level keys:", list(obj) if isinstance(obj, dict) else type(obj).__name__)
    if isinstance(obj, dict) and isinstance(obj.get("jsonData"), dict):
        print("jsonData keys:", list(obj["jsonData"])[:20])
PY
