python3 - <<'PY'
import json
p = "artifacts/v1.168/samples/sanity_input.json"
data = json.load(open(p))

def check(x, path="$"):
    if isinstance(x, dict):
        page = x.get("page")
        if isinstance(page, dict) and str(page.get("name", "")).lower() == "gridwall_smartphones":
            print("MATCHING PAGE:", path)
            print("webinteraction_name:", repr(x.get("webinteraction_name")))
        if "webinteraction_name" in x:
            print("FIELD FOUND:", path, "TYPE:", type(x["webinteraction_name"]).__name__)
        for k, v in x.items():
            check(v, path + "." + k)
    elif isinstance(x, list):
        for i, v in enumerate(x):
            check(v, f"{path}[{i}]")

print("ROOT TYPE:", type(data).__name__)
check(data)
PY
