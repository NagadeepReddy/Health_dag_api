python3 - <<'PY'
from pathlib import Path

d = Path("artifacts/v1.168-max/maxserve_cta_extension")
base = d.parent

paths = [
    base.parent / "v1.168/core-artifact/pipeline.py",
    base / "cta_max/live_cta_pipeline_bridge.py",
    d / "cta_worker_adapter.py",
]

for p in paths:
    assert p.is_file(), f"MISSING: {p}"
    print("FOUND:", p)

worker = (d / "cta_spawn_worker.py").read_text()
launcher = (d / "cta_native_launcher.py").read_text()

for token in ("CTAFactoryWrapper", "install_cta_scheduler_hook",
              "pipeline.cta_adapter", "pipeline._cta_native_pipeline"):
    assert token in worker, f"MISSING WIRING: {token}"

assert "install_cta_spawn_entry()" in launcher
assert "run_module" in launcher

print("CTA NATIVE FACTORY WIRING: STATIC PASS")
PY
