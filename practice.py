python - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/cta_max/run_transformer_max.py")
s = p.read_text()

old = '''out = model.execute(x, pos)[0]
max_out = np.asarray(out)
max_out = np.asarray(max_out)
np.save(BASE + "/transformer_max_output.npy", max_out)'''

new = '''out = model.execute(x, pos)[0]
max_out = out._to_numpy()
np.save(BASE + "/transformer_max_output.npy", max_out)'''

assert old in s, "TARGET BLOCK NOT FOUND - NO CHANGE MADE"
p.write_text(s.replace(old, new))
print("MAX TENSOR _to_numpy FIX APPLIED")
PY

python -m py_compile artifacts/v1.168-max/cta_max/run_transformer_max.py && echo "RUNNER SYNTAX CLEAN"
