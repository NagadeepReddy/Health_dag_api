
cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
import json

repo = Path.cwd()
pipeline = repo / "artifacts/v1.472/core-artifact/pipeline.py"

print("=== PZAAS NLP CONFIG RESOLUTION ===")

print("\n=== ORIGINAL CONFIG_DIRS ===")
if pipeline.exists():
    for n, line in enumerate(pipeline.read_text(errors="replace").splitlines(), 1):
        if "CONFIG_DIRS" in line or "self.dbert_path" in line:
            print(f"{n}: {line.strip()}")

roots = [
    repo / "artifacts/v1.472/config",
    Path("/mnt/all-MiniLM-L6-v2"),
    Path("/application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168/config"),
    Path("/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113/config"),
]

found = []

print("\n=== VERIFIED CONFIGURATION FILES ===")
for root in roots:
    print("\nDIRECTORY:", root)
    print("EXISTS:", root.is_dir())

    if not root.is_dir():
        continue

    for p in sorted(root.rglob("config.json")):
        try:
            data = json.loads(p.read_text())
            if not isinstance(data, dict):
                continue
            print("CONFIG:", p)
            print("MODEL TYPE:", data.get("model_type"))
            print("ARCHITECTURE:", data.get("architectures"))
            print("HIDDEN SIZE:", data.get("hidden_size"))
            print("LAYERS:", data.get("num_hidden_layers"))
            print("TOKENIZER JSON:", (p.parent / "tokenizer.json").exists())
            print("TOKENIZER CONFIG:", (p.parent / "tokenizer_config.json").exists())
            found.append(p)
        except (OSError, ValueError):
            continue

print("\n=== FINAL RESULTS ===")
print("CONFIG FILES FOUND:", len(found))
print("ORIGINAL DS: UNCHANGED")
print("CTA / BPLAN: UNCHANGED")
print("FILES MODIFIED: NONE")

if found:
    print("NEXT: VERIFY ORIGINAL MODEL CONFIG COMPATIBILITY")
else:
    print("BLOCKED: REQUIRED NLP CONFIG NOT LOCATED")
PY
