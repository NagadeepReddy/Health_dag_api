
cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
python3 - <<'PY'
from pathlib import Path
p = Path("artifacts/v1.168/core-artifact")
print("MODEL DIRECTORY EXISTS:", p.is_dir())
if p.is_dir():
    for f in sorted(p.iterdir()):
        print(f.name, "DIR" if f.is_dir() else "FILE")
    cfg = p / "config.json"
    if cfg.is_file():
        import json
        data = json.loads(cfg.read_text())
        print("MODEL_TYPE:", data.get("model_type"))
        print("ARCHITECTURES:", data.get("architectures"))
    else:
        print("CONFIG.JSON: MISSING")
PY
