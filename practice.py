curl -fsS --max-time 15 http://127.0.0.1:18768/openapi.json \
| python3 -c '
import json,sys
paths=json.load(sys.stdin).get("paths",{})
print("BPLAN ROUTE:", "PASS" if "post" in paths.get("/bplan/predict",{}) else "MISSING")
print("BPLAN ENDPOINT:", "/bplan/predict")
'
