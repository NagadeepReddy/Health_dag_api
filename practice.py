python3 - <<'PY'
from pathlib import Path
import ast

p = Path(
    "/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029/"
    "native_batch2/cta_worker_adapter.py"
)

assert p.is_file(), "STOP: Adapter missing"
source = p.read_text()
tree = ast.parse(source)

print("=== CTA BATCH ROUTING CHECK ===")

checks = {
    "Batch method": "def predict_batch" in source,
    "Original preprocessing": "original_preprocess" in source,
    "MAX batch backend": "infer_max_batch" in source,
    "Normal model substitution": "pipeline.model_base = model" in source,
    "Simulation model substitution": "pipeline.model_atc = model" in source,
    "Original inference execution": "pipeline.predict_raw(body)" in source,
    "Preprocess cache": "cached_preprocess" in source,
    "Original model restoration": "pipeline.model_base = original_base" in source,
}

for name, result in checks.items():
    print(f"{name}: {'PRESENT' if result else 'MISSING'}")

print("SYNTAX: PASS")
print("NO FILES MODIFIED")
PY
