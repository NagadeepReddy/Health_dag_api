python3 - <<'PY'
from pathlib import Path

root = Path("/application1/sajjna8/rt-pzai-bplan-v1")
p = root / "artifacts/v1.113-max/maxserve_bplan_extension/bplan_max_dev/grecbase_fusion_full_head_72_max.py"

source = p.read_text()

old_dir = 'WDIR = Path(__file__).parent / "grecbase_integration_weights"'
old_checkpoint = '"artifacts/v1.168/core-artifact/model_0_base.pt"'

assert source.count(old_dir) == 1, "STOP: weight directory pattern differs"
assert source.count(old_checkpoint) == 1, "STOP: checkpoint pattern differs"

new_dir = '''WDIR = Path(__file__).resolve().parent.parent / "max_weights"
BPLAN_BASE_PT = Path(__file__).resolve().parents[3] / "artifacts/v1.113/core-artifact/base_model.pt"'''

updated = source.replace(old_dir, new_dir)
updated = updated.replace(old_checkpoint, "str(BPLAN_BASE_PT)")

assert (root / "artifacts/v1.113/core-artifact/base_model.pt").is_file()
assert (p.parent.parent / "max_weights/manifest.json").is_file()

p.write_text(updated)

print("BPLAN MAX GRAPH WEIGHT PATHS: UPDATED")
print("BPLAN CHECKPOINT: CONFIGURED")
print("ORIGINAL CTA SOURCE: UNCHANGED")
print("ORIGINAL BPLAN DS CODE: UNCHANGED")
PY
