python3 - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/cta_max/live_cta_pipeline_bridge.py")
s = p.read_text()
target = "result = np.asarray(infer_max_live(model_in),dtype=np.float32)"

if target not in s:
    print("EXACT LINE NOT FOUND — no changes made")
elif "MAX INFERENCE EXECUTED:" in s:
    print("MARKER ALREADY EXISTS")
else:
    backup = p.with_suffix(".py.before_marker")
    backup.write_text(s)
    s = s.replace(
        target,
        target + '\n        print("MAX INFERENCE EXECUTED:", result.shape, flush=True)',
        1
    )
    compile(s, str(p), "exec")
    p.write_text(s)
    print("MAX EXECUTION MARKER: READY")
PY
