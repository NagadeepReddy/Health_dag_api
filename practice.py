cd /application/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

python3 - <<'PY'
from pathlib import Path
import ast
import shutil

p = Path("artifacts/v1.168-max/cta_max/grecbase_fusion_order_correct_max.py")
backup = p.with_name(p.name + ".before_duplicate_seq_dense_fix")

assert backup.is_file(), "STOP: Backup missing"

current = p.read_text()
previous = backup.read_text()

assert current.count("seq = postprocess(sx2)") == 1, "STOP: Current version unexpected"
assert previous.count("seq_raw = postprocess(sx2)") == 1, "STOP: Backup version unexpected"

ast.parse(previous)

shutil.copy2(backup, p)

print("RESTORE SUCCESS")
print("Previous MAX implementation restored")
print("Python syntax PASS")
print("Original backup preserved")
PY
