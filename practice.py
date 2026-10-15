podman exec -i cta-max-serving-poc python3 -c '
import sys, json
from pipeline import pipeline as CTA

body = json.load(sys.stdin)
p = CTA()
p.load()
result = p.predict_raw(body)

prediction = result.get("jsonData", {}).get("prediction", {})
print("PYTORCH BASELINE: COMPLETED")
print("OFFER COUNT:", len(prediction.get("offerList", [])))
print("IS NEW RECOMMENDATION:", prediction.get("isNewRcmd"))
' < /tmp/cta_max_tiles_test.json
