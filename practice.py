python3 - <<'PY'
from pathlib import Path
import re

root = Path("/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension")
f = root / "bplan_max_dev/sequence_postprocess_max.py"
weights = root / "bplan_helper_weights_stage/grecbase_integration_weights"

assert f.is_file() and weights.is_dir(), "STOP: required files missing"
assert (weights / "out_norm1_g.npy").is_file(), "STOP: weight missing"

src = f.read_text()
pattern = r"""(["'])(/application1/[^"']*/grecbase_integration_weights/?)(\1)"""

def replace(match):
    trailing = match.group(2).endswith("/")
    expression = (
        '(str(__import__("pathlib").Path(__file__).resolve().parents[1] '
        '/ "bplan_helper_weights_stage" / "grecbase_integration_weights"))'
    )
    return f'({expression} + "/")' if trailing else expression

updated, count = re.subn(pattern, replace, src)
assert count > 0, "STOP: path structure differs; unchanged"
compile(updated, str(f), "exec")
f.write_text(updated)

print("BPLAN POSTPROCESS PORTABLE PATH: PASS")
print("REFERENCES FIXED:", count)
print("ORIGINAL DS AND CTA: UNCHANGED")
PY
