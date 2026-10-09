python - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/cta_max/context_head_deep.py")
s = p.read_text()

old = "deep_out = ops.maximum(deep_out, deep_out * 0.2)"
new = "deep_out = ops.relu(deep_out) - (ops.relu(-deep_out) * 0.2)"

if old not in s:
    raise SystemExit("Expected old LeakyReLU line not found - no changes made")

p.write_text(s.replace(old, new))
print("MAX LEAKYRELU FIXED")
PY
