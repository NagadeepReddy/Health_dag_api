cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

echo "=== REAL CTA INPUT ==="
python3 - <<'PY'
import json
from pathlib import Path

p = Path("artifacts/v1.168-max/samples/sanity_input.json")
if not p.is_file():
    p = Path("artifacts/v1.167/samples/sanity_input.json")

print("File:", p)
if p.is_file():
    data = json.loads(p.read_text())
    print("Type:", type(data).__name__)
    print("Top-level keys:", list(data) if isinstance(data, dict) else "Array")
else:
    print("REAL INPUT NOT FOUND")
PY

echo "=== CTA SERVING INTEGRATION ==="
grep -nE 'register_cta_routes|add_api_route|/v1/invocations|/v2/cta|cta_adapter|async def|def ' \
  artifacts/v1.168-max/maxserve_cta_extension/cta_router.py \
  artifacts/v1.168-max/maxserve_cta_extension/cta_worker_adapter.py
