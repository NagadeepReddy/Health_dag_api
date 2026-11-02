python3 - <<'PY'
from pathlib import Path
import py_compile

f = Path("/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension/bplan_max_dev/parallel_transformer_block_2layers.py")

src = f.read_text()
old = '"/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension/bplan_helper_weights_stage/grecbase_integration_weights/"'
new = '(str(__import__("pathlib").Path(__file__).resolve().parents[1] / "bplan_helper_weights_stage" / "grecbase_integration_weights") + "/")'

assert src.count(old) == 1, "STOP: expected path not found exactly once"
updated = src.replace(old, new)
compile(updated, str(f), "exec")
f.write_text(updated)
py_compile.compile(str(f), doraise=True)

print("BPLAN PORTABLE WEIGHT PATH: FIXED")
print("BPLAN SYNTAX: PASS")
print("ORIGINAL DS AND CTA: UNCHANGED")
PY
