python - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/cta_max/run_transformer_max.py")
s = p.read_text()

old = '''np.save(BASE + "/transformer_max_output.npy", max_out)'''
new = '''max_out = max_out.to_numpy()
np.save(BASE + "/transformer_max_output.npy", max_out)'''

if old not in s:
    raise SystemExit("TARGET SAVE LINE NOT FOUND - NO CHANGE MADE")

s = s.replace(old, new)
p.write_text(s)

compile(s, str(p), "exec")
print("MAX TENSOR OUTPUT CONVERSION FIXED")
print("RUNNER SYNTAX CLEAN")
PY
