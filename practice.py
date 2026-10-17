
python3 - <<'PY'
from runpy import run_path

path = "artifacts/v1.168-max/maxserve_cta_extension/cta_worker_adapter.py"
CTAWorkerAdapter = run_path(path)["CTAWorkerAdapter"]

calls = {"created": 0, "loaded": 0, "attached": 0}

class MockPipeline:
    def load(self):
        calls["loaded"] += 1

    def predict_raw(self, body):
        return {"received": body}

def factory():
    calls["created"] += 1
    return MockPipeline()

def attach(pipeline):
    calls["attached"] += 1

adapter = CTAWorkerAdapter(factory, attach)

assert adapter.predict({"request": 1}) == {"received": {"request": 1}}
assert adapter.predict({"request": 2}) == {"received": {"request": 2}}
assert calls == {"created": 1, "loaded": 1, "attached": 1}

print("CTA ADAPTER CONTRACT: PASS")
print("ONE-TIME INITIALIZATION: PASS")
print("JSON FORWARDING: PASS")
PY
