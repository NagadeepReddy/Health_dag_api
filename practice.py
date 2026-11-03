ROOT=/application1/sajjna8/rt-pzai-bplan-v1

podman --root /application1/podman/storage \
  --runroot /run/containers/storage run --rm -i \
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

print("PYTORCH BASELINE: START", flush=True)

body = json.loads(Path("test_samples/test_sample_1.json").read_text())
p = pipeline()
print("LOADING ORIGINAL PYTORCH MODEL", flush=True)
p.load()
print("RUNNING ORIGINAL PREDICTION", flush=True)
response = p.predict_raw(body)

output = Path("/results/bplan_pytorch_final_same_request.json")
output.write_text(json.dumps(response, default=str))

print("FINAL PREDICTION KEYS:",
      list(response.get("jsonData", {}).get("prediction", {})))
print("PYTORCH BASELINE SAVED:", output)
print("PYTORCH SAME-REQUEST BASELINE: PASS", flush=True)
PY
