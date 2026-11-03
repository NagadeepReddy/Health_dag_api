python3 - <<'PY'
import json
from pathlib import Path

root = Path("/application1/sajjna8/rt-pzai-bplan-v1")
files = {
    "PYTORCH": root / "artifacts/v1.113-max/maxserve_bplan_extension/bplan_pytorch_baseline.json",
    "NATIVE": Path("/tmp/bplan_response_trace.json"),
}

for name, file in files.items():
    data = json.loads(file.read_text())
    prediction = data.get("jsonData", {}).get("prediction", {})

    print(f"\n=== {name} ===")
    print("PREDICTION KEYS:", list(prediction))

    for key, value in prediction.items():
        if isinstance(value, list):
            ids = []
            def collect(x):
                if isinstance(x, dict):
                    if "propositionId" in x:
                        ids.append(str(x["propositionId"]))
                    for v in x.values():
                        collect(v)
                elif isinstance(x, list):
                    for v in x:
                        collect(v)
            collect(value)

            print(
                key,
                "LIST SIZE:", len(value),
                "RECOMMENDATION IDS:", len(ids),
                "UNIQUE:", len(set(ids))
            )
            print("IDS:", ids[:30])
PY
