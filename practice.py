cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
python3 -B -S - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/cta_max/run_live_max_inference.py")
s = p.read_text()
backup = Path(str(p) + ".pre_memory_cleanup.bak")

checks = {
    "Backup exists": backup.is_file(),
    "Checkpoint cleanup installed": "del state" in s,
    "Garbage collection installed": "gc.collect()" in s,
    "Weight registry preserved": "weights_registry=weights_registry" in s,
    "MAX cache preserved": 'infer_max_live._max_model = model' in s,
    "Cleanup before compilation": s.index("del state") < s.index("model = session.load("),
}

for name, passed in checks.items():
    print(f"{name}: {'PASS' if passed else 'FAIL'}")

compile(s, str(p), "exec")
print("PYTHON SYNTAX: PASS")
print("MAX STARTUP: NOT PERFORMED")

if not all(checks.values()):
    raise SystemExit("STOP: validation failed")
PY
