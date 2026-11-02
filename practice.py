ROOT=/application1/sajjna8/rt-pzai-bplan-v1
P=(podman --root /application1/podman/storage --runroot /run/containers/storage)

"${P[@]}" exec -i bplan-debug /opt/venv/bin/python - <<'PY'
import json
from pathlib import Path
from pipeline import pipeline

sample = Path("/workspace/artifacts/v1.113/core-artifact/test_samples/test_sample_myplan_bundle.json")
model = pipeline()
result = model.predict_raw(json.loads(sample.read_text()))

Path("/tmp/bplan_pytorch_myplan.json").write_text(json.dumps(result))
print("PYTORCH BASELINE SAVED")
PY

"${P[@]}" cp \
  bplan-debug:/tmp/bplan_pytorch_myplan.json \
  /tmp/bplan_pytorch_myplan.json || exit 1

python3 - <<'PY'
import json
from pathlib import Path

def load(path):
    obj = json.loads(Path(path).read_text())
    data = obj["jsonData"]
    if isinstance(data, str):
        data = json.loads(data)
    return data["prediction"]["ctaList"], obj.get("transactionMetadata", {})

pt, pm = load("/tmp/bplan_pytorch_myplan.json")
mx, mm = load("/tmp/bplan_myplan_trace.json")

print("\n=== PYTORCH VS MAX PARITY ===")
print("PYTORCH INFERENCE:", "inference" in pm)
print("MAX INFERENCE:", "inference" in mm)

passed = len(pt) == len(mx)

for i in range(max(len(pt), len(mx))):
    a = pt[i] if i < len(pt) else []
    b = mx[i] if i < len(mx) else []

    ids_a = [x.get("propositionId") for x in a]
    ids_b = [x.get("propositionId") for x in b]

    exact = a == b
    same_ids = sorted(map(str, ids_a)) == sorted(map(str, ids_b))

    print(f"\nLIST {i}")
    print("PYTORCH COUNT:", len(a))
    print("MAX COUNT:", len(b))
    print("EXACT MATCH:", exact)
    print("SAME IDS:", same_ids)
    print("SAME ORDER:", ids_a == ids_b)

    passed &= exact

print("\nBUSINESS PARITY:", "PASS" if passed else "DIFFERENT")
print("FULL MODEL PARITY:",
      "NOT TESTED — FALLBACK" if "inference" not in pm and "inference" not in mm
      else "REQUIRES NUMERICAL VALIDATION")
PY
