python - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/cta_max/context_head_deep.py")
s = p.read_text()

old = '''deep_out = ops.concat(deep_out, axis=-1)
        deep_out = self.deep_norm(deep_out)'''

new = '''deep_out = ops.concat(deep_out, axis=-1)

        # Original ContextHead: self.deep_act = nn.LeakyReLU(0.2)
        deep_out = ops.maximum(deep_out, deep_out * 0.2)

        deep_out = self.deep_norm(deep_out)'''

if old not in s:
    raise SystemExit("Expected deep block not found - no file changes made")

p.write_text(s.replace(old, new))
print("LEAKYRELU 0.2 ADDED")
PY
