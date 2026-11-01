python3 - <<'PY'
from pathlib import Path
import re

p = Path("/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension/bplan_max_dev/grecbase_fusion_full_head_72_max.py")
src = p.read_text()

repo = p.resolve().parents[4]
base = repo / "artifacts/v1.113/core-artifact/base_model.pt"
weights = p.parent.parent / "max_weights/manifest.json"

assert base.is_file(), f"Missing BPLAN checkpoint: {base}"
assert weights.is_file(), f"Missing BPLAN weights: {weights}"

updated, n1 = re.subn(
    r"""(?m)^WDIR\s*=\s*Path\(__file__\)\.parent\s*/\s*['"]grecbase_integration_weights['"]\s*$""",
    """WDIR = Path(__file__).resolve().parent.parent / "max_weights"
BPLAN_BASE_PT = Path(__file__).resolve().parents[4] / "artifacts/v1.113/core-artifact/base_model.pt" """.rstrip(),
    src
)

updated, n2 = re.subn(
    r"""['"]artifacts/v1\.168/core-artifact/model_0_base\.pt['"]""",
    "str(BPLAN_BASE_PT)",
    updated
)

assert n1 == 1 and n2 == 1, f"STOP: unexpected matches WDIR={n1}, checkpoint={n2}"

compile(updated, str(p), "exec")
p.write_text(updated)

print("BPLAN MAX WEIGHT PATHS: PASS")
print("BPLAN CHECKPOINT:", base)
print("BPLAN MAX WEIGHTS:", weights.parent)
print("ORIGINAL DS AND CTA: UNCHANGED")
PY
