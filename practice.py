curl -sS --max-time 10 http://127.0.0.1:18768/openapi.json \
  | python3 -c '
import json,sys
data=json.load(sys.stdin)
paths=data.get("paths",{})
assert "/bplan/predict" in paths, "BPLAN route missing"
assert "post" in paths["/bplan/predict"], "POST method missing"
print("BPLAN NATIVE HTTP ROUTE: PASS")
print("ENDPOINT: /bplan/predict")
print("SERVER: MODULAR MAX SERVE")
'
