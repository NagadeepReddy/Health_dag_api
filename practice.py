ROOT=/application1/sajjna8/rt-pzai-bplan-v1
MAX=/tmp/bplan_verified_result.json
P=(podman --root /application1/podman/storage --runroot /run/containers/storage)

if [ ! -f "$MAX" ]; then
  echo "STOP: Saved MAX first-test response not found"
elif ! "${P[@]}" inspect bplan-debug >/dev/null 2>&1; then
  echo "STOP: BPLAN container not found"
else
  "${P[@]}" exec -i bplan-debug /opt/venv/bin/python - <<'PY'
import json
from pathlib import Path
from pipeline import pipeline

sample = Path("/workspace/artifacts/v1.113/core-artifact/test_samples/test_sample_1.json")
model = pipeline()
result = model.predict_raw(json.loads(sample.read_text()))
Path("/tmp/bplan_pytorch_first.json").write_text(json.dumps(result))
print("PYTORCH FIRST SAMPLE: SAVED", flush=True)
PY

  if [ $? -eq 0 ]; then
    "${P[@]}" cp bplan-debug:/tmp/bplan_pytorch_first.json /tmp/bplan_pytorch_first.json &&
    python3 - <<'PY'
import json
from pathlib import Path

def load(path):
    obj = json.loads(Path(path).read_text())
    data = obj.get("jsonData", {})
    if isinstance(data, str):
        data = json.loads(data)
    return obj, data

pt, p = load("/tmp/bplan_pytorch_first.json")
mx, m = load("/tmp/bplan_verified_result.json")

for label, obj in (("PYTORCH", pt), ("MAX", mx)):
    meta = obj.get("transactionMetadata", {})
    print(label, "INFERENCE RECORDED:",
          isinstance(meta, dict) and "inference" in meta)

print("BUSINESS OUTPUT EXACT MATCH:", p == m)

def normalize(value):
    if isinstance(value, dict):
        return {k: normalize(v) for k,v in value.items() if k != "order"}
    if isinstance(value, list):
        return sorted((normalize(v) for v in value),
                      key=lambda v: json.dumps(v, sort_keys=True))
    return value

print("BUSINESS MATCH IGNORING ORDER:",
      normalize(p) == normalize(m))
print("NUMERICAL TENSOR PARITY: NOT VERIFIED BY THIS TEST")
PY
  fi
fi
