python3 - <<'PY'
from pathlib import Path
import re

root = Path("/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension")
f = root / "bplan_max_dev/parallel_transformer_block_2layers.py"
weights = root / "bplan_helper_weights_stage/grecbase_integration_weights"

assert weights.is_dir(), "STOP: weight directory missing"

src = f.read_text()
pattern = r"""(["'])(/application1/[^"']*/grecbase_integration_weights/)\1"""
matches = re.findall(pattern, src)

print("ABSOLUTE PATH REFERENCES:", len(matches))
assert matches, "STOP: no matching paths; file unchanged"

replacement = '(str(__import__("pathlib").Path(__file__).resolve().parents[1] / "bplan_helper_weights_stage" / "grecbase_integration_weights") + "/")'

updated = re.sub(pattern, lambda m: replacement, src)
compile(updated, str(f), "exec")
f.write_text(updated)

print("BPLAN PORTABLE WEIGHT PATH: FIXED")
print("BPLAN SYNTAX: PASS")
print("ORIGINAL DS AND CTA: UNCHANGED")
PY
