cd /application1/sajjna8/rt-pzai-bplan-v1 && python3 - <<'PY'
import json
p = "artifacts/v1.113/samples/sanity_input.json"
data = json.load(open(p))

def inspect(x, path="root", depth=0):
    if depth > 5:
        return
    if isinstance(x, dict):
        print(path, "KEYS:", list(x.keys())[:20])
        for k, v in x.items():
            if isinstance(v, (dict, list)):
                inspect(v, path + "." + k, depth + 1)
    elif isinstance(x, list):
        print(path, "LIST LENGTH:", len(x))
        if x:
            inspect(x[0], path + "[0]", depth + 1)

inspect(data)
PY
