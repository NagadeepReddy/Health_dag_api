cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
import ast, json

r = Path("artifacts/v1.472-max/pzaas_max")
m = json.loads((r/"pzaas_base_weights/manifest.json").read_text())

for name in ("grecbase_get_path_max.py", "nlp_bert_in_graph.py"):
    p = r/name
    print(f"\n=== {name} ===")
    lines = p.read_text().splitlines()

    for i, line in enumerate(lines, 1):
        if i <= 85:
            print(f"{i}: {line[:150]}")

print("\n=== RELEVANT PZAAS WEIGHTS ===")
for prefix in ("remove_tasks_", "nlp_encoder.", "nlp_dense_", "moe_"):
    keys = [k for k in m if k.startswith(prefix)]
    print(prefix, "COUNT:", len(keys))
    for key in keys[:8]:
        print(" ", key, m[key]["shape"])

print("\n=== GRAPH REFERENCES ===")
p = r/"grecbase_fusion_full_head_72_max.py"
for i, line in enumerate(p.read_text().splitlines(), 1):
    if "get_path" in line or "nlp_bert" in line:
        print(f"{i}: {line[:160]}")

print("\nREAD-ONLY INSPECTION: COMPLETE")
PY
