python3 - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_spawn_worker.py")
s = p.read_text()
old = "        return self.original_factory()"
assert s.count(old) == 1, "Unexpected factory code — no changes made"

new = '''        pipeline = self.original_factory()

        from pathlib import Path
        import sys
        base = Path(__file__).resolve().parent.parent
        for folder in (
            base,
            base / "cta_max",
            base.parent / "v1.168" / "core-artifact",
        ):
            if str(folder) not in sys.path:
                sys.path.insert(0, str(folder))

        from pipeline import pipeline as CTA
        from cta_max.live_cta_pipeline_bridge import attach_max
        from cta_worker_adapter import CTAWorkerAdapter

        pipeline.cta_adapter = CTAWorkerAdapter(CTA, attach_max)
        pipeline._cta_native_pipeline = True
        return pipeline'''

updated = s.replace(old, new)
compile(updated, str(p), "exec")
p.write_text(updated)
print("REAL CTA FACTORY WIRING: SYNTAX PASS")
PY
