cat > artifacts/v1.168-max/cta_max/serve_max.py <<'PY'
import sys
from pathlib import Path
from fastapi import FastAPI

root = Path(__file__).resolve().parents[3]
sys.path[:0] = [
    str(root / "artifacts/v1.168/core-artifact"),
    str(root / "artifacts/v1.168-max"),
    str(root / "artifacts/v1.168-max/cta_max"),
]

from pipeline import pipeline as CTA
from cta_max.live_cta_pipeline_bridge import attach_max

app = FastAPI()
model = None

@app.on_event("startup")
def startup():
    global model
    p = CTA()
    p.load()
    model = attach_max(p)

@app.get("/health")
def health():
    return {"status": "ready" if model is not None else "loading"}

@app.post("/predict")
def predict(body: dict):
    return model.predict_raw(body)
PY

python3 -m py_compile artifacts/v1.168-max/cta_max/serve_max.py && echo "MAX SERVING ADAPTER: CREATED"
