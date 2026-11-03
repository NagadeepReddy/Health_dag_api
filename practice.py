cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
import json

r = Path("artifacts/v1.472")
s = (r/"core-artifact/pipeline.py").read_text().splitlines()

print("=== MODEL INITIALIZATION ===")
for i in range(1185, 1261):
    line = s[i-1].strip()
    if any(k in line for k in ("self.model_", "loadModel(", "loadBaseModel(", "loadTransferModel(", "model_suffix", "task_item_weights")):
        print(f"{i}: {line[:180]}")

print("\n=== ORIGINAL PZAAS SAMPLES ===")
for p in sorted((r/"samples").glob("*.json")):
    if "output" in p.name:
        continue
    try:
        d = json.loads(p.read_text())
        print(f"\n{p.name}")
        if not isinstance(d, dict):
            print("JSON type:", type(d).__name__)
            continue
        print("Top-level keys:", list(d)[:15])
        def inspect(x, depth=0):
            if depth > 5:
                return
            if isinstance(x, dict):
                for k,v in x.items():
                    if k in ("category", "pageContext", "query_intent") and isinstance(v, (str, int, float)):
                        print(f"  {k}: {str(v)[:100]}")
                    elif isinstance(v, (dict, list)):
                        inspect(v, depth+1)
            elif isinstance(x, list):
                for v in x[:2]:
                    inspect(v, depth+1)
        inspect(d)
    except Exception as e:
        print(p.name, type(e).__name__)
PY
