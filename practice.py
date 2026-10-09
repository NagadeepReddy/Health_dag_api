python - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/cta_max/run_transformer_max.py")
s = p.read_text()

old = '''np.load(
        "artifacts/v1.168-max/cta_max/sequence_weights/"
        "sequence_transformer.ptransformer.0.fn.norm1.g.npy"
    )'''

new = '''np.load(
        str(next(
            Path("artifacts/v1.168-max/cta_max/sequence_weights").glob("*norm1*g*.npy")
        ))
    )'''

assert old in s, "Expected hard-coded norm1 np.load not found"

# Path is needed by the new expression.
if "from pathlib import Path" not in s:
    s = "from pathlib import Path\\n" + s

p.write_text(s.replace(old, new, 1))

print("NORM1 REAL EXPORTED FILE AUTO-RESOLVED")
PY
