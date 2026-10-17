
python3 - <<'PY'
from pathlib import Path
import ast

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_worker_adapter.py")

if p.exists():
    raise SystemExit("STOP — adapter already exists; not overwriting")

code = '''
class CTAWorkerAdapter:
    """Runtime adapter for the existing CTA + MAX pipeline."""

    def __init__(self, pipeline_factory, attach_max):
        self.pipeline_factory = pipeline_factory
        self.attach_max = attach_max
        self.pipeline = None

    def initialize(self):
        if self.pipeline is None:
            pipeline = self.pipeline_factory()
            pipeline.load()
            self.attach_max(pipeline)
            self.pipeline = pipeline
        return self.pipeline

    def predict(self, body):
        if not isinstance(body, dict):
            raise TypeError("CTA request must be a JSON object")
        return self.initialize().predict_raw(body)
'''

ast.parse(code)
p.write_text(code)
print("CTA WORKER ADAPTER CREATED — SYNTAX PASS")
print("Original DS files unchanged")
PY
