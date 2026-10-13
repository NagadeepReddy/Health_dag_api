python - <<'PY'
import ast
from pathlib import Path

original = Path("artifacts/v1.168/utils/dependency-utils/models.py")
target = Path("artifacts/v1.168-max/cta_max/grecbase_get_path_max.py")

tree = ast.parse(original.read_text())
cls = next(n for n in ast.walk(tree)
           if isinstance(n, ast.ClassDef) and n.name == "GRecBase")
fn = next(n for n in cls.body
          if isinstance(n, ast.FunctionDef) and n.name == "get_path")

original_method = ast.get_source_segment(original.read_text(), fn)
assert "self.remove_tasks_act1(task_out)" in original_method
assert "remove_tasks_dense2" not in original_method

source = target.read_text()
old = 'return linear(hidden, "remove_tasks_dense2")'
new = 'return hidden'

assert source.count(old) == 1, "STOP: MAX source differs from expected"

backup = target.with_name(target.name + ".before_output_fix.bak")
assert not backup.exists(), "STOP: backup already exists"

backup.write_text(source)
updated = source.replace(old, new, 1)
ast.parse(updated)
target.write_text(updated)

print("ORIGINAL PYTORCH GET_PATH VERIFIED: PASS")
print("INCORRECT EXTRA MAX OUTPUT LAYER: REMOVED")
print("EXPECTED OUTPUT DIMENSION: 2048")
print("MAX SOURCE SYNTAX: PASS")
print("BACKUP:", backup)
print("ORIGINAL PYTORCH AND DS CODE: UNCHANGED")
PY
