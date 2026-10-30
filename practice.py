PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
from pathlib import Path
import shutil
import re

root = Path("/application1/cta_max_true_batch_dev_20261028/batch2_candidate/cta_max")
graph = root / "grecbase_fusion_batch2_draft.py"
helper = root / "grecbase_aux_features_max.py"

old = "from cta_max.grecbase_aux_branches_max import grecbase_aux_features"
new = "from cta_max.grecbase_aux_features_max import grecbase_aux_features"

assert graph.is_file() and helper.is_file(), "STOP: Candidate files missing"

source = graph.read_text()
fixed = helper.read_text()

assert re.search(r"\[\s*2\s*,\s*256\s*\]", fixed)
assert re.search(r"\[\s*2\s*,\s*1\s*,\s*128\s*\]", fixed)

if old in source:
    assert source.count(old) == 1
    updated = source.replace(old, new)
    compile(updated, str(graph), "exec")
    compile(fixed, str(helper), "exec")

    backup = graph.with_name(graph.name + ".before_batch2_helper_fix")
    if not backup.exists():
        shutil.copy2(graph, backup)

    graph.write_text(updated)
    print("BATCH-2 HELPER IMPORT: FIXED")
    print("BACKUP: PRESERVED")
elif new in source:
    print("BATCH-2 HELPER IMPORT: ALREADY FIXED")
else:
    raise RuntimeError("STOP: Unexpected import; no change")

print("SYNTAX: PASS")
print("ORIGINAL DS: UNCHANGED")
print("ORIGINAL MAX: UNCHANGED")
print("CONTAINERS RESTARTED: NONE")
print("NEXT: Verify isolated runtime and native Batch-2")
PY
