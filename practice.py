REPO=/application1/sajjna8/rt-pzai-bplan-v1
PIPE="$REPO/artifacts/v1.113/core-artifact/pipeline.py"
SAMPLES="$REPO/artifacts/v1.113/core-artifact/test_samples"

echo "=== ORIGINAL JSON ENTRY ==="
sed -n '3933,4015p' "$PIPE"

echo "=== ORIGINAL POSTPROCESS ==="
sed -n '2608,2655p' "$PIPE"

echo "=== REAL JSON SAMPLE STRUCTURE ==="
SAMPLES="$SAMPLES" python3 - <<'PY'
import json, os
from pathlib import Path

for path in sorted(Path(os.environ["SAMPLES"]).glob("test_sample_[12].json")):
    data = json.loads(path.read_text())
    print(path.name, "TYPE:", type(data).__name__)
    if isinstance(data, dict):
        print("TOP-LEVEL KEYS:", list(data))
        for k, v in data.items():
            print(" ", k, ":", type(v).__name__,
                  "KEYS:", list(v)[:15] if isinstance(v, dict) else "")
PY
