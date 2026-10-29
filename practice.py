python3 - <<'PY'
from pathlib import Path
import ast

p = Path(
    "/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029/"
    "native_batch2/cta_worker_adapter.py"
)

source = p.read_text()
tree = ast.parse(source)

method = next(
    n for n in ast.walk(tree)
    if isinstance(n, ast.FunctionDef)
    and n.name == "predict_batch"
)

checks = {
    "BATCH METHOD": True,
    "PREPROCESS CACHE": "cached_preprocess" in source,
    "ORIGINAL PREPROCESS RESTORE":
        "pipeline.preprocess = original_preprocess" in source,
    "MODEL RESTORE":
        "pipeline.model_base = original_base" in source
        and "pipeline.model_atc = original_atc" in source,
    "MULTI-INFERENCE RESTRICTION":
        "model.calls != 1" in source,
}

for name, result in checks.items():
    print(f"{name}: {'PRESENT' if result else 'MISSING'}")

print("SYNTAX: PASS")
print("NO FILES MODIFIED")
PY
