python3 - <<'PY'
import json

p = "/tmp/cta_max_tiles_response.json"
r = json.load(open(p))

print("RESPONSE TYPE:", type(r).__name__)
print("TOP-LEVEL KEYS:", list(r.keys()))
prediction = r.get("jsonData", {}).get("prediction", r.get("prediction", {}))
print("PREDICTION TYPE:", type(prediction).__name__)
if isinstance(prediction, dict):
    print("PREDICTION KEYS:", list(prediction.keys()))
    print("OFFER COUNT:", len(prediction.get("offerList", [])))
    print("IS NEW RECOMMENDATION:", prediction.get("isNewRcmd"))
PY
