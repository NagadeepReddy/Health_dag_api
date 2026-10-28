cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
python3 -B -S - <<'PY'
from pathlib import Path
import shutil

p = Path("artifacts/v1.168-max/cta_max/run_live_max_inference.py")
backup = p.with_name(p.name + ".pre_memory_cleanup.bak")

s = p.read_text()
target = '    model = getattr(infer_max_live, "_max_model", None)'
replacement = '''    # Release temporary checkpoint references before MAX compilation.
    # weights_registry retains the required NumPy weight arrays.
    del state
    import gc
    gc.collect()

''' + target

if s.count(target) != 1:
    raise SystemExit("STOP: expected insertion point not unique")

if "del state\n    import gc" in s:
    raise SystemExit("STOP: cleanup already installed")

if backup.exists():
    raise SystemExit("STOP: backup already exists")

updated = s.replace(target, replacement, 1)
compile(updated, str(p), "exec")

if shutil.disk_usage("/application1").free < 1024**3:
    raise SystemExit("STOP: insufficient disk space")

shutil.copy2(p, backup)
p.write_text(updated)

print("MAX TEMPORARY CHECKPOINT CLEANUP: INSTALLED")
print("BACKUP:", backup)
print("PYTHON SYNTAX: PASS")
print("DS CODE: UNCHANGED")
print("MAX STARTUP: NOT PERFORMED")
PY
