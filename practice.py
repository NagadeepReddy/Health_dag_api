cd /application/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

python - <<'PY'
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

base = Path("artifacts/v1.168-max/cta_max")

names = [
    "grecbase_fusion_order_correct_max.py",
    "sequence_transformer_max.py",
    "sequence_postprocess_max.py",
    "parallel_transformer_block.py",
    "run_real_sanity_max_full.py",
]

required = {
    "grecbase_fusion_order_correct_max.py",
    "sequence_transformer_max.py",
    "run_real_sanity_max_full.py",
}

missing = [n for n in required if not (base / n).is_file()]
if missing:
    raise SystemExit(f"STOP: Missing required files: {missing}")

output = Path("cta_max_source_review.zip")

with ZipFile(output, "w", ZIP_DEFLATED) as z:
    for name in names:
        p = base / name
        if p.is_file():
            z.write(p, arcname=name)

print("SOURCE PACKAGE READY:", output.resolve())
print("NO MODEL CODE, PYTORCH CODE, OR WEIGHTS CHANGED")
PY
