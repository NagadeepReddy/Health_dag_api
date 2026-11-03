cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path

r = Path("artifacts/v1.472")
print("=== PZAAS TEST FIXTURES (EXCLUDING BPLAN) ===")
for p in sorted(r.rglob("*")):
    if (p.is_file() and p.suffix.lower() in
        (".json", ".jsonl") and
        "bplan" not in str(p).lower() and
        any(x in str(p).lower() for x in
            ("sample", "sanity", "test_input", "test_request"))):
        print(p)

print("\n=== BASE / SKU MODEL INITIALIZATION ===")
s = (r/"core-artifact/pipeline.py").read_text().splitlines()
for i, line in enumerate(s, 1):
    if ("self.model_base =" in line or
        "self.model_sku =" in line or
        "self.task_item_weights_sku =" in line):
        print(f"{i}: {line.strip()[:180]}")

print("\n=== MODEL CHECKPOINTS ===")
for p in sorted((r/"core-artifact").glob("model_0_*.pt")):
    print(p.name)
PY
