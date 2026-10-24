cd /application1/sajjna8/rt-pzaas-cta-offers-v1

python3 - <<'PY'
from pathlib import Path

base = Path("artifacts/v1.168-max/cta_max")
for name in ("run_real_sanity_input_adapter.py", "run_live_max_inference.py"):
    p = base / name
    s = p.read_text()
    old = 'BASE = Path("artifacts/v1.168-max/cta_max")'
    new = 'BASE = Path(__file__).resolve().parent'
    if old in s:
        p.write_text(s.replace(old, new, 1))
    elif new not in s:
        raise RuntimeError(f"Unexpected BASE definition: {p}")
    print(f"ABSOLUTE PATH FIX: {name} PASS")

print("ROTARY LOADER PATH FIX COMPLETE")
PY
