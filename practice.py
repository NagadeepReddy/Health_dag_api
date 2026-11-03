ROOT=/application1/sajjna8/rt-pzai-bplan-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage run --rm \
  --pull=never --network=host \
  -v "$ROOT:/workspace:ro" \
  -v /tmp:/results \
  -w /workspace/artifacts/v1.113/core-artifact \
  -e PYTHONPATH=/workspace/artifacts/v1.113/core-artifact:/workspace/artifacts/v1.113/utils/dependency-utils \
  --entrypoint /opt/venv/bin/python \
  localhost/cta-max-faiss:local -u - <<'PY'
import json
from pathlib import Path
from pipeline import pipeline

sample = Path("test_samples/test_sample_1.json")
body = json.loads(sample.read_text())

print("PYTORCH SAME-REQUEST BASELINE: START", flush=True)
p = pipeline()
p.load()
response = p.predict_raw(body)

output = Path("/results/bplan_pytorch_final_same_request.json")
output.write_text(json.dumps(response, default=str))

prediction = response.get("jsonData", {}).get("prediction", {})
print("PREDICTION KEYS:", list(prediction))
print("FINAL RESPONSE SAVED:", output)
print("PYTORCH SAME-REQUEST BASELINE: PASS")
PY
