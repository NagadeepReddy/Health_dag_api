python3 - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/cta_max/run_live_max_inference.py")
s = p.read_text()

old_session = "session = InferenceSession(devices=[device])"
new_session = """session = getattr(infer_max_live, "_max_session", None)
    if session is None:
        session = InferenceSession(devices=[device])"""

old_load = """model = session.load(
        graph, weights_registry=weights_registry
    )"""
new_load = """model = getattr(infer_max_live, "_max_model", None)
    if model is None:
        model = session.load(
            graph, weights_registry=weights_registry
        )
        infer_max_live._max_session = session
        infer_max_live._max_model = model"""

assert s.count(old_session) == 1, "STOP: session code differs"
assert s.count(old_load) == 1, "STOP: load code differs"
assert p.with_name(p.name + ".before_persistent_max").exists(), "STOP: backup missing"

updated = s.replace(old_session, new_session).replace(old_load, new_load)
compile(updated, str(p), "exec")
p.write_text(updated)
print("PASS: Persistent MAX model caching added; syntax valid")
PY
