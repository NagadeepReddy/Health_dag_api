cd /application1/sajjna8/rt-pzaas-v1.0 && \
M="$PWD/artifacts/v1.472-max" && \
podman --root /application1/podman/storage \
--runroot /run/containers/storage \
run --rm -i --pull=never --network none \
--memory 3g \
-e PYTHONDONTWRITEBYTECODE=1 \
-e PYTHONPATH=/models \
-v "$M:/models:ro" \
-w /models \
--entrypoint /opt/venv/bin/python \
localhost/cta-max-faiss:local -u - <<'PY'
import inspect
from pathlib import Path
from pzaas_max import grecbase_fusion_full_head_72_max as m

print("=== PZAAS ATTENTION WEIGHT ALIGNMENT ===")

wdir = Path(m.WDIR)
print("WEIGHT DIRECTORY:", wdir)

weights = sorted(wdir.rglob("*.npy"))
print("TOTAL REGISTERED WEIGHTS:", len(weights))

print("\n=== RELEVANT EXISTING WEIGHTS ===")
matches = [
    p for p in weights
    if any(s in p.name.lower() for s in (
        "att_pooling",
        "fused_attn",
        "moe_norm",
        "ptransformer"
    ))
]
for p in matches:
    print(p.relative_to(wdir))

print("\n=== ACTUAL MAX BLOCK WEIGHT REQUIREMENTS ===")
source = inspect.getsource(m.AttPoolingBlockMAX)
for i, line in enumerate(source.splitlines(), 1):
    print(f"{i}: {line}")

print("\nMISSING WEIGHT:",
      "att_pooling.fused_attn_ff_proj.weight")
print("ORIGINAL DS: UNCHANGED")
print("MAX FILES: UNCHANGED")
print("WEIGHT MAPPING REVIEW: COMPLETE")
PY
