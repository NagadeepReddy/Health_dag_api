cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
import json

r = Path("artifacts/v1.472-max/pzaas_max")
m = json.loads((r/"pzaas_base_weights/manifest.json").read_text())

key = "sequence_transformer.item_embedding.weight"
shape = m[key]["shape"]
vocab = shape[0]

cfg = json.loads(
    Path("artifacts/v1.472/config/torch_model_params_base.json").read_text()
)
if isinstance(cfg, list):
    cfg = cfg[0]

assert vocab == cfg["seq_dim"], "PZAAS vocabulary mismatch"
assert vocab == 10030, "Unexpected checkpoint vocabulary"

p = r/"sequence_transformer_max.py"
s = p.read_text()

old = "vocab_size=10727"
new = f"vocab_size={vocab}"

if s.count(old) == 2:
    updated = s.replace(old, new)
    compile(updated, str(p), "exec")
    p.write_text(updated)
    print("PZAAS SEQUENCE VOCABULARY: UPDATED")
elif s.count(new) == 2:
    print("PZAAS SEQUENCE VOCABULARY: ALREADY CORRECT")
else:
    raise SystemExit("STOP: Unexpected vocabulary definitions")

print("PZAAS VOCAB SIZE:", vocab)

files = sorted(r.glob("*.py"))
for file in files:
    compile(file.read_text(), str(file), "exec")
print("GRAPH PYTHON SYNTAX: PASS", len(files), "files")

print("\n=== REMAINING LEGACY REFERENCES ===")
count = 0
for file in files:
    for i, line in enumerate(file.read_text().splitlines(), 1):
        if "v1.168" in line or "cta_max/" in line:
            print(f"{file.name}:{i}: {line.strip()[:120]}")
            count += 1

print("LEGACY REFERENCE COUNT:", count)
print("OTHER DIMENSIONS / MAX COMPILATION: PENDING")
print("ORIGINAL DS: UNCHANGED")
PY
