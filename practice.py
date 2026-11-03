cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
import json
from pathlib import Path

models = {
    "PZAAS": Path("artifacts/v1.472"),
    "CTA": Path("/application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168")
}

configs = {}
for name, root in models.items():
    matches = sorted(root.rglob("torch_model_params_base.json"))
    print(f"\n=== {name} BASE CONFIG ===")
    if not matches:
        print("Base config not found")
        continue
    p = matches[0]
    data = json.loads(p.read_text())
    if isinstance(data, list):
        data = data[0]
    configs[name] = data
    print("Path:", p)
    print("Keys:", sorted(data))

if len(configs) == 2:
    a, b = configs["PZAAS"], configs["CTA"]
    print("\n=== CONFIG DIFFERENCES ===")
    diff = 0
    for key in sorted(set(a) | set(b)):
        if a.get(key) != b.get(key):
            diff += 1
            if diff <= 35:
                print(f"{key}: PZAAS={str(a.get(key))[:90]} | CTA={str(b.get(key))[:90]}")
    print("Total differing parameters:", diff)
PY
