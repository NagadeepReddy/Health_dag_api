python3 - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/cta_max/live_cta_pipeline_bridge.py")
s = p.read_text()

old = "    pipeline.model_atc = MaxCTAInference()\n"
new = (
    "    max_model = MaxCTAInference()\n"
    "    pipeline.model_base = max_model\n"
    "    pipeline.model_atc = max_model\n"
)

if old not in s:
    print("EXPECTED LINE NOT FOUND — no changes made")
else:
    updated = s.replace(old, new, 1)
    compile(updated, str(p), "exec")
    backup = p.with_suffix(".py.before_base_bridge")
    if backup.exists():
        print("BACKUP EXISTS — no changes made")
    else:
        backup.write_text(s)
        p.write_text(updated)
        print("MAX BASE + ATC BRIDGE: READY")
        print("ORIGINAL DS CODE: UNCHANGED")
PY
