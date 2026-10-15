python3 - <<'PY'
import json

data = json.load(open("/tmp/cta_max_smoketest.json"))

def check(obj, path="$"):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k.lower() in ("category", "contextinfo"):
                print(path + "." + k, repr(v)[:300])
            check(v, path + "." + k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            check(v, f"{path}[{i}]")

check(data)
PY
