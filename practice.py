cd /application1/sajjna8/rt-pzaas-cta-offers-v1

python3 - <<'PY'
from pathlib import Path
from collections import Counter

base = Path("artifacts/v1.168-max")
reg = base / "maxserve_cta_extension/cta_architecture_registration.py"

print("=== CTA ARCHITECTURE WEIGHT SETTINGS ===")
for n, line in enumerate(reg.read_text().splitlines(), 1):
    if any(x in line for x in (
        "llama_arch", "default_encoding",
        "supported_encodings", "default_weights_format",
        "weight_adapters", "pipeline_model"
    )):
        print(f"{n}: {line.strip()}")

print("\n=== AVAILABLE MODEL WEIGHTS ===")
extensions = {".npy", ".npz", ".pt", ".pth", ".safetensors", ".gguf"}
for folder in [base / "cta_native_model", base / "cta_max"]:
    files = [p for p in folder.rglob("*") if p.is_file() and p.suffix in extensions] if folder.exists() else []
    print(folder, dict(Counter(p.suffix for p in files)))
    print("Samples:", [str(p.relative_to(base)) for p in files[:5]])
PY
