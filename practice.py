ROOT=/application1/sajjna8/rt-pzai-bplan-v1
P=(podman --root /application1/podman/storage --runroot /run/containers/storage)

AVAILABLE=$(awk '/MemAvailable:/ {print int($2/1024)}' /proc/meminfo)
echo "AVAILABLE MEMORY: ${AVAILABLE} MiB"

if [ "$AVAILABLE" -lt 12000 ]; then
  echo "STOP: Insufficient free memory for separate PyTorch baseline"
else
  "${P[@]}" exec -i bplan-debug /opt/venv/bin/python - <<'PY'
import json, time
from pathlib import Path

from pipeline import pipeline

sample = Path(
    "/workspace/artifacts/v1.113/core-artifact/"
    "test_samples/test_sample_myplan_bundle.json"
)
expected_path = sample.with_name(
    "test_sample_myplan_bundle_output.json"
)

body = json.loads(sample.read_text())
expected = json.loads(expected_path.read_text())

print("ORIGINAL PYTORCH BASELINE: START", flush=True)
start = time.monotonic()

model = pipeline()
actual = model.predict_raw(body)

def lists(obj):
    data = obj["jsonData"]
    if isinstance(data, str):
        data = json.loads(data)
    return data["prediction"]["ctaList"]

def ids(group):
    return [str(x.get("propositionId")) for x in group]

for i, (e, a) in enumerate(zip(lists(expected), lists(actual))):
    print(f"LIST {i}")
    print(" EXPECTED:", ids(e))
    print(" PYTORCH: ", ids(a))

print("PYTORCH VS SAVED EXPECTED:",
      "MATCH" if lists(expected) == lists(actual) else "DIFFERENT")
print("BASELINE ELAPSED:", round(time.monotonic()-start, 1), "seconds")
PY
fi
