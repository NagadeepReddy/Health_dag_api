podman exec -i cta-max-serving-poc python3 -c '
import json, sys, contextlib
from pipeline import pipeline as CTA

body = json.load(sys.stdin)
with contextlib.redirect_stdout(sys.stderr):
    p = CTA()
    p.load()
    result = p.predict_raw(body)

print(json.dumps(result, default=str))
' < /tmp/cta_max_tiles_test.json > /tmp/cta_pytorch_tiles_response.json && \
python3 - <<'PY'
import json

def prediction(path):
    r = json.load(open(path))
    return r["jsonData"]["prediction"]

pt = prediction("/tmp/cta_pytorch_tiles_response.json")
mx = prediction("/tmp/cta_max_tiles_response.json")

print("PYTORCH OFFERS:", len(pt.get("offerList", [])))
print("MAX OFFERS:", len(mx.get("offerList", [])))
print("OFFER LIST EXACT MATCH:", pt.get("offerList") == mx.get("offerList"))
print("RECOMMENDATION FLAG MATCH:", pt.get("isNewRcmd") == mx.get("isNewRcmd"))
PY
